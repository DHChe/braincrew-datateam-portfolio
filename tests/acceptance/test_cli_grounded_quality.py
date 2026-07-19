from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

DATASET_PATH = Path("datasets/grounded/grounded_cases_v1.json")
OBSERVATIONS_PATH = Path("tests/fixtures/grounded_observations_v1.json")
SUT_SHA = "c318b2192006bdb36a5bd5b3a2bc403425b45701"


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "braincrew.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def grounded_command(output_dir: Path, run_id: str) -> tuple[str, ...]:
    return (
        "run-grounded",
        "--dataset",
        str(DATASET_PATH),
        "--observations",
        str(OBSERVATIONS_PATH),
        "--output-dir",
        str(output_dir),
        "--run-id",
        run_id,
        "--sut-sha",
        SUT_SHA,
    )


def read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def canonical_digest(value: object) -> str:
    serialized = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"sha256:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"


def test_cli_executes_grounded_fixture_to_a_versioned_immutable_artifact(tmp_path: Path) -> None:
    result = run_cli(*grounded_command(tmp_path / "artifacts", "grounded-e2e"))

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    artifact = read_json(Path(summary["artifact_path"]))
    assert summary["run_state"] == "COMPLETED"
    assert artifact["schema_version"] == "grounded-run-artifact-v1"
    assert artifact["run"]["run_id"] == "grounded-e2e"  # type: ignore[index]
    assert artifact["provenance"]["dataset"]["id"] == "braincrew-answer-quality"  # type: ignore[index]
    assert artifact["provenance"]["dataset"]["version"] == "1.0.0"  # type: ignore[index]
    assert artifact["provenance"]["adapter"] == {  # type: ignore[index]
        "version": "fixture-grounded-sut-v1",
        "execution_mode": "fixture",
    }
    assert artifact["provenance"]["sut"]["commit_sha"] == SUT_SHA  # type: ignore[index]
    compatibility = artifact["provenance"]["compatibility"]  # type: ignore[index]
    assert compatibility["evaluator_version"] == "grounded-answer-v1"
    assert compatibility["proposition_contract_version"] == "claim-proposition-v1"
    assert compatibility["traversal_contract_version"] == "claim-traversal-v1"
    assert compatibility["atomizer_version"] == "claim-atomizer-v1"
    assert compatibility["normalizer_version"] == "claim-normalizer-v1"
    assert compatibility["matcher_set_version"] == "claim-matcher-set-v1"
    assert compatibility["proposition_catalog_version"] == "claim-proposition-catalog-v1"
    assert compatibility["source_resolution_version"] == "source-text-resolution-v1"
    assert compatibility["guard_version"] == "high-risk-guard-v1"
    assert compatibility["answer_mode_contract_version"] == "answer-mode-v1"
    assert compatibility["abstention_contract_version"] == "abstention-v1"
    assert compatibility["visibility_contract_version"] == "answer-visibility-v1"
    for digest_field in (
        "atomizer_digest",
        "normalizer_digest",
        "matcher_set_digest",
        "proposition_catalog_digest",
        "case_catalog_digest",
        "answer_mode_contract_digest",
        "abstention_contract_digest",
        "visibility_contract_digest",
    ):
        assert compatibility[digest_field].startswith("sha256:")
    aggregate = artifact["logical_result"]["evaluation"]["aggregate"]  # type: ignore[index]
    assert aggregate["claim_support_precision"]["exact"] == "13/16"
    assert aggregate["citation_precision"]["exact"] == "69/80"
    assert aggregate["citation_coverage"]["exact"] == "73/80"
    assert aggregate["answer_mode_accuracy"]["exact"] == "49/50"
    assert aggregate["abstention_accuracy"]["exact"] == "4/5"
    assert len(artifact["logical_result"]["evaluation"]["case_evaluations"]) == 50  # type: ignore[index]
    assert artifact["logical_digest"] == summary["logical_digest"]


def test_grounded_result_store_rejects_collision_without_mutation(tmp_path: Path) -> None:
    output_dir = tmp_path / "artifacts"
    first = run_cli(*grounded_command(output_dir, "grounded-collision"))
    assert first.returncode == 0, first.stderr
    artifact_path = output_dir / "grounded-collision.json"
    original = artifact_path.read_bytes()

    second = run_cli(*grounded_command(output_dir, "grounded-collision"))

    assert second.returncode == 2
    assert artifact_path.read_bytes() == original


