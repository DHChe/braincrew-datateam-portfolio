from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from typer.testing import CliRunner

from braincrew.cli import app

FIXTURES = Path(__file__).parents[1] / "fixtures"
DATASET_MANIFEST = Path(__file__).parents[2] / "datasets" / "dataset_manifest_v1.json"


def _write_compatible_summary(source_name: str, destination: Path) -> None:
    payload = cast(
        dict[str, Any],
        json.loads((FIXTURES / source_name).read_text(encoding="utf-8")),
    )
    manifest = cast(
        dict[str, Any],
        json.loads(DATASET_MANIFEST.read_text(encoding="utf-8")),
    )
    payload["provenance"]["dataset_digest"] = manifest["content_digest"]
    destination.write_text(json.dumps(payload), encoding="utf-8")


def test_cli_exports_replay_validated_dashboard_json(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    _write_compatible_summary("comparison_baseline_v1.json", baseline_path)
    _write_compatible_summary("comparison_candidate_pass_v1.json", candidate_path)
    comparison_dir = tmp_path / "comparison"
    runner = CliRunner()
    comparison = runner.invoke(
        app,
        [
            "compare",
            "--baseline",
            str(baseline_path),
            "--candidate",
            str(candidate_path),
            "--comparison-id",
            "dashboard-golden",
            "--output-dir",
            str(comparison_dir),
        ],
    )
    assert comparison.exit_code == 0, comparison.output
    comparison_summary = cast(dict[str, str], json.loads(comparison.stdout))
    output_path = tmp_path / "dashboard-export.json"

    exported = runner.invoke(
        app,
        [
            "export-dashboard",
            "--comparison",
            comparison_summary["json_artifact_path"],
            "--dataset-manifest",
            str(DATASET_MANIFEST),
            "--output",
            str(output_path),
        ],
    )

    assert exported.exit_code == 0, exported.output
    summary = cast(dict[str, str], json.loads(exported.stdout))
    document = cast(dict[str, Any], json.loads(output_path.read_text(encoding="utf-8")))
    assert summary == {
        "comparison_id": "dashboard-golden",
        "decision": "PASS",
        "logical_digest": document["logical_digest"],
        "output_path": str(output_path),
    }
    assert document["schema_version"] == "dashboard-export-v1"
    assert document["totals"] == {"case_count": 15, "gate_count": 3, "metric_count": 6}
