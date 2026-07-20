from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import duckdb
from typer.testing import CliRunner

from braincrew.cli import app

FIXTURES = Path(__file__).parents[1] / "fixtures"
BASELINE = FIXTURES / "comparison_baseline_v1.json"


def _compare(
    runner: CliRunner,
    *,
    candidate_name: str,
    comparison_id: str,
    output_dir: Path,
) -> dict[str, str]:
    result = runner.invoke(
        app,
        [
            "compare",
            "--baseline",
            str(BASELINE),
            "--candidate",
            str(FIXTURES / candidate_name),
            "--comparison-id",
            comparison_id,
            "--output-dir",
            str(output_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    return cast(dict[str, str], json.loads(result.stdout))


def test_installed_cli_compares_pass_fail_invalid_and_replays(tmp_path: Path) -> None:
    runner = CliRunner()

    passed = _compare(
        runner,
        candidate_name="comparison_candidate_pass_v1.json",
        comparison_id="pass",
        output_dir=tmp_path / "pass",
    )
    failed = _compare(
        runner,
        candidate_name="comparison_candidate_fail_v1.json",
        comparison_id="fail",
        output_dir=tmp_path / "fail",
    )
    invalid = _compare(
        runner,
        candidate_name="comparison_candidate_invalid_v1.json",
        comparison_id="invalid",
        output_dir=tmp_path / "invalid",
    )
    repeated = {
        decision: _compare(
            runner,
            candidate_name=f"comparison_candidate_{decision}_v1.json",
            comparison_id=f"{decision}-repeat",
            output_dir=tmp_path / f"{decision}-repeat",
        )
        for decision in ("pass", "fail", "invalid")
    }

    assert (passed["decision"], failed["decision"], invalid["decision"]) == (
        "PASS",
        "FAIL",
        "INVALID",
    )
    for decision, original in {
        "pass": passed,
        "fail": failed,
        "invalid": invalid,
    }.items():
        assert repeated[decision]["logical_digest"] == original["logical_digest"]
        for result in (original, repeated[decision]):
            replay = runner.invoke(
                app,
                ["replay", "--artifact", result["json_artifact_path"]],
            )
            assert replay.exit_code == 0, replay.output
            assert json.loads(replay.stdout)["logical_digest"] == result["logical_digest"]
    cache_path = Path(passed["duckdb_cache_path"])
    with duckdb.connect(str(cache_path), read_only=True) as connection:
        row = connection.execute(
            "SELECT decision, count(*) FROM comparison_cases GROUP BY decision"
        ).fetchone()
    assert row == ("PASS", 90)
