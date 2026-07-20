from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, Never

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from braincrew.ax_http_adapter import (
    AxCanonicalRequest,
    AxHttpAdapter,
    AxHttpAdapterConfig,
    AxHttpFailure,
    AxRequestContext,
    CapabilityManifest,
    CorpusCapability,
    HttpAttempt,
    OperationCapability,
    OperationName,
    load_ax_http_contract,
)
from braincrew.dataset_registry import DatasetValidationReport
from braincrew.digest import canonical_digest
from braincrew.repository import RepositoryState, capture_repository_state


class StrictLiveContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LiveRunConfiguration(StrictLiveContract):
    top_k: Literal[5]
    evidence_limit: Literal[3, 5]


class LiveVerificationPlan(StrictLiveContract):
    candidate_plan_version: Literal["candidate-plan-v1"]
    baseline: LiveRunConfiguration
    candidate: LiveRunConfiguration


class LiveDatasetIdentity(StrictLiveContract):
    id: str
    version: str
    digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    verification_case_count: Literal[30]


class LiveRepositoryEvidence(StrictLiveContract):
    commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    dirty_worktree: bool


class LiveCorpusIdentity(StrictLiveContract):
    id: str
    version: str
    digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class LivePromptIdentity(StrictLiveContract):
    id: str
    digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class _ImmutableLiveDict[ValueT](dict[str, ValueT]):
    def _reject_mutation(self, *args: object, **kwargs: object) -> Never:
        del args, kwargs
        raise TypeError("live preflight mappings are immutable")

    __setitem__ = _reject_mutation
    __delitem__ = _reject_mutation
    __ior__ = _reject_mutation
    clear = _reject_mutation
    pop = _reject_mutation
    popitem = _reject_mutation
    setdefault = _reject_mutation
    update = _reject_mutation


