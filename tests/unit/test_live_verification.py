from __future__ import annotations

import copy
import hashlib
import inspect
import json
import operator
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError
from pytest import MonkeyPatch

import braincrew.live_verification as live_verification
from braincrew.ax_http_adapter import (
    AxHttpAdapter,
    AxHttpAdapterConfig,
    AxRequestContext,
    CapabilityManifest,
)
from braincrew.dataset_registry import validate_dataset_bundle
from braincrew.live_verification import build_live_preflight_artifact
from braincrew.repository import RepositoryState

PINNED_AX_SHA = "a5391ae8aa2b0d1342809f3599283b7759d6e4e3"
V2_MANIFEST_PATH = Path("datasets/dataset_manifest_v2.json")


def _complete_environment() -> dict[str, str]:
    return {
        "AX_BASE_URL": "https://ax.example.test",
        "AX_REPOSITORY": "/synthetic/ax",
        "AX_TENANT_ID": "00000000-0000-4000-8000-000000000015",
        "AX_USER_ID": "evaluation-plane",
        "AX_ROLES": "Employee,Executive,HRPractitioner",
        "AX_CORPUS_IDENTITIES_JSON": json.dumps(
            {
                role: {
                    "id": "ax-visible-retrieval:00000000-0000-4000-8000-000000000015",
                    "version": "retrieval-inventory-v1",
                    "digest": f"sha256:{digit * 64}",
                }
                for role, digit in (
                    ("Employee", "a"),
                    ("Executive", "b"),
                    ("HRPractitioner", "c"),
                )
            },
            sort_keys=True,
        ),
        "AX_PROMPT_ID": "ax-answer-prompt-v1",
        "AX_PROMPT_HASH": "sha256:" + "b" * 64,
        "AX_MODEL_PROVIDER": "openai",
        "AX_MODEL_NAME": "pinned-model",
        "AX_MODEL_PARAMETERS_JSON": '{"temperature": 0}',
        "AX_PARSING_ATTACHMENT_MAP_JSON": (
            '{"synthetic-rule-015":"00000000-0000-4000-8000-000000000015",'
            '"synthetic-rule-016":"00000000-0000-4000-8000-000000000016",'
            '"synthetic-rule-017":"00000000-0000-4000-8000-000000000017",'
            '"synthetic-rule-018":"00000000-0000-4000-8000-000000000018",'
            '"synthetic-rule-019":"00000000-0000-4000-8000-000000000019",'
            '"synthetic-rule-020":"00000000-0000-4000-8000-000000000020"}'
        ),
    }


def _v2_environment() -> dict[str, str]:
    return _complete_environment()


def test_live_preflight_v2_derives_exact_ax_roles_without_a_crosswalk(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )

    artifact = build_live_preflight_artifact(
        preflight_id="dataset-native-authorization",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_v2_environment(),
    )

    assert artifact.state == "BLOCKED"
    assert [blocker.code for blocker in artifact.blockers] == ["LIVE_CAPABILITY_EVIDENCE_MISSING"]
    assert artifact.execution_identity is not None
    assert artifact.execution_identity.authorization_roles == (
        "Employee",
        "Executive",
        "HRPractitioner",
    )
    assert set(artifact.execution_identity.corpora) == set(
        artifact.execution_identity.authorization_roles
    )
    assert not hasattr(artifact.execution_identity, "role_mapping")


def test_live_preflight_v2_blocks_the_legacy_role_bearing_dataset(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )

    artifact = build_live_preflight_artifact(
        preflight_id="legacy-role-dataset",
        validation=validate_dataset_bundle(Path("datasets/dataset_manifest_v1.json")),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_v2_environment(),
    )

    assert [(blocker.code, blocker.category) for blocker in artifact.blockers] == [
        ("LIVE_DATASET_AUTHORIZATION_SCHEMA_UNSUPPORTED", "provenance")
    ]


