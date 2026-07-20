from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

import pytest

from braincrew.comparison import ExperimentRunSummary, compare_runs
from braincrew.dashboard_export import export_dashboard_artifact
from braincrew.result_store import write_comparison_artifact

FIXTURES = Path(__file__).parents[1] / "fixtures"
DATASET_MANIFEST = Path(__file__).parents[2] / "datasets" / "dataset_manifest_v1.json"


def _load_payload(name: str) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def _comparison_artifact(tmp_path: Path, *, first_case_id: str | None = None) -> Path:
    manifest = cast(
        dict[str, Any],
        json.loads(DATASET_MANIFEST.read_text(encoding="utf-8")),
    )
    baseline_payload = _load_payload("comparison_baseline_v1.json")
    candidate_payload = _load_payload("comparison_candidate_pass_v1.json")
    for payload in (baseline_payload, candidate_payload):
        payload["provenance"]["dataset_digest"] = manifest["content_digest"]
        if first_case_id is not None:
            payload["cases"][0]["case_id"] = first_case_id
    artifact = compare_runs(
        ExperimentRunSummary.model_validate(baseline_payload),
        ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="dashboard-golden",
    )
    json_path, _ = write_comparison_artifact(artifact, tmp_path)
    return json_path


def test_dashboard_export_copies_canonical_comparison_without_recalculation(
    tmp_path: Path,
) -> None:
    comparison_path = _comparison_artifact(tmp_path / "comparison")

    exported = export_dashboard_artifact(
        comparison_path,
        tmp_path / "dashboard-data.json",
        dataset_manifest_path=DATASET_MANIFEST,
    )
    source = cast(
        dict[str, Any],
        json.loads(comparison_path.read_text(encoding="utf-8")),
    )

    assert exported.schema_version == "dashboard-export-v1"
    assert exported.source_schema_version == "experiment-comparison-artifact-v1"
    assert exported.decision == source["decision"] == "PASS"
    assert exported.logical_digest == source["logical_digest"]
    assert [gate.model_dump(mode="json") for gate in exported.gates] == source["gates"]
    assert exported.totals.case_count == len(source["case_deltas"]) == 15
    assert exported.totals.metric_count == len(source["macro_deltas"]) == 6
    assert exported.totals.gate_count == len(source["gates"]) == 3
    assert exported.baseline.execution_mode == source["baseline"]["provenance"]["execution_mode"]
    assert (
        exported.baseline.evaluation_plane_sha
        == source["baseline"]["provenance"]["evaluation_plane_sha"]
    )
    assert exported.baseline.sut_sha == source["baseline"]["provenance"]["sut_sha"]
    assert {
        metric.name: (str(metric.baseline), str(metric.candidate), str(metric.delta))
        for metric in exported.metrics
    } == {
        name: (
            source["macro_baseline"][name],
            source["macro_candidate"][name],
            source["macro_deltas"][name],
        )
        for name in source["macro_deltas"]
    }
    assert exported.cases[0].case_id == source["case_deltas"][0]["case_id"]
    assert set(exported.cases[0].model_dump()) == {
        "case_id",
        "metrics",
        "latency_relative_delta",
        "cost_relative_delta",
        "candidate_failures",
    }
    assert (tmp_path / "dashboard-data.json").is_file()


def test_dashboard_export_rejects_non_publishable_case_identifier(tmp_path: Path) -> None:
    comparison_path = _comparison_artifact(
        tmp_path / "comparison",
        first_case_id="employee@example.com",
    )
    output_path = tmp_path / "dashboard-data.json"

    with pytest.raises(ValueError, match="publishable case identifier"):
        export_dashboard_artifact(
            comparison_path,
            output_path,
            dataset_manifest_path=DATASET_MANIFEST,
        )

    assert not output_path.exists()


def test_dashboard_export_rejects_sensitive_looking_slug_identifier(tmp_path: Path) -> None:
    comparison_path = _comparison_artifact(
        tmp_path / "comparison",
        first_case_id="SSN-123",
    )
    output_path = tmp_path / "dashboard-data.json"

    with pytest.raises(ValueError, match="publishable case identifier"):
        export_dashboard_artifact(
            comparison_path,
            output_path,
            dataset_manifest_path=DATASET_MANIFEST,
        )

    assert not output_path.exists()


def test_dashboard_export_rejects_non_reproducing_comparison(tmp_path: Path) -> None:
    comparison_path = _comparison_artifact(tmp_path / "comparison")
    payload = cast(
        dict[str, Any],
        json.loads(comparison_path.read_text(encoding="utf-8")),
    )
    payload["decision"] = "FAIL"
    comparison_path.write_text(json.dumps(payload), encoding="utf-8")
    output_path = tmp_path / "dashboard-data.json"

    with pytest.raises(ValueError, match="does not reproduce"):
        export_dashboard_artifact(
            comparison_path,
            output_path,
            dataset_manifest_path=DATASET_MANIFEST,
        )

    assert not output_path.exists()


def test_dashboard_export_rejects_unapproved_dataset_manifest(tmp_path: Path) -> None:
    comparison_path = _comparison_artifact(tmp_path / "comparison")
    manifest = cast(
        dict[str, Any],
        json.loads(DATASET_MANIFEST.read_text(encoding="utf-8")),
    )
    manifest["provenance"]["license"] = "proprietary"
    manifest_path = tmp_path / "dataset-manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output_path = tmp_path / "dashboard-data.json"

    with pytest.raises(ValueError, match="not approved for publication"):
        export_dashboard_artifact(
            comparison_path,
            output_path,
            dataset_manifest_path=manifest_path,
        )

    assert not output_path.exists()


def test_dashboard_export_is_create_only(tmp_path: Path) -> None:
    comparison_path = _comparison_artifact(tmp_path / "comparison")
    output_path = tmp_path / "dashboard-data.json"
    output_path.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        export_dashboard_artifact(
            comparison_path,
            output_path,
            dataset_manifest_path=DATASET_MANIFEST,
        )

    assert output_path.read_text(encoding="utf-8") == "existing"
