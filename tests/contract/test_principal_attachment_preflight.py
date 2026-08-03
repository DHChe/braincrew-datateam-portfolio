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
from braincrew import corpus_qualification
from braincrew.ax_http_adapter import AxHttpAdapterConfig
from braincrew.contracts import ParsingCase
from braincrew.dataset_registry import DatasetValidationReport, validate_dataset_bundle
from braincrew.digest import canonical_digest
from braincrew.parsing_run import load_parsing_dataset

PROJECT_ROOT = Path(__file__).parents[2]
DATASET_MANIFEST = PROJECT_ROOT / "datasets" / "dataset_manifest_v3.json"
PINNED_AX_SHA = live_preflight.PINNED_AX_SHA
PROVISIONED_AX_SHA = "2bcaee3495fd7b3f624398819575cd86a5a15c47"
EVALUATION_SHA = "93c8e8dabab855b7f2f700df73cd04ce38995f29"
TENANT_ID = "11111111-1111-1111-1111-111111111111"
OWNER_USER_ID = "22222222-2222-2222-2222-222222222222"
FOREIGN_TENANT_ID = "99999999-9999-4999-8999-999999999999"
FOREIGN_USER_ID = "33333333-3333-4333-8333-333333333333"
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


def test_live_verification_v2_composes_dataset_roles_and_reviewed_probes(
    dataset_validation: DatasetValidationReport,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-77-contract",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(),
    )

    if artifact.schema_version != "live-verification-preflight-artifact-v2":
        pytest.fail(f"unexpected schema: {artifact.schema_version}")
    if artifact.dataset_identity is None or artifact.dataset_identity.version != "3.0.0":
        pytest.fail("v2 artifact did not retain the frozen v3 dataset identity")
    observed_roles = {observation.request.roles[0] for observation in artifact.corpus_observations}
    if observed_roles != {"Employee", "Executive", "HRPractitioner"}:
        pytest.fail(f"unexpected corpus roles: {sorted(observed_roles)}")
    if len(artifact.parse_observations) != 6:
        pytest.fail(f"unexpected parse observation count: {len(artifact.parse_observations)}")
    if artifact.blockers:
        pytest.fail(f"unexpected blockers: {artifact.blockers}")
    if artifact.readiness != "READY":
        pytest.fail(f"unexpected readiness verdict: {artifact.readiness}")


def test_live_verification_v2_retains_unreviewed_mapping_as_not_ready(
    dataset_validation: DatasetValidationReport,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        pytest.fail("unreviewed mapping must block before HTTP")

    mapping = {
        **APPROVED_ATTACHMENTS,
        "synthetic-rule-020": "00000000-0000-0000-0000-000000000020",
    }
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-unreviewed-mapping",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=mapping,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=httpx.MockTransport(handler),
    )

    if requests:
        pytest.fail(f"unexpected HTTP requests: {requests}")
    if artifact.readiness != "NOT_READY":
        pytest.fail(f"unexpected readiness verdict: {artifact.readiness}")
    if [blocker.code for blocker in artifact.blockers] != ["PARSE_ATTACHMENT_MAPPING_INVALID"]:
        pytest.fail(f"unexpected blockers: {artifact.blockers}")
    if artifact.blockers[0].detail != "mapping_missing_malformed_or_unreviewed":
        pytest.fail(f"unexpected blocker detail: {artifact.blockers[0].detail}")


def test_live_verification_v2_retains_unreviewed_subject_as_not_ready(
    dataset_validation: DatasetValidationReport,
) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        pytest.fail("unreviewed subject must block before HTTP")

    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-unreviewed-subject",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=FOREIGN_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=httpx.MockTransport(handler),
    )

    if requests:
        pytest.fail(f"unexpected HTTP requests: {requests}")
    if artifact.readiness != "NOT_READY":
        pytest.fail(f"unexpected readiness verdict: {artifact.readiness}")
    if [blocker.code for blocker in artifact.blockers] != ["EVALUATION_PRINCIPAL_SUBJECT_INVALID"]:
        pytest.fail(f"unexpected blockers: {artifact.blockers}")
    if artifact.blockers[0].detail != "subject_is_not_reviewed_owner":
        pytest.fail(f"unexpected blocker detail: {artifact.blockers[0].detail}")