def test_execute_live_preflight_v2_discovers_each_role_with_isolated_headers(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )
    corpus_roles: list[str] = []
    parse_roles: list[str] = []
    parse_attachment_ids: list[str] = []
    digest_by_role = {
        "Employee": "a",
        "Executive": "b",
        "HRPractitioner": "c",
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/v1/evaluation/attachments/"):
            parse_roles.append(request.headers["x-ax-roles"])
            parse_attachment_ids.append(request.url.path.split("/")[-2])
            return _capability_handler(request)
        if request.url.path != "/v1/evaluation/corpus-identity":
            return _capability_handler(request)
        role = request.headers["x-ax-roles"]
        corpus_roles.append(role)
        return httpx.Response(
            200,
            json={
                "schema_version": "ax-corpus-identity-v1",
                "corpus_id": "ax-visible-retrieval:00000000-0000-4000-8000-000000000015",
                "corpus_version": "retrieval-inventory-v1",
                "corpus_digest": f"sha256:{digest_by_role[role] * 64}",
                "principal_roles": [role],
                "inventory_count": 30,
                "counts": {
                    "record_kind": {"seed": 30},
                    "corpus_mode": {"synthetic": 30},
                    "embedding_status": {"embedded": 30},
                    "embedding_model": {"text-embedding-3-small": 30},
                },
                "contributing_versions": ["braincrew-evaluation-dataset@2.0.0"],
                "generated_at": "2026-07-20T06:30:00Z",
            },
        )

    artifact = live_verification.execute_live_preflight(
        preflight_id="role-isolated-capabilities",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_v2_environment(),
        transport=httpx.MockTransport(handler),
    )

    assert artifact.state == "READY"
    assert corpus_roles == ["Employee", "Executive", "HRPractitioner"]
    assert set(artifact.capability_manifests) == set(corpus_roles)
    assert parse_roles == ["HRPractitioner"] * 6
    assert parse_attachment_ids == [
        f"00000000-0000-4000-8000-{case_number:012d}" for case_number in range(15, 21)
    ]
    assert set(artifact.parse_observations) == {
        f"synthetic-rule-{case_number:03d}" for case_number in range(15, 21)
    }
    assert all(
        "extracted_text" not in evidence.model_dump_json()
        for evidence in artifact.parse_observations.values()
    )
    assert all(
        manifest.request.roles == (role,) and manifest.corpus.principal_roles == [role]
        for role, manifest in artifact.capability_manifests.items()
    )

    valid_payload = artifact.model_dump(mode="json")
    contradictory_ready = copy.deepcopy(valid_payload)
    contradictory_ready["blockers"] = [
        {
            "code": "TEST_BLOCKER",
            "category": "capability",
            "detail": "a READY artifact cannot contain a blocker",
            "required_action": "remove the contradiction",
        }
    ]
    missing_role_capability = copy.deepcopy(valid_payload)
    del missing_role_capability["capability_manifests"]["Executive"]
    missing_parse_observation = copy.deepcopy(valid_payload)
    del missing_parse_observation["parse_observations"]["synthetic-rule-015"]
    duplicate_roles = copy.deepcopy(valid_payload)
    duplicate_roles["execution_identity"]["authorization_roles"].append("Employee")

    for invalid_payload in (
        contradictory_ready,
        missing_role_capability,
        missing_parse_observation,
        duplicate_roles,
    ):
        with pytest.raises(ValidationError):
            live_verification.LiveVerificationPreflightArtifact.model_validate(invalid_payload)


def test_execute_live_preflight_blocks_when_a_real_parse_probe_fails(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/v1/evaluation/attachments/"):
            return httpx.Response(
                503,
                json={"detail": "audit_persistence_failed"},
                headers={"retry-after": "0"},
            )
        return _capability_handler(request)

    artifact = live_verification.execute_live_preflight(
        preflight_id="parse-probe-failure",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_v2_environment(),
        transport=httpx.MockTransport(handler),
    )

    assert artifact.state == "BLOCKED"
    assert [blocker.code for blocker in artifact.blockers] == ["LIVE_PARSE_OBSERVATION_FAILED"]
    assert set(artifact.capability_manifests) == {
        "Employee",
        "Executive",
        "HRPractitioner",
    }


def _capability_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/health/ready":
        return httpx.Response(
            200,
            json={
                "status": "ready",
                "service": "ax-engine-api",
                "dependencies": {"postgresql": "ready"},
            },
        )
    if request.url.path == "/openapi.json":
        return httpx.Response(
            200,
            json={
                "openapi": "3.1.0",
                "info": {"title": "AX", "version": "0.1.0"},
                "paths": {
                    "/v1/evaluation/attachments/{attachment_id}/parse-observation": {"get": {}},
                    "/v1/evaluation/corpus-identity": {"get": {}},
                    "/v1/retrieval/search": {"post": {}},
                    "/v1/answers/generate": {"post": {}},
                    "/v1/retrieval/source-text/{record_kind}/{record_id}": {"get": {}},
                },
            },
        )
    if request.url.path == "/v1/evaluation/corpus-identity":
        role = request.headers["x-ax-roles"]
        digest_by_role = {"Employee": "a", "Executive": "b", "HRPractitioner": "c"}
        return httpx.Response(
            200,
            json={
                "schema_version": "ax-corpus-identity-v1",
                "corpus_id": ("ax-visible-retrieval:00000000-0000-4000-8000-000000000015"),
                "corpus_version": "retrieval-inventory-v1",
                "corpus_digest": f"sha256:{digest_by_role[role] * 64}",
                "principal_roles": [role],
                "inventory_count": 30,
                "counts": {
                    "record_kind": {"seed": 30},
                    "corpus_mode": {"synthetic": 30},
                    "embedding_status": {"embedded": 30},
                    "embedding_model": {"text-embedding-3-small": 30},
                },
                "contributing_versions": ["braincrew-evaluation-dataset@2.0.0"],
                "generated_at": "2026-07-20T06:30:00Z",
            },
        )
    if request.url.path.startswith("/v1/evaluation/attachments/"):
        attachment_id = request.url.path.split("/")[-2]
        return httpx.Response(
            200,
            json={
                "schema_version": "ax-parse-observation-v1",
                "attachment_id": attachment_id,
                "lifecycle_state": "materialized",
                "parse_state": "succeeded",
                "materialization_state": "materialized",
                "parse_available": True,
                "parser_name": "ax-docx-parser",
                "parser_version": "1.0.0",
                "failure_code": None,
                "extracted_text": "synthetic public rule",
                "extracted_text_digest": "sha256:"
                + hashlib.sha256(b"synthetic public rule").hexdigest(),
                "text_truncated": False,
                "evidence_spans": [],
                "headings": [],
                "metadata": {"language": "ko"},
                "table": None,
                "list": None,
                "unavailable_fields": ["table", "list"],
            },
        )
    raise AssertionError(f"unexpected request: {request.url}")


def _capability_manifests() -> dict[str, CapabilityManifest]:
    manifests: dict[str, CapabilityManifest] = {}
    for role in ("Employee", "Executive", "HRPractitioner"):
        adapter = AxHttpAdapter(
            AxHttpAdapterConfig(
                base_url="https://ax.example.test",
                sut_commit_sha=PINNED_AX_SHA,
                tenant_id="00000000-0000-4000-8000-000000000015",
                user_id="evaluation-plane",
                roles=(role,),
            ),
            transport=httpx.MockTransport(_capability_handler),
        )
        manifests[role] = adapter.preflight(
            context=AxRequestContext(
                run_id="issue-15-preflight",
                case_id=f"preflight-{role}",
                eval_correlation_id=f"issue-15-preflight-{role}",
            ),
            corpus_id="ax-visible-retrieval:00000000-0000-4000-8000-000000000015",
            corpus_version="retrieval-inventory-v1",
        )
    return manifests


def test_execute_live_preflight_calls_the_pinned_adapter_and_preserves_capabilities(
    monkeypatch: MonkeyPatch,
) -> None:
    assert hasattr(live_verification, "execute_live_preflight")
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )

    artifact = live_verification.execute_live_preflight(
        preflight_id="adapter-capability-preflight",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_complete_environment(),
        transport=httpx.MockTransport(_capability_handler),
    )

    assert set(artifact.capability_manifests) == {
        "Employee",
        "Executive",
        "HRPractitioner",
    }
    assert all(
        manifest.sut_commit_sha == PINNED_AX_SHA
        for manifest in artifact.capability_manifests.values()
    )
    assert artifact.execution_identity is not None
    assert artifact.execution_identity.authorization_roles == (
        "Employee",
        "Executive",
        "HRPractitioner",
    )
    assert artifact.execution_identity.corpora["Executive"].digest == "sha256:" + "b" * 64
    assert artifact.execution_identity.prompt.id == "ax-answer-prompt-v1"
    assert artifact.execution_identity.prompt.digest == "sha256:" + "b" * 64
    assert artifact.execution_identity.model.parameters == {"temperature": 0}
    with pytest.raises(TypeError):
        artifact.execution_identity.model.parameters["temperature"] = 1
    assert artifact.execution_identity.parsing_attachment_mapping == {
        f"synthetic-rule-{case_number:03d}": (f"00000000-0000-4000-8000-{case_number:012d}")
        for case_number in range(15, 21)
    }
    with pytest.raises(TypeError):
        artifact.execution_identity.corpora["Executive"] = artifact.execution_identity.corpora[
            "Employee"
        ]
    with pytest.raises(TypeError):
        artifact.execution_identity.parsing_attachment_mapping["synthetic-rule-015"] = (
            "00000000-0000-4000-8000-000000000099"
        )
    assert artifact.execution_identity.evaluator_versions == {
        "grounded": "grounded-answer-v1",
        "operational": "operational-v1",
        "parsing": "parsing-quality-v1",
        "retrieval": "retrieval-quality-v1",
    }
    with pytest.raises(TypeError):
        operator.setitem(
            artifact.execution_identity.evaluator_versions,
            "parsing",
            "mutated-version",
        )
    assert artifact.execution_identity.adapter_versions == {
        "grounded": "ax-sut-http-v1",
        "parsing": "ax-sut-http-v1",
        "retrieval": "ax-sut-http-v1",
    }
    with pytest.raises(TypeError):
        operator.setitem(
            artifact.execution_identity.adapter_versions,
            "parsing",
            "mutated-adapter",
        )
    executive_capability = artifact.capability_manifests["Executive"]
    assert isinstance(executive_capability.attempts, tuple)
    with pytest.raises(TypeError):
        operator.setitem(
            executive_capability.dependencies,
            "postgresql",
            "mutated",
        )
    with pytest.raises(TypeError):
        operator.setitem(
            executive_capability.operations,
            "parse",
            executive_capability.operations["parse"],
        )
    with pytest.raises(TypeError):
        operator.setitem(
            executive_capability.corpus.counts["record_kind"],
            "seed",
            31,
        )
    with pytest.raises(TypeError):
        executive_capability.corpus.principal_roles.append("Employee")
    with pytest.raises(TypeError):
        executive_capability.corpus.contributing_versions.append("mutated-version")
    with pytest.raises(TypeError):
        artifact.capability_manifests["Executive"] = executive_capability
    assert artifact.state == "READY"
    assert artifact.blockers == ()


def test_execute_live_preflight_persists_an_unreachable_sut_as_an_access_blocker(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )

    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    artifact = live_verification.execute_live_preflight(
        preflight_id="unreachable-ax",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_complete_environment(),
        transport=httpx.MockTransport(unreachable),
    )

    assert artifact.state == "BLOCKED"
    assert [(blocker.code, blocker.category) for blocker in artifact.blockers] == [
        ("LIVE_AX_PREFLIGHT_UNREACHABLE", "access")
    ]
    assert artifact.capability_manifests == {}


def test_live_preflight_blocks_a_dirty_evaluation_plane_before_live_execution() -> None:
    artifact = build_live_preflight_artifact(
        preflight_id="dirty-evaluation-plane",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=True),
        environment={},
    )

    assert "LIVE_EVALUATION_PLANE_DIRTY" in {blocker.code for blocker in artifact.blockers}


