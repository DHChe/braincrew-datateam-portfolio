from __future__ import annotations

import json
from pathlib import Path

from pytest import MonkeyPatch
from typer.testing import CliRunner

from braincrew.cli import app

MANIFEST = Path("datasets/dataset_manifest_v2.json")


def _set_complete_live_environment(monkeypatch: MonkeyPatch, *, repository: Path) -> None:
    values = {
        "AX_BASE_URL": "http://127.0.0.1:9",
        "AX_REPOSITORY": str(repository),
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
        "AX_PARSING_ATTACHMENT_MAP_JSON": json.dumps(
            {
                f"synthetic-rule-{case_number:03d}": (f"00000000-0000-4000-8000-{case_number:012d}")
                for case_number in range(15, 21)
            },
            sort_keys=True,
        ),
        "AX_PROMPT_ID": "ax-answer-prompt-v1",
        "AX_PROMPT_HASH": "sha256:" + "b" * 64,
        "AX_MODEL_PROVIDER": "openai",
        "AX_MODEL_NAME": "pinned-model",
        "AX_MODEL_PARAMETERS_JSON": '{"temperature": 0}',
    }
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_live_preflight_persists_and_replays_exact_missing_authority_blockers(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    for name in (
        "AX_BASE_URL",
        "AX_REPOSITORY",
        "AX_TENANT_ID",
        "AX_USER_ID",
        "AX_ROLES",
        "AX_PARSING_ATTACHMENT_MAP_JSON",
        "AX_BEARER_TOKEN",
        "AX_CORPUS_IDENTITIES_JSON",
        "AX_PROMPT_ID",
        "AX_PROMPT_HASH",
        "AX_MODEL_PROVIDER",
        "AX_MODEL_NAME",
        "AX_MODEL_PARAMETERS_JSON",
    ):
        monkeypatch.delenv(name, raising=False)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "preflight-live",
            "--manifest",
            str(MANIFEST),
            "--output-dir",
            str(tmp_path),
            "--preflight-id",
            "issue-15-missing-authority",
        ],
    )

    assert result.exit_code == 2, result.output
    summary = json.loads(result.stdout)
    assert summary["preflight_state"] == "BLOCKED"
    artifact_path = Path(summary["artifact_path"])
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact["schema_version"] == "live-verification-preflight-artifact-v2"
    assert artifact["dataset"]["id"] == "braincrew-evaluation-dataset"
    assert artifact["dataset"]["version"] == "2.0.0"
    assert artifact["dataset"]["verification_case_count"] == 30
    assert artifact["plan"]["baseline"] == {"evidence_limit": 3, "top_k": 5}
    assert artifact["plan"]["candidate"] == {"evidence_limit": 5, "top_k": 5}
    missing_codes = [
        blocker["code"] for blocker in artifact["blockers"] if blocker["code"].endswith("_MISSING")
    ]
    assert missing_codes == [
        "LIVE_BASE_URL_MISSING",
        "LIVE_SUT_REPOSITORY_MISSING",
        "LIVE_TENANT_ID_MISSING",
        "LIVE_USER_ID_MISSING",
        "LIVE_ROLES_MISSING",
        "LIVE_PARSING_ATTACHMENT_MAPPING_MISSING",
        "LIVE_CORPUS_IDENTITIES_MISSING",
        "LIVE_PROMPT_ID_MISSING",
        "LIVE_PROMPT_HASH_MISSING",
        "LIVE_MODEL_PROVIDER_MISSING",
        "LIVE_MODEL_NAME_MISSING",
        "LIVE_MODEL_PARAMETERS_MISSING",
    ]
    assert "bearer_token" not in artifact_path.read_text(encoding="utf-8").lower()

    replay = runner.invoke(app, ["replay", "--artifact", str(artifact_path)])

    assert replay.exit_code == 0, replay.output
    replay_summary = json.loads(replay.stdout)
    assert replay_summary["preflight_state"] == "BLOCKED"
    assert replay_summary["logical_digest"] == summary["logical_digest"]


def test_live_preflight_blocks_before_http_when_the_pinned_sut_checkout_is_unavailable(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    missing_repository = tmp_path / "missing-ax"
    _set_complete_live_environment(monkeypatch, repository=missing_repository)
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "preflight-live",
            "--manifest",
            str(MANIFEST),
            "--output-dir",
            str(tmp_path / "artifacts"),
            "--preflight-id",
            "issue-15-missing-sut-checkout",
        ],
    )

    assert result.exit_code == 2, result.output
    summary = json.loads(result.stdout)
    artifact = json.loads(Path(summary["artifact_path"]).read_text(encoding="utf-8"))
    access_blockers = [
        blocker["code"]
        for blocker in artifact["blockers"]
        if blocker["code"] == "LIVE_SUT_REPOSITORY_UNAVAILABLE"
    ]
    assert access_blockers == ["LIVE_SUT_REPOSITORY_UNAVAILABLE"]


def test_live_preflight_artifact_is_create_only_and_replay_rejects_tampering(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    for name in (
        "AX_BASE_URL",
        "AX_REPOSITORY",
        "AX_TENANT_ID",
        "AX_USER_ID",
        "AX_ROLES",
        "AX_PARSING_ATTACHMENT_MAP_JSON",
        "AX_CORPUS_IDENTITIES_JSON",
        "AX_PROMPT_ID",
        "AX_PROMPT_HASH",
        "AX_MODEL_PROVIDER",
        "AX_MODEL_NAME",
        "AX_MODEL_PARAMETERS_JSON",
    ):
        monkeypatch.delenv(name, raising=False)
    runner = CliRunner()
    command = [
        "preflight-live",
        "--manifest",
        str(MANIFEST),
        "--output-dir",
        str(tmp_path),
        "--preflight-id",
        "issue-15-create-only",
    ]

    first = runner.invoke(app, command)
    artifact_path = tmp_path / "issue-15-create-only.json"
    original_bytes = artifact_path.read_bytes()
    second = runner.invoke(app, command)

    assert first.exit_code == 2
    assert second.exit_code == 2
    assert "Artifact already exists" in second.stderr
    assert artifact_path.read_bytes() == original_bytes

    artifact = json.loads(original_bytes)
    artifact["plan"]["candidate"]["evidence_limit"] = 3
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
    replay = runner.invoke(app, ["replay", "--artifact", str(artifact_path)])

    assert replay.exit_code == 2
    assert "Invalid artifact" in replay.stderr
