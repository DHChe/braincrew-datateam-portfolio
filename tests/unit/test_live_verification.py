from __future__ import annotations

import inspect
import operator
from pathlib import Path

import httpx
import pytest
from pytest import MonkeyPatch

import braincrew.live_verification as live_verification
from braincrew.ax_http_adapter import (
    AxHttpAdapter,
    AxHttpAdapterConfig,
    AxRequestContext,
)
from braincrew.dataset_registry import validate_dataset_bundle
from braincrew.live_verification import build_live_preflight_artifact
from braincrew.repository import RepositoryState

PINNED_AX_SHA = "c318b2192006bdb36a5bd5b3a2bc403425b45701"


def _complete_environment() -> dict[str, str]:
    return {
        "AX_BASE_URL": "https://ax.example.test",
        "AX_REPOSITORY": "/synthetic/ax",
        "AX_TENANT_ID": "00000000-0000-4000-8000-000000000015",
        "AX_USER_ID": "evaluation-plane",
        "AX_ROLES": "Executive",
        "AX_CORPUS_ID": "synthetic-hr-v1",
        "AX_CORPUS_VERSION": "1.0.0",
        "AX_CORPUS_DIGEST": "sha256:" + "a" * 64,
        "AX_PROMPT_ID": "ax-answer-prompt-v1",
        "AX_PROMPT_HASH": "sha256:" + "b" * 64,
        "AX_MODEL_PROVIDER": "openai",
        "AX_MODEL_NAME": "pinned-model",
        "AX_MODEL_PARAMETERS_JSON": '{"temperature": 0}',
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
                    "/v1/retrieval/search": {"post": {}},
                    "/v1/answers/generate": {"post": {}},
                    "/v1/retrieval/source-text/{record_kind}/{record_id}": {"get": {}},
                },
            },
        )
    raise AssertionError(f"unexpected request: {request.url}")


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
        validation=validate_dataset_bundle(Path("datasets/dataset_manifest_v1.json")),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_complete_environment(),
        transport=httpx.MockTransport(_capability_handler),
    )

    assert artifact.capability_manifest is not None
    assert artifact.capability_manifest.sut_commit_sha == PINNED_AX_SHA
    assert artifact.execution_identity is not None
    assert artifact.execution_identity.corpus.id == "synthetic-hr-v1"
    assert artifact.execution_identity.corpus.digest == "sha256:" + "a" * 64
    assert artifact.execution_identity.prompt.id == "ax-answer-prompt-v1"
    assert artifact.execution_identity.prompt.digest == "sha256:" + "b" * 64
    assert artifact.execution_identity.model.parameters == {"temperature": 0}
    with pytest.raises(TypeError):
        artifact.execution_identity.model.parameters["temperature"] = 1
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
    assert isinstance(artifact.capability_manifest.attempts, tuple)
    with pytest.raises(TypeError):
        operator.setitem(
            artifact.capability_manifest.dependencies,
            "postgresql",
            "mutated",
        )
    with pytest.raises(TypeError):
        operator.setitem(
            artifact.capability_manifest.operations,
            "parse",
            artifact.capability_manifest.operations["parse"],
        )
    assert [blocker.code for blocker in artifact.blockers if blocker.category == "capability"] == [
        "LIVE_REQUIRED_OPERATION_UNAVAILABLE",
        "LIVE_CORPUS_IDENTITY_UNVERIFIED",
    ]


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
        validation=validate_dataset_bundle(Path("datasets/dataset_manifest_v1.json")),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_complete_environment(),
        transport=httpx.MockTransport(unreachable),
    )

    assert artifact.state == "BLOCKED"
    assert [(blocker.code, blocker.category) for blocker in artifact.blockers] == [
        ("LIVE_AX_PREFLIGHT_UNREACHABLE", "access")
    ]
    assert artifact.capability_manifest is None


def test_live_preflight_blocks_a_dirty_evaluation_plane_before_live_execution() -> None:
    artifact = build_live_preflight_artifact(
        preflight_id="dirty-evaluation-plane",
        validation=validate_dataset_bundle(Path("datasets/dataset_manifest_v1.json")),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=True),
        environment={},
    )

    assert "LIVE_EVALUATION_PLANE_DIRTY" in {blocker.code for blocker in artifact.blockers}