def test_live_preflight_blocks_a_sut_corpus_digest_mismatch() -> None:
    manifests = _capability_manifests()
    environment = _complete_environment()
    corpus_identities = json.loads(environment["AX_CORPUS_IDENTITIES_JSON"])
    corpus_identities["Executive"]["digest"] = "sha256:" + "d" * 64
    environment["AX_CORPUS_IDENTITIES_JSON"] = json.dumps(corpus_identities, sort_keys=True)

    assert "capability_manifests" in inspect.signature(build_live_preflight_artifact).parameters
    artifact = build_live_preflight_artifact(
        preflight_id="known-capability-gaps",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=environment,
        capability_manifests=manifests,
    )

    capability_blockers = [
        blocker for blocker in artifact.blockers if blocker.category == "capability"
    ]
    assert [(blocker.code, blocker.detail) for blocker in capability_blockers] == [
        (
            "LIVE_CORPUS_IDENTITY_MISMATCH",
            "Executive: AX-visible corpus does not match the pinned identity",
        )
    ]
    assert artifact.capability_manifests["Executive"].model_dump(mode="json") == manifests[
        "Executive"
    ].model_dump(mode="json")


def test_live_preflight_blocks_unproven_dataset_corpus_provenance() -> None:
    manifests = _capability_manifests()
    unproven_corpus = manifests["Executive"].corpus.model_copy(
        update={"contributing_versions": ["bprime-2026-07-04"]}
    )
    manifests["Executive"] = manifests["Executive"].model_copy(update={"corpus": unproven_corpus})

    artifact = build_live_preflight_artifact(
        preflight_id="unproven-corpus-provenance",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_complete_environment(),
        capability_manifests=manifests,
    )

    provenance_blockers = [
        blocker
        for blocker in artifact.blockers
        if blocker.code == "LIVE_CORPUS_DATASET_PROVENANCE_MISMATCH"
    ]
    assert [(blocker.code, blocker.required_action) for blocker in provenance_blockers] == [
        (
            "LIVE_CORPUS_DATASET_PROVENANCE_MISMATCH",
            "provision and review a role-visible public or synthetic corpus mapped to "
            "braincrew-evaluation-dataset@2.0.0",
        )
    ]


