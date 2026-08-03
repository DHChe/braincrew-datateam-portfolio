from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import pytest
from pydantic import ValidationError

import braincrew.live_preflight as live_preflight
from braincrew.dataset_registry import DatasetValidationReport, validate_dataset_bundle

PROJECT_ROOT = Path(__file__).parents[2]
DATASET_MANIFEST = PROJECT_ROOT / "datasets" / "dataset_manifest_v3.json"
PINNED_AX_SHA = "5b0f5f2ae2cfb4c4870a2228f9aa226e009241f5"
PROVISIONED_AX_SHA = "2bcaee3495fd7b3f624398819575cd86a5a15c47"
UNRELATED_AX_SHA = "7b6f480c52583a3ff12e3af809eba6510a7a2348"
EVALUATION_SHA = "93c8e8dabab855b7f2f700df73cd04ce38995f29"
TENANT_ID = "11111111-1111-1111-1111-111111111111"
SYNTHETIC_SUBJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SYNTHETIC_OTHER_SUBJECT_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
SYNTHETIC_ATTACHMENTS = {
    "synthetic-rule-015": "10000000-0000-4000-8000-000000000015",
    "synthetic-rule-016": "10000000-0000-4000-8000-000000000016",
    "synthetic-rule-017": "10000000-0000-4000-8000-000000000017",
    "synthetic-rule-018": "10000000-0000-4000-8000-000000000018",
    "synthetic-rule-019": "10000000-0000-4000-8000-000000000019",
    "synthetic-rule-020": "10000000-0000-4000-8000-000000000020",
}


@pytest.fixture(scope="module")
def dataset_validation() -> DatasetValidationReport:
    validation = validate_dataset_bundle(DATASET_MANIFEST)
    assert validation.state == "VALID"
    return validation


def _continuity_warrant_payload(**overrides: Any) -> dict[str, Any]:
    payload = live_preflight.REVIEWED_PROVISIONING_CONTINUITY_WARRANT.model_dump(mode="python")
    payload.update(overrides)
    return payload


def test_equal_commit_binding_requires_same_commit_reason() -> None:
    with pytest.raises(
        ValidationError,
        match="equal AX commits require the same-commit acceptance reason",
    ):
        live_preflight.ReceiptSutCommitBinding(
            provisioned_at_sha=PROVISIONED_AX_SHA,
            under_test_sha=PROVISIONED_AX_SHA,
            acceptance_reason="reviewed-provisioning-continuity",
        )


def test_equal_commit_binding_refuses_continuity_warrant() -> None:
    with pytest.raises(
        ValidationError,
        match="equal AX commits must not claim a continuity warrant",
    ):
        live_preflight.ReceiptSutCommitBinding(
            provisioned_at_sha=PROVISIONED_AX_SHA,
            under_test_sha=PROVISIONED_AX_SHA,
            acceptance_reason="same-reviewed-commit",
            continuity_warrant=live_preflight.REVIEWED_PROVISIONING_CONTINUITY_WARRANT,
        )


@pytest.mark.parametrize(
    ("acceptance_reason", "continuity_warrant"),
    [
        (
            "same-reviewed-commit",
            live_preflight.REVIEWED_PROVISIONING_CONTINUITY_WARRANT,
        ),
        ("reviewed-provisioning-continuity", None),
    ],
    ids=["continuity-reason", "continuity-warrant"],
)
def test_divergent_commit_binding_requires_continuity_reason_and_warrant(
    acceptance_reason: str,
    continuity_warrant: live_preflight.ReceiptSutContinuityWarrant | None,
) -> None:
    with pytest.raises(
        ValidationError,
        match="divergent AX commits require a reviewed continuity warrant",
    ):
        live_preflight.ReceiptSutCommitBinding.model_validate(
            {
                "provisioned_at_sha": PROVISIONED_AX_SHA,
                "under_test_sha": PINNED_AX_SHA,
                "acceptance_reason": acceptance_reason,
                "continuity_warrant": continuity_warrant,
            }
        )


