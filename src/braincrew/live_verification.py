from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Literal, Never
from uuid import UUID

import httpx
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

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
    ParseObservation,
    load_ax_http_contract,
)
from braincrew.contracts import (
    AxAuthorizationRole,
    ParsingDatasetDocumentV2,
    RetrievalDatasetDocumentV2,
)
from braincrew.dataset_registry import DatasetValidationReport
from braincrew.digest import canonical_digest
from braincrew.grounded_contracts import GroundedDatasetDocumentV2
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


class _ImmutableLiveList[ValueT](list[ValueT]):
    def _reject_mutation(self, *args: object, **kwargs: object) -> Never:
        del args, kwargs
        raise TypeError("live preflight sequences are immutable")

    __setitem__ = _reject_mutation
    __delitem__ = _reject_mutation
    __iadd__ = _reject_mutation
    __imul__ = _reject_mutation
    append = _reject_mutation
    clear = _reject_mutation
    extend = _reject_mutation
    insert = _reject_mutation
    pop = _reject_mutation
    remove = _reject_mutation
    reverse = _reject_mutation
    sort = _reject_mutation


def _freeze_live_value(value: object) -> object:
    if isinstance(value, dict):
        return _ImmutableLiveDict({key: _freeze_live_value(item) for key, item in value.items()})
    if isinstance(value, list):
        return _ImmutableLiveList(_freeze_live_value(item) for item in value)
    if isinstance(value, tuple):
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
    authorization_roles: tuple[AxAuthorizationRole, ...]
    corpora: dict[str, LiveCorpusIdentity]
    prompt: LivePromptIdentity
    model: LiveModelIdentity
    parsing_attachment_mapping: dict[str, str]
    parsing_authorization_roles: dict[str, AxAuthorizationRole]
    evaluator_versions: dict[str, str]
    adapter_versions: dict[str, str]

    @field_validator(
        "corpora",
        "parsing_attachment_mapping",
        "parsing_authorization_roles",
        "evaluator_versions",
        "adapter_versions",
    )
    @classmethod
    def freeze_version_maps(cls, versions: dict[str, str]) -> dict[str, str]:
        return _ImmutableLiveDict(versions)

    @model_validator(mode="after")
    def validate_role_identity(self) -> LiveExecutionIdentity:
        if self.authorization_roles != tuple(sorted(set(self.authorization_roles))):
            raise ValueError("authorization roles must be sorted and unique")
        if set(self.corpora) != set(self.authorization_roles):
            raise ValueError("corpus identities must exactly cover authorization roles")
        if set(self.parsing_attachment_mapping) != set(self.parsing_authorization_roles):
            raise ValueError(
                "parsing attachment and authorization mappings must cover the same documents"
            )
        if not set(self.parsing_authorization_roles.values()) <= set(self.authorization_roles):
            raise ValueError("parsing authorization mappings must use declared authorization roles")
        return self


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

    @field_validator("corpus")
    @classmethod
    def freeze_corpus_evidence(cls, corpus: CorpusCapability) -> CorpusCapability:
        return corpus.model_copy(
            update={
                "principal_roles": _freeze_live_value(corpus.principal_roles),
                "counts": _freeze_live_value(corpus.counts),
                "contributing_versions": _freeze_live_value(corpus.contributing_versions),
            }
        )

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


class LiveParseObservationEvidence(StrictLiveContract):
    schema_version: Literal["live-parse-observation-evidence-v1"]
    authorization_role: AxAuthorizationRole
    document_id: str
    attachment_id: str
    response_schema_version: Literal["ax-parse-observation-v1"]
    response_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    parse_available: Literal[True]
    parser_name: str | None
    parser_version: str | None
    attempts: tuple[HttpAttempt, ...]


