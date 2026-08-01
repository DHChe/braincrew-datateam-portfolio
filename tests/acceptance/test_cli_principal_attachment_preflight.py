from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import UTC, datetime
from inspect import signature
from pathlib import Path
from typing import Any, cast

import httpx
import pytest
from typer.testing import CliRunner

import braincrew.cli as cli
import braincrew.live_preflight as live_preflight
from braincrew import corpus_qualification
from braincrew.cli import app
from braincrew.contracts import ParsingCase
from braincrew.dataset_registry import validate_dataset_bundle
from braincrew.digest import canonical_digest
from braincrew.parsing_run import load_parsing_dataset
from braincrew.repository import RepositoryState

PROJECT_ROOT = Path(__file__).parents[2]
PINNED_AX_SHA = live_preflight.PINNED_AX_SHA
PROVISIONED_AX_SHA = "2bcaee3495fd7b3f624398819575cd86a5a15c47"
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
ANSI_ESCAPE_SEQUENCE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def test_v3_manifest_documents_can_differ_from_reviewed_probes_and_capture_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _install_reviewed_receipt(tmp_path, monkeypatch)
    validation = validate_dataset_bundle(PROJECT_ROOT / "datasets/dataset_manifest_v3.json")
    assert validation.state == "VALID"
    assert validation.snapshot is not None
    manifest_verification_ids = {
        case.document.id: case
        for case in validation.snapshot.parsing_dataset.cases
        if case.split == "verification"
    }
    reviewed_probe_cases = _reviewed_probe_cases()
    # Issue #75 acceptance item 3: manifest membership does not select live probes.
    assert set(manifest_verification_ids).isdisjoint(reviewed_probe_cases)
    attachment_documents = {
        attachment_id: document_id for document_id, attachment_id in APPROVED_ATTACHMENTS.items()
    }
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        attachment_id = request.url.path.split("/")[-2]
        document_id = attachment_documents[attachment_id]
        case = reviewed_probe_cases[document_id]
        payload = _parse_response(case, attachment_id=attachment_id)
        if document_id == "synthetic-rule-019":
            payload["headings"] = []
            payload["metadata"] = {}
            payload["unavailable_fields"] = ["headings", "list", "metadata", "table"]
        return httpx.Response(200, json=payload)

    artifact = live_preflight.capture_principal_attachment_preflight(
        run_id="issue-34-acceptance",
        captured_at=datetime(2026, 7, 22, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=validation,
        handoff_receipt_path=receipt_path,
        transport=httpx.MockTransport(handler),
    )

    assert artifact.schema_version == "principal-attachment-preflight-evidence-v1"
    assert artifact.capture_state == "captured"
    assert artifact.blockers == ()
    assert artifact.corpus_observations == ()
    assert artifact.dataset_identity is not None
    assert artifact.dataset_identity.id == "braincrew-evaluation-dataset"
    assert artifact.dataset_identity.version == "3.0.0"
    assert (
        artifact.dataset_identity.content_digest
        == "sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d"
    )
    assert artifact.dataset_identity.component_digests.model_dump() == {
        "parsing": "sha256:33e17fbb4d3f5485df1482de37e472e1b20fceef922c9b1dda90f8d9dfc25f73",
        "retrieval": "sha256:9687ead24590cab1b9d244ef876f226545a1fb1aa2013c50e4be7a63430c8408",
        "grounded": "sha256:f76a9a1fa9a6a4b467f76ce7649dc7c15f5ad7c615d6cbb20ed3394e486d94b2",
    }
    assert len(artifact.parse_observations) == 6
    assert [request.headers["x-ax-user-id"] for request in requests] == [OWNER_USER_ID] * 6
    assert [request.headers["x-ax-roles"] for request in requests] == ["HRPractitioner"] * 6
    assert {
        observation.request.case_id: observation.response.attachment_id
        for observation in artifact.parse_observations
    } == APPROVED_ATTACHMENTS
    assert all(
        observation.response.parser_name == "utf8-text"
        and observation.response.parser_version == "stdlib-1"
        and observation.response.evidence_spans
        and observation.response_digest.startswith("sha256:")
        for observation in artifact.parse_observations
    )
    sparse = next(
        observation
        for observation in artifact.parse_observations
        if observation.request.case_id == "synthetic-rule-019"
    )
    assert sparse.response.headings_count == 0
    assert sparse.response.metadata_keys == ()
    assert sparse.response.table_shape is None
    assert sparse.response.list_shape is None
    assert not hasattr(artifact, "parsing_evaluation")
    assert "READY" not in artifact.model_dump_json()

    artifact_path = live_preflight.write_live_preflight_artifact(
        artifact,
        tmp_path / "issue-34-live-preflight-evidence.json",
    )
    retained = artifact_path.read_text(encoding="utf-8")
    assert all(
        case.document.canonical_text not in retained for case in reviewed_probe_cases.values()
    )
    assert '"extracted_text"' not in retained
    assert '"text"' not in retained

    replay = _replay_in_process(artifact_path, receipt_path)

    assert replay.returncode == 0, replay.stderr
    summary = cast(dict[str, Any], json.loads(replay.stdout))
    assert summary["capture_state"] == "captured"
    assert summary["schema_version"] == "principal-attachment-preflight-evidence-v1"
    assert summary["parse_observation_count"] == 6
    assert summary["blocker_count"] == 0
    assert summary["logical_digest"] == artifact.logical_digest

    payload = cast(dict[str, Any], json.loads(retained))
    parse_observations = cast(list[dict[str, Any]], payload["parse_observations"])
    first_response = cast(dict[str, Any], parse_observations[0]["response"])
    first_spans = cast(list[dict[str, Any]], first_response["evidence_spans"])
    first_spans[0]["text_digest"] = "sha256:" + "0" * 64
    parse_observations[0]["response_digest"] = canonical_digest(first_response)
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    invalid_span_replay = _replay_in_process(artifact_path, receipt_path)

    assert invalid_span_replay.returncode == 2
    assert "Invalid artifact" in invalid_span_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    parse_observations = cast(list[dict[str, Any]], payload["parse_observations"])
    first_response = cast(dict[str, Any], parse_observations[0]["response"])
    first_spans = cast(list[dict[str, Any]], first_response["evidence_spans"])
    first_spans[0]["id"] = "unsafe span id"
    parse_observations[0]["response_digest"] = canonical_digest(first_response)
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    unsafe_span_id_replay = _replay_in_process(artifact_path, receipt_path)

    assert unsafe_span_id_replay.returncode == 2
    assert "Invalid artifact" in unsafe_span_id_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    parse_observations = cast(list[dict[str, Any]], payload["parse_observations"])
    second_request = cast(dict[str, Any], parse_observations[1]["request"])
    second_request["tenant_id"] = "33333333-3333-3333-3333-333333333333"
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    inconsistent_tenant_replay = _replay_in_process(artifact_path, receipt_path)

    assert inconsistent_tenant_replay.returncode == 2
    assert "Invalid artifact" in inconsistent_tenant_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    parse_observations = cast(list[dict[str, Any]], payload["parse_observations"])
    first_request = cast(dict[str, Any], parse_observations[0]["request"])
    first_request["query"] = "employee salary details"
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    non_parse_payload_replay = _replay_in_process(artifact_path, receipt_path)

    assert non_parse_payload_replay.returncode == 2
    assert "Invalid artifact" in non_parse_payload_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    parse_observations = cast(list[dict[str, Any]], payload["parse_observations"])
    first_response = cast(dict[str, Any], parse_observations[0]["response"])
    first_response["parser_name"] = "markdown-text"
    parse_observations[0]["response_digest"] = canonical_digest(first_response)
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    semantically_invalid_replay = _replay_in_process(artifact_path, receipt_path)

    assert semantically_invalid_replay.returncode == 2
    assert "Invalid artifact" in semantically_invalid_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    parse_observations = cast(list[dict[str, Any]], payload["parse_observations"])
    parse_observations.pop()
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    incomplete_replay = _replay_in_process(artifact_path, receipt_path)

    assert incomplete_replay.returncode == 2
    assert "Invalid artifact" in incomplete_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    payload.pop("dataset_identity")
    payload.pop("capture_contract")
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    missing_identity_replay = _replay_in_process(artifact_path, receipt_path)

    assert missing_identity_replay.returncode == 2
    assert "Invalid artifact" in missing_identity_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    dataset_identity = cast(dict[str, Any], payload["dataset_identity"])
    dataset_identity["content_digest"] = "sha256:" + "0" * 64
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    tampered_replay = _replay_in_process(artifact_path, receipt_path)

    assert tampered_replay.returncode == 2
    assert "Invalid artifact" in tampered_replay.stderr


def test_blocked_principal_attachment_capture_cannot_replay_without_dataset_identity(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _install_reviewed_receipt(tmp_path, monkeypatch)
    validation = validate_dataset_bundle(PROJECT_ROOT / "datasets/dataset_manifest_v3.json")
    assert validation.state == "VALID"

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("synthetic endpoint unavailable", request=request)

    artifact = live_preflight.capture_principal_attachment_preflight(
        run_id="issue-34-blocked-acceptance",
        captured_at=datetime(2026, 7, 22, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=validation,
        handoff_receipt_path=receipt_path,
        transport=httpx.MockTransport(handler),
    )

    assert artifact.schema_version == "principal-attachment-preflight-evidence-v1"
    assert artifact.capture_contract == "principal-attachment-preflight-v1"
    assert artifact.dataset_identity is not None
    assert [blocker.code for blocker in artifact.blockers] == ["LIVE_PARSE_OBSERVATION_UNREACHABLE"]
    assert artifact.blockers[0].request is not None
    assert artifact.blockers[0].request.tenant_id == TENANT_ID
    assert artifact.blockers[0].request.user_id == OWNER_USER_ID
    assert artifact.blockers[0].request.roles == ("HRPractitioner",)

    artifact_path = live_preflight.write_live_preflight_artifact(
        artifact,
        tmp_path / "issue-34-blocked-live-preflight-evidence.json",
    )
    retained = artifact_path.read_text(encoding="utf-8")
    payload = cast(dict[str, Any], json.loads(retained))
    blockers = cast(list[dict[str, Any]], payload["blockers"])
    blocker_request = cast(dict[str, Any], blockers[0]["request"])
    blocker_request["user_id"] = "33333333-3333-3333-3333-333333333333"
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    inconsistent_principal_replay = _replay_in_process(artifact_path, receipt_path)

    assert inconsistent_principal_replay.returncode == 2
    assert "Invalid artifact" in inconsistent_principal_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    blockers = cast(list[dict[str, Any]], payload["blockers"])
    attempts = cast(list[dict[str, Any]], blockers[0]["attempts"])
    attempts[0]["outcome"] = "success"
    attempts[0]["status_code"] = 200
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    inconsistent_blocker_replay = _replay_in_process(artifact_path, receipt_path)

    assert inconsistent_blocker_replay.returncode == 2
    assert "Invalid artifact" in inconsistent_blocker_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    blockers = cast(list[dict[str, Any]], payload["blockers"])
    blockers[0]["attempts"] = []
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    attemptless_replay = _replay_in_process(artifact_path, receipt_path)

    assert attemptless_replay.returncode == 2
    assert "Invalid artifact" in attemptless_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    payload["blockers"] = []
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    incomplete_replay = _replay_in_process(artifact_path, receipt_path)

    assert incomplete_replay.returncode == 2
    assert "Invalid artifact" in incomplete_replay.stderr

    payload = cast(dict[str, Any], json.loads(retained))
    payload.pop("dataset_identity")
    payload.pop("capture_contract")
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    replay = _replay_in_process(artifact_path, receipt_path)

    assert replay.returncode == 2
    assert "Invalid artifact" in replay.stderr


def test_real_cli_principal_replay_without_handoff_receipt_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _install_reviewed_receipt(tmp_path, monkeypatch)
    validation = validate_dataset_bundle(PROJECT_ROOT / "datasets/dataset_manifest_v3.json")
    assert validation.state == "VALID"

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("synthetic endpoint unavailable", request=request)

    artifact = live_preflight.capture_principal_attachment_preflight(
        run_id="issue-67-real-cli-missing-receipt",
        captured_at=datetime(2026, 7, 26, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=validation,
        handoff_receipt_path=receipt_path,
        transport=httpx.MockTransport(handler),
    )
    artifact_path = live_preflight.write_live_preflight_artifact(
        artifact,
        tmp_path / "principal-artifact-without-receipt.json",
    )

    replay = _run_cli_subprocess("replay", "--artifact", str(artifact_path))

    assert replay.returncode == 2
    assert "requires the reviewed handoff receipt" in replay.stderr


def test_reviewed_live_verification_capture_derives_receipt_bound_inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _install_reviewed_receipt(tmp_path, monkeypatch)
    validation = validate_dataset_bundle(PROJECT_ROOT / "datasets/dataset_manifest_v3.json")
    capture = getattr(live_preflight, "capture_reviewed_live_verification_preflight", None)
    if capture is None:
        pytest.fail("reviewed live verification capture entry point is missing")
    if "tenant_id" in signature(capture).parameters:
        pytest.fail("reviewed tenant remains a typed capture input")

    artifact = capture(
        run_id="issue-82-derived-inputs",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        dataset_validation=validation,
        handoff_receipt_path=receipt_path,
        transport=_live_verification_transport(),
    )

    if artifact.readiness != "READY":
        pytest.fail(f"receipt-bound capture did not reach READY: {artifact.blockers}")
    if len(artifact.parse_observations) != 6:
        pytest.fail("receipt-bound capture did not derive all reviewed attachment mappings")
    observed_users = {
        observation.request.user_id
        for observation in (*artifact.parse_observations, *artifact.corpus_observations)
    }
    if observed_users != {OWNER_USER_ID}:
        pytest.fail(f"receipt-bound capture used unexpected subjects: {sorted(observed_users)}")
    observed_tenants = {
        observation.request.tenant_id
        for observation in (*artifact.parse_observations, *artifact.corpus_observations)
    }
    if observed_tenants != {TENANT_ID}:
        pytest.fail(f"receipt-bound capture used unexpected tenants: {sorted(observed_tenants)}")


def test_cli_live_verification_ready_writes_create_only_artifact_and_exits_zero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _install_reviewed_receipt(tmp_path, monkeypatch)
    output_path = tmp_path / "live-verification-ready.json"
    capture_calls: list[dict[str, Any]] = []

    def capture_with_mock_transport(**kwargs: Any) -> live_preflight.LivePreflightArtifact:
        capture_calls.append(kwargs)
        return live_preflight.capture_live_verification_preflight(
            **kwargs,
            tenant_id=TENANT_ID,
            user_id=OWNER_USER_ID,
            attachment_mapping=APPROVED_ATTACHMENTS,
            transport=_live_verification_transport(),
        )

    monkeypatch.setattr(
        cli,
        "capture_reviewed_live_verification_preflight",
        capture_with_mock_transport,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "_capture_repository_state",
        lambda: RepositoryState(commit_sha=EVALUATION_SHA, dirty_worktree=False),
    )

    result = _capture_live_verification_in_process(
        output_path=output_path,
        receipt_path=receipt_path,
        run_id="issue-82-ready",
    )

    if result.returncode != 0:
        pytest.fail(f"READY capture exited {result.returncode}: {result.stderr}")
    if not output_path.is_file():
        pytest.fail("READY capture did not write its artifact")
    summary = cast(dict[str, Any], json.loads(result.stdout))
    if summary.get("artifact_path") != output_path.name:
        pytest.fail(f"capture exposed an unexpected artifact path: {summary}")
    if summary.get("readiness") != "READY":
        pytest.fail(f"capture summary lost READY: {summary}")
    if len(capture_calls) != 1:
        pytest.fail(f"capture command invoked the capture {len(capture_calls)} times")
    call = capture_calls[0]
    if call.get("evaluation_plane_sha") != EVALUATION_SHA:
        pytest.fail("capture command did not derive the current Evaluation Plane SHA")
    if call.get("sut_commit_sha") != PINNED_AX_SHA:
        pytest.fail("capture command did not derive the pinned AX SHA")
    if call.get("handoff_receipt_path") != receipt_path:
        pytest.fail("capture command did not forward the selected handoff receipt path")
    dataset_validation = call.get("dataset_validation")
    if getattr(dataset_validation, "state", None) != "VALID":
        pytest.fail("capture command did not derive the frozen v3 dataset validation")
    captured_at = call.get("captured_at")
    if not isinstance(captured_at, datetime) or captured_at.utcoffset() != UTC.utcoffset(None):
        pytest.fail("capture command did not derive an aware UTC capture timestamp")
    if (
        str(receipt_path) in result.stdout
        or receipt_path.read_text(encoding="utf-8") in result.stdout
    ):
        pytest.fail("capture summary exposed the reviewed receipt path or contents")

    retained = output_path.read_bytes()
    duplicate = _capture_live_verification_in_process(
        output_path=output_path,
        receipt_path=receipt_path,
        run_id="issue-82-ready",
    )

    if duplicate.returncode != 2:
        pytest.fail(f"duplicate capture exited {duplicate.returncode}, expected no-artifact code 2")
    if output_path.read_bytes() != retained:
        pytest.fail("duplicate capture overwrote the create-only artifact")
    if len(capture_calls) != 1:
        pytest.fail("duplicate output was discovered only after another live capture")


def test_cli_live_verification_dirty_worktree_exits_two_before_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _install_reviewed_receipt(tmp_path, monkeypatch)
    output_path = tmp_path / "dirty-worktree-must-not-capture.json"

    def unexpected_capture(**kwargs: Any) -> live_preflight.LivePreflightArtifact:
        pytest.fail(f"dirty worktree reached capture with arguments: {sorted(kwargs)}")

    monkeypatch.setattr(
        cli,
        "capture_reviewed_live_verification_preflight",
        unexpected_capture,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "_capture_repository_state",
        lambda: RepositoryState(commit_sha=EVALUATION_SHA, dirty_worktree=True),
    )

    result = _capture_live_verification_in_process(
        output_path=output_path,
        receipt_path=receipt_path,
        run_id="issue-82-dirty-worktree",
    )

    if result.returncode != 2:
        pytest.fail(f"dirty worktree exited {result.returncode}, expected no-artifact code 2")
    if output_path.exists():
        pytest.fail("dirty worktree produced an artifact")
    if "clean committed Evaluation Plane checkout" not in result.stderr:
        pytest.fail(f"dirty worktree refusal was not actionable: {result.stderr}")


def test_cli_live_verification_output_refuses_a_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _install_reviewed_receipt(tmp_path, monkeypatch)

    def unexpected_capture(**kwargs: Any) -> live_preflight.LivePreflightArtifact:
        pytest.fail(f"directory output reached capture with arguments: {sorted(kwargs)}")

    monkeypatch.setattr(
        cli,
        "capture_reviewed_live_verification_preflight",
        unexpected_capture,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "_capture_repository_state",
        lambda: RepositoryState(commit_sha=EVALUATION_SHA, dirty_worktree=False),
    )

    result = _capture_live_verification_in_process(
        output_path=tmp_path,
        receipt_path=receipt_path,
        run_id="issue-82-directory-output",
    )

    if result.returncode != 2:
        pytest.fail(f"directory output exited {result.returncode}, expected usage code 2")
    if "Invalid value for '--output'" not in result.stderr or "directory" not in result.stderr:
        pytest.fail(f"directory output was not rejected as an invalid option: {result.stderr}")


def test_cli_live_verification_help_has_no_tenant_option() -> None:
    result = CliRunner().invoke(app, ["capture-live-verification", "--help"])

    if result.exit_code != 0:
        pytest.fail(f"capture help exited {result.exit_code}: {result.stderr}")
    if "--tenant-id" in result.stdout:
        pytest.fail("capture help still exposes the reviewed tenant as an operator input")


def test_cli_live_verification_not_ready_writes_artifact_and_exits_three(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _install_reviewed_receipt(tmp_path, monkeypatch)
    output_path = tmp_path / "live-verification-not-ready.json"

    def capture_with_mock_transport(**kwargs: Any) -> live_preflight.LivePreflightArtifact:
        return live_preflight.capture_live_verification_preflight(
            **kwargs,
            tenant_id=TENANT_ID,
            user_id=OWNER_USER_ID,
            attachment_mapping=APPROVED_ATTACHMENTS,
            transport=_live_verification_transport(corpus_failure_status=503),
        )

    monkeypatch.setattr(
        cli,
        "capture_reviewed_live_verification_preflight",
        capture_with_mock_transport,
        raising=False,
    )
    monkeypatch.setattr(
        cli,
        "_capture_repository_state",
        lambda: RepositoryState(commit_sha=EVALUATION_SHA, dirty_worktree=False),
    )

    result = _capture_live_verification_in_process(
        output_path=output_path,
        receipt_path=receipt_path,
        run_id="issue-82-not-ready",
    )

    if result.returncode != 3:
        pytest.fail(f"NOT_READY capture exited {result.returncode}, expected gate code 3")
    if not output_path.is_file():
        pytest.fail("NOT_READY capture did not preserve its artifact")
    summary = cast(dict[str, Any], json.loads(result.stdout))
    if summary.get("readiness") != "NOT_READY" or summary.get("blocker_count") != 1:
        pytest.fail(f"NOT_READY capture summary lost its verdict or blocker: {summary}")
    replay = live_preflight.replay_live_preflight_artifact(
        output_path,
        handoff_receipt_path=receipt_path,
    )
    if replay.get("readiness") != "NOT_READY":
        pytest.fail(f"NOT_READY artifact did not replay its verdict: {replay}")


def test_cli_replay_dispatches_live_verification_v2(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt_path = _install_reviewed_receipt(tmp_path, monkeypatch)
    validation = validate_dataset_bundle(PROJECT_ROOT / "datasets/dataset_manifest_v3.json")
    artifact = live_preflight.capture_live_verification_preflight(
        run_id="issue-82-v2-replay",
        captured_at=datetime(2026, 7, 27, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        base_url="https://ax.example.test",
        tenant_id=TENANT_ID,
        user_id=OWNER_USER_ID,
        attachment_mapping=APPROVED_ATTACHMENTS,
        dataset_validation=validation,
        handoff_receipt_path=receipt_path,
        transport=_live_verification_transport(),
    )
    artifact_path = live_preflight.write_live_preflight_artifact(
        artifact,
        tmp_path / "live-verification-v2-replay.json",
    )

    result = _replay_in_process(artifact_path, receipt_path)

    if result.returncode != 0:
        pytest.fail(f"v2 CLI replay exited {result.returncode}: {result.stderr}")
    summary = cast(dict[str, Any], json.loads(result.stdout))
    if summary.get("readiness") != "READY":
        pytest.fail(f"v2 CLI replay lost the validated verdict: {summary}")
    if summary.get("logical_digest") != artifact.logical_digest:
        pytest.fail(f"v2 CLI replay lost the validated logical digest: {summary}")


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


def _reviewed_probe_cases() -> dict[str, ParsingCase]:
    parsing_dataset = load_parsing_dataset(PROJECT_ROOT / "datasets/parsing/parsing_cases_v1.json")
    cases = {
        case.document.id: case for case in parsing_dataset.cases if case.split == "verification"
    }
    assert set(cases) == set(live_preflight.REVIEWED_PARSING_SOURCE_EVIDENCE)
    return cases


def _install_reviewed_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
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
    digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    monkeypatch.setattr(live_preflight, "REVIEWED_HANDOFF_RECEIPT_SHA256", digest)
    return receipt_path


def _replay_in_process(
    artifact_path: Path,
    receipt_path: Path,
) -> subprocess.CompletedProcess[str]:
    arguments = [
        "replay",
        "--artifact",
        str(artifact_path),
        "--handoff-receipt",
        str(receipt_path),
    ]
    result = CliRunner().invoke(app, arguments)
    return subprocess.CompletedProcess(
        args=arguments,
        returncode=result.exit_code,
        stdout=result.stdout,
        stderr=result.stderr,
    )


def _run_cli_subprocess(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "braincrew-eval", *arguments],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _capture_live_verification_in_process(
    *,
    output_path: Path,
    receipt_path: Path,
    run_id: str,
) -> subprocess.CompletedProcess[str]:
    arguments = [
        "capture-live-verification",
        "--output",
        str(output_path),
        "--run-id",
        run_id,
        "--base-url",
        "https://ax.example.test",
        "--handoff-receipt",
        str(receipt_path),
    ]
    result = CliRunner().invoke(app, arguments)
    return subprocess.CompletedProcess(
        args=arguments,
        returncode=result.exit_code,
        stdout=result.stdout,
        stderr=ANSI_ESCAPE_SEQUENCE.sub("", result.stderr),
    )


def _live_verification_transport(
    *,
    corpus_failure_status: int | None = None,
) -> httpx.MockTransport:
    cases = _reviewed_probe_cases()
    attachment_documents = {
        attachment_id: document_id for document_id, attachment_id in APPROVED_ATTACHMENTS.items()
    }

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/evaluation/corpus-identity":
            if corpus_failure_status is not None:
                return httpx.Response(corpus_failure_status, json={"detail": "starting"})
            role = request.headers["x-ax-roles"]
            digest_digit = {
                "Employee": "1",
                "Executive": "2",
                "HRPractitioner": "3",
            }[role]
            return httpx.Response(
                200,
                json={
                    "schema_version": "ax-corpus-identity-v1",
                    "corpus_id": f"ax-visible-retrieval:{TENANT_ID}",
                    "corpus_version": "retrieval-inventory-v1",
                    "corpus_digest": f"sha256:{digest_digit * 64}",
                    "principal_roles": [role],
                    "inventory_count": 6,
                    "counts": {"record_kind": {"source_chunk": 6}},
                    "contributing_versions": [corpus_qualification.SEED_VERSION],
                    "generated_at": "2026-07-27T00:00:00Z",
                },
            )
        attachment_id = request.url.path.split("/")[-2]
        document_id = attachment_documents[attachment_id]
        return httpx.Response(
            200,
            json=_parse_response(cases[document_id], attachment_id=attachment_id),
        )

    return httpx.MockTransport(handler)
