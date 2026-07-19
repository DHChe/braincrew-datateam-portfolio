from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

DATASET_PATH = Path(__file__).parents[2] / "datasets" / "retrieval" / "retrieval_cases_v1.json"
OBSERVATIONS_PATH = Path(__file__).parents[1] / "fixtures" / "retrieval_observations_v1.json"
SUT_SHA = "c318b2192006bdb36a5bd5b3a2bc403425b45701"


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "braincrew.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def retrieval_command(
    output_dir: Path,
    run_id: str,
    observations_path: Path = OBSERVATIONS_PATH,
) -> tuple[str, ...]:
    return (
        "run-retrieval",
        "--dataset",
        str(DATASET_PATH),
        "--observations",
        str(observations_path),
        "--output-dir",
        str(output_dir),
        "--run-id",
        run_id,
        "--sut-sha",
        SUT_SHA,
    )


def test_cli_executes_thirty_retrieval_cases_to_an_exactly_versioned_artifact(
    tmp_path: Path,
) -> None:
    result = run_cli(*retrieval_command(tmp_path / "artifacts", "retrieval-e2e"))

    assert result.returncode == 0, result.stderr
    command_result = json.loads(result.stdout)
    artifact = read_json(Path(command_result["artifact_path"]))
    assert command_result["run_state"] == "COMPLETED"
    assert "gate_decision" not in command_result
    assert artifact["schema_version"] == "retrieval-run-artifact-v1"
    assert artifact["run"]["run_id"] == "retrieval-e2e"
    assert artifact["run"]["execution_mode"] == "fixture"
    assert artifact["provenance"]["dataset"]["id"] == "braincrew-retrieval-quality"
    assert artifact["provenance"]["dataset"]["version"] == "1.0.0"
    assert artifact["provenance"]["dataset"]["content_digest"].startswith("sha256:")
    assert artifact["provenance"]["adapter"] == {
        "version": "fixture-retrieval-sut-v1",
        "execution_mode": "fixture",
    }
    assert artifact["provenance"]["evaluator"] == {"version": "retrieval-quality-v1"}
    assert artifact["provenance"]["sut"]["commit_sha"] == SUT_SHA
    assert artifact["provenance"]["sut"]["executed"] is False
    assert artifact["logical_result"]["evaluation"]["coverage"]["total_cases"] == 30
    first_observation = artifact["logical_result"]["observation_snapshot"]["observations"][0]
    assert first_observation["query"] == "연차휴가 신청 기한은 언제인가"
    assert first_observation["candidates"][0]["record_id"] == "synthetic-rule-001"
    assert first_observation["candidates"][0]["rank"] == 1
    assert first_observation["candidates"][0]["authority_level"] == 1
    assert artifact["logical_digest"] == command_result["logical_digest"]


def test_cli_persists_forbidden_visibility_as_a_complete_hard_failure_with_case_evidence(
    tmp_path: Path,
) -> None:
    observations = read_json(OBSERVATIONS_PATH)
    dataset = read_json(DATASET_PATH)
    forbidden = dataset["cases"][0]["expected"]["forbidden_sources"][0]
    observations["observations"][0]["candidates"] = [
        {
            "rank": 1,
            **forbidden,
            "visibility_allowed": True,
            "visibility_reason": "unexpected_role_scope_allow",
        }
    ]
    observations_path = tmp_path / "forbidden-observations.json"
    observations_path.write_text(json.dumps(observations, ensure_ascii=False), encoding="utf-8")

    result = run_cli(
        *retrieval_command(tmp_path / "artifacts", "retrieval-forbidden", observations_path)
    )

    assert result.returncode == 0, result.stderr
    command_result = json.loads(result.stdout)
    artifact = read_json(Path(command_result["artifact_path"]))
    evaluation = artifact["logical_result"]["evaluation"]
    assert command_result["run_state"] == "COMPLETED"
    assert "PASS" not in result.stdout
    assert evaluation["hard_failure_cases"] == ["retrieval-001"]
    assert evaluation["case_results"][0]["failure_codes"] == [
        "R-RELEVANT-EVIDENCE-MISS",
        "R-AUTHORITY-ORDER-INVERSION",
        "R-FORBIDDEN-VISIBILITY",
    ]


def test_retrieval_result_store_rejects_run_id_collisions_without_mutation(
    tmp_path: Path,
) -> None:
    arguments = retrieval_command(tmp_path / "artifacts", "immutable-retrieval")
    first = run_cli(*arguments)
    assert first.returncode == 0, first.stderr
    artifact_path = Path(json.loads(first.stdout)["artifact_path"])
    original_bytes = artifact_path.read_bytes()

    collision = run_cli(*arguments)

    assert collision.returncode == 2
    assert "Artifact already exists" in collision.stderr
    assert artifact_path.read_bytes() == original_bytes


def test_replay_recomputes_retrieval_evaluation_and_logical_digest(tmp_path: Path) -> None:
    run_result = run_cli(*retrieval_command(tmp_path / "artifacts", "retrieval-replay"))
    assert run_result.returncode == 0, run_result.stderr
    run_summary = json.loads(run_result.stdout)

    replay_result = run_cli("replay", "--artifact", run_summary["artifact_path"])

    assert replay_result.returncode == 0, replay_result.stderr
    replay_summary = json.loads(replay_result.stdout)
    assert replay_summary["run_state"] == "COMPLETED"
    assert "gate_decision" not in replay_summary
    assert replay_summary["logical_digest"] == run_summary["logical_digest"]


def test_replay_rejects_tampered_retrieval_evaluation(tmp_path: Path) -> None:
    run_result = run_cli(*retrieval_command(tmp_path / "artifacts", "retrieval-tamper"))
    assert run_result.returncode == 0, run_result.stderr
    artifact_path = Path(json.loads(run_result.stdout)["artifact_path"])
    artifact = read_json(artifact_path)
    artifact["logical_result"]["evaluation"]["case_results"][0]["recall_at_5"] = {
        "numerator": 0,
        "denominator": 1,
        "display_value": "0.0000",
    }
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")

    replay_result = run_cli("replay", "--artifact", str(artifact_path))

    assert replay_result.returncode == 2
    assert "Invalid artifact" in replay_result.stderr