class LiveVerificationPreflightArtifact(StrictLiveContract):
    schema_version: Literal["live-verification-preflight-artifact-v2"]
    preflight_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    state: Literal["READY", "BLOCKED"]
    dataset: LiveDatasetIdentity
    plan: LiveVerificationPlan
    evaluation_plane: LiveRepositoryEvidence
    sut: LiveRepositoryEvidence | None
    execution_identity: LiveExecutionIdentity | None
    capability_manifests: dict[str, LiveCapabilityEvidence]
    parse_observations: dict[str, LiveParseObservationEvidence]
    blockers: tuple[LivePreflightBlocker, ...]
    logical_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @field_validator("capability_manifests")
    @classmethod
    def freeze_capability_manifests(
        cls,
        manifests: dict[str, LiveCapabilityEvidence],
    ) -> dict[str, LiveCapabilityEvidence]:
        return _ImmutableLiveDict(manifests)

    @field_validator("parse_observations")
    @classmethod
    def freeze_parse_observations(
        cls,
        observations: dict[str, LiveParseObservationEvidence],
    ) -> dict[str, LiveParseObservationEvidence]:
        return _ImmutableLiveDict(observations)

    @model_validator(mode="after")
    def validate_preflight_state(self) -> LiveVerificationPreflightArtifact:
        expected_state = "BLOCKED" if self.blockers else "READY"
        if self.state != expected_state:
            raise ValueError("preflight state must agree with the blocker set")
        dataset_is_v2 = (
            self.dataset.id == "braincrew-evaluation-dataset" and self.dataset.version == "2.0.0"
        )
        if not dataset_is_v2 and not any(
            blocker.code == "LIVE_DATASET_AUTHORIZATION_SCHEMA_UNSUPPORTED"
            for blocker in self.blockers
        ):
            raise ValueError("non-v2 dataset evidence requires the typed schema blocker")
        if self.execution_identity is None:
            if self.capability_manifests or self.parse_observations:
                raise ValueError("live AX evidence requires an execution identity")
            if self.state == "READY":
                raise ValueError("READY requires a frozen execution identity")
            return self
        required_roles = set(self.execution_identity.authorization_roles)
        if not set(self.capability_manifests) <= required_roles:
            raise ValueError("capability evidence contains an undeclared authorization role")
        parsing_documents = set(self.execution_identity.parsing_attachment_mapping)
        if not set(self.parse_observations) <= parsing_documents:
            raise ValueError("parse evidence contains an undeclared parsing document")
        for document_id, evidence in self.parse_observations.items():
            if (
                evidence.document_id != document_id
                or evidence.attachment_id
                != self.execution_identity.parsing_attachment_mapping[document_id]
                or evidence.authorization_role
                != self.execution_identity.parsing_authorization_roles[document_id]
            ):
                raise ValueError("parse evidence does not match the frozen execution identity")
        if self.state == "READY":
            if self.sut is None or self.sut.dirty_worktree or self.evaluation_plane.dirty_worktree:
                raise ValueError("READY requires clean pinned repository evidence")
            if set(self.capability_manifests) != required_roles:
                raise ValueError("READY capability evidence must exactly cover authorization roles")
            if set(self.parse_observations) != parsing_documents:
                raise ValueError("READY parse evidence must exactly cover parsing documents")
            if any(
                evidence.request.roles != (role,) or evidence.corpus.principal_roles != [role]
                for role, evidence in self.capability_manifests.items()
            ):
                raise ValueError("READY capability evidence must prove each isolated role")
        return self


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
    (
        "AX_PARSING_ATTACHMENT_MAP_JSON",
        "LIVE_PARSING_ATTACHMENT_MAPPING_MISSING",
        "provide reviewed AX attachment UUIDs for all six frozen parsing Verification documents",
    ),
    (
        "AX_CORPUS_IDENTITIES_JSON",
        "LIVE_CORPUS_IDENTITIES_MISSING",
        "provide one frozen AX-visible corpus identity for every Verification authorization role",
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
_AX_SUPPORTED_ROLES = frozenset({"Executive", "HRAdmin", "HRPractitioner", "Employee"})


def _reject_nonfinite_json(value: str) -> Never:
    raise ValueError(f"non-finite JSON constant is forbidden: {value}")


def _build_execution_identity(
    environment: Mapping[str, str],
    *,
    verification_roles: frozenset[AxAuthorizationRole],
    parsing_authorization_roles: Mapping[str, AxAuthorizationRole],
) -> tuple[LiveExecutionIdentity | None, tuple[LivePreflightBlocker, ...]]:
    identity_names = {
        "AX_CORPUS_IDENTITIES_JSON",
        "AX_PROMPT_ID",
        "AX_PROMPT_HASH",
        "AX_MODEL_PROVIDER",
        "AX_MODEL_NAME",
        "AX_MODEL_PARAMETERS_JSON",
        "AX_PARSING_ATTACHMENT_MAP_JSON",
    }
    if any(not environment.get(name, "").strip() for name in identity_names):
        return None, ()
    blockers: list[LivePreflightBlocker] = []
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
    authorized_roles = {
        role.strip() for role in environment.get("AX_ROLES", "").split(",") if role.strip()
    }
    if authorized_roles != verification_roles or not verification_roles.issubset(
        _AX_SUPPORTED_ROLES
    ):
        blockers.append(
            LivePreflightBlocker(
                code="LIVE_AUTHORIZATION_ROLE_SET_MISMATCH",
                category="configuration",
                detail=(
                    "AX_ROLES must equal the canonical authorization roles in the frozen "
                    "Verification dataset"
                ),
                required_action=(
                    "authorize exactly the dataset-declared AX roles without a role crosswalk"
                ),
            )
        )
    try:
        raw_corpora = json.loads(environment["AX_CORPUS_IDENTITIES_JSON"])
    except ValueError:
        raw_corpora = None
    corpora: dict[str, LiveCorpusIdentity] | None = None
    if isinstance(raw_corpora, dict) and set(raw_corpora) == verification_roles:
        try:
            corpora = {
                str(role): LiveCorpusIdentity.model_validate(identity)
                for role, identity in raw_corpora.items()
            }
        except ValidationError:
            corpora = None
    if corpora is None:
        blockers.append(
            LivePreflightBlocker(
                code="LIVE_CORPUS_IDENTITIES_INVALID",
                category="configuration",
                detail=(
                    "AX_CORPUS_IDENTITIES_JSON must provide one strict corpus identity for "
                    "every Verification authorization role"
                ),
                required_action=(
                    "capture and review the Employee, Executive, and HRPractitioner corpus "
                    "identities separately"
                ),
            )
        )
    try:
        raw_attachment_mapping = json.loads(environment["AX_PARSING_ATTACHMENT_MAP_JSON"])
    except ValueError:
        raw_attachment_mapping = None
    attachment_mapping: dict[str, str] | None = None
    parsing_document_ids = frozenset(parsing_authorization_roles)
    if (
        isinstance(raw_attachment_mapping, dict)
        and set(raw_attachment_mapping) == parsing_document_ids
    ):
        normalized_attachments: dict[str, str] = {}
        try:
            for document_id, attachment_id in raw_attachment_mapping.items():
                if not isinstance(attachment_id, str):
                    raise ValueError("attachment identity must be a string")
                parsed_id = UUID(attachment_id)
                if str(parsed_id) != attachment_id:
                    raise ValueError("attachment identity must be a canonical UUID")
                normalized_attachments[str(document_id)] = attachment_id
        except ValueError:
            normalized_attachments = {}
        if len(normalized_attachments) == len(parsing_document_ids):
            attachment_mapping = normalized_attachments
    if attachment_mapping is None:
        blockers.append(
            LivePreflightBlocker(
                code="LIVE_PARSING_ATTACHMENT_MAPPING_INVALID",
                category="configuration",
                detail=(
                    "AX_PARSING_ATTACHMENT_MAP_JSON must map exactly the six frozen parsing "
                    "document identities to canonical AX attachment UUIDs"
                ),
                required_action=(
                    "provision and review all six synthetic parsing attachments before preflight"
                ),
            )
        )
    if blockers or model_parameters is None or corpora is None or attachment_mapping is None:
        return None, tuple(blockers)
    return (
        LiveExecutionIdentity(
            authorization_roles=tuple(sorted(verification_roles)),
            corpora=corpora,
            prompt=LivePromptIdentity(
                id=environment["AX_PROMPT_ID"].strip(),
                digest=prompt_digest,
            ),
            model=LiveModelIdentity(
                provider=environment["AX_MODEL_PROVIDER"].strip(),
                name=environment["AX_MODEL_NAME"].strip(),
                parameters=model_parameters,
            ),
            parsing_attachment_mapping=attachment_mapping,
            parsing_authorization_roles=dict(parsing_authorization_roles),
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
    capability_manifests: Mapping[str, CapabilityManifest] | None = None,
    parse_observations: Mapping[str, LiveParseObservationEvidence] | None = None,
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
    parsing_dataset = snapshot.parsing_dataset
    retrieval_dataset = snapshot.retrieval_dataset
    grounded_dataset = snapshot.grounded_dataset
    if (
        snapshot.manifest.schema_version == "dataset-manifest-v2"
        and isinstance(parsing_dataset, ParsingDatasetDocumentV2)
        and isinstance(retrieval_dataset, RetrievalDatasetDocumentV2)
        and isinstance(grounded_dataset, GroundedDatasetDocumentV2)
    ):
        verification_roles: frozenset[AxAuthorizationRole] = frozenset(
            {
                case.authorization_role
                for case in parsing_dataset.cases
                if case.split == "verification"
            }
            | {
                case.authorization_role
                for case in retrieval_dataset.cases
                if case.split == "verification"
            }
            | {
                case.authorization_role
                for case in grounded_dataset.cases
                if case.split == "Verification"
            }
        )
        authorization_schema_supported = True
    else:
        verification_roles = frozenset()
        authorization_schema_supported = False
        blocker_list.append(
            LivePreflightBlocker(
                code="LIVE_DATASET_AUTHORIZATION_SCHEMA_UNSUPPORTED",
                category="provenance",
                detail=(
                    "live Verification requires dataset-manifest-v2 with canonical AX "
                    "authorization_role and separate persona fields"
                ),
                required_action=("use the reviewed braincrew-evaluation-dataset@2.0.0 bundle"),
            )
        )
    parsing_authorization_roles = (
        {
            case.document.id: case.authorization_role
            for case in parsing_dataset.cases
            if case.split == "verification"
        }
        if isinstance(parsing_dataset, ParsingDatasetDocumentV2)
        else {}
    )
    if authorization_schema_supported:
        execution_identity, identity_blockers = _build_execution_identity(
            environment,
            verification_roles=verification_roles,
            parsing_authorization_roles=parsing_authorization_roles,
        )
        blocker_list.extend(identity_blockers)
    else:
        execution_identity = None
    capability_evidence = _ImmutableLiveDict(
        {
            role: LiveCapabilityEvidence.model_validate(manifest.model_dump(mode="python"))
            for role, manifest in (capability_manifests or {}).items()
        }
    )
    parse_evidence = _ImmutableLiveDict(dict(parse_observations or {}))
    if execution_identity is not None and not capability_evidence and not additional_blockers:
        blocker_list.append(
            LivePreflightBlocker(
                code="LIVE_CAPABILITY_EVIDENCE_MISSING",
                category="capability",
                detail="AX capabilities and role-visible corpus identities were not discovered",
                required_action="discover AX capabilities separately for every required role",
            )
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
    if capability_evidence:
        expected_roles = (
            set(execution_identity.authorization_roles) if execution_identity is not None else set()
        )
        if set(capability_evidence) != expected_roles:
            blocker_list.append(
                LivePreflightBlocker(
                    code="LIVE_CAPABILITY_ROLE_COVERAGE_MISMATCH",
                    category="capability",
                    detail="capability manifests do not cover every dataset authorization role",
                    required_action="discover AX capabilities separately for every required role",
                )
            )
        for role, role_capability in capability_evidence.items():
            if role_capability.readiness_status != "ready":
                blocker_list.append(
                    LivePreflightBlocker(
                        code="LIVE_AX_NOT_READY",
                        category="capability",
                        detail=f"{role}: AX readiness status is {role_capability.readiness_status}",
                        required_action="restore AX readiness before either live run",
                    )
                )
            if sut is None or role_capability.sut_commit_sha != sut.commit_sha:
                blocker_list.append(
                    LivePreflightBlocker(
                        code="LIVE_CAPABILITY_SUT_SHA_MISMATCH",
                        category="provenance",
                        detail=f"{role}: capability manifest does not match the AX checkout",
                        required_action="regenerate capabilities from the exact pinned AX checkout",
                    )
                )
            if role_capability.request.roles != (
                role,
            ) or role_capability.corpus.principal_roles != [role]:
                blocker_list.append(
                    LivePreflightBlocker(
                        code="LIVE_CAPABILITY_ROLE_MISMATCH",
                        category="capability",
                        detail=f"{role}: AX did not verify the isolated requested role",
                        required_action="repeat discovery with exactly one AX role per principal",
                    )
                )
            for operation_name in (
                "preflight",
                "corpus_identity",
                "parse",
                "retrieve",
                "answer",
                "source_text",
            ):
                operation = role_capability.operations.get(operation_name)
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
                            detail=f"{role}/{operation_name}: {unavailable_reason}",
                            required_action=(
                                "provide the reviewed AX observability or endpoint contract"
                            ),
                        )
                    )
            corpus = role_capability.corpus
            expected_corpus = (
                execution_identity.corpora.get(role) if execution_identity is not None else None
            )
            if not corpus.verified_by_sut:
                blocker_list.append(
                    LivePreflightBlocker(
                        code="LIVE_CORPUS_IDENTITY_UNVERIFIED",
                        category="capability",
                        detail=(
                            f"{role}/{corpus.id}@{corpus.version}: "
                            f"{corpus.reason or 'AX_CORPUS_IDENTITY_NOT_EXPOSED'}"
                        ),
                        required_action="verify the role-visible corpus through pinned AX",
                    )
                )
            elif expected_corpus is None or (
                corpus.id,
                corpus.version,
                corpus.digest,
            ) != (
                expected_corpus.id,
                expected_corpus.version,
                expected_corpus.digest,
            ):
                blocker_list.append(
                    LivePreflightBlocker(
                        code="LIVE_CORPUS_IDENTITY_MISMATCH",
                        category="capability",
                        detail=f"{role}: AX-visible corpus does not match the pinned identity",
                        required_action="pin the exact AX-visible corpus identity for this role",
                    )
                )
            dataset_provenance_version = (
                f"{snapshot.manifest.dataset_id}@{snapshot.manifest.dataset_version}"
            )
            if (
                corpus.verified_by_sut
                and dataset_provenance_version not in corpus.contributing_versions
            ):
                blocker_list.append(
                    LivePreflightBlocker(
                        code="LIVE_CORPUS_DATASET_PROVENANCE_MISMATCH",
                        category="provenance",
                        detail=(
                            f"{role}: AX-visible corpus does not prove the frozen Verification "
                            f"dataset {dataset_provenance_version}"
                        ),
                        required_action=(
                            "provision and review a role-visible public or synthetic corpus "
                            f"mapped to {dataset_provenance_version}"
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
    if (
        execution_identity is not None
        and capability_evidence
        and not parse_evidence
        and not blocker_list
    ):
        blocker_list.append(
            LivePreflightBlocker(
                code="LIVE_PARSE_OBSERVATION_EVIDENCE_MISSING",
                category="capability",
                detail="strict AX parse observations were not probed for the frozen attachments",
                required_action="probe every frozen parsing attachment through its exact AX role",
            )
        )
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
        "capability_manifests": {
            role: evidence.model_dump(mode="json") for role, evidence in capability_evidence.items()
        },
        "parse_observations": {
            document_id: evidence.model_dump(mode="json")
            for document_id, evidence in parse_evidence.items()
        },
        "blockers": [blocker.model_dump(mode="json") for blocker in blockers],
    }
    return LiveVerificationPreflightArtifact(
        schema_version="live-verification-preflight-artifact-v2",
        preflight_id=preflight_id,
        state="BLOCKED" if blockers else "READY",
        dataset=dataset,
        plan=plan,
        evaluation_plane=repository,
        sut=sut,
        execution_identity=execution_identity,
        capability_manifests=capability_evidence,
        parse_observations=parse_evidence,
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
    discovery_blocker_codes = {"LIVE_CAPABILITY_EVIDENCE_MISSING"}
    if (
        any(blocker.code not in discovery_blocker_codes for blocker in initial.blockers)
        or initial.sut is None
        or initial.execution_identity is None
    ):
        return initial
    capability_manifests: dict[str, CapabilityManifest] = {}
    adapters: dict[str, AxHttpAdapter] = {}
    for role in initial.execution_identity.authorization_roles:
        try:
            adapter_config = AxHttpAdapterConfig(
                base_url=environment["AX_BASE_URL"],
                sut_commit_sha=initial.sut.commit_sha,
                tenant_id=environment["AX_TENANT_ID"],
                user_id=environment["AX_USER_ID"],
                roles=(role,),
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
                        detail=f"{role}: AX request identity configuration is invalid",
                        required_action=(
                            "provide a valid authorized AX endpoint and synthetic request identity"
                        ),
                    ),
                ),
            )
        adapter = AxHttpAdapter(adapter_config, transport=transport)
        adapters[role] = adapter
        expected_corpus = initial.execution_identity.corpora[role]
        try:
            capability_manifests[role] = adapter.preflight(
                context=AxRequestContext(
                    run_id=preflight_id,
                    case_id=f"preflight-{role}",
                    eval_correlation_id=f"{preflight_id}-{role}-capability",
                ),
                corpus_id=expected_corpus.id,
                corpus_version=expected_corpus.version,
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
                        detail=f"{role}: the configured AX endpoint could not be reached",
                        required_action=(
                            "start or authorize access to pinned AX before either run"
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
                        detail=f"{role}/{error.operation}: {error.failure_code}",
                        required_action=(
                            "resolve the recorded AX preflight failure before either run"
                        ),
                    ),
                ),
            )
    parse_observations: dict[str, LiveParseObservationEvidence] = {}
    for document_id in sorted(initial.execution_identity.parsing_attachment_mapping):
        role = initial.execution_identity.parsing_authorization_roles[document_id]
        attachment_id = initial.execution_identity.parsing_attachment_mapping[document_id]
        try:
            observation: ParseObservation = adapters[role].parse(
                context=AxRequestContext(
                    run_id=preflight_id,
                    case_id=f"preflight-parse-{document_id}",
                    eval_correlation_id=f"{preflight_id}-{document_id}-parse",
                ),
                document_id=attachment_id,
            )
        except httpx.HTTPError:
            return build_live_preflight_artifact(
                preflight_id=preflight_id,
                validation=validation,
                evaluation_state=evaluation_state,
                environment=environment,
                capability_manifests=capability_manifests,
                parse_observations=parse_observations,
                additional_blockers=(
                    LivePreflightBlocker(
                        code="LIVE_PARSE_OBSERVATION_UNREACHABLE",
                        category="access",
                        detail=f"{document_id}: the AX parse-observation endpoint was unreachable",
                        required_action=(
                            "restore authorized access to every frozen parse observation"
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
                capability_manifests=capability_manifests,
                parse_observations=parse_observations,
                additional_blockers=(
                    LivePreflightBlocker(
                        code="LIVE_PARSE_OBSERVATION_FAILED",
                        category="capability",
                        detail=f"{document_id}/{error.operation}: {error.failure_code}",
                        required_action=(
                            "resolve the recorded parse-observation failure before either run"
                        ),
                    ),
                ),
            )
        response = observation.response
        if response.attachment_id != attachment_id or not response.parse_available:
            failure_code = (
                "LIVE_PARSE_OBSERVATION_IDENTITY_MISMATCH"
                if response.attachment_id != attachment_id
                else "LIVE_PARSE_OBSERVATION_UNAVAILABLE"
            )
            return build_live_preflight_artifact(
                preflight_id=preflight_id,
                validation=validation,
                evaluation_state=evaluation_state,
                environment=environment,
                capability_manifests=capability_manifests,
                parse_observations=parse_observations,
                additional_blockers=(
                    LivePreflightBlocker(
                        code=failure_code,
                        category="capability",
                        detail=(
                            f"{document_id}: AX did not return the required available "
                            "parse observation"
                        ),
                        required_action=(
                            "provision and verify the exact frozen synthetic attachment"
                        ),
                    ),
                ),
            )
        parse_observations[document_id] = LiveParseObservationEvidence(
            schema_version="live-parse-observation-evidence-v1",
            authorization_role=role,
            document_id=document_id,
            attachment_id=attachment_id,
            response_schema_version=response.schema_version,
            response_digest=canonical_digest(response.model_dump(mode="json")),
            parse_available=True,
            parser_name=response.parser_name,
            parser_version=response.parser_version,
            attempts=tuple(observation.attempts),
        )
    return build_live_preflight_artifact(
        preflight_id=preflight_id,
        validation=validation,
        evaluation_state=evaluation_state,
        environment=environment,
        capability_manifests=capability_manifests,
        parse_observations=parse_observations,
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
        "capability_manifests": {
            role: evidence.model_dump(mode="json")
            for role, evidence in stored.capability_manifests.items()
        },
        "parse_observations": {
            document_id: evidence.model_dump(mode="json")
            for document_id, evidence in stored.parse_observations.items()
        },
        "blockers": [blocker.model_dump(mode="json") for blocker in stored.blockers],
    }
    recomputed_digest = canonical_digest(logical_payload)
    if stored.logical_digest != recomputed_digest:
        raise ValueError("live preflight artifact does not reproduce its stored digest")
    return {
        "preflight_state": stored.state,
        "logical_digest": recomputed_digest,
    }