def test_live_verification_v2_retains_corpus_transport_failure_as_not_ready(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-corpus-503",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(corpus_failure_status=503),
    )

    if artifact.readiness != "NOT_READY":
        pytest.fail(f"unexpected readiness verdict: {artifact.readiness}")
    if [blocker.code for blocker in artifact.blockers] != ["LIVE_CORPUS_IDENTITY_FAILED"]:
        pytest.fail(f"unexpected blockers: {artifact.blockers}")
    blocker = artifact.blockers[0]
    if blocker.operation != "corpus_identity" or blocker.case_id != "corpus-Employee":
        pytest.fail(f"unexpected corpus blocker identity: {blocker}")
    if blocker.detail != "AX_TRANSIENT_RETRIES_EXHAUSTED":
        pytest.fail(f"unexpected blocker detail: {blocker.detail}")
    if [attempt.outcome for attempt in blocker.attempts] != [
        "retryable_http",
        "retryable_http",
        "retryable_http",
    ]:
        pytest.fail(f"unexpected blocker attempts: {blocker.attempts}")

    artifact_path = live_preflight.write_live_preflight_artifact(
        artifact,
        tmp_path / "not-ready-live-verification-preflight-artifact-v2.json",
    )
    replay = live_preflight.replay_live_preflight_artifact(
        artifact_path,
        handoff_receipt_path=_reviewed_receipt_path(),
    )
    if replay["readiness"] != "NOT_READY":
        pytest.fail(f"unexpected replay verdict: {replay['readiness']}")


def test_live_verification_v2_refuses_role_missing_qualified_seed(
    dataset_validation: DatasetValidationReport,
) -> None:
    with pytest.raises(ValueError, match="qualified seed contribution"):
        live_preflight.capture_live_verification_preflight(
            run_id="issue-77-missing-seed",
            captured_at=datetime(2026, 7, 27, tzinfo=UTC),
            evaluation_plane_sha=EVALUATION_SHA,
            sut_commit_sha=PINNED_AX_SHA,
            base_url="https://ax.example.test",
            tenant_id=TENANT_ID,
            user_id=OWNER_USER_ID,
            attachment_mapping=APPROVED_ATTACHMENTS,
            dataset_validation=dataset_validation,
            handoff_receipt_path=_reviewed_receipt_path(),
            transport=_live_verification_transport(missing_seed_role="Employee"),
        )


def test_live_verification_v2_is_create_only_and_replays_logical_digest(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-77-replay",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(),
    )
    artifact_path = tmp_path / "live-verification-preflight-artifact-v2.json"
    live_preflight.write_live_preflight_artifact(artifact, artifact_path)

    with pytest.raises(FileExistsError):
        live_preflight.write_live_preflight_artifact(artifact, artifact_path)

    replay = live_preflight.replay_live_preflight_artifact(
        artifact_path,
        handoff_receipt_path=_reviewed_receipt_path(),
    )

    if replay["logical_digest"] != artifact.logical_digest:
        pytest.fail("v2 replay did not reproduce the stored logical digest")
    if replay["corpus_observation_count"] != 3:
        pytest.fail(f"unexpected corpus replay count: {replay['corpus_observation_count']}")
    if replay["parse_observation_count"] != 6:
        pytest.fail(f"unexpected parse replay count: {replay['parse_observation_count']}")