@pytest.mark.parametrize(
    ("provisioned_at_sha", "under_test_sha"),
    [
        (UNRELATED_AX_SHA, PINNED_AX_SHA),
        (PROVISIONED_AX_SHA, UNRELATED_AX_SHA),
    ],
    ids=["provisioned-at", "under-test"],
)
def test_divergent_commit_binding_requires_warrant_to_bind_both_commits(
    provisioned_at_sha: str,
    under_test_sha: str,
) -> None:
    with pytest.raises(
        ValidationError,
        match="continuity warrant must bind both divergent AX commits",
    ):
        live_preflight.ReceiptSutCommitBinding(
            provisioned_at_sha=provisioned_at_sha,
            under_test_sha=under_test_sha,
            acceptance_reason="reviewed-provisioning-continuity",
            continuity_warrant=live_preflight.REVIEWED_PROVISIONING_CONTINUITY_WARRANT,
        )


def test_continuity_warrant_requires_matching_source_tree_hashes() -> None:
    with pytest.raises(
        ValidationError,
        match="continuity warrant source trees must match through provisioning",
    ):
        live_preflight.ReceiptSutContinuityWarrant.model_validate(
            _continuity_warrant_payload(last_equivalent_source_tree_sha="f" * 40)
        )


@pytest.mark.parametrize(
    "changed_paths",
    [(), ("docs/runbook.md",)],
    ids=["empty", "outside-backend-src"],
)
def test_continuity_warrant_requires_reviewed_backend_source_paths(
    changed_paths: tuple[str, ...],
) -> None:
    with pytest.raises(
        ValidationError,
        match="continuity warrant must name reviewed AX source changes",
    ):
        live_preflight.ReceiptSutContinuityWarrant.model_validate(
            _continuity_warrant_payload(changed_paths=changed_paths)
        )


def test_absent_reviewed_receipt_refuses_with_distinct_error(
    tmp_path: Path,
    dataset_validation: DatasetValidationReport,
) -> None:
    with pytest.raises(ValueError, match="reviewed handoff receipt is unreadable"):
        _capture(
            dataset_validation,
            handoff_receipt_path=tmp_path / "missing-handoff.json",
        )


def test_receipt_digest_mismatch_refuses_without_literal_fallback(
    tmp_path: Path,
    dataset_validation: DatasetValidationReport,
) -> None:
    receipt_path = _write_receipt(tmp_path)

    with pytest.raises(ValueError, match="reviewed handoff receipt digest does not match"):
        _capture(dataset_validation, handoff_receipt_path=receipt_path)


@pytest.mark.parametrize(
    ("state", "completion_confirmed"),
    [("FAILED", True), ("COMPLETED", False)],
)
def test_incomplete_receipt_state_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dataset_validation: DatasetValidationReport,
    state: str,
    completion_confirmed: bool,
) -> None:
    receipt_path = _write_receipt(
        tmp_path,
        state=state,
        completion_confirmed=completion_confirmed,
    )
    _pin_fixture_digest(monkeypatch, receipt_path)

    with pytest.raises(ValueError, match="reviewed handoff receipt is not completed"):
        _capture(dataset_validation, handoff_receipt_path=receipt_path)


def test_unrelated_ax_sha_is_distinct_from_both_reviewed_commits() -> None:
    if UNRELATED_AX_SHA in {PINNED_AX_SHA, PROVISIONED_AX_SHA}:
        pytest.fail("UNRELATED_AX_SHA must differ from both reviewed AX commits")


def test_receipt_from_unrelated_commit_refuses_as_unreviewed_provisioning(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dataset_validation: DatasetValidationReport,
) -> None:
    receipt_path = _write_receipt(tmp_path, repository_commit_sha=UNRELATED_AX_SHA)
    _pin_fixture_digest(monkeypatch, receipt_path)

    with pytest.raises(
        ValueError,
        match="receipt commit does not match the reviewed provisioning commit",
    ):
        _capture(dataset_validation, handoff_receipt_path=receipt_path)


