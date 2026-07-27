from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterator, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

import braincrew.live_preflight as live_preflight
from braincrew.ax_http_adapter import AxHttpAdapterConfig
from braincrew.contracts import ParsingCase
from braincrew.dataset_registry import DatasetValidationReport, validate_dataset_bundle
from braincrew.digest import canonical_digest
from braincrew.parsing_run import load_parsing_dataset

PROJECT_ROOT = Path(__file__).parents[2]
DATASET_MANIFEST = PROJECT_ROOT / "datasets" / "dataset_manifest_v3.json"
PINNED_AX_SHA = "2bcaee3495fd7b3f624398819575cd86a5a15c47"
EVALUATION_SHA = "93c8e8dabab855b7f2f700df73cd04ce38995f29"
TENANT_ID = "11111111-1111-1111-1111-111111111111"
OWNER_USER_ID = "22222222-2222-2222-2222-222222222222"
APPROVED_ATTACHMENTS = {
    "synthetic-rule-015": "2c7d525b-7463-463e-8893-0d37009775de",
    "synthetic-rule-016": "e2d16eeb-c86e-45be-994f-fe3aecfc3f8d",
    "synthetic-rule-017": "87dcebfe-f3cf-47cd-8e0c-c03a6a28270f",
    "synthetic-rule-018": "816b01c3-a571-4f02-9f14-32e71d7fb2ee",
    "synthetic-rule-019": "07b849ea-5e0a-44f7-87c9-600f539d7d9a",
    "synthetic-rule-020": "569dc67a-5ba8-4a00-a0d8-e03a8ac43449",
}
HOSTILE_CORRELATION_ID = "Bearer secret-material"
HOSTILE_CORRELATION_DIGEST = "sha256:" + hashlib.sha256(HOSTILE_CORRELATION_ID.encode()).hexdigest()
REVIEWED_RECEIPT_PATH: Path | None = None


@pytest.fixture(scope="module")
def dataset_validation() -> DatasetValidationReport:
    validation = validate_dataset_bundle(DATASET_MANIFEST)
    assert validation.state == "VALID"
    assert validation.snapshot is not None
    return validation


@pytest.fixture(autouse=True)
def reviewed_receipt_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[None]:
    global REVIEWED_RECEIPT_PATH
    receipt_path = _write_reviewed_receipt(tmp_path)
    digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    monkeypatch.setattr(live_preflight, "REVIEWED_HANDOFF_RECEIPT_SHA256", digest)
    REVIEWED_RECEIPT_PATH = receipt_path
    yield
    REVIEWED_RECEIPT_PATH = None


def test_adapter_config_rejects_noncanonical_tenant_and_user_uuids() -> None:
    for tenant_id, user_id in (
        ("NOT-A-UUID", OWNER_USER_ID),
        ("AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA", OWNER_USER_ID),
        (TENANT_ID, "evaluation-plane"),
        (TENANT_ID, "BBBBBBBB-BBBB-4BBB-8BBB-BBBBBBBBBBBB"),
    ):
        with pytest.raises(ValidationError, match="canonical UUID"):
            AxHttpAdapterConfig(
                base_url="https://ax.example.test",
                sut_commit_sha=PINNED_AX_SHA,
                tenant_id=tenant_id,
                user_id=user_id,
                roles=("HRPractitioner",),
            )