def test_principal_attachment_schema_still_refuses_corpus_observations(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-77-principal-refusal",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(),
    )
    payload = artifact.model_dump(mode="json")
    payload["schema_version"] = "principal-attachment-preflight-evidence-v1"
    payload["readiness"] = None
    payload["capture_contract"] = "principal-attachment-preflight-v1"
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path = tmp_path / "invalid-principal-with-corpus.json"
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="principal attachment capture cannot contain corpus observations",
    ):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_non_v2_replay_refuses_readiness_verdict(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    principal_artifact = live_preflight.capture_principal_attachment_preflight(
        run_id="issue-80-principal-v1-readiness",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(404, json={"detail": "not_found"})
        ),
    )
    generic_artifact = live_preflight.build_live_preflight_artifact(
        run_id="issue-80-generic-v1-readiness",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        corpus_observations=(),
        parse_observations=(),
        blockers=(live_preflight.LivePreflightBlocker(code="LIVE_VERIFICATION_BLOCKED"),),
    )

    for schema_name, artifact in (
        ("principal-v1", principal_artifact),
        ("generic-v1", generic_artifact),
    ):
        artifact_path = _write_tampered_artifact(
            artifact,
            tmp_path,
            name=f"{schema_name}-readiness",
            mutate=lambda payload: payload.update(readiness="READY"),
        )

        with pytest.raises(ValueError, match="only live verification schema may declare readiness"):
            live_preflight.replay_live_preflight_artifact(
                artifact_path,
                handoff_receipt_path=_reviewed_receipt_path(),
            )