def test_live_preflight_blocks_missing_role_specific_corpus_identities(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )
    environment = _complete_environment()
    del environment["AX_CORPUS_IDENTITIES_JSON"]

    artifact = build_live_preflight_artifact(
        preflight_id="missing-role-corpus-identities",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=environment,
    )

    assert [(blocker.code, blocker.required_action) for blocker in artifact.blockers] == [
        (
            "LIVE_CORPUS_IDENTITIES_MISSING",
            "provide one frozen AX-visible corpus identity for every Verification "
            "authorization role",
        )
    ]


def test_live_preflight_blocks_missing_parsing_attachment_mapping(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )
    environment = _complete_environment()
    del environment["AX_PARSING_ATTACHMENT_MAP_JSON"]

    artifact = build_live_preflight_artifact(
        preflight_id="missing-parsing-attachment-mapping",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=environment,
    )

    assert [(blocker.code, blocker.required_action) for blocker in artifact.blockers] == [
        (
            "LIVE_PARSING_ATTACHMENT_MAPPING_MISSING",
            "provide reviewed AX attachment UUIDs for all six frozen parsing Verification "
            "documents",
        )
    ]


def test_live_preflight_rejects_an_ax_role_set_that_differs_from_the_dataset(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )
    environment = _complete_environment()
    environment["AX_ROLES"] += ",Manager"

    artifact = build_live_preflight_artifact(
        preflight_id="mismatched-authorization-role-set",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=environment,
    )

    assert [(blocker.code, blocker.category) for blocker in artifact.blockers] == [
        ("LIVE_AUTHORIZATION_ROLE_SET_MISMATCH", "configuration")
    ]


