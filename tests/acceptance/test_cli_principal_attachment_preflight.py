from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx

import braincrew.live_preflight as live_preflight
from braincrew.contracts import ParsingCase
from braincrew.dataset_registry import validate_dataset_bundle

PROJECT_ROOT = Path(__file__).parents[2]
PINNED_AX_SHA = "72805930d9addd8ea41743d1922acf8de621c3f8"
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


def test_six_reviewed_owner_probes_create_raw_text_free_replayable_evidence(
    tmp_path: Path,
) -> None:
    validation = validate_dataset_bundle(PROJECT_ROOT / "datasets/dataset_manifest_v2.json")
    assert validation.state == "VALID"
    assert validation.snapshot is not None
    cases = {
        case.document.id: case
        for case in validation.snapshot.parsing_dataset.cases
        if case.split == "verification"
    }
    attachment_documents = {
        attachment_id: document_id for document_id, attachment_id in APPROVED_ATTACHMENTS.items()
    }
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        attachment_id = request.url.path.split("/")[-2]
        document_id = attachment_documents[attachment_id]
        case = cases[document_id]
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
        transport=httpx.MockTransport(handler),
    )

    assert artifact.capture_state == "captured"
    assert artifact.blockers == ()
    assert artifact.corpus_observations == ()
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
    assert all(case.document.canonical_text not in retained for case in cases.values())
    assert '"extracted_text"' not in retained
    assert '"text"' not in retained

    replay = subprocess.run(
        ["uv", "run", "braincrew-eval", "replay", "--artifact", str(artifact_path)],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert replay.returncode == 0, replay.stderr
    summary = cast(dict[str, Any], json.loads(replay.stdout))
    assert summary["capture_state"] == "captured"
    assert summary["parse_observation_count"] == 6
    assert summary["blocker_count"] == 0
    assert summary["logical_digest"] == artifact.logical_digest


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