def _freeze_live_value(value: object) -> object:
    if isinstance(value, dict):
        return _ImmutableLiveDict({key: _freeze_live_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_live_value(item) for item in value)
    return value


class LiveModelIdentity(StrictLiveContract):
    provider: str
    name: str
    parameters: dict[str, object]

    @field_validator("parameters")
    @classmethod
    def freeze_parameters(cls, parameters: dict[str, object]) -> dict[str, object]:
        return _ImmutableLiveDict(
            {key: _freeze_live_value(value) for key, value in parameters.items()}
        )


class LiveExecutionIdentity(StrictLiveContract):
    corpus: LiveCorpusIdentity
    prompt: LivePromptIdentity
    model: LiveModelIdentity
    evaluator_versions: dict[str, str]
    adapter_versions: dict[str, str]

    @field_validator("evaluator_versions", "adapter_versions")
    @classmethod
    def freeze_version_maps(cls, versions: dict[str, str]) -> dict[str, str]:
        return _ImmutableLiveDict(versions)


class LiveCapabilityEvidence(StrictLiveContract):
    schema_version: Literal["ax-capability-manifest-v1"]
    adapter_version: Literal["ax-sut-http-v1"]
    sut_repository: str
    sut_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    request: AxCanonicalRequest
    readiness_status: str
    dependencies: dict[str, str]
    corpus: CorpusCapability
    operations: dict[OperationName, OperationCapability]
    attempts: tuple[HttpAttempt, ...]

    @field_validator("dependencies", "operations")
    @classmethod
    def freeze_capability_maps[ValueT](
        cls,
        values: dict[str, ValueT],
    ) -> dict[str, ValueT]:
        return _ImmutableLiveDict(values)


class LivePreflightBlocker(StrictLiveContract):
    code: str
    category: Literal["access", "capability", "configuration", "provenance"]
    detail: str
    required_action: str


class LiveVerificationPreflightArtifact(StrictLiveContract):
    schema_version: Literal["live-verification-preflight-artifact-v1"]
    preflight_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    state: Literal["READY", "BLOCKED"]
    dataset: LiveDatasetIdentity
    plan: LiveVerificationPlan
    evaluation_plane: LiveRepositoryEvidence
    sut: LiveRepositoryEvidence | None
    execution_identity: LiveExecutionIdentity | None
    capability_manifest: LiveCapabilityEvidence | None
    blockers: tuple[LivePreflightBlocker, ...]
    logical_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


_REQUIRED_LIVE_SETTINGS: tuple[tuple[str, str, str], ...] = (
    ("AX_BASE_URL", "LIVE_BASE_URL_MISSING", "provide the authorized live AX base URL"),
    (
        "AX_REPOSITORY",
        "LIVE_SUT_REPOSITORY_MISSING",
        "provide the local pinned AX repository path",
    ),
    ("AX_TENANT_ID", "LIVE_TENANT_ID_MISSING", "provide an authorized synthetic tenant UUID"),
    ("AX_USER_ID", "LIVE_USER_ID_MISSING", "provide the evaluation user identity"),
    ("AX_ROLES", "LIVE_ROLES_MISSING", "provide the authorized AX role set"),
    ("AX_CORPUS_ID", "LIVE_CORPUS_ID_MISSING", "provide the frozen public corpus identity"),
    (
        "AX_CORPUS_VERSION",
        "LIVE_CORPUS_VERSION_MISSING",
        "provide the frozen public corpus version",
    ),
    (
        "AX_CORPUS_DIGEST",
        "LIVE_CORPUS_DIGEST_MISSING",
        "provide the frozen public corpus digest",
    ),
    ("AX_PROMPT_ID", "LIVE_PROMPT_ID_MISSING", "provide the frozen prompt identity"),
    ("AX_PROMPT_HASH", "LIVE_PROMPT_HASH_MISSING", "provide the frozen prompt digest"),
    (
        "AX_MODEL_PROVIDER",
        "LIVE_MODEL_PROVIDER_MISSING",
        "provide the authorized model provider identity",
    ),
    ("AX_MODEL_NAME", "LIVE_MODEL_NAME_MISSING", "provide the frozen model identity"),
    (
        "AX_MODEL_PARAMETERS_JSON",
        "LIVE_MODEL_PARAMETERS_MISSING",
        "provide the frozen model parameter document",
    ),
)

_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _reject_nonfinite_json(value: str) -> Never:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _build_execution_identity(
    environment: Mapping[str, str],
) -> tuple[LiveExecutionIdentity | None, tuple[LivePreflightBlocker, ...]]:
    identity_names = {
        "AX_CORPUS_ID",
        "AX_CORPUS_VERSION",
        "AX_CORPUS_DIGEST",
        "AX_PROMPT_ID",
        "AX_PROMPT_HASH",
        "AX_MODEL_PROVIDER",
        "AX_MODEL_NAME",
        "AX_MODEL_PARAMETERS_JSON",
    }
    if any(not environment.get(name, "").strip() for name in identity_names):
        return None, ()
    blockers: list[LivePreflightBlocker] = []
    corpus_digest = environment["AX_CORPUS_DIGEST"].strip()
    if _DIGEST_PATTERN.fullmatch(corpus_digest) is None:
        blockers.append(
            LivePreflightBlocker(
                code="LIVE_CORPUS_DIGEST_INVALID",
                category="configuration",
                detail="AX_CORPUS_DIGEST is not a canonical sha256 digest",
                required_action="provide the frozen public corpus sha256 digest",
            )
        )
    prompt_digest = environment["AX_PROMPT_HASH"].strip()
    if _DIGEST_PATTERN.fullmatch(prompt_digest) is None:
        blockers.append(
            LivePreflightBlocker(
                code="LIVE_PROMPT_HASH_INVALID",
                category="configuration",
                detail="AX_PROMPT_HASH is not a canonical sha256 digest",
                required_action="provide the frozen prompt sha256 digest",
            )
        )
    model_parameters: dict[str, object] | None = None
    try:
        raw_parameters = json.loads(
            environment["AX_MODEL_PARAMETERS_JSON"],
            parse_constant=_reject_nonfinite_json,
        )
    except ValueError:
        raw_parameters = None
    if isinstance(raw_parameters, dict):
        model_parameters = raw_parameters
    else:
        blockers.append(
            LivePreflightBlocker(
                code="LIVE_MODEL_PARAMETERS_INVALID",
                category="configuration",
                detail="AX_MODEL_PARAMETERS_JSON is not a JSON object",
                required_action="provide the frozen model parameters as one JSON object",
            )
        )
    if blockers or model_parameters is None:
        return None, tuple(blockers)
    return (
        LiveExecutionIdentity(
            corpus=LiveCorpusIdentity(
                id=environment["AX_CORPUS_ID"].strip(),
                version=environment["AX_CORPUS_VERSION"].strip(),
                digest=corpus_digest,
            ),
            prompt=LivePromptIdentity(
                id=environment["AX_PROMPT_ID"].strip(),
                digest=prompt_digest,
            ),
            model=LiveModelIdentity(
                provider=environment["AX_MODEL_PROVIDER"].strip(),
                name=environment["AX_MODEL_NAME"].strip(),
                parameters=model_parameters,
            ),
            evaluator_versions={
                "grounded": "grounded-answer-v1",
                "operational": "operational-v1",
                "parsing": "parsing-quality-v1",
                "retrieval": "retrieval-quality-v1",
            },
            adapter_versions={
                "grounded": "ax-sut-http-v1",
                "parsing": "ax-sut-http-v1",
                "retrieval": "ax-sut-http-v1",
            },
        ),
        (),
    )


def build_live_preflight_artifact(
    *,
    preflight_id: str,
    validation: DatasetValidationReport,
    evaluation_state: RepositoryState,
    environment: Mapping[str, str],
    capability_manifest: CapabilityManifest | None = None,
    additional_blockers: tuple[LivePreflightBlocker, ...] = (),
) -> LiveVerificationPreflightArtifact:
    if validation.state != "VALID" or validation.snapshot is None:
        raise ValueError("live Verification requires a valid frozen dataset bundle")
    snapshot = validation.snapshot
    verification_case_count = sum(case.split == "Verification" for case in snapshot.case_records)
    if verification_case_count != 30:
        raise ValueError("live Verification requires exactly 30 frozen Verification cases")
    blocker_list = [
        LivePreflightBlocker(
            code=code,
            category="access"
            if name in {"AX_BASE_URL", "AX_TENANT_ID", "AX_ROLES"}
            else "configuration",
            detail=f"{name} is not configured",
            required_action=required_action,
        )
        for name, code, required_action in _REQUIRED_LIVE_SETTINGS
        if not environment.get(name, "").strip()
    ]
    execution_identity, identity_blockers = _build_execution_identity(environment)
    blocker_list.extend(identity_blockers)
    capability_evidence = (
        LiveCapabilityEvidence.model_validate(capability_manifest.model_dump(mode="python"))
        if capability_manifest is not None
        else None
    )
    sut: LiveRepositoryEvidence | None = None
    repository_value = environment.get("AX_REPOSITORY", "").strip()
    if repository_value:
        repository_path = Path(repository_value)
        try:
            sut_state = capture_repository_state(repository_path)
        except (OSError, subprocess.CalledProcessError):
            blocker_list.append(
                LivePreflightBlocker(
                    code="LIVE_SUT_REPOSITORY_UNAVAILABLE",
                    category="access",
                    detail="the configured AX repository is unavailable or is not a Git checkout",
                    required_action="provide access to the pinned AX Git checkout",
                )
            )
        else:
            sut = LiveRepositoryEvidence(
                commit_sha=sut_state.commit_sha,
                dirty_worktree=sut_state.dirty_worktree,
            )
            pinned_sha = load_ax_http_contract().sut_commit_sha
            if sut_state.commit_sha != pinned_sha:
                blocker_list.append(
                    LivePreflightBlocker(
                        code="LIVE_SUT_SHA_MISMATCH",
                        category="provenance",
                        detail=(
                            f"AX HEAD {sut_state.commit_sha} does not match pinned SHA {pinned_sha}"
                        ),
                        required_action=(
                            "checkout the pinned AX commit without changing product behavior"
                        ),
                    )
                )
            if sut_state.dirty_worktree:
                blocker_list.append(
                    LivePreflightBlocker(
                        code="LIVE_SUT_DIRTY",
                        category="provenance",
                        detail="the pinned AX checkout has uncommitted changes",
                        required_action="use a clean pinned AX checkout for both live runs",
                    )
                )
    if capability_evidence is not None:
        if sut is None or capability_evidence.sut_commit_sha != sut.commit_sha:
            blocker_list.append(
                LivePreflightBlocker(
                    code="LIVE_CAPABILITY_SUT_SHA_MISMATCH",
                    category="provenance",
                    detail="the capability manifest does not match the verified AX checkout",
                    required_action="regenerate capabilities from the exact pinned AX checkout",
                )
            )
        for operation_name in ("preflight", "parse", "retrieve", "answer", "source_text"):
            operation = capability_evidence.operations.get(operation_name)
            if operation is None or not operation.available:
                unavailable_reason = (
                    operation.reason
                    if operation is not None and operation.reason
                    else "AX_OPERATION_NOT_DECLARED"
                )
                blocker_list.append(
                    LivePreflightBlocker(
                        code="LIVE_REQUIRED_OPERATION_UNAVAILABLE",
                        category="capability",
                        detail=f"{operation_name}: {unavailable_reason}",
                        required_action=(
                            "provide the separately reviewed AX observability or endpoint contract"
                        ),
                    )
                )
        if not capability_evidence.corpus.verified_by_sut:
            corpus = capability_evidence.corpus
            blocker_list.append(
                LivePreflightBlocker(
                    code="LIVE_CORPUS_IDENTITY_UNVERIFIED",
                    category="capability",
                    detail=(
                        f"{corpus.id}@{corpus.version}: "
                        f"{corpus.reason or 'AX_CORPUS_IDENTITY_NOT_EXPOSED'}"
                    ),
                    required_action=(
                        "provide a pinned AX boundary that verifies the frozen public "
                        "corpus identity"
                    ),
                )
            )
    if evaluation_state.dirty_worktree:
        blocker_list.append(
            LivePreflightBlocker(
                code="LIVE_EVALUATION_PLANE_DIRTY",
                category="provenance",
                detail="the Evaluation Plane checkout has uncommitted changes",
                required_action=(
                    "commit the reviewed Issue #15 implementation before creating live run evidence"
                ),
            )
        )
    blocker_list.extend(additional_blockers)
    blockers = tuple(blocker_list)
    dataset = LiveDatasetIdentity(
        id=snapshot.manifest.dataset_id,
        version=snapshot.manifest.dataset_version,
        digest=snapshot.dataset_digest,
        verification_case_count=30,
    )
    plan = LiveVerificationPlan(
        candidate_plan_version="candidate-plan-v1",
        baseline=LiveRunConfiguration(top_k=5, evidence_limit=3),
        candidate=LiveRunConfiguration(top_k=5, evidence_limit=5),
    )
    repository = LiveRepositoryEvidence(
        commit_sha=evaluation_state.commit_sha,
        dirty_worktree=evaluation_state.dirty_worktree,
    )
    logical_payload = {
        "state": "BLOCKED" if blockers else "READY",
        "dataset": dataset.model_dump(mode="json"),
        "plan": plan.model_dump(mode="json"),
        "evaluation_plane": repository.model_dump(mode="json"),
        "sut": sut.model_dump(mode="json") if sut is not None else None,
        "execution_identity": (
            execution_identity.model_dump(mode="json") if execution_identity is not None else None
        ),
        "capability_manifest": (
            capability_evidence.model_dump(mode="json") if capability_evidence is not None else None
        ),
        "blockers": [blocker.model_dump(mode="json") for blocker in blockers],
    }
    return LiveVerificationPreflightArtifact(
        schema_version="live-verification-preflight-artifact-v1",
        preflight_id=preflight_id,
        state="BLOCKED" if blockers else "READY",
        dataset=dataset,
        plan=plan,
        evaluation_plane=repository,
        sut=sut,
        execution_identity=execution_identity,
        capability_manifest=capability_evidence,
        blockers=blockers,
        logical_digest=canonical_digest(logical_payload),
    )


def execute_live_preflight(
    *,
    preflight_id: str,
    validation: DatasetValidationReport,
    evaluation_state: RepositoryState,
    environment: Mapping[str, str],
    transport: httpx.BaseTransport | None = None,
) -> LiveVerificationPreflightArtifact:
    initial = build_live_preflight_artifact(
        preflight_id=preflight_id,
        validation=validation,
        evaluation_state=evaluation_state,
        environment=environment,
    )
    if initial.blockers or initial.sut is None:
        return initial
    roles = tuple(role.strip() for role in environment["AX_ROLES"].split(",") if role.strip())
    try:
        adapter_config = AxHttpAdapterConfig(
            base_url=environment["AX_BASE_URL"],
            sut_commit_sha=initial.sut.commit_sha,
            tenant_id=environment["AX_TENANT_ID"],
            user_id=environment["AX_USER_ID"],
            roles=roles,
            bearer_token=environment.get("AX_BEARER_TOKEN") or None,
        )
    except ValidationError:
        return build_live_preflight_artifact(
            preflight_id=preflight_id,
            validation=validation,
            evaluation_state=evaluation_state,
            environment=environment,
            additional_blockers=(
                LivePreflightBlocker(
                    code="LIVE_ADAPTER_CONFIGURATION_INVALID",
                    category="configuration",
                    detail="the AX base URL, tenant, user, or role configuration is invalid",
                    required_action=(
                        "provide a valid authorized AX endpoint and synthetic request identity"
                    ),
                ),
            ),
        )
    adapter = AxHttpAdapter(adapter_config, transport=transport)
    try:
        capability_manifest = adapter.preflight(
            context=AxRequestContext(
                run_id=preflight_id,
                case_id="preflight",
                eval_correlation_id=f"{preflight_id}-capability",
            ),
            corpus_id=environment["AX_CORPUS_ID"],
            corpus_version=environment["AX_CORPUS_VERSION"],
        )
    except httpx.HTTPError:
        return build_live_preflight_artifact(
            preflight_id=preflight_id,
            validation=validation,
            evaluation_state=evaluation_state,
            environment=environment,
            additional_blockers=(
                LivePreflightBlocker(
                    code="LIVE_AX_PREFLIGHT_UNREACHABLE",
                    category="access",
                    detail="the configured AX live endpoint could not be reached",
                    required_action=(
                        "start or authorize access to the pinned AX service before either run"
                    ),
                ),
            ),
        )
    except AxHttpFailure as error:
        return build_live_preflight_artifact(
            preflight_id=preflight_id,
            validation=validation,
            evaluation_state=evaluation_state,
            environment=environment,
            additional_blockers=(
                LivePreflightBlocker(
                    code="LIVE_AX_PREFLIGHT_FAILED",
                    category="access",
                    detail=f"{error.operation}: {error.failure_code}",
                    required_action="resolve the recorded AX preflight failure before either run",
                ),
            ),
        )
    return build_live_preflight_artifact(
        preflight_id=preflight_id,
        validation=validation,
        evaluation_state=evaluation_state,
        environment=environment,
        capability_manifest=capability_manifest,
    )


def write_live_preflight_artifact(
    artifact: LiveVerificationPreflightArtifact,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{artifact.preflight_id}.json"
    serialized = json.dumps(
        artifact.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    with path.open("x", encoding="utf-8") as output_file:
        output_file.write(serialized + "\n")
    return path


def replay_live_preflight_artifact(
    raw_artifact: object,
) -> dict[str, str]:
    stored = LiveVerificationPreflightArtifact.model_validate(raw_artifact)
    logical_payload = {
        "state": stored.state,
        "dataset": stored.dataset.model_dump(mode="json"),
        "plan": stored.plan.model_dump(mode="json"),
        "evaluation_plane": stored.evaluation_plane.model_dump(mode="json"),
        "sut": stored.sut.model_dump(mode="json") if stored.sut is not None else None,
        "execution_identity": (
            stored.execution_identity.model_dump(mode="json")
            if stored.execution_identity is not None
            else None
        ),
        "capability_manifest": (
            stored.capability_manifest.model_dump(mode="json")
            if stored.capability_manifest is not None
            else None
        ),
        "blockers": [blocker.model_dump(mode="json") for blocker in stored.blockers],
    }
    recomputed_digest = canonical_digest(logical_payload)
    if stored.logical_digest != recomputed_digest:
        raise ValueError("live preflight artifact does not reproduce its stored digest")
    return {
        "preflight_state": stored.state,
        "logical_digest": recomputed_digest,
    }
