from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from braincrew.ax_http_adapter import (
    AxHttpAdapter,
    AxHttpAdapterConfig,
    AxHttpFailure,
    AxRequestContext,
    AxTransientFailure,
    CapabilityManifest,
    load_ax_http_contract,
    write_capability_manifest,
)

PINNED_AX_SHA = "3bb27f870d244fbc8debba91eb408e825caa9e03"
TENANT_ID = "11111111-1111-1111-1111-111111111111"
USER_ID = "22222222-2222-2222-2222-222222222222"


def test_preflight_records_evaluation_operations_without_claiming_a_corpus_probe() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health/ready":
            return httpx.Response(
                200,
                json={
                    "status": "ready",
                    "service": "ax-engine-api",
                    "dependencies": {
                        "postgresql": "ready",
                        "redis": "ready",
                        "neo4j": "ready",
                        "clamav": "ready",
                        "worker": "ready",
                    },
                },
            )
        if request.url.path == "/openapi.json":
            return httpx.Response(
                200,
                json={
                    "openapi": "3.1.0",
                    "info": {"title": "AX Portfolio HR/Labor Engine", "version": "0.1.0"},
                    "paths": {
                        "/v1/evaluation/corpus-identity": {"get": {}},
                        "/v1/evaluation/attachments/{attachment_id}/parse-observation": {"get": {}},
                        "/v1/retrieval/search": {"post": {}},
                        "/v1/answers/generate": {"post": {}},
                        "/v1/retrieval/source-text/{record_kind}/{record_id}": {"get": {}},
                    },
                },
            )
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    adapter = AxHttpAdapter(
        AxHttpAdapterConfig(
            base_url="https://ax.example.test",
            sut_commit_sha=PINNED_AX_SHA,
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            roles=("Executive",),
        ),
        transport=httpx.MockTransport(handler),
    )

    manifest = adapter.preflight(
        context=AxRequestContext(
            run_id="run-7",
            case_id="preflight",
            eval_correlation_id="eval-7-preflight",
        ),
        corpus_id="synthetic-hr-v1",
        corpus_version="1.0.0",
    )

    assert manifest.schema_version == "ax-capability-manifest-v1"
    assert manifest.adapter_version == "ax-sut-http-v1"
    assert manifest.sut_commit_sha == PINNED_AX_SHA
    assert manifest.sut_repository == "https://github.com/DHChe/AX_portfolio"
    assert manifest.request.run_id == "run-7"
    assert manifest.request.case_id == "preflight"
    assert manifest.request.corpus_id == "synthetic-hr-v1"
    assert manifest.request.corpus_version == "1.0.0"
    assert manifest.readiness_status == "ready"
    assert manifest.corpus.id == "synthetic-hr-v1"
    assert manifest.corpus.version == "1.0.0"
    assert manifest.corpus.verified_by_sut is False
    assert manifest.corpus.reason == "AX_CORPUS_IDENTITY_NOT_PROBED"
    assert manifest.operations["preflight"].available is True
    assert manifest.operations["retrieve"].available is True
    assert manifest.operations["answer"].available is True
    assert manifest.operations["source_text"].available is True
    assert manifest.operations["corpus_identity"].available is True
    assert manifest.operations["parse"].available is True
    assert [attempt.operation for attempt in manifest.attempts] == ["preflight", "preflight"]
    assert all(attempt.outcome == "success" for attempt in manifest.attempts)


def test_packaged_contract_locks_field_mappings_and_response_schema_digests() -> None:
    contract = load_ax_http_contract()

    assert contract.sut_commit_sha == PINNED_AX_SHA

    retrieve = contract.operations["retrieve"]
    assert retrieve.request_mapping["query"] == "body.query"
    assert retrieve.request_mapping["top_k"] == "body.top_k"
    assert retrieve.response_mapping["candidates"] == "body.candidates"
    assert (
        retrieve.expected_schema_digest
        == "sha256:3d7cc3cbfe89e1c4ae795dd5167c211cb560a9089f9f09b1bc56aa82bc04ea8b"
    )

    parse = contract.operations["parse"]
    assert parse.path == "/v1/evaluation/attachments/{attachment_id}/parse-observation"
    assert parse.request_mapping["attachment_id"] == "path.attachment_id"
    assert parse.response_mapping["attachment_id"] == "body.attachment_id"
    assert (
        parse.expected_schema_digest
        == "sha256:988f71991c9075a1be7bb411742dfde11b6537cd8f7433cecf76afd679627810"
    )

    corpus_identity = contract.operations["corpus_identity"]
    assert corpus_identity.path == "/v1/evaluation/corpus-identity"
    assert corpus_identity.request_mapping["roles"] == "header.x-ax-roles"
    assert corpus_identity.response_mapping["corpus_digest"] == "body.corpus_digest"
    assert (
        corpus_identity.expected_schema_digest
        == "sha256:3203d2d6358152e93e2396e76ceb619d3a83a0443bfd95d42b743ffdd65abed5"
    )