def test_cli_rejects_sut_sha_that_disagrees_with_grounded_observations(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "artifacts"
    command = list(grounded_command(output_dir, "grounded-sut-mismatch"))
    command[-1] = "d" * 40

    result = run_cli(*command)

    assert result.returncode == 2
    assert "does not match observation SUT SHA" in result.stderr
    assert not output_dir.exists()


def test_replay_recomputes_grounded_evaluation_and_digest(tmp_path: Path) -> None:
    run_result = run_cli(*grounded_command(tmp_path / "artifacts", "grounded-replay"))
    assert run_result.returncode == 0, run_result.stderr
    run_summary = json.loads(run_result.stdout)

    replay_result = run_cli("replay", "--artifact", run_summary["artifact_path"])

    assert replay_result.returncode == 0, replay_result.stderr
    replay_summary = json.loads(replay_result.stdout)
    assert replay_summary["run_state"] == "COMPLETED"
    assert replay_summary["logical_digest"] == run_summary["logical_digest"]


def test_replay_rejects_tampered_grounded_metric(tmp_path: Path) -> None:
    run_result = run_cli(*grounded_command(tmp_path / "artifacts", "grounded-tamper"))
    assert run_result.returncode == 0, run_result.stderr
    run_summary = json.loads(run_result.stdout)
    artifact_path = Path(run_summary["artifact_path"])
    artifact = read_json(artifact_path)
    artifact["logical_result"]["evaluation"]["aggregate"]["claim_support_precision"][  # type: ignore[index]
        "display"
    ] = "1.0000"
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    replay_result = run_cli("replay", "--artifact", str(artifact_path))

    assert replay_result.returncode == 2
    assert "Invalid artifact" in replay_result.stderr


def test_replay_rejects_rehashed_compatibility_digest_that_disagrees_with_snapshots(
    tmp_path: Path,
) -> None:
    run_result = run_cli(*grounded_command(tmp_path / "artifacts", "grounded-compatibility"))
    assert run_result.returncode == 0, run_result.stderr
    artifact_path = Path(json.loads(run_result.stdout)["artifact_path"])
    artifact = read_json(artifact_path)
    artifact["provenance"]["compatibility"]["matcher_set_digest"] = "sha256:" + "0" * 64  # type: ignore[index]
    artifact["logical_digest"] = canonical_digest(
        {
            "provenance": artifact["provenance"],
            "logical_result": artifact["logical_result"],
        }
    )
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    replay_result = run_cli("replay", "--artifact", str(artifact_path))

    assert replay_result.returncode == 2
    assert "Invalid artifact" in replay_result.stderr


def test_replay_rejects_rehashed_answer_contract_digest_that_disagrees_with_snapshots(
    tmp_path: Path,
) -> None:
    run_result = run_cli(*grounded_command(tmp_path / "artifacts", "answer-compatibility"))
    assert run_result.returncode == 0, run_result.stderr
    artifact_path = Path(json.loads(run_result.stdout)["artifact_path"])
    artifact = read_json(artifact_path)
    artifact["provenance"]["compatibility"]["answer_mode_contract_digest"] = (  # type: ignore[index]
        "sha256:" + "0" * 64
    )
    artifact["logical_digest"] = canonical_digest(
        {
            "provenance": artifact["provenance"],
            "logical_result": artifact["logical_result"],
        }
    )
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    replay_result = run_cli("replay", "--artifact", str(artifact_path))

    assert replay_result.returncode == 2
    assert "Invalid artifact" in replay_result.stderr


def test_replay_rejects_rehashed_dataset_digest_that_disagrees_with_snapshot(
    tmp_path: Path,
) -> None:
    run_result = run_cli(*grounded_command(tmp_path / "artifacts", "dataset-provenance"))
    assert run_result.returncode == 0, run_result.stderr
    artifact_path = Path(json.loads(run_result.stdout)["artifact_path"])
    artifact = read_json(artifact_path)
    artifact["provenance"]["dataset"]["content_digest"] = "sha256:" + "0" * 64  # type: ignore[index]
    artifact["logical_digest"] = canonical_digest(
        {
            "provenance": artifact["provenance"],
            "logical_result": artifact["logical_result"],
        }
    )
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    replay_result = run_cli("replay", "--artifact", str(artifact_path))

    assert replay_result.returncode == 2
    assert "Invalid artifact" in replay_result.stderr


def test_replay_rejects_rehashed_sut_identity_that_disagrees_with_observation_snapshot(
    tmp_path: Path,
) -> None:
    run_result = run_cli(*grounded_command(tmp_path / "artifacts", "sut-provenance"))
    assert run_result.returncode == 0, run_result.stderr
    artifact_path = Path(json.loads(run_result.stdout)["artifact_path"])
    artifact = read_json(artifact_path)
    artifact["provenance"]["sut"]["commit_sha"] = "d" * 40  # type: ignore[index]
    artifact["logical_digest"] = canonical_digest(
        {
            "provenance": artifact["provenance"],
            "logical_result": artifact["logical_result"],
        }
    )
    artifact_path.write_text(json.dumps(artifact), encoding="utf-8")

    replay_result = run_cli("replay", "--artifact", str(artifact_path))

    assert replay_result.returncode == 2
    assert "Invalid artifact" in replay_result.stderr
