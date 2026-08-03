from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast

DATASET_PATH = Path(__file__).parents[2] / "datasets" / "parsing" / "parsing_cases_v1.json"
OBSERVATIONS_PATH = Path(__file__).parents[1] / "fixtures" / "parsing_observations_v1.json"
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


def write_fixture_observations(path: Path, *, unavailable_case: str | None = None) -> Path:
    fixture = read_json(OBSERVATIONS_PATH)
    if unavailable_case is not None:
        observation = next(
            item for item in fixture["observations"] if item["case_id"] == unavailable_case
        )
        observation.update(
            {
                "parse_available": False,
                "parser_version": None,
                "failure_code": "AX_PARSE_OBSERVABILITY_UNAVAILABLE",
                "evidence_spans": [],
                "headings": [],
                "metadata": {},
                "table": None,
                "list": None,
            }
        )
    path.write_text(
        json.dumps(fixture, ensure_ascii=False),
        encoding="utf-8",
    )
    return path


def parsing_command(
    observations_path: Path,
    output_dir: Path,
    run_id: str,
) -> tuple[str, ...]:
    return (
        "run-parsing",
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


def test_cli_executes_twenty_parsing_cases_to_an_exactly_versioned_artifact(
    tmp_path: Path,
) -> None:
    observations_path = OBSERVATIONS_PATH

    result = run_cli(*parsing_command(observations_path, tmp_path / "artifacts", "parsing-e2e"))

    assert result.returncode == 0, result.stderr
    command_result = json.loads(result.stdout)
    artifact = read_json(Path(command_result["artifact_path"]))
    assert command_result["run_state"] == "COMPLETED"
    assert "gate_decision" not in command_result
    assert artifact["schema_version"] == "parsing-run-artifact-v1"
    assert artifact["run"]["run_id"] == "parsing-e2e"
    assert artifact["run"]["execution_mode"] == "fixture"
    assert artifact["provenance"]["dataset"]["id"] == "braincrew-parsing-quality"
    assert artifact["provenance"]["dataset"]["version"] == "1.0.0"
    assert artifact["provenance"]["dataset"]["content_digest"].startswith("sha256:")
    assert artifact["provenance"]["adapter"] == {
        "version": "fixture-parsing-sut-v1",
        "parser_version": "fixture-parser-v1",
        "execution_mode": "fixture",
    }
    assert artifact["provenance"]["evaluator"] == {"version": "parsing-quality-v2"}
    assert artifact["provenance"]["sut"]["commit_sha"] == SUT_SHA
    assert artifact["provenance"]["sut"]["executed"] is False
    assert artifact["logical_result"]["evaluation"]["state"] == "COMPLETED"
    assert artifact["logical_result"]["evaluation"]["coverage"]["total_cases"] == 20
    assert len(artifact["logical_result"]["evaluation"]["case_results"]) == 20
    assert artifact["logical_digest"] == command_result["logical_digest"]


def test_replay_recomputes_parsing_evaluation_and_logical_digest(tmp_path: Path) -> None:
    run_result = run_cli(
        *parsing_command(OBSERVATIONS_PATH, tmp_path / "artifacts", "parsing-replay")
    )
    assert run_result.returncode == 0, run_result.stderr
    run_summary = json.loads(run_result.stdout)

    replay_result = run_cli("replay", "--artifact", run_summary["artifact_path"])

    assert replay_result.returncode == 0, replay_result.stderr
    replay_summary = json.loads(replay_result.stdout)
    assert replay_summary["run_state"] == "COMPLETED"
    assert "gate_decision" not in replay_summary
    assert replay_summary["logical_digest"] == run_summary["logical_digest"]


def test_cli_persists_unobservable_parsing_as_invalid_without_an_aggregate(
    tmp_path: Path,
) -> None:
    observations_path = write_fixture_observations(
        tmp_path / "unavailable-observations.json",
        unavailable_case="parsing-015",
    )

    result = run_cli(*parsing_command(observations_path, tmp_path / "artifacts", "invalid-parse"))

    assert result.returncode == 0, result.stderr
    command_result = json.loads(result.stdout)
    artifact = read_json(Path(command_result["artifact_path"]))
    evaluation = artifact["logical_result"]["evaluation"]
    assert command_result["run_state"] == "INVALID"
    assert "PASS" not in result.stdout
    assert evaluation["state"] == "INVALID"
    assert evaluation["aggregate"] is None
    assert evaluation["invalid_reasons"] == [
        "parsing-015:AX_PARSE_OBSERVABILITY_UNAVAILABLE",
        "VERIFICATION_EVIDENCE_SPAN_DENOMINATOR_BELOW_6",
    ]


def test_parsing_result_store_rejects_run_id_collisions_without_mutation(tmp_path: Path) -> None:
    observations_path = OBSERVATIONS_PATH
    arguments = parsing_command(observations_path, tmp_path / "artifacts", "immutable-parsing")
    first = run_cli(*arguments)
    assert first.returncode == 0, first.stderr
    artifact_path = Path(json.loads(first.stdout)["artifact_path"])
    original_bytes = artifact_path.read_bytes()

    collision = run_cli(*arguments)

    assert collision.returncode == 2
    assert "Artifact already exists" in collision.stderr
    assert artifact_path.read_bytes() == original_bytes