def test_preflight_uses_the_same_bounded_retry_policy_as_live_operations() -> None:
    health_attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal health_attempts
        if request.url.path == "/health/ready":
            health_attempts += 1
            if health_attempts == 1:
                return httpx.Response(503, json={"detail": "starting"})
            return httpx.Response(
                200,
                json={"status": "ready", "service": "ax-engine-api", "dependencies": {}},
            )
        if request.url.path == "/openapi.json":
            return httpx.Response(
                200,
                json={"openapi": "3.1.0", "info": {}, "paths": {}},
            )
        raise AssertionError(f"unexpected request: {request.url}")

    manifest = _adapter(handler).preflight(
        context=AxRequestContext(
            run_id="run-7",
            case_id="preflight-retry",
            eval_correlation_id="eval-7-preflight-retry",
        ),
        corpus_id="synthetic-hr-v1",
        corpus_version="1.0.0",
    )

    assert health_attempts == 2
    assert [attempt.outcome for attempt in manifest.attempts] == [
        "retryable_http",
        "success",
        "success",
    ]


def test_capability_manifest_is_written_once_and_round_trips(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health/ready":
            return httpx.Response(
                200,
                json={"status": "ready", "service": "ax-engine-api", "dependencies": {}},
            )
        return httpx.Response(
            200,
            json={"openapi": "3.1.0", "info": {}, "paths": {}},
        )

    manifest = _adapter(handler).preflight(
        context=AxRequestContext(
            run_id="run-7",
            case_id="preflight-write",
            eval_correlation_id="eval-7-preflight-write",
        ),
        corpus_id="synthetic-hr-v1",
        corpus_version="1.0.0",
    )
    path = tmp_path / "ax-capability.json"

    written = write_capability_manifest(manifest, path)

    assert written == path
    assert CapabilityManifest.model_validate_json(path.read_text(encoding="utf-8")) == manifest
    original = path.read_bytes()
    with pytest.raises(FileExistsError):
        write_capability_manifest(manifest, path)
    assert path.read_bytes() == original


def test_retrieve_preserves_request_identity_and_ax_response_provenance() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json=_retrieval_response())

    adapter = _adapter(handler)
    context = AxRequestContext(
        run_id="run-7",
        case_id="retrieval-1",
        eval_correlation_id="eval-7-retrieval-1",
    )

    observation = adapter.retrieve(context=context, query="징계 절차", top_k=5)

    assert observation.context == context
    assert observation.request.operation == "retrieve"
    assert observation.request.tenant_id == TENANT_ID
    assert observation.request.user_id == USER_ID
    assert observation.request.roles == ("Executive",)
    assert observation.request.timeout_seconds == 10.0
    assert observation.request.query == "징계 절차"
    assert observation.request.top_k == 5
    assert observation.query == "징계 절차"
    assert observation.top_k == 5
    assert observation.response.correlation_id == "retrieval:fixture"
    assert observation.response.candidates[0].record_id == "chunk-1"
    assert observation.response.candidates[0].visibility_decision == {
        "allowed": True,
        "reason": "executive_full_access",
    }
    assert len(observation.attempts) == 1
    assert observation.attempts[0].outcome == "success"
    assert captured_request is not None
    assert captured_request.headers["x-ax-tenant-id"] == TENANT_ID
    assert captured_request.headers["x-ax-roles"] == "Executive"
    assert captured_request.headers["x-eval-run-id"] == "run-7"
    assert captured_request.headers["x-eval-case-id"] == "retrieval-1"
    assert captured_request.headers["x-eval-correlation-id"] == "eval-7-retrieval-1"
    assert json.loads(captured_request.read()) == {"query": "징계 절차", "top_k": 5}


def test_retrieve_retries_a_timeout_and_preserves_both_attempts() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        if request_count == 1:
            raise httpx.ReadTimeout("fixture timeout", request=request)
        return httpx.Response(200, json=_retrieval_response())

    observation = _adapter(handler).retrieve(
        context=AxRequestContext(
            run_id="run-7",
            case_id="retrieval-timeout",
            eval_correlation_id="eval-7-retrieval-timeout",
        ),
        query="징계 절차",
        top_k=5,
    )

    assert request_count == 2
    assert [attempt.attempt_number for attempt in observation.attempts] == [1, 2]
    assert [attempt.outcome for attempt in observation.attempts] == ["timeout", "success"]


