from __future__ import annotations

from collections.abc import Callable

import httpx
import pytest
from pydantic import ValidationError

from braincrew.ax_http_adapter import (
    AxHttpAdapter,
    AxHttpAdapterConfig,
    AxHttpFailure,
    AxRequestContext,
    CorpusIdentityResponse,
    ParseObservationResponse,
)

PINNED_AX_SHA = "72805930d9addd8ea41743d1922acf8de621c3f8"
TENANT_ID = "11111111-1111-1111-1111-111111111111"
USER_ID = "22222222-2222-2222-2222-222222222222"
TEXT_DIGEST = "sha256:" + "1" * 64
CORPUS_DIGEST = "sha256:" + "2" * 64


def test_corpus_identity_preserves_principal_request_and_strict_response() -> None:
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(200, json=_corpus_identity_response())

    context = _context("corpus-HRPractitioner")
    observation = _adapter(handler).corpus_identity(context=context)

    assert observation.context == context
    assert observation.request.operation == "corpus_identity"
    assert observation.request.roles == ("HRPractitioner",)
    assert observation.response.schema_version == "ax-corpus-identity-v1"
    assert observation.response.principal_roles == ["HRPractitioner"]
    assert observation.response.corpus_digest == CORPUS_DIGEST
    assert [attempt.outcome for attempt in observation.attempts] == ["success"]
    assert captured is not None
    assert captured.url.path == "/v1/evaluation/corpus-identity"
    assert captured.headers["x-ax-roles"] == "HRPractitioner"
    assert captured.headers["x-eval-case-id"] == "corpus-HRPractitioner"


def test_parse_safely_encodes_the_attachment_and_preserves_complete_evidence() -> None:
    captured: httpx.Request | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured
        captured = request
        return httpx.Response(200, json=_parse_response(attachment_id="attachment/1"))

    context = _context("synthetic-rule-015")
    observation = _adapter(handler).parse(
        context=context,
        attachment_id="attachment/1",
    )

    assert observation.context == context
    assert observation.request.operation == "parse"
    assert observation.request.attachment_id == "attachment/1"
    assert observation.request.roles == ("HRPractitioner",)
    assert observation.response.attachment_id == "attachment/1"
    assert observation.response.parser_name == "ax-fixture-parser"
    assert observation.response.extracted_text_digest == TEXT_DIGEST
    assert observation.response.evidence_spans[0].start_char == 0
    assert observation.response.evidence_spans[0].end_char == 11
    assert observation.response.evidence_spans[0].source_text_digest == TEXT_DIGEST
    assert observation.attempts[0].outcome == "success"
    assert captured is not None
    assert captured.url.raw_path == (b"/v1/evaluation/attachments/attachment%2F1/parse-observation")


@pytest.mark.parametrize(
    ("status_code", "detail"),
    [
        (400, "evaluation_principal_id_invalid"),
        (401, "evaluation_principal_subject_invalid"),
        (404, "not_found"),
    ],
)
def test_parse_preserves_bounded_permanent_detail_without_retry(
    status_code: int,
    detail: str,
) -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(status_code, json={"detail": detail})

    with pytest.raises(AxHttpFailure) as caught:
        _adapter(handler).parse(
            context=_context(f"parse-{status_code}"),
            attachment_id="00000000-0000-0000-0000-000000000015",
        )

    assert request_count == 1
    assert caught.value.failure_code == "AX_PERMANENT_HTTP_FAILURE"
    assert caught.value.detail == detail
    assert len(caught.value.attempts) == 1
    assert caught.value.attempts[0].outcome == "permanent_http"


def test_parse_preserves_the_existing_bounded_retry_policy() -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        if request_count < 3:
            return httpx.Response(503, json={"detail": "starting"})
        return httpx.Response(
            200,
            json=_parse_response(attachment_id="00000000-0000-0000-0000-000000000015"),
        )

    observation = _adapter(handler).parse(
        context=_context("parse-retry"),
        attachment_id="00000000-0000-0000-0000-000000000015",
    )

    assert request_count == 3
    assert [attempt.outcome for attempt in observation.attempts] == [
        "retryable_http",
        "retryable_http",
        "success",
    ]


def _adapter(handler: Callable[[httpx.Request], httpx.Response]) -> AxHttpAdapter:
    return AxHttpAdapter(
        AxHttpAdapterConfig(
            base_url="https://ax.example.test",
            sut_commit_sha=PINNED_AX_SHA,
            tenant_id=TENANT_ID,
            user_id=USER_ID,
            roles=("HRPractitioner",),
        ),
        transport=httpx.MockTransport(handler),
    )


def _context(case_id: str) -> AxRequestContext:
    return AxRequestContext(
        run_id="run-live-substrate",
        case_id=case_id,
        eval_correlation_id=f"eval-live-{case_id}",
    )


def _corpus_identity_response() -> dict[str, object]:
    return {
        "schema_version": "ax-corpus-identity-v1",
        "corpus_id": f"ax-visible-retrieval:{TENANT_ID}",
        "corpus_version": "retrieval-inventory-v1",
        "corpus_digest": CORPUS_DIGEST,
        "principal_roles": ["HRPractitioner"],
        "inventory_count": 6,
        "counts": {
            "record_kind": {"source_chunk": 6},
            "corpus_mode": {"demo": 6},
        },
        "contributing_versions": ["braincrew-evaluation-dataset-2.0.0"],
        "generated_at": "2026-07-22T00:00:00Z",
    }


def _parse_response(*, attachment_id: str) -> dict[str, object]:
    return {
        "schema_version": "ax-parse-observation-v1",
        "attachment_id": attachment_id,
        "lifecycle_state": "materialized",
        "parse_state": "succeeded",
        "materialization_state": "materialized",
        "parse_available": True,
        "parser_name": "ax-fixture-parser",
        "parser_version": "1.0.0",
        "failure_code": None,
        "extracted_text": "징계 절차 원문",
        "extracted_text_digest": TEXT_DIGEST,
        "text_truncated": False,
        "evidence_spans": [
            {
                "id": "span-1",
                "text": "징계 절차 원문",
                "start_char": 0,
                "end_char": 11,
                "source_text_digest": TEXT_DIGEST,
            }
        ],
        "headings": ["징계 절차"],
        "metadata": {"language": "ko"},
        "table": {"columns": ["단계"], "rows": [["소명"]]},
        "list": {"items": ["통지", "소명"], "ordered": True},
        "unavailable_fields": [],
    }


@pytest.mark.parametrize(
    ("model", "payload"),
    [
        (CorpusIdentityResponse, _corpus_identity_response()),
        (ParseObservationResponse, _parse_response(attachment_id="attachment-1")),
    ],
)
def test_live_evaluation_responses_reject_unpublished_fields(
    model: type[CorpusIdentityResponse] | type[ParseObservationResponse],
    payload: dict[str, object],
) -> None:
    payload["unexpected"] = "contract drift"

    with pytest.raises(ValidationError):
        model.model_validate(payload)