def test_live_preflight_blocks_the_known_parse_and_corpus_capability_gaps() -> None:
    adapter = AxHttpAdapter(
        AxHttpAdapterConfig(
            base_url="https://ax.example.test",
            sut_commit_sha=PINNED_AX_SHA,
            tenant_id="00000000-0000-4000-8000-000000000015",
            user_id="evaluation-plane",
            roles=("Executive",),
        ),
        transport=httpx.MockTransport(_capability_handler),
    )
    capability_manifest = adapter.preflight(
        context=AxRequestContext(
            run_id="issue-15-preflight",
            case_id="preflight",
            eval_correlation_id="issue-15-preflight",
        ),
        corpus_id="synthetic-hr-v1",
        corpus_version="1.0.0",
    )

    assert "capability_manifest" in inspect.signature(build_live_preflight_artifact).parameters
    artifact = build_live_preflight_artifact(
        preflight_id="known-capability-gaps",
        validation=validate_dataset_bundle(Path("datasets/dataset_manifest_v1.json")),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment={},
        capability_manifest=capability_manifest,
    )

    capability_blockers = [
        blocker for blocker in artifact.blockers if blocker.category == "capability"
    ]
    assert [(blocker.code, blocker.detail) for blocker in capability_blockers] == [
        (
            "LIVE_REQUIRED_OPERATION_UNAVAILABLE",
            "parse: AX_PARSE_OBSERVABILITY_UNAVAILABLE",
        ),
        (
            "LIVE_CORPUS_IDENTITY_UNVERIFIED",
            "synthetic-hr-v1@1.0.0: AX_CORPUS_IDENTITY_NOT_EXPOSED",
        ),
    ]
    assert artifact.capability_manifest is not None
    assert artifact.capability_manifest.model_dump(mode="json") == capability_manifest.model_dump(
        mode="json"
    )


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
    environment["AX_CORPUS_DIGEST"] = "not-a-digest"
    environment["AX_PROMPT_HASH"] = "also-not-a-digest"
    environment["AX_MODEL_PARAMETERS_JSON"] = invalid_parameters

    artifact = build_live_preflight_artifact(
        preflight_id="invalid-fixed-identities",
        validation=validate_dataset_bundle(Path("datasets/dataset_manifest_v1.json")),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=environment,
    )

    assert artifact.state == "BLOCKED"
    assert artifact.execution_identity is None
    assert [blocker.code for blocker in artifact.blockers] == [
        "LIVE_CORPUS_DIGEST_INVALID",
        "LIVE_PROMPT_HASH_INVALID",
        "LIVE_MODEL_PARAMETERS_INVALID",
    ]


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
        validation=validate_dataset_bundle(Path("datasets/dataset_manifest_v1.json")),
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
    adapter = AxHttpAdapter(
        AxHttpAdapterConfig(
            base_url="https://ax.example.test",
            sut_commit_sha=PINNED_AX_SHA,
            tenant_id="00000000-0000-4000-8000-000000000015",
            user_id="evaluation-plane",
            roles=("Executive",),
        ),
        transport=httpx.MockTransport(_capability_handler),
    )
    capability_manifest = adapter.preflight(
        context=AxRequestContext(
            run_id="incomplete-capability",
            case_id="preflight",
            eval_correlation_id="incomplete-capability",
        ),
        corpus_id="synthetic-hr-v1",
        corpus_version="1.0.0",
    )
    incomplete_operations = dict(capability_manifest.operations)
    del incomplete_operations["parse"]
    incomplete_manifest = capability_manifest.model_copy(
        update={"sut_commit_sha": "f" * 40, "operations": incomplete_operations}
    )

    artifact = build_live_preflight_artifact(
        preflight_id="incomplete-capability",
        validation=validate_dataset_bundle(Path("datasets/dataset_manifest_v1.json")),
        evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
        environment=_complete_environment(),
        capability_manifest=incomplete_manifest,
    )

    assert [(blocker.code, blocker.category) for blocker in artifact.blockers] == [
        ("LIVE_CAPABILITY_SUT_SHA_MISMATCH", "provenance"),
        ("LIVE_REQUIRED_OPERATION_UNAVAILABLE", "capability"),
        ("LIVE_CORPUS_IDENTITY_UNVERIFIED", "capability"),
    ]
    assert artifact.blockers[1].detail == "parse: AX_OPERATION_NOT_DECLARED"