def test_retrieve_retries_http_429_and_preserves_the_retryable_failure() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        if request_count == 1:
            return httpx.Response(429, json={"detail": "rate_limited"})
        return httpx.Response(200, json=_retrieval_response())

    observation = _adapter(handler).retrieve(
        context=AxRequestContext(
            run_id="run-7",
            case_id="retrieval-429",
            eval_correlation_id="eval-7-retrieval-429",
        ),
        query="징계 절차",
        top_k=5,
    )

    assert request_count == 2
    assert [attempt.status_code for attempt in observation.attempts] == [429, 200]
    assert [attempt.outcome for attempt in observation.attempts] == [
        "retryable_http",
        "success",
    ]


def test_retrieve_stops_after_two_retries_for_http_5xx() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(503, json={"detail": "service_unavailable"})

    with pytest.raises(AxTransientFailure) as caught:
        _adapter(handler).retrieve(
            context=AxRequestContext(
                run_id="run-7",
                case_id="retrieval-503",
                eval_correlation_id="eval-7-retrieval-503",
            ),
            query="징계 절차",
            top_k=5,
        )

    assert request_count == 3
    assert caught.value.failure_code == "AX_TRANSIENT_RETRIES_EXHAUSTED"
    assert caught.value.request.case_id == "retrieval-503"
    assert [attempt.status_code for attempt in caught.value.attempts] == [503, 503, 503]
    assert all(attempt.outcome == "retryable_http" for attempt in caught.value.attempts)


def test_retrieve_does_not_retry_a_permanent_http_failure() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(401, json={"detail": "bearer_token_required"})

    with pytest.raises(AxHttpFailure) as caught:
        _adapter(handler).retrieve(
            context=AxRequestContext(
                run_id="run-7",
                case_id="retrieval-401",
                eval_correlation_id="eval-7-retrieval-401",
            ),
            query="징계 절차",
            top_k=5,
        )

    assert request_count == 1
    assert caught.value.failure_code == "AX_PERMANENT_HTTP_FAILURE"
    assert caught.value.detail == "bearer_token_required"
    assert caught.value.request.run_id == "run-7"
    assert caught.value.request.case_id == "retrieval-401"
    assert caught.value.request.query == "징계 절차"
    assert len(caught.value.attempts) == 1
    assert caught.value.attempts[0].status_code == 401
    assert caught.value.attempts[0].outcome == "permanent_http"


def test_retrieve_rejects_a_schema_mismatch_without_retrying() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            200,
            json={"query": "징계 절차", "top_k": 5, "candidates": []},
        )

    with pytest.raises(AxHttpFailure) as caught:
        _adapter(handler).retrieve(
            context=AxRequestContext(
                run_id="run-7",
                case_id="retrieval-schema",
                eval_correlation_id="eval-7-retrieval-schema",
            ),
            query="징계 절차",
            top_k=5,
        )

    assert request_count == 1
    assert caught.value.failure_code == "AX_RESPONSE_SCHEMA_MISMATCH"
    assert len(caught.value.attempts) == 1
    assert caught.value.attempts[0].status_code == 200
    assert caught.value.attempts[0].outcome == "schema_error"


def test_answer_preserves_structured_claims_citations_and_provider_metadata() -> None:
    captured_request: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_request
        captured_request = request
        return httpx.Response(200, json=_answer_response())

    context = AxRequestContext(
        run_id="run-7",
        case_id="answer-1",
        eval_correlation_id="eval-7-answer-1",
    )
    observation = _adapter(handler).answer(
        context=context,
        query="징계 절차",
        top_k=5,
        evidence_limit=3,
    )

    assert observation.context == context
    assert observation.response.answer_mode == "direct_grounded"
    assert observation.response.structured_answer.answer == "소명 기회를 부여해야 합니다."
    assert observation.response.citations[0].record_id == "chunk-1"
    assert observation.response.provider_metadata["model"] == "fixture-answer-v1"
    assert observation.response.answer_correlation_id == "answer:fixture"
    assert len(observation.attempts) == 1
    assert captured_request is not None
    assert json.loads(captured_request.read()) == {
        "query": "징계 절차",
        "top_k": 5,
        "evidence_limit": 3,
    }


def test_source_text_preserves_permission_checked_text_and_provenance() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/retrieval/source-text/source_chunk/chunk-1"
        return httpx.Response(
            200,
            headers={"x-correlation-id": "http:fixture"},
            json={
                "record_kind": "source_chunk",
                "record_id": "chunk-1",
                "text": "징계는 소명 기회를 포함한다.",
                "provenance": {
                    "source_id": "rule-1",
                    "source_text_digest": "sha256:fixture",
                },
                "correlation_id": "source:fixture",
            },
        )

    observation = _adapter(handler).source_text(
        context=AxRequestContext(
            run_id="run-7",
            case_id="source-1",
            eval_correlation_id="eval-7-source-1",
        ),
        record_kind="source_chunk",
        record_id="chunk-1",
    )

    assert observation.response.text == "징계는 소명 기회를 포함한다."
    assert observation.response.provenance["source_id"] == "rule-1"
    assert observation.response.correlation_id == "source:fixture"
    assert observation.attempts[0].response_correlation_id == "http:fixture"


