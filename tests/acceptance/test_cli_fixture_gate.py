from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

FIXTURE_PATH = Path(__file__).parents[1] / "fixtures" / "issue_6_case_v1.json"
SUT_SHA = "b" * 40
PUBLISHED_LIVE_CAPTURE_MANIFEST_PATH = (
    Path(__file__).parents[2]
    / "evidence"
    / "capture-baseline-2026-07-31"
    / "issue-15-phase1-baseline-2026-07-31.capture-manifest.json"
)
PUBLISHED_LIVE_EVALUATION_ARTIFACT_PATH = (
    Path(__file__).parents[2]
    / "evidence"
    / "eval-baseline-2026-07-31"
    / "issue-15-phase1-baseline-2026-07-31.json"
)
PUBLISHED_LIVE_CAPTURE_LOGICAL_DIGEST = (
    "sha256:775a85295fb5db2f9cfb6e1aa5504206ea3b629a032452932ca685a7ab1a5049"
)
PUBLISHED_LIVE_EVALUATION_LOGICAL_DIGEST = (
    "sha256:9435c9daaa21e4e3129dad997a9dff79717452a2c1f112acfd7a95ba3e80f6fb"
)


def git_output(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "braincrew.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def test_run_executes_one_fixture_case_from_cli_to_gate_artifact(tmp_path: Path) -> None:
    result = run_cli(
        "run",
        "--case",
        str(FIXTURE_PATH),
        "--output-dir",
        str(tmp_path),
        "--run-id",
        "acceptance-run",
        "--sut-sha",
        SUT_SHA,
    )

    assert result.returncode == 0, result.stderr
    command_result = json.loads(result.stdout)
    artifact_path = Path(command_result["artifact_path"])
    artifact = read_json(artifact_path)

    assert command_result["gate_decision"] == "PASS"
    assert command_result["logical_digest"].startswith("sha256:")
    assert artifact["schema_version"] == "run-artifact-v1"
    assert artifact["run"]["run_id"] == "acceptance-run"
    assert artifact["run"]["execution_mode"] == "fixture"
    assert artifact["provenance"]["evaluation_plane"]["commit_sha"] == git_output(
        "rev-parse", "HEAD"
    )
    assert artifact["provenance"]["evaluation_plane"]["dirty_worktree"] is bool(
        git_output("status", "--porcelain")
    )
    assert artifact["provenance"]["sut"]["commit_sha"] == SUT_SHA
    assert artifact["provenance"]["sut"]["executed"] is False
    assert artifact["provenance"]["adapter"]["version"] == "fixture-sut-v1"
    assert artifact["provenance"]["evaluator"]["version"] == "exact-answer-v1"
    assert artifact["provenance"]["prompt"]["id"] == "fixture-prompt-not-called"
    assert artifact["provenance"]["model"]["name"] == "not-called"
    assert artifact["logical_result"]["observation"]["answer_mode"] == "answer"
    assert artifact["logical_result"]["evaluation"]["score"] == 1
    assert artifact["logical_result"]["gate"]["decision"] == "PASS"
    assert artifact["logical_digest"] == command_result["logical_digest"]

    repeated_result = run_cli(
        "run",
        "--case",
        str(FIXTURE_PATH),
        "--output-dir",
        str(tmp_path),
        "--run-id",
        "acceptance-rerun",
        "--sut-sha",
        SUT_SHA,
    )

    assert repeated_result.returncode == 0, repeated_result.stderr
    assert json.loads(repeated_result.stdout)["logical_digest"] == command_result["logical_digest"]


def test_replay_recomputes_the_same_logical_digest_and_gate_decision(tmp_path: Path) -> None:
    run_result = run_cli(
        "run",
        "--case",
        str(FIXTURE_PATH),
        "--output-dir",
        str(tmp_path),
        "--run-id",
        "replay-source",
        "--sut-sha",
        SUT_SHA,
    )
    assert run_result.returncode == 0, run_result.stderr
    run_summary = json.loads(run_result.stdout)

    replay_result = run_cli("replay", "--artifact", run_summary["artifact_path"])

    assert replay_result.returncode == 0, replay_result.stderr
    replay_summary = json.loads(replay_result.stdout)
    assert replay_summary["gate_decision"] == run_summary["gate_decision"]
    assert replay_summary["logical_digest"] == run_summary["logical_digest"]


def test_replay_reproduces_published_live_artifact_digests() -> None:
    capture_result = run_cli("replay", "--artifact", str(PUBLISHED_LIVE_CAPTURE_MANIFEST_PATH))

    assert capture_result.returncode == 0, capture_result.stderr
    capture_summary = json.loads(capture_result.stdout)
    assert capture_summary["logical_digest"] == PUBLISHED_LIVE_CAPTURE_LOGICAL_DIGEST
    assert capture_summary["grounded_case_count"] == "15"
    assert capture_summary["retrieval_case_count"] == "9"

    evaluation_result = run_cli(
        "replay", "--artifact", str(PUBLISHED_LIVE_EVALUATION_ARTIFACT_PATH)
    )

    assert evaluation_result.returncode == 0, evaluation_result.stderr
    evaluation_summary = json.loads(evaluation_result.stdout)
    assert evaluation_summary["logical_digest"] == PUBLISHED_LIVE_EVALUATION_LOGICAL_DIGEST
    assert evaluation_summary["run_state"] == "INVALID"


def test_run_rejects_overwriting_an_existing_artifact(tmp_path: Path) -> None:
    arguments = (
        "run",
        "--case",
        str(FIXTURE_PATH),
        "--output-dir",
        str(tmp_path),
        "--run-id",
        "immutable-run",
        "--sut-sha",
        SUT_SHA,
    )
    first_result = run_cli(*arguments)
    assert first_result.returncode == 0, first_result.stderr
    artifact_path = Path(json.loads(first_result.stdout)["artifact_path"])
    original_bytes = artifact_path.read_bytes()

    overwrite_result = run_cli(*arguments)

    assert overwrite_result.returncode == 2
    assert "Artifact already exists" in overwrite_result.stderr
    assert artifact_path.read_bytes() == original_bytes


def test_invalid_fixture_fails_explicitly_without_partial_artifact(tmp_path: Path) -> None:
    invalid_case_path = tmp_path / "invalid-case.json"
    invalid_case_path.write_text(
        json.dumps(
            {
                "schema_version": "fixture-case-v1",
                "dataset": {
                    "id": "invalid-fixture",
                    "version": "1.0.0",
                    "corpus_id": "synthetic-hr-v1",
                },
                "case": {
                    "id": "fixture-invalid",
                    "split": "fixture",
                    "query": "응답이 없는 잘못된 fixture",
                    "expected_answer": "이 값은 평가되면 안 됩니다.",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    result = run_cli(
        "run",
        "--case",
        str(invalid_case_path),
        "--output-dir",
        str(tmp_path / "artifacts"),
        "--run-id",
        "invalid-run",
        "--sut-sha",
        SUT_SHA,
    )

    assert result.returncode == 2
    assert "Invalid fixture input" in result.stderr
    assert not (tmp_path / "artifacts" / "invalid-run.json").exists()


def test_non_utf8_fixture_fails_explicitly_without_traceback(tmp_path: Path) -> None:
    invalid_case_path = tmp_path / "non-utf8-case.json"
    invalid_case_path.write_bytes(b"\xff\xfe")

    result = run_cli(
        "run",
        "--case",
        str(invalid_case_path),
        "--output-dir",
        str(tmp_path / "artifacts"),
        "--run-id",
        "non-utf8-run",
        "--sut-sha",
        SUT_SHA,
    )

    assert result.returncode == 2
    assert "Invalid fixture input" in result.stderr
    assert "Traceback" not in result.stderr
    assert not (tmp_path / "artifacts" / "non-utf8-run.json").exists()


def test_replay_rejects_a_tampered_logical_result_explicitly(tmp_path: Path) -> None:
    run_result = run_cli(
        "run",
        "--case",
        str(FIXTURE_PATH),
        "--output-dir",
        str(tmp_path),
        "--run-id",
        "tampered-run",
        "--sut-sha",
        SUT_SHA,
    )
    assert run_result.returncode == 0, run_result.stderr
    artifact_path = Path(json.loads(run_result.stdout)["artifact_path"])
    artifact = read_json(artifact_path)
    artifact["logical_result"]["evaluation"]["score"] = 0
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    replay_result = run_cli("replay", "--artifact", str(artifact_path))

    assert replay_result.returncode == 2
    assert "Invalid artifact" in replay_result.stderr


def test_replay_requires_the_complete_run_artifact_envelope(tmp_path: Path) -> None:
    run_result = run_cli(
        "run",
        "--case",
        str(FIXTURE_PATH),
        "--output-dir",
        str(tmp_path),
        "--run-id",
        "missing-envelope-run",
        "--sut-sha",
        SUT_SHA,
    )
    assert run_result.returncode == 0, run_result.stderr
    artifact_path = Path(json.loads(run_result.stdout)["artifact_path"])
    artifact = read_json(artifact_path)
    del artifact["run"]
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    replay_result = run_cli("replay", "--artifact", str(artifact_path))

    assert replay_result.returncode == 2
    assert "Invalid artifact" in replay_result.stderr


def test_run_id_cannot_escape_the_output_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "artifacts"

    result = run_cli(
        "run",
        "--case",
        str(FIXTURE_PATH),
        "--output-dir",
        str(output_dir),
        "--run-id",
        "../escaped",
        "--sut-sha",
        SUT_SHA,
    )

    assert result.returncode == 2
    assert "Invalid run ID" in result.stderr
    assert not (tmp_path / "escaped.json").exists()


def test_run_rejects_a_malformed_sut_commit_identity(tmp_path: Path) -> None:
    arguments = [
        "run",
        "--case",
        str(FIXTURE_PATH),
        "--output-dir",
        str(tmp_path),
        "--run-id",
        "invalid-commit",
        "--sut-sha",
        "not-a-commit",
    ]

    result = run_cli(*arguments)

    assert result.returncode == 2
    assert "Invalid commit SHA" in result.stderr
    assert not (tmp_path / "invalid-commit.json").exists()


def test_dataset_digest_excludes_fixture_execution_configuration(tmp_path: Path) -> None:
    original_result = run_cli(
        "run",
        "--case",
        str(FIXTURE_PATH),
        "--output-dir",
        str(tmp_path),
        "--run-id",
        "dataset-original",
        "--sut-sha",
        SUT_SHA,
    )
    assert original_result.returncode == 0, original_result.stderr
    original_artifact = read_json(Path(json.loads(original_result.stdout)["artifact_path"]))

    variant_fixture = read_json(FIXTURE_PATH)
    variant_fixture["fixture_sut"]["answer"] = "의도적으로 다른 fixture 응답"
    variant_fixture["prompt"]["id"] = "different-fixture-prompt"
    variant_fixture["model"]["name"] = "different-not-called-model"
    variant_path = tmp_path / "variant-fixture.json"
    variant_path.write_text(json.dumps(variant_fixture, ensure_ascii=False), encoding="utf-8")

    variant_result = run_cli(
        "run",
        "--case",
        str(variant_path),
        "--output-dir",
        str(tmp_path),
        "--run-id",
        "dataset-variant",
        "--sut-sha",
        SUT_SHA,
    )
    assert variant_result.returncode == 0, variant_result.stderr
    variant_artifact = read_json(Path(json.loads(variant_result.stdout)["artifact_path"]))

    assert original_artifact["provenance"]["dataset"]["source_type"] == "synthetic"
    assert original_artifact["provenance"]["dataset"]["license"] == "CC0-1.0"
    assert (
        original_artifact["provenance"]["dataset"]["content_digest"]
        == variant_artifact["provenance"]["dataset"]["content_digest"]
    )