def test_reviewed_provisioning_receipt_is_accepted_for_newer_sut_for_warranted_reason(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _write_receipt(tmp_path)
    _pin_fixture_digest(monkeypatch, receipt_path)

    binding = live_preflight._load_reviewed_handoff_binding(receipt_path)

    assert binding.commit_binding.provisioned_at_sha == PROVISIONED_AX_SHA
    assert binding.commit_binding.under_test_sha == PINNED_AX_SHA
    assert binding.commit_binding.acceptance_reason == "reviewed-provisioning-continuity"
    assert binding.commit_binding.continuity_warrant is not None
    assert binding.commit_binding.continuity_warrant.model_dump(mode="json") == {
        "schema_version": "receipt-sut-continuity-warrant-v1",
        "method": "reviewed-ax-source-diff",
        "provisioned_at_sha": PROVISIONED_AX_SHA,
        "last_provisioning_equivalent_sha": "d7930978d7b0cb41668a86acd9fe77c16068801d",
        "under_test_sha": PINNED_AX_SHA,
        "provisioned_source_tree_sha": "846c06ba9461c97a75b16caf7b85570e0c0f14fd",
        "last_equivalent_source_tree_sha": "846c06ba9461c97a75b16caf7b85570e0c0f14fd",
        "changed_paths": [
            "backend/src/ax_engine/answers/contracts.py",
            "backend/src/ax_engine/answers/service.py",
            "backend/src/ax_engine/attachments/jobs.py",
        ],
        "provisioning_state_affected": False,
    }


def test_reviewed_provisioning_receipt_is_accepted_for_same_reviewed_sut(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _write_receipt(tmp_path)
    _pin_fixture_digest(monkeypatch, receipt_path)
    monkeypatch.setattr(
        live_preflight,
        "PINNED_AX_SHA",
        live_preflight.REVIEWED_PROVISIONED_AX_SHA,
    )

    binding = live_preflight._load_reviewed_handoff_binding(receipt_path)

    assert binding.commit_binding.provisioned_at_sha == live_preflight.REVIEWED_PROVISIONED_AX_SHA
    assert binding.commit_binding.under_test_sha == live_preflight.REVIEWED_PROVISIONED_AX_SHA
    assert binding.commit_binding.acceptance_reason == "same-reviewed-commit"
    assert binding.commit_binding.continuity_warrant is None


def test_preflight_artifact_refuses_sut_commit_that_is_not_the_under_test_pin() -> None:
    with pytest.raises(
        ValidationError,
        match="live preflight artifact SUT commit does not match the under-test AX commit",
    ):
        live_preflight.build_live_preflight_artifact(
            run_id="issue-94-under-test-pin",
            captured_at=datetime(2026, 7, 30, tzinfo=UTC),
            evaluation_plane_sha=EVALUATION_SHA,
            sut_commit_sha=PROVISIONED_AX_SHA,
            corpus_observations=(),
            parse_observations=(),
            blockers=(),
        )


def test_divergent_commits_refuse_when_warrant_does_not_bind_current_under_test_pin(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _write_receipt(tmp_path)
    _pin_fixture_digest(monkeypatch, receipt_path)
    monkeypatch.setattr(live_preflight, "PINNED_AX_SHA", UNRELATED_AX_SHA)

    with pytest.raises(
        ValueError,
        match="continuity warrant does not bind the current AX commits",
    ):
        live_preflight._load_reviewed_handoff_binding(receipt_path)


@pytest.mark.parametrize(
    "attachment_mapping",
    [
        dict(list(SYNTHETIC_ATTACHMENTS.items())[:-1]),
        {
            **SYNTHETIC_ATTACHMENTS,
            "synthetic-rule-999": "10000000-0000-4000-8000-000000000999",
        },
    ],
    ids=["five", "seven"],
)
def test_receipt_with_other_than_six_attachments_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dataset_validation: DatasetValidationReport,
    attachment_mapping: Mapping[str, str],
) -> None:
    receipt_path = _write_receipt(
        tmp_path,
        attachment_mapping=attachment_mapping,
    )
    _pin_fixture_digest(monkeypatch, receipt_path)

    with pytest.raises(ValueError, match="exactly six attachments"):
        _capture(dataset_validation, handoff_receipt_path=receipt_path)


def test_receipt_probe_set_not_matching_reviewed_identity_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dataset_validation: DatasetValidationReport,
) -> None:
    incomplete_mapping = dict(SYNTHETIC_ATTACHMENTS)
    incomplete_mapping.pop("synthetic-rule-020")
    incomplete_mapping["synthetic-rule-999"] = "10000000-0000-4000-8000-000000000999"
    receipt_path = _write_receipt(tmp_path, attachment_mapping=incomplete_mapping)
    _pin_fixture_digest(monkeypatch, receipt_path)

    with pytest.raises(ValueError, match="reviewed case mapping is incomplete"):
        _capture(dataset_validation, handoff_receipt_path=receipt_path)


def test_approved_mapping_refuses_probe_evidence_not_matching_reviewed_receipt() -> None:
    mismatched_probe_evidence = {
        case_id: evidence
        for case_id, evidence in live_preflight.REVIEWED_PARSING_SOURCE_EVIDENCE.items()
        if case_id != "synthetic-rule-020"
    }

    assert (
        live_preflight._approved_mapping(
            SYNTHETIC_ATTACHMENTS,
            mismatched_probe_evidence,
            SYNTHETIC_ATTACHMENTS,
        )
        is False
    )


def test_receipt_subject_different_from_caller_refuses_before_http(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    dataset_validation: DatasetValidationReport,
) -> None:
    receipt_path = _write_receipt(tmp_path, subject_id=SYNTHETIC_OTHER_SUBJECT_ID)
    _pin_fixture_digest(monkeypatch, receipt_path)

    artifact = _capture(dataset_validation, handoff_receipt_path=receipt_path)

    assert [blocker.code for blocker in artifact.blockers] == [
        "EVALUATION_PRINCIPAL_SUBJECT_INVALID"
    ]
    assert artifact.blockers[0].detail == "subject_is_not_reviewed_owner"


def test_principal_artifact_build_without_reviewed_binding_refuses(
    dataset_validation: DatasetValidationReport,
) -> None:
    dataset_identity = live_preflight._frozen_dataset_identity(dataset_validation)
    assert dataset_identity is not None

    with pytest.raises(ValidationError, match="requires reviewed handoff binding"):
        live_preflight.build_live_preflight_artifact(
            run_id="issue-67-missing-binding",
            captured_at=datetime(2026, 7, 26, tzinfo=UTC),
            evaluation_plane_sha=EVALUATION_SHA,
            sut_commit_sha=PINNED_AX_SHA,
            corpus_observations=(),
            parse_observations=(),
            blockers=(),
            dataset_identity=dataset_identity,
            capture_contract="principal-attachment-preflight-v1",
        )


def test_principal_artifact_replay_without_receipt_refuses(tmp_path: Path) -> None:
    artifact_path = tmp_path / "principal-artifact.json"
    artifact_path.write_text(
        json.dumps(
            {
                "schema_version": "principal-attachment-preflight-evidence-v1",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="requires the reviewed handoff receipt",
    ):
        live_preflight.replay_live_preflight_artifact(
            artifact_path,
            handoff_receipt_path=None,
        )


def _capture(
    validation: DatasetValidationReport,
    *,
    handoff_receipt_path: Path,
    sut_commit_sha: str = PINNED_AX_SHA,
) -> live_preflight.LivePreflightArtifact:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("receipt refusal must happen before HTTP", request=request)

    return live_preflight.capture_principal_attachment_preflight(
        run_id="issue-67-receipt-binding",
        captured_at=datetime(2026, 7, 26, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=sut_commit_sha,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=SYNTHETIC_SUBJECT_ID,
        attachment_mapping=SYNTHETIC_ATTACHMENTS,
        dataset_validation=validation,
        handoff_receipt_path=handoff_receipt_path,
        transport=httpx.MockTransport(handler),
    )


def _write_receipt(
    tmp_path: Path,
    *,
    state: str = "COMPLETED",
    completion_confirmed: bool = True,
    repository_commit_sha: str = PROVISIONED_AX_SHA,
    subject_id: str = SYNTHETIC_SUBJECT_ID,
    attachment_mapping: Mapping[str, str] = SYNTHETIC_ATTACHMENTS,
) -> Path:
    receipt: dict[str, Any] = {
        "repository": {"commit_sha": repository_commit_sha, "dirty": False},
        "target": {"subject_id": subject_id, "tenant_id": TENANT_ID},
        "state": state,
        "completion_confirmed": completion_confirmed,
        "attachments": [
            {
                "case_id": case_id,
                "attachment_id": attachment_id,
                "approval": {
                    "approval_id": f"00000000-0000-4000-8000-{index:012d}",
                },
            }
            for index, (case_id, attachment_id) in enumerate(
                attachment_mapping.items(),
                start=1,
            )
        ],
    }
    receipt_path = tmp_path / "synthetic-handoff.json"
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    return receipt_path


def _pin_fixture_digest(monkeypatch: pytest.MonkeyPatch, receipt_path: Path) -> None:
    digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    monkeypatch.setattr(live_preflight, "REVIEWED_HANDOFF_RECEIPT_SHA256", digest)