def test_adapter_config_rejects_a_non_uuid_tenant_before_http() -> None:
    with pytest.raises(ValidationError, match="tenant_id"):
        AxHttpAdapterConfig(
            base_url="https://ax.example.test",
            sut_commit_sha=PINNED_AX_SHA,
            tenant_id="demo-tenant",
            user_id=USER_ID,
            roles=("Executive",),
        )


def test_adapter_config_never_serializes_the_bearer_credential() -> None:
    config = AxHttpAdapterConfig(
        base_url="https://ax.example.test",
        sut_commit_sha=PINNED_AX_SHA,
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        roles=("Executive",),
        bearer_token="secret-token",
    )

    assert "bearer_token" not in config.model_dump()
    assert "secret-token" not in repr(config)


def _adapter(handler: Callable[[httpx.Request], httpx.Response]) -> AxHttpAdapter:
    return AxHttpAdapter(
        AxHttpAdapterConfig(
            base_url="https://ax.example.test",
            sut_commit_sha=PINNED_AX_SHA,
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            roles=("Executive",),
        ),
        transport=httpx.MockTransport(handler),
    )


def _retrieval_response() -> dict[str, object]:
    candidate = {
        "vector_record_id": "vec-1",
        "record_kind": "source_chunk",
        "record_id": "chunk-1",
        "snippet": "징계는 소명 기회를 포함한다.",
        "source_id": "rule-1",
        "chunk_id": "chunk-1",
        "evidence_span_id": None,
        "source_class": "company_rule",
        "authority_level": 30,
        "provenance": {"source_id": "rule-1", "chunk_id": "chunk-1"},
        "metadata": {"answer_use": "grounding_allowed"},
        "retrieval_score": 0.12,
        "retrieval_score_kind": "pgvector_l2_distance",
        "visibility_decision": {"allowed": True, "reason": "executive_full_access"},
        "synthetic": True,
        "demo_company": True,
        "corpus_mode": "demo",
    }
    return {
        "query": "징계 절차",
        "top_k": 5,
        "max_top_k": 10,
        "answer_mode": "direct_grounded",
        "candidates": [candidate],
        "matched_evidence": [candidate],
        "risk_tags": [],
        "visibility_decisions": [
            {
                "vector_record_id": "vec-1",
                "allowed": True,
                "reason": "executive_full_access",
            }
        ],
        "correlation_id": "retrieval:fixture",
        "audit_recorded": True,
        "precedent_capability_enabled": True,
        "provider_free": True,
        "notices": [],
        "currentness_checks": [],
        "natural_language_answer_generated": False,
    }


def _answer_response() -> dict[str, object]:
    citation = {
        "source_id": "rule-1",
        "chunk_id": "chunk-1",
        "evidence_span_id": None,
        "record_kind": "source_chunk",
        "record_id": "chunk-1",
        "source_class": "company_rule",
        "authority_level": 30,
        "synthetic": True,
        "demo_company": True,
        "corpus_mode": "demo",
        "snippet": "징계는 소명 기회를 포함한다.",
        "claim_paths": ["answer"],
    }
    return {
        "query": "징계 절차",
        "answer_mode": "direct_grounded",
        "structured_answer": {
            "summary": "소명 기회가 필요합니다.",
            "answer": "소명 기회를 부여해야 합니다.",
            "grounds": ["취업규칙의 징계 절차"],
            "review_points": [],
            "additional_checks": [],
            "risk_warning": "",
            "citations": [citation],
        },
        "citations": [citation],
        "reference_context": [],
        "retrieval_correlation_id": "retrieval:fixture",
        "answer_correlation_id": "answer:fixture",
        "audit_recorded": True,
        "natural_language_answer_generated": True,
        "provider_metadata": {
            "provider_adapter": "fixture",
            "model": "fixture-answer-v1",
            "provider_store": False,
            "llm_call_performed": True,
            "llm_call_succeeded": True,
        },
        "evidence_packaging": {
            "selected_count": 1,
            "selected_record_ids": ["chunk-1"],
            "selected_source_ids": ["rule-1"],
            "skipped_record_ids": [],
            "char_cap": 12000,
            "total_chars": 20,
            "truncated": False,
            "llm_evidence_transfer_allowed": True,
        },
    }