@pytest.mark.parametrize("principal_field", ["tenant_id", "user_id"])
def test_malformed_principal_blocks_before_the_first_http_operation(
    dataset_validation: DatasetValidationReport,
    principal_field: str,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise AssertionError("malformed principals must stop before HTTP")

    tenant_id = "evaluation-plane" if principal_field == "tenant_id" else TENANT_ID
    user_id = "evaluation-plane" if principal_field == "user_id" else OWNER_USER_ID

    artifact = _capture(
        dataset_validation,
        tenant_id=tenant_id,
        user_id=user_id,
        transport=httpx.MockTransport(handler),
    )

    assert requests == []
    assert artifact.parse_observations == ()
    assert [blocker.code for blocker in artifact.blockers] == ["EVALUATION_PRINCIPAL_ID_INVALID"]
    assert artifact.blockers[0].operation is None


def test_unknown_or_inactive_subject_is_nonretryable_and_typed(
    dataset_validation: DatasetValidationReport,
) -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(
            401,
            json={"detail": "evaluation_principal_subject_invalid"},
        )

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert request_count == 1
    assert artifact.parse_observations == ()
    assert [blocker.code for blocker in artifact.blockers] == [
        "EVALUATION_PRINCIPAL_SUBJECT_INVALID"
    ]
    assert artifact.blockers[0].case_id == "synthetic-rule-015"


@pytest.mark.parametrize(
    "mapping",
    [
        {key: value for key, value in APPROVED_ATTACHMENTS.items() if key != "synthetic-rule-020"},
        {**APPROVED_ATTACHMENTS, "synthetic-rule-020": "not-a-uuid"},
        {
            **APPROVED_ATTACHMENTS,
            "synthetic-rule-020": "00000000-0000-0000-0000-000000000020",
        },
    ],
)
def test_missing_malformed_or_unreviewed_mapping_blocks_without_http(
    dataset_validation: DatasetValidationReport,
    mapping: Mapping[str, str],
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        raise AssertionError("invalid mappings must stop before HTTP")

    artifact = _capture(
        dataset_validation,
        mapping=mapping,
        transport=httpx.MockTransport(handler),
    )

    assert requests == []
    assert [blocker.code for blocker in artifact.blockers] == ["PARSE_ATTACHMENT_MAPPING_INVALID"]


def test_nonfrozen_dataset_identity_blocks_before_http(
    dataset_validation: DatasetValidationReport,
) -> None:
    assert dataset_validation.snapshot is not None
    wrong_digest = "sha256:" + "0" * 64
    forged_snapshot = dataset_validation.snapshot.model_copy(
        update={
            "manifest": dataset_validation.snapshot.manifest.model_copy(
                update={"content_digest": wrong_digest}
            ),
            "dataset_digest": wrong_digest,
        }
    )
    forged_validation = dataset_validation.model_copy(
        update={
            "snapshot": forged_snapshot,
            "computed_dataset_digest": wrong_digest,
        }
    )
    cases = _reviewed_probe_cases()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        requested = _requested_attachment(request)
        document_id = _attachment_documents()[requested]
        return httpx.Response(
            200,
            json=_parse_response(cases[document_id], attachment_id=requested),
        )

    artifact = _capture(forged_validation, transport=httpx.MockTransport(handler))

    assert requests == []
    assert [blocker.code for blocker in artifact.blockers] == ["PARSE_ATTACHMENT_MAPPING_INVALID"]
    assert artifact.blockers[0].detail == "dataset_identity_mismatch"


def test_nonfrozen_dataset_component_digest_blocks_before_http(
    dataset_validation: DatasetValidationReport,
) -> None:
    assert dataset_validation.snapshot is not None
    snapshot = dataset_validation.snapshot
    wrong_digest = "sha256:" + "0" * 64
    forged_components = snapshot.manifest.components.model_copy(
        update={
            "parsing": snapshot.manifest.components.parsing.model_copy(
                update={"content_digest": wrong_digest}
            )
        }
    )
    forged_snapshot = snapshot.model_copy(
        update={
            "manifest": snapshot.manifest.model_copy(update={"components": forged_components}),
            "component_digests": {**snapshot.component_digests, "parsing": wrong_digest},
        }
    )
    forged_validation = dataset_validation.model_copy(
        update={
            "snapshot": forged_snapshot,
            "computed_component_digests": {
                **dataset_validation.computed_component_digests,
                "parsing": wrong_digest,
            },
        }
    )
    cases = _reviewed_probe_cases()
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        requested = _requested_attachment(request)
        document_id = _attachment_documents()[requested]
        return httpx.Response(
            200,
            json=_parse_response(cases[document_id], attachment_id=requested),
        )

    artifact = _capture(forged_validation, transport=httpx.MockTransport(handler))

    assert requests == []
    assert [blocker.code for blocker in artifact.blockers] == ["PARSE_ATTACHMENT_MAPPING_INVALID"]
    assert artifact.blockers[0].detail == "dataset_identity_mismatch"


def test_nonexistent_attachment_is_a_mapping_blocker_without_retry(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        return httpx.Response(404, json={"detail": "not_found"})

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert request_count == 1
    assert [blocker.code for blocker in artifact.blockers] == ["PARSE_ATTACHMENT_MAPPING_INVALID"]
    assert artifact.blockers[0].detail == "attachment_not_found"

    artifact_path = live_preflight.write_live_preflight_artifact(
        artifact,
        tmp_path / "nonexistent-attachment-evidence.json",
    )
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    payload["blockers"][0]["code"] = "EVALUATION_PRINCIPAL_SUBJECT_INVALID"
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="contradicts its terminal attempt"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_inaccessible_attachment_preserves_the_live_operation_blocker(
    dataset_validation: DatasetValidationReport,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("synthetic endpoint unavailable", request=request)

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert [blocker.code for blocker in artifact.blockers] == ["LIVE_PARSE_OBSERVATION_UNREACHABLE"]
    assert len(artifact.blockers[0].attempts) == 1
    assert artifact.blockers[0].attempts[0].operation == "parse"
    assert artifact.blockers[0].attempts[0].attempt_number == 1
    assert artifact.blockers[0].attempts[0].method == "GET"
    assert artifact.blockers[0].attempts[0].path == (
        "/v1/evaluation/attachments/2c7d525b-7463-463e-8893-0d37009775de/parse-observation"
    )
    assert artifact.blockers[0].attempts[0].outcome == "request_error"
    assert artifact.blockers[0].attempts[0].status_code is None
    assert artifact.blockers[0].request is not None
    assert artifact.blockers[0].request.tenant_id == TENANT_ID
    assert artifact.blockers[0].request.user_id == OWNER_USER_ID
    assert artifact.blockers[0].request.roles == ("HRPractitioner",)


def test_request_error_attempt_cannot_claim_a_response_correlation(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("synthetic endpoint unavailable", request=request)

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))
    artifact_path = live_preflight.write_live_preflight_artifact(
        artifact,
        tmp_path / "request-error-evidence.json",
    )
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    payload["blockers"][0]["attempts"][0]["response_correlation_id"] = "sha256:" + "0" * 64
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="cannot declare a response correlation"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_unavailable_parse_preserves_the_existing_typed_live_blocker(
    dataset_validation: DatasetValidationReport,
) -> None:
    cases = _reviewed_probe_cases()

    def handler(request: httpx.Request) -> httpx.Response:
        requested = _requested_attachment(request)
        document_id = _attachment_documents()[requested]
        payload = _parse_response(cases[document_id], attachment_id=requested)
        payload.update(
            parse_available=False,
            parser_name=None,
            parser_version=None,
            failure_code="parse_unavailable",
            extracted_text=None,
            extracted_text_digest=None,
            evidence_spans=[],
        )
        return httpx.Response(200, json=payload)

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert [blocker.code for blocker in artifact.blockers] == ["LIVE_PARSE_OBSERVATION_UNAVAILABLE"]
    assert artifact.blockers[0].detail == "parse_unavailable"
    assert [attempt.outcome for attempt in artifact.blockers[0].attempts] == ["success"]


def test_mismatched_attachment_identity_is_a_mapping_blocker(
    dataset_validation: DatasetValidationReport,
) -> None:
    cases = _reviewed_probe_cases()

    def handler(request: httpx.Request) -> httpx.Response:
        requested = _requested_attachment(request)
        document_id = _attachment_documents()[requested]
        return httpx.Response(
            200,
            json=_parse_response(
                cases[document_id],
                attachment_id="00000000-0000-0000-0000-000000000000",
            ),
        )

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert [blocker.code for blocker in artifact.blockers] == ["PARSE_ATTACHMENT_MAPPING_INVALID"]
    assert artifact.blockers[0].detail == "attachment_identity_mismatch"


@pytest.mark.parametrize(
    ("mutation", "detail"),
    [
        (lambda payload: payload.update(parser_name=None), "parser_identity_missing"),
        (
            lambda payload: payload.update(parser_name="markdown-text"),
            "parser_identity_mismatch",
        ),
        (
            lambda payload: payload.update(
                extracted_text_digest="sha256:" + "f" * 64,
            ),
            "source_text_digest_mismatch",
        ),
        (
            lambda payload: payload.update(failure_code="parse_materialization_failed"),
            "parse_failure_code_present",
        ),
    ],
)
def test_successful_transport_with_invalid_strict_evidence_remains_blocked(
    dataset_validation: DatasetValidationReport,
    mutation: Callable[[dict[str, Any]], None],
    detail: str,
) -> None:
    cases = _reviewed_probe_cases()

    def handler(request: httpx.Request) -> httpx.Response:
        requested = _requested_attachment(request)
        document_id = _attachment_documents()[requested]
        payload = _parse_response(cases[document_id], attachment_id=requested)
        mutation(payload)
        return httpx.Response(200, json=payload)

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert [blocker.code for blocker in artifact.blockers] == ["LIVE_PARSE_OBSERVATION_FAILED"]
    assert artifact.blockers[0].detail == detail
    assert artifact.parse_observations == ()


def test_unsafe_span_identifier_is_blocked_without_retaining_it(
    dataset_validation: DatasetValidationReport,
) -> None:
    cases = _reviewed_probe_cases()
    unsafe_span_id = "Bearer secret-material"

    def handler(request: httpx.Request) -> httpx.Response:
        requested = _requested_attachment(request)
        document_id = _attachment_documents()[requested]
        payload = _parse_response(cases[document_id], attachment_id=requested)
        payload["evidence_spans"][0]["id"] = unsafe_span_id
        return httpx.Response(200, json=payload)

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert [blocker.code for blocker in artifact.blockers] == ["LIVE_PARSE_OBSERVATION_FAILED"]
    assert artifact.blockers[0].detail == "evidence_span_invalid"
    assert unsafe_span_id not in artifact.model_dump_json()


def test_available_parse_with_empty_spans_remains_measureable(
    dataset_validation: DatasetValidationReport,
) -> None:
    cases = _reviewed_probe_cases()

    def handler(request: httpx.Request) -> httpx.Response:
        requested = _requested_attachment(request)
        document_id = _attachment_documents()[requested]
        payload = _parse_response(cases[document_id], attachment_id=requested)
        if document_id == "synthetic-rule-015":
            payload["evidence_spans"] = []
        return httpx.Response(200, json=payload)

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert artifact.blockers == ()
    assert len(artifact.parse_observations) == 6
    assert artifact.parse_observations[0].response.evidence_spans == ()


def test_exhausted_parse_retries_are_retained_with_the_blocker(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            503,
            headers={"x-correlation-id": HOSTILE_CORRELATION_ID},
            json={"detail": "starting"},
        )

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert artifact.capture_contract == "principal-attachment-preflight-v1"
    assert artifact.dataset_identity is not None
    assert [blocker.code for blocker in artifact.blockers] == ["LIVE_PARSE_OBSERVATION_FAILED"]
    assert [attempt.outcome for attempt in artifact.blockers[0].attempts] == [
        "retryable_http",
        "retryable_http",
        "retryable_http",
    ]
    assert [attempt.status_code for attempt in artifact.blockers[0].attempts] == [503, 503, 503]
    assert [attempt.response_correlation_id for attempt in artifact.blockers[0].attempts] == [
        HOSTILE_CORRELATION_DIGEST,
        HOSTILE_CORRELATION_DIGEST,
        HOSTILE_CORRELATION_DIGEST,
    ]
    assert HOSTILE_CORRELATION_ID not in artifact.model_dump_json()

    artifact_path = live_preflight.write_live_preflight_artifact(
        artifact,
        tmp_path / "exhausted-retry-evidence.json",
    )
    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    final_attempt = payload["blockers"][0]["attempts"][-1]
    final_attempt["attempt_number"] = 1
    payload["blockers"][0]["attempts"] = [final_attempt]
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="three exhausted attempts"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_retries_are_retained_when_recovered_response_evidence_is_rejected(
    dataset_validation: DatasetValidationReport,
) -> None:
    cases = _reviewed_probe_cases()
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        if request_count < 3:
            return httpx.Response(
                503,
                headers={"x-correlation-id": HOSTILE_CORRELATION_ID},
                json={"detail": "starting"},
            )
        requested = _requested_attachment(request)
        document_id = _attachment_documents()[requested]
        payload = _parse_response(cases[document_id], attachment_id=requested)
        payload["parser_name"] = "markdown-text"
        return httpx.Response(
            200,
            headers={"x-correlation-id": HOSTILE_CORRELATION_ID},
            json=payload,
        )

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert [blocker.code for blocker in artifact.blockers] == ["LIVE_PARSE_OBSERVATION_FAILED"]
    assert artifact.blockers[0].detail == "parser_identity_mismatch"
    assert [attempt.outcome for attempt in artifact.blockers[0].attempts] == [
        "retryable_http",
        "retryable_http",
        "success",
    ]
    assert [attempt.status_code for attempt in artifact.blockers[0].attempts] == [503, 503, 200]
    assert [attempt.response_correlation_id for attempt in artifact.blockers[0].attempts] == [
        HOSTILE_CORRELATION_DIGEST,
        HOSTILE_CORRELATION_DIGEST,
        HOSTILE_CORRELATION_DIGEST,
    ]
    assert HOSTILE_CORRELATION_ID not in artifact.model_dump_json()


def test_retryable_parse_failures_retain_attempts_and_then_complete_six_probes(
    dataset_validation: DatasetValidationReport,
) -> None:
    cases = _reviewed_probe_cases()
    request_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        if request_count < 3:
            return httpx.Response(
                503,
                headers={"x-correlation-id": HOSTILE_CORRELATION_ID},
                json={"detail": "starting"},
            )
        requested = _requested_attachment(request)
        document_id = _attachment_documents()[requested]
        return httpx.Response(
            200,
            headers={"x-correlation-id": HOSTILE_CORRELATION_ID},
            json=_parse_response(cases[document_id], attachment_id=requested),
        )

    artifact = _capture(dataset_validation, transport=httpx.MockTransport(handler))

    assert artifact.blockers == ()
    assert len(artifact.parse_observations) == 6
    assert [attempt.outcome for attempt in artifact.parse_observations[0].attempts] == [
        "retryable_http",
        "retryable_http",
        "success",
    ]
    assert [
        attempt.response_correlation_id for attempt in artifact.parse_observations[0].attempts
    ] == [HOSTILE_CORRELATION_DIGEST] * 3
    assert HOSTILE_CORRELATION_ID not in artifact.model_dump_json()
    assert request_count == 8


def _capture(
    validation: DatasetValidationReport,
    *,
    tenant_id: str = TENANT_ID,
    user_id: str = OWNER_USER_ID,
    mapping: Mapping[str, str] = APPROVED_ATTACHMENTS,
    transport: httpx.BaseTransport,
) -> live_preflight.LivePreflightArtifact:
    return live_preflight.capture_principal_attachment_preflight(
        run_id="issue-34-contract",
        captured_at=datetime(2026, 7, 22, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=tenant_id,
        user_id=user_id,
        attachment_mapping=mapping,
        dataset_validation=validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=transport,
    )


def _reviewed_probe_cases() -> dict[str, ParsingCase]:
    parsing_dataset = load_parsing_dataset(
        PROJECT_ROOT / "datasets" / "parsing" / "parsing_cases_v1.json"
    )
    cases = {
        case.document.id: case for case in parsing_dataset.cases if case.split == "verification"
    }
    assert set(cases) == set(live_preflight.REVIEWED_PARSING_SOURCE_EVIDENCE)
    return cases


def _attachment_documents() -> dict[str, str]:
    return {
        attachment_id: document_id for document_id, attachment_id in APPROVED_ATTACHMENTS.items()
    }


def _reviewed_receipt_path() -> Path:
    assert REVIEWED_RECEIPT_PATH is not None
    return REVIEWED_RECEIPT_PATH


def _write_reviewed_receipt(tmp_path: Path) -> Path:
    receipt_path = tmp_path / "synthetic-reviewed-handoff.json"
    receipt_path.write_text(
        json.dumps(
            {
                "repository": {"commit_sha": PINNED_AX_SHA},
                "target": {"subject_id": OWNER_USER_ID},
                "state": "COMPLETED",
                "completion_confirmed": True,
                "attachments": [
                    {
                        "case_id": case_id,
                        "attachment_id": attachment_id,
                    }
                    for case_id, attachment_id in APPROVED_ATTACHMENTS.items()
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return receipt_path


def _requested_attachment(request: httpx.Request) -> str:
    return request.url.path.split("/")[-2]


def _parse_response(case: ParsingCase, *, attachment_id: str) -> dict[str, Any]:
    expected = case.expected
    return {
        "schema_version": "ax-parse-observation-v1",
        "attachment_id": attachment_id,
        "lifecycle_state": "materialized",
        "parse_state": "succeeded",
        "materialization_state": "materialized",
        "parse_available": True,
        "parser_name": "utf8-text",
        "parser_version": "stdlib-1",
        "failure_code": None,
        "extracted_text": case.document.canonical_text,
        "extracted_text_digest": expected.evidence_spans[0].source_text_digest,
        "text_truncated": False,
        "evidence_spans": [span.model_dump(mode="json") for span in expected.evidence_spans],
        "headings": list(expected.structure.headings),
        "metadata": dict(expected.metadata),
        "table": None if expected.table is None else expected.table.model_dump(mode="json"),
        "list": None if expected.list is None else expected.list.model_dump(mode="json"),
        "unavailable_fields": [],
    }
