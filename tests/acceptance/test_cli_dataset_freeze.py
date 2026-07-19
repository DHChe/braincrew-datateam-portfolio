from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

MANIFEST_PATH = Path("datasets/dataset_manifest_v1.json")
PARSING_OBSERVATIONS = Path("tests/fixtures/parsing_observations_v1.json")
RETRIEVAL_OBSERVATIONS = Path("tests/fixtures/retrieval_observations_v1.json")
GROUNDED_OBSERVATIONS = Path("tests/fixtures/grounded_observations_v1.json")
SUT_SHA = "c318b2192006bdb36a5bd5b3a2bc403425b45701"


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "braincrew.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def dataset_command(
    output_dir: Path,
    run_id: str,
    *,
    parsing_observations: Path = PARSING_OBSERVATIONS,
) -> tuple[str, ...]:
    return (
        "run-dataset",
        "--manifest",
        str(MANIFEST_PATH),
        "--parsing-observations",
        str(parsing_observations),
        "--retrieval-observations",
        str(RETRIEVAL_OBSERVATIONS),
        "--grounded-observations",
        str(GROUNDED_OBSERVATIONS),
        "--output-dir",
        str(output_dir),
        "--run-id",
        run_id,
        "--sut-sha",
        SUT_SHA,
    )


def read_json(path: Path) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def canonical_digest(value: object) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"


def test_cli_creates_replays_and_repeats_the_full_immutable_fixture_artifact(
    tmp_path: Path,
) -> None:
    first = run_cli(*dataset_command(tmp_path / "first", "dataset-full-first"))

    assert first.returncode == 0, first.stderr
    first_summary = json.loads(first.stdout)
    artifact_path = Path(first_summary["artifact_path"])
    artifact = read_json(artifact_path)
    assert first_summary["run_state"] == "COMPLETED"
    assert artifact["schema_version"] == "dataset-run-artifact-v1"
    assert artifact["run"]["run_id"] == "dataset-full-first"
    assert artifact["provenance"]["dataset"]["id"] == "braincrew-evaluation-dataset"
    assert artifact["provenance"]["dataset"]["version"] == "1.0.0"
    assert artifact["provenance"]["dataset"]["content_digest"] == (
        "sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b"
    )
    assert artifact["provenance"]["sut"]["commit_sha"] == SUT_SHA
    evaluation = artifact["logical_result"]["evaluation"]
    assert evaluation["total_cases"] == 100
    assert evaluation["scored_cases"] == 100
    assert len(evaluation["parsing"]["case_results"]) == 20
    assert len(evaluation["retrieval"]["case_results"]) == 30
    assert len(evaluation["grounded"]["case_evaluations"]) == 50
    assert artifact["logical_digest"] == first_summary["logical_digest"]

    replay = run_cli("replay", "--artifact", str(artifact_path))
    assert replay.returncode == 0, replay.stderr
    replay_summary = json.loads(replay.stdout)
    assert replay_summary["run_state"] == "COMPLETED"
    assert replay_summary["logical_digest"] == first_summary["logical_digest"]

    second = run_cli(*dataset_command(tmp_path / "second", "dataset-full-second"))
    assert second.returncode == 0, second.stderr
    second_summary = json.loads(second.stdout)
    assert second_summary["logical_digest"] == first_summary["logical_digest"]


def test_replay_rejects_rehashed_scoring_content_tampering(tmp_path: Path) -> None:
    run = run_cli(*dataset_command(tmp_path / "artifacts", "dataset-tamper"))
    assert run.returncode == 0, run.stderr
    artifact_path = Path(json.loads(run.stdout)["artifact_path"])
    artifact = read_json(artifact_path)
    retrieval_case = artifact["logical_result"]["dataset_snapshot"]["retrieval_dataset"]["cases"][0]
    retrieval_case["query"] = f"{retrieval_case['query']} tampered"
    artifact["logical_digest"] = canonical_digest(
        {
            "provenance": artifact["provenance"],
            "logical_result": artifact["logical_result"],
        }
    )
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")

    replay = run_cli("replay", "--artifact", str(artifact_path))

    assert replay.returncode == 2
    assert "Invalid artifact" in replay.stderr


def test_result_store_rejects_collision_without_mutating_the_first_artifact(
    tmp_path: Path,
) -> None:
    command = dataset_command(tmp_path / "artifacts", "dataset-collision")
    first = run_cli(*command)
    assert first.returncode == 0, first.stderr
    artifact_path = Path(json.loads(first.stdout)["artifact_path"])
    original = artifact_path.read_bytes()

    collision = run_cli(*command)

    assert collision.returncode == 2
    assert "Artifact already exists" in collision.stderr
    assert artifact_path.read_bytes() == original


def test_cli_persists_missing_verification_observation_as_invalid(
    tmp_path: Path,
) -> None:
    observations = read_json(PARSING_OBSERVATIONS)
    observations["observations"] = observations["observations"][:-1]
    observations_path = tmp_path / "parsing-missing.json"
    observations_path.write_text(
        json.dumps(observations, ensure_ascii=False),
        encoding="utf-8",
    )

    result = run_cli(
        *dataset_command(
            tmp_path / "artifacts",
            "dataset-missing",
            parsing_observations=observations_path,
        )
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    artifact = read_json(Path(summary["artifact_path"]))
    assert summary["run_state"] == "INVALID"
    evaluation = artifact["logical_result"]["evaluation"]
    assert evaluation["scored_cases"] == 99
    assert "DATASET_CASE_COVERAGE_INVALID" in evaluation["invalid_reasons"]
    assert evaluation["parsing"]["aggregate"] is None
