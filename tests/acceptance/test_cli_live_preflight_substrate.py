from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import httpx
import pytest

from braincrew.ax_http_adapter import (
    AxHttpAdapter,
    AxHttpAdapterConfig,
    AxRequestContext,
)
from braincrew.digest import canonical_digest
from braincrew.live_preflight import (
    LivePreflightBlocker,
    build_live_preflight_artifact,
    write_live_preflight_artifact,
)

PROJECT_ROOT = Path(__file__).parents[2]
PINNED_AX_SHA = "72805930d9addd8ea41743d1922acf8de621c3f8"
EVALUATION_SHA = "fdbb732ee05a9de5270c91a82f0930da0413107b"
TENANT_ID = "11111111-1111-1111-1111-111111111111"
USER_ID = "22222222-2222-2222-2222-222222222222"
ATTACHMENT_ID = "33333333-3333-3333-3333-333333333333"
SOURCE_TEXT = "징계 절차 원문"
SOURCE_DIGEST = "sha256:" + hashlib.sha256(SOURCE_TEXT.encode()).hexdigest()
CORPUS_DIGEST = "sha256:" + "2" * 64


def test_create_only_live_preflight_evidence_is_sanitized_and_cli_replayable(
    tmp_path: Path,
) -> None:
    adapter = _adapter()
    corpus_observation = adapter.corpus_identity(context=_context("corpus"))
    parse_observation = adapter.parse(
        context=_context("synthetic-rule-015"),
        attachment_id=ATTACHMENT_ID,
    )
    artifact = build_live_preflight_artifact(
        run_id="run-live-substrate",
        captured_at=datetime(2026, 7, 22, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        corpus_observations=(corpus_observation,),
        parse_observations=(parse_observation,),
        blockers=(
            LivePreflightBlocker(
                code="AX_PERMANENT_HTTP_FAILURE",
                operation="parse",
                case_id="synthetic-rule-016",
                detail="not_found",
            ),
        ),
    )
    artifact_path = tmp_path / "live-preflight-evidence.json"

    written = write_live_preflight_artifact(artifact, artifact_path)

    assert written == artifact_path
    payload = _read_json(artifact_path)
    assert payload["schema_version"] == "live-preflight-evidence-v1"
    assert payload["capture_state"] == "captured"
    assert payload["evaluation_plane_sha"] == EVALUATION_SHA
    assert payload["sut_commit_sha"] == PINNED_AX_SHA
    parse_evidence = payload["parse_observations"][0]
    assert parse_evidence["request"]["roles"] == ["HRPractitioner"]
    assert parse_evidence["response"]["attachment_id"] == ATTACHMENT_ID
    assert parse_evidence["response"]["extracted_text_digest"] == SOURCE_DIGEST
    assert "extracted_text" not in parse_evidence["response"]
    span = parse_evidence["response"]["evidence_spans"][0]
    assert "text" not in span
    assert span["text_digest"] == SOURCE_DIGEST
    assert span["source_text_digest"] == SOURCE_DIGEST
    assert parse_evidence["response_digest"].startswith("sha256:")

    retained = artifact_path.read_text(encoding="utf-8")
    for forbidden in (
        SOURCE_TEXT,
        "Bearer",
        "credential",
        "authorization",
        "postgresql://",
        str(tmp_path),
        "READY",
    ):
        assert forbidden not in retained

    original = artifact_path.read_bytes()
    with pytest.raises(FileExistsError):
        write_live_preflight_artifact(artifact, artifact_path)
    assert artifact_path.read_bytes() == original

    replay = _run_cli("replay", "--artifact", str(artifact_path))

    assert replay.returncode == 0, replay.stderr
    replay_summary = json.loads(replay.stdout)
    assert replay_summary["logical_digest"] == payload["logical_digest"]
    assert replay_summary["capture_state"] == "captured"
    assert replay_summary["corpus_observation_count"] == 1
    assert replay_summary["parse_observation_count"] == 1
    assert replay_summary["blocker_count"] == 1


def test_live_preflight_replay_preserves_legacy_v1_omitted_defaults(
    tmp_path: Path,
) -> None:
    adapter = _adapter()
    artifact = build_live_preflight_artifact(
        run_id="run-live-substrate-legacy",
        captured_at=datetime(2026, 7, 22, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        corpus_observations=(),
        parse_observations=(
            adapter.parse(
                context=_context("synthetic-rule-015", run_id="run-live-substrate-legacy"),
                attachment_id=ATTACHMENT_ID,
            ),
        ),
        blockers=(
            LivePreflightBlocker(
                code="AX_PERMANENT_HTTP_FAILURE",
                operation="parse",
                case_id="synthetic-rule-016",
                detail="not_found",
            ),
        ),
    )
    payload = artifact.model_dump(mode="json")
    blocker = cast(list[dict[str, Any]], payload["blockers"])[0]
    blocker["code"] = "LIVE_PARSE_OBSERVATION_FAILED"
    blocker["case_id"] = "legacy-case"
    blocker["detail"] = "legacy_parse_failed"
    payload.pop("dataset_identity")
    payload.pop("capture_contract")
    blocker.pop("attempts")
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path = tmp_path / "legacy-live-preflight-evidence.json"
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    replay = _run_cli("replay", "--artifact", str(artifact_path))

    assert replay.returncode == 0, replay.stderr
    replay_summary = json.loads(replay.stdout)
    assert replay_summary["schema_version"] == "live-preflight-evidence-v1"
    assert replay_summary["logical_digest"] == payload["logical_digest"]


def test_generic_live_preflight_rejects_new_blocker_request_payload() -> None:
    observation = _adapter().parse(
        context=_context("synthetic-rule-015"),
        attachment_id=ATTACHMENT_ID,
    )
    blocker_request = observation.request.model_copy(
        update={"query": "private employee salary query"}
    )

    with pytest.raises(ValueError, match="generic live preflight blocker cannot retain a request"):
        build_live_preflight_artifact(
            run_id="run-live-substrate",
            captured_at=datetime(2026, 7, 22, tzinfo=UTC),
            evaluation_plane_sha=EVALUATION_SHA,
            sut_commit_sha=PINNED_AX_SHA,
            corpus_observations=(),
            parse_observations=(),
            blockers=(
                LivePreflightBlocker(
                    code="AX_PERMANENT_HTTP_FAILURE",
                    operation="parse",
                    case_id="synthetic-rule-015",
                    request=blocker_request,
                    detail="not_found",
                ),
            ),
        )


def test_generic_live_preflight_replays_legacy_non_safe_span_id(
    tmp_path: Path,
) -> None:
    adapter = _adapter()
    artifact = build_live_preflight_artifact(
        run_id="run-live-substrate-legacy-span",
        captured_at=datetime(2026, 7, 22, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        corpus_observations=(),
        parse_observations=(
            adapter.parse(
                context=_context(
                    "synthetic-rule-015",
                    run_id="run-live-substrate-legacy-span",
                ),
                attachment_id=ATTACHMENT_ID,
            ),
        ),
        blockers=(),
    )
    payload = artifact.model_dump(mode="json")
    observation = cast(list[dict[str, Any]], payload["parse_observations"])[0]
    response = cast(dict[str, Any], observation["response"])
    spans = cast(list[dict[str, Any]], response["evidence_spans"])
    spans[0]["id"] = "legacy span id"
    observation["response_digest"] = canonical_digest(response)
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path = tmp_path / "legacy-span-live-preflight-evidence.json"
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    replay = _run_cli("replay", "--artifact", str(artifact_path))

    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)["logical_digest"] == payload["logical_digest"]


def test_live_preflight_replay_preserves_legacy_generic_reviewed_attachment(
    tmp_path: Path,
) -> None:
    adapter = _adapter()
    artifact = build_live_preflight_artifact(
        run_id="run-live-substrate-reviewed-legacy",
        captured_at=datetime(2026, 7, 22, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        corpus_observations=(),
        parse_observations=(
            adapter.parse(
                context=_context(
                    "synthetic-rule-015",
                    run_id="run-live-substrate-reviewed-legacy",
                ),
                attachment_id=ATTACHMENT_ID,
            ),
        ),
        blockers=(),
    )
    payload = artifact.model_dump(mode="json")
    observation = cast(list[dict[str, Any]], payload["parse_observations"])[0]
    request = cast(dict[str, Any], observation["request"])
    response = cast(dict[str, Any], observation["response"])
    reviewed_attachment = "2c7d525b-7463-463e-8893-0d37009775de"
    request["attachment_id"] = reviewed_attachment
    response["attachment_id"] = reviewed_attachment
    observation["response_digest"] = canonical_digest(response)
    payload.pop("dataset_identity")
    payload.pop("capture_contract")
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path = tmp_path / "legacy-reviewed-live-preflight-evidence.json"
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    replay = _run_cli("replay", "--artifact", str(artifact_path))

    assert replay.returncode == 0, replay.stderr
    assert json.loads(replay.stdout)["logical_digest"] == payload["logical_digest"]


def test_live_preflight_replay_rejects_tampering_and_raw_text_injection(
    tmp_path: Path,
) -> None:
    adapter = _adapter()
    run_id = "run-live-substrate-tamper"
    artifact = build_live_preflight_artifact(
        run_id=run_id,
        captured_at=datetime(2026, 7, 22, tzinfo=UTC),
        evaluation_plane_sha=EVALUATION_SHA,
        sut_commit_sha=PINNED_AX_SHA,
        corpus_observations=(adapter.corpus_identity(context=_context("corpus", run_id=run_id)),),
        parse_observations=(
            adapter.parse(
                context=_context("synthetic-rule-015", run_id=run_id),
                attachment_id=ATTACHMENT_ID,
            ),
        ),
        blockers=(),
    )
    artifact_path = write_live_preflight_artifact(
        artifact,
        tmp_path / "tampered-live-preflight-evidence.json",
    )
    payload = _read_json(artifact_path)
    payload["parse_observations"][0]["response"]["parser_version"] = "tampered"
    payload["logical_digest"] = canonical_digest(
        {key: value for key, value in payload.items() if key != "logical_digest"}
    )
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    digest_rejected = _run_cli("replay", "--artifact", str(artifact_path))

    assert digest_rejected.returncode == 2
    assert "response digest" in digest_rejected.stderr

    payload = _read_json(artifact_path)
    payload["parse_observations"][0]["response"]["extracted_text"] = SOURCE_TEXT
    artifact_path.write_text(json.dumps(payload), encoding="utf-8")

    raw_text_rejected = _run_cli("replay", "--artifact", str(artifact_path))

    assert raw_text_rejected.returncode == 2
    assert "Invalid artifact" in raw_text_rejected.stderr


def test_live_preflight_artifact_rejects_private_paths_and_mixed_run_identity(
    tmp_path: Path,
) -> None:
    private_attachment = str(tmp_path / "private-attachment.txt")
    adapter = _adapter(attachment_id=private_attachment)
    private_parse = adapter.parse(
        context=_context("private-path"),
        attachment_id=private_attachment,
    )

    with pytest.raises(ValueError, match="private path"):
        build_live_preflight_artifact(
            run_id="run-live-substrate",
            captured_at=datetime(2026, 7, 22, tzinfo=UTC),
            evaluation_plane_sha=EVALUATION_SHA,
            sut_commit_sha=PINNED_AX_SHA,
            corpus_observations=(),
            parse_observations=(private_parse,),
            blockers=(),
        )

    adapter = _adapter()
    with pytest.raises(ValueError, match="run_id"):
        build_live_preflight_artifact(
            run_id="different-run",
            captured_at=datetime(2026, 7, 22, tzinfo=UTC),
            evaluation_plane_sha=EVALUATION_SHA,
            sut_commit_sha=PINNED_AX_SHA,
            corpus_observations=(adapter.corpus_identity(context=_context("corpus")),),
            parse_observations=(),
            blockers=(),
        )


def _adapter(*, attachment_id: str = ATTACHMENT_ID) -> AxHttpAdapter:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/evaluation/corpus-identity":
            return httpx.Response(200, json=_corpus_identity_response())
        if request.url.path.endswith("/parse-observation"):
            return httpx.Response(200, json=_parse_response(attachment_id=attachment_id))
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

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


def _context(
    case_id: str,
    *,
    run_id: str = "run-live-substrate",
) -> AxRequestContext:
    return AxRequestContext(
        run_id=run_id,
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


def _parse_response(*, attachment_id: str = ATTACHMENT_ID) -> dict[str, object]:
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
        "extracted_text": SOURCE_TEXT,
        "extracted_text_digest": SOURCE_DIGEST,
        "text_truncated": False,
        "evidence_spans": [
            {
                "id": "span-1",
                "text": SOURCE_TEXT,
                "start_char": 0,
                "end_char": len(SOURCE_TEXT),
                "source_text_digest": SOURCE_DIGEST,
            }
        ],
        "headings": ["징계 절차"],
        "metadata": {"language": "ko"},
        "table": {"columns": ["단계"], "rows": [["소명"]]},
        "list": {"items": ["통지", "소명"], "ordered": True},
        "unavailable_fields": [],
    }


def _read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["uv", "run", "braincrew-eval", *arguments],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