@pytest.mark.parametrize("invalid_parameters", ("[not-json", '{"temperature": NaN}'))
def test_live_preflight_turns_malformed_fixed_identity_inputs_into_blockers(
    monkeypatch: MonkeyPatch,
    invalid_parameters: str,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )
    environment = _complete_environment()
    corpus_identities = json.loads(environment["AX_CORPUS_IDENTITIES_JSON"])
    corpus_identities["Employee"]["digest"] = "not-a-digest"
    environment["AX_CORPUS_IDENTITIES_JSON"] = json.dumps(corpus_identities, sort_keys=True)
    environment["AX_PROMPT_HASH"] = "also-not-a-digest"
    environment["AX_MODEL_PARAMETERS_JSON"] = invalid_parameters

    artifact = build_live_preflight_artifact(
        preflight_id="invalid-fixed-identities",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=environment,
    )

    assert artifact.state == "BLOCKED"
    assert artifact.execution_identity is None
    assert {blocker.code for blocker in artifact.blockers} == {
        "LIVE_CORPUS_IDENTITIES_INVALID",
        "LIVE_PROMPT_HASH_INVALID",
        "LIVE_MODEL_PARAMETERS_INVALID",
    }


def test_execute_live_preflight_records_invalid_adapter_authority_without_http(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )
    environment = _complete_environment()
    environment["AX_TENANT_ID"] = "not-a-uuid"

    artifact = live_verification.execute_live_preflight(
        preflight_id="invalid-adapter-authority",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=environment,
        transport=httpx.MockTransport(
            lambda request: (_ for _ in ()).throw(AssertionError(f"unexpected HTTP: {request}"))
        ),
    )

    assert artifact.state == "BLOCKED"
    assert [(blocker.code, blocker.category) for blocker in artifact.blockers] == [
        ("LIVE_ADAPTER_CONFIGURATION_INVALID", "configuration")
    ]


def test_live_preflight_fails_closed_for_incomplete_or_mismatched_capability_evidence(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        live_verification,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )
    manifests = _capability_manifests()
    incomplete_operations = dict(manifests["Executive"].operations)
    del incomplete_operations["corpus_identity"]
    manifests["Executive"] = manifests["Executive"].model_copy(
        update={"sut_commit_sha": "f" * 40, "operations": incomplete_operations}
    )

    artifact = build_live_preflight_artifact(
        preflight_id="incomplete-capability",
        validation=validate_dataset_bundle(V2_MANIFEST_PATH),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_complete_environment(),
        capability_manifests=manifests,
    )

    assert [(blocker.code, blocker.category) for blocker in artifact.blockers] == [
        ("LIVE_CAPABILITY_SUT_SHA_MISMATCH", "provenance"),
        ("LIVE_REQUIRED_OPERATION_UNAVAILABLE", "capability"),
    ]
    assert artifact.blockers[1].detail == "Executive/corpus_identity: AX_OPERATION_NOT_DECLARED"