@pytest.mark.parametrize(
    ("mutation", "value", "message"),
    [
        ("user_id", FOREIGN_USER_ID, "reviewed subject"),
        ("tenant_id", FOREIGN_TENANT_ID, "one tenant identity"),
        ("tenant_id", "NOT-A-UUID", "canonical tenant UUID"),
        ("case_id", "corpus-unreviewed", "corpus request identity"),
        ("eval_correlation_id", "unreviewed-correlation", "corpus request identity"),
        ("query", "salary of the CEO", "unrelated payload"),
        ("timeout_seconds", 30.0, "frozen request timeout"),
    ],
)
def test_live_verification_v2_replay_refuses_corpus_request_mutations(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
    mutation: str,
    value: object,
    message: str,
) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        for observation in payload["corpus_observations"]:
            request = observation["request"]
            request[mutation] = value
            if mutation in {"case_id", "eval_correlation_id"}:
                observation["context"][mutation] = value

    artifact_path = _write_tampered_live_verification_artifact(
        dataset_validation,
        tmp_path,
        name=f"corpus-request-{mutation}",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match=message):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("empty", "bounded attempt evidence"),
        ("plaintext_correlation", "digest-only"),
        ("terminal_failure", "successful final attempt"),
    ],
)
def test_live_verification_v2_replay_refuses_invalid_corpus_attempt_evidence(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        observation = payload["corpus_observations"][0]
        if mutation == "empty":
            observation["attempts"] = []
        elif mutation == "plaintext_correlation":
            observation["attempts"][0]["response_correlation_id"] = HOSTILE_CORRELATION_ID
        else:
            observation["attempts"][-1]["outcome"] = "permanent_http"
            observation["attempts"][-1]["status_code"] = 503

    artifact_path = _write_tampered_live_verification_artifact(
        dataset_validation,
        tmp_path,
        name=f"corpus-attempt-{mutation}",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match=message):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_keeps_principal_parse_validation(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["parse_observations"][0]["request"]["user_id"] = FOREIGN_USER_ID

    artifact_path = _write_tampered_live_verification_artifact(
        dataset_validation,
        tmp_path,
        name="foreign-parse-subject",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match="reviewed owner role"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_refuses_mismatched_corpus_role_evidence(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        observation = payload["corpus_observations"][0]
        response = observation["response"]
        response["principal_roles"] = ["Executive"]
        observation["response_digest"] = canonical_digest(response)

    artifact_path = _write_tampered_live_verification_artifact(
        dataset_validation,
        tmp_path,
        name="mismatched-corpus-role",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match="invalid corpus role evidence"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_requires_all_three_corpus_roles(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["corpus_observations"].pop()

    artifact_path = _write_tampered_live_verification_artifact(
        dataset_validation,
        tmp_path,
        name="missing-corpus-role",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match="requires all three corpus roles"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_requires_its_capture_contract(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["capture_contract"] = None

    artifact_path = _write_tampered_live_verification_artifact(
        dataset_validation,
        tmp_path,
        name="missing-v2-contract",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match="requires its capture contract"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_requires_frozen_dataset_identity(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["dataset_identity"] = None

    artifact_path = _write_tampered_live_verification_artifact(
        dataset_validation,
        tmp_path,
        name="missing-v2-dataset",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match="requires frozen dataset identity"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_refuses_retained_blocker_when_ready(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        payload["blockers"] = [
            live_preflight.LivePreflightBlocker(code="LIVE_VERIFICATION_BLOCKED").model_dump(
                mode="json"
            )
        ]

    artifact_path = _write_tampered_live_verification_artifact(
        dataset_validation,
        tmp_path,
        name="retained-v2-blocker",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match="READY live verification capture cannot retain blockers"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("missing_readiness", "requires a readiness verdict"),
        ("not_ready_without_blocker", "NOT_READY live verification capture requires a blocker"),
        ("multiple_blockers", "requires at most one terminal blocker"),
    ],
)
def test_live_verification_v2_replay_refuses_readiness_contradictions(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    def mutate(payload: dict[str, Any]) -> None:
        if mutation == "missing_readiness":
            payload["readiness"] = None
        elif mutation == "not_ready_without_blocker":
            payload["readiness"] = "NOT_READY"
        else:
            blocker = live_preflight.LivePreflightBlocker(
                code="LIVE_VERIFICATION_BLOCKED"
            ).model_dump(mode="json")
            payload["readiness"] = "NOT_READY"
            payload["blockers"] = [blocker, blocker]

    artifact_path = _write_tampered_live_verification_artifact(
        dataset_validation,
        tmp_path,
        name=f"readiness-{mutation}",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match=message):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_refuses_forged_pre_probe_blocker_detail(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-forged-pre-probe-blocker",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=FOREIGN_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=httpx.MockTransport(
            lambda request: pytest.fail(f"unexpected HTTP request: {request}")
        ),
    )

    artifact_path = _write_tampered_artifact(
        artifact,
        tmp_path,
        name="forged-pre-probe-blocker",
        mutate=lambda payload: payload["blockers"][0].update(detail="forged_detail"),
    )

    with pytest.raises(ValueError, match="pre-probe live verification blocker is inconsistent"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_keeps_principal_blocker_validation(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-forged-principal-blocker",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=httpx.MockTransport(
            lambda request: httpx.Response(404, json={"detail": "not_found"})
        ),
    )

    artifact_path = _write_tampered_artifact(
        artifact,
        tmp_path,
        name="forged-principal-blocker",
        mutate=lambda payload: payload["blockers"][0].update(detail="forged_detail"),
    )

    with pytest.raises(ValueError, match="blocker contradicts its terminal attempt"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_refuses_corpus_evidence_after_principal_blocker(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    blocked_artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-principal-blocked-with-corpus",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=FOREIGN_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=httpx.MockTransport(
            lambda request: pytest.fail(f"unexpected HTTP request: {request}")
        ),
    )
    ready_artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-principal-blocked-with-corpus",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(),
    )

    artifact_path = _write_tampered_artifact(
        blocked_artifact,
        tmp_path,
        name="principal-blocked-with-corpus",
        mutate=lambda payload: payload.update(
            corpus_observations=[
                observation.model_dump(mode="json")
                for observation in ready_artifact.corpus_observations
            ]
        ),
    )

    with pytest.raises(ValueError, match="principal-blocked live verification"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_refuses_duplicate_completed_corpus_role(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-duplicate-completed-corpus-role",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(
            corpus_failure_status=503,
            corpus_failure_role="HRPractitioner",
        ),
    )

    def mutate(payload: dict[str, Any]) -> None:
        observation = payload["corpus_observations"][1]
        request = observation["request"]
        context = observation["context"]
        response = observation["response"]
        request["roles"] = ["Employee"]
        request["case_id"] = "corpus-Employee"
        request["eval_correlation_id"] = "issue-80-duplicate-completed-corpus-role-corpus-Employee"
        context["case_id"] = request["case_id"]
        context["eval_correlation_id"] = request["eval_correlation_id"]
        response["principal_roles"] = ["Employee"]
        observation["response_digest"] = canonical_digest(response)

    artifact_path = _write_tampered_artifact(
        artifact,
        tmp_path,
        name="duplicate-completed-corpus-role",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match="completed corpus role prefix is inconsistent"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_requires_blocker_to_name_next_corpus_role(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-blocker-next-corpus-role",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(
            corpus_failure_status=503,
            corpus_failure_role="HRPractitioner",
        ),
    )

    def mutate(payload: dict[str, Any]) -> None:
        blocker = payload["blockers"][0]
        blocker["case_id"] = "corpus-Employee"
        blocker["request"]["roles"] = ["Employee"]
        blocker["request"]["case_id"] = "corpus-Employee"
        blocker["request"]["eval_correlation_id"] = (
            "issue-80-blocker-next-corpus-role-corpus-Employee"
        )

    artifact_path = _write_tampered_artifact(
        artifact,
        tmp_path,
        name="blocker-not-next-corpus-role",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match="corpus blocker identity is inconsistent"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_refuses_response_correlation_on_timeout_blocker(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-timeout-blocker-correlation",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(corpus_failure_status=503),
    )

    def mutate(payload: dict[str, Any]) -> None:
        terminal_attempt = payload["blockers"][0]["attempts"][-1]
        terminal_attempt["outcome"] = "timeout"
        terminal_attempt["status_code"] = None
        terminal_attempt["response_correlation_id"] = HOSTILE_CORRELATION_DIGEST

    artifact_path = _write_tampered_artifact(
        artifact,
        tmp_path,
        name="timeout-blocker-with-response-correlation",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match="cannot declare a response correlation"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_v2_replay_refuses_foreign_tenant_corpus_blocker(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-80-foreign-tenant-corpus-blocker",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(corpus_failure_status=503),
    )

    artifact_path = _write_tampered_artifact(
        artifact,
        tmp_path,
        name="foreign-tenant-corpus-blocker",
        mutate=lambda payload: payload["blockers"][0]["request"].update(
            tenant_id=FOREIGN_TENANT_ID
        ),
    )

    with pytest.raises(ValueError, match="one tenant identity"):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("code", "corpus blocker identity is inconsistent"),
        ("case_id", "corpus blocker identity is inconsistent"),
        ("request_case_id", "corpus request identity is inconsistent"),
        ("missing_request", "corpus blocker requires its canonical request"),
        ("missing_dataset_identity", "corpus blocker requires frozen dataset identity"),
        ("terminal_success", "corpus blocker contradicts its terminal attempt"),
        ("missing_detail", "corpus blocker requires a typed detail"),
        ("detail", "corpus blocker contradicts its terminal attempt"),
    ],
)
def test_live_verification_v2_replay_refuses_forged_corpus_blocker(
    dataset_validation: DatasetValidationReport,
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id=f"issue-80-forged-corpus-blocker-{mutation}",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(corpus_failure_status=503),
    )

    def mutate(payload: dict[str, Any]) -> None:
        blocker = payload["blockers"][0]
        if mutation == "code":
            blocker["code"] = "LIVE_VERIFICATION_BLOCKED"
        elif mutation == "case_id":
            blocker["case_id"] = "corpus-Executive"
        elif mutation == "request_case_id":
            blocker["request"]["case_id"] = "corpus-Executive"
        elif mutation == "missing_request":
            blocker["request"] = None
        elif mutation == "missing_dataset_identity":
            payload["dataset_identity"] = None
        elif mutation == "terminal_success":
            blocker["attempts"][-1]["outcome"] = "success"
            blocker["attempts"][-1]["status_code"] = 200
        elif mutation == "missing_detail":
            blocker["detail"] = None
        else:
            blocker["detail"] = "AX_REQUEST_FAILURE"

    artifact_path = _write_tampered_artifact(
        artifact,
        tmp_path,
        name=f"forged-corpus-blocker-{mutation}",
        mutate=mutate,
    )

    with pytest.raises(ValueError, match=message):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=_reviewed_receipt_path(),
        )


def test_live_verification_capture_aborts_before_corpus_when_parse_is_blocked(
    dataset_validation: DatasetValidationReport,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/evaluation/corpus-identity":
            pytest.fail("blocked parsing probes must abort before corpus capture")
        return httpx.Response(404, json={"detail": "not_found"})

    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-77-blocked-parse",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=dataset_validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=httpx.MockTransport(handler),
    )

    if artifact.readiness != "NOT_READY":
        pytest.fail(f"unexpected readiness verdict: {artifact.readiness}")
    if [blocker.code for blocker in artifact.blockers] != ["PARSE_ATTACHMENT_MAPPING_INVALID"]:
        pytest.fail(f"unexpected blockers: {artifact.blockers}")
    if artifact.blockers[0].detail != "attachment_not_found":
        pytest.fail(f"unexpected blocker detail: {artifact.blockers[0].detail}")


def _write_tampered_live_verification_artifact(
    validation: DatasetValidationReport,
    tmp_path: Path,
    *,
    name: str,
    mutate: Callable[[dict[str, Any]], None],
) -> Path:
    artifact = live_preflight.capture_live_verification_preflight(
        run_id=f"issue-77-{name}",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=validation,
        handoff_receipt_path=_reviewed_receipt_path(),
        transport=_live_verification_transport(),
    )
    payload = artifact.model_dump(mode="json")
    mutate(payload)
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path = tmp_path / f"{name}.json"
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")
    return artifact_path


def _write_tampered_artifact(
    artifact: live_preflight.LivePreflightArtifact,
    tmp_path: Path,
    *,
    name: str,
    mutate: Callable[[dict[str, Any]], None],
) -> Path:
    payload = artifact.model_dump(mode="json")
    mutate(payload)
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path = tmp_path / f"{name}.json"
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")
    return artifact_path


def _live_verification_transport(
    *,
    missing_seed_role: str | None = None,
    corpus_failure_status: int | None = None,
    corpus_failure_role: str | None = None,
) -> httpx.MockTransport:
    cases = _reviewed_probe_cases()
    attachments = _attachment_documents()

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/evaluation/corpus-identity":
            role = request.headers["x-ax-roles"]
            if corpus_failure_status is not None and (
                corpus_failure_role is None or role == corpus_failure_role
            ):
                return httpx.Response(
                    corpus_failure_status,
                    json={"detail": "starting"},
                )
            role_digest_digit = {
                "Employee": "1",
                "Executive": "2",
                "HRPractitioner": "3",
            }[role]
            contributing_versions = (
                [] if role == missing_seed_role else [corpus_qualification.SEED_VERSION]
            )
            return httpx.Response(
                200,
                json={
                    "schema_version": "ax-corpus-identity-v1",
                    "corpus_id": f"ax-visible-retrieval:{TENANT_ID}",
                    "corpus_version": "retrieval-inventory-v1",
                    "corpus_digest": f"sha256:{role_digest_digit * 64}",
                    "principal_roles": [role],
                    "inventory_count": 6,
                    "counts": {"record_kind": {"source_chunk": 6}},
                    "contributing_versions": contributing_versions,
                    "generated_at": "2026-07-27T00:00:00Z",
                },
            )
        requested = _requested_attachment(request)
        document_id = attachments[requested]
        return httpx.Response(
            200,
            json=_parse_response(cases[document_id], attachment_id=requested),
        )

    return httpx.MockTransport(handler)


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
                "repository": {"commit_sha": PROVISIONED_AX_SHA},
                "target": {
                    "subject_id": OWNER_USER_ID,
                    "tenant_id": TENANT_ID,
                },
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
