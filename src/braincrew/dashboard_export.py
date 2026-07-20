"""Validated projection of canonical comparison evidence for the static dashboard."""

from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Literal

from pydantic import Field

from braincrew.comparison import (
    ComparisonArtifact,
    FailureIdentity,
    FailureTaxonomyDelta,
    GateTrace,
    OperationalDelta,
)
from braincrew.contracts import StrictContract
from braincrew.dataset_registry import DatasetManifest
from braincrew.result_store import replay_comparison_artifact

PUBLIC_CASE_ID_PATTERN = re.compile(r"(?:CASE|GA|parsing|retrieval)-[0-9]{3}\Z")


class DashboardDataset(StrictContract):
    id: str
    version: str
    content_digest: str
    source_type: Literal["synthetic"]
    license: Literal["CC0-1.0"]


class DashboardRun(StrictContract):
    role: Literal["baseline", "candidate"]
    evidence_limit: int = Field(gt=0)
    execution_mode: Literal["fixture", "live"]
    evaluation_plane_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    sut_sha: str = Field(pattern=r"^[0-9a-f]{40}$")


class DashboardTotals(StrictContract):
    case_count: int = Field(gt=0)
    metric_count: int = Field(gt=0)
    gate_count: Literal[3]


class DashboardMetric(StrictContract):
    name: str
    baseline: Decimal
    candidate: Decimal
    delta: Decimal


class DashboardCaseMetric(DashboardMetric):
    pass


class DashboardCaseEvidence(StrictContract):
    case_id: str
    metrics: tuple[DashboardCaseMetric, ...]
    latency_relative_delta: Decimal | None
    cost_relative_delta: Decimal | None
    candidate_failures: tuple[FailureIdentity, ...]


class DashboardExportDocument(StrictContract):
    schema_version: Literal["dashboard-export-v1"]
    source_schema_version: Literal["experiment-comparison-artifact-v1"]
    comparison_id: str
    decision: Literal["PASS", "FAIL", "INVALID"]
    logical_digest: str
    dataset: DashboardDataset
    baseline: DashboardRun
    candidate: DashboardRun
    totals: DashboardTotals
    metrics: tuple[DashboardMetric, ...]
    operational_delta: OperationalDelta | None
    failure_taxonomy: FailureTaxonomyDelta
    gates: tuple[GateTrace, GateTrace, GateTrace]
    reasons: tuple[str, ...]
    cases: tuple[DashboardCaseEvidence, ...]


def _load_dataset_manifest(path: Path) -> DatasetManifest:
    return DatasetManifest.model_validate_json(path.read_text(encoding="utf-8"))


def _dashboard_document(
    artifact: ComparisonArtifact,
    manifest: DatasetManifest,
) -> DashboardExportDocument:
    provenance = artifact.baseline.provenance
    if (
        provenance.dataset_id != manifest.dataset_id
        or provenance.dataset_version != manifest.dataset_version
        or provenance.dataset_digest != manifest.content_digest
    ):
        raise ValueError("comparison dataset does not match the canonical manifest")
    if manifest.provenance.source_type != "synthetic" or manifest.provenance.license != "CC0-1.0":
        raise ValueError("dataset manifest is not approved for publication")
    if len(artifact.gates) != 3:
        raise ValueError("comparison must contain the canonical three-gate trace")

    baseline_cases = {case.case_id: case for case in artifact.baseline.cases}
    candidate_cases = {case.case_id: case for case in artifact.candidate.cases}
    if any(PUBLIC_CASE_ID_PATTERN.fullmatch(case_id) is None for case_id in baseline_cases):
        raise ValueError("comparison contains a non-publishable case identifier")
    cases = tuple(
        DashboardCaseEvidence(
            case_id=item.case_id,
            metrics=tuple(
                DashboardCaseMetric(
                    name=name,
                    baseline=baseline_cases[item.case_id].metrics[name],
                    candidate=candidate_cases[item.case_id].metrics[name],
                    delta=delta,
                )
                for name, delta in sorted(item.metric_deltas.items())
            ),
            latency_relative_delta=item.latency_relative_delta,
            cost_relative_delta=item.cost_relative_delta,
            candidate_failures=candidate_cases[item.case_id].failures,
        )
        for item in artifact.case_deltas
    )
    return DashboardExportDocument(
        schema_version="dashboard-export-v1",
        source_schema_version=artifact.schema_version,
        comparison_id=artifact.comparison_id,
        decision=artifact.decision,
        logical_digest=artifact.logical_digest,
        dataset=DashboardDataset(
            id=provenance.dataset_id,
            version=provenance.dataset_version,
            content_digest=provenance.dataset_digest,
            source_type="synthetic",
            license="CC0-1.0",
        ),
        baseline=DashboardRun(
            role="baseline",
            evidence_limit=provenance.evidence_limit,
            execution_mode=provenance.execution_mode,
            evaluation_plane_sha=provenance.evaluation_plane_sha,
            sut_sha=provenance.sut_sha,
        ),
        candidate=DashboardRun(
            role="candidate",
            evidence_limit=artifact.candidate.provenance.evidence_limit,
            execution_mode=artifact.candidate.provenance.execution_mode,
            evaluation_plane_sha=artifact.candidate.provenance.evaluation_plane_sha,
            sut_sha=artifact.candidate.provenance.sut_sha,
        ),
        totals=DashboardTotals(
            case_count=len(artifact.case_deltas),
            metric_count=len(artifact.macro_deltas),
            gate_count=3,
        ),
        metrics=tuple(
            DashboardMetric(
                name=name,
                baseline=artifact.macro_baseline[name],
                candidate=artifact.macro_candidate[name],
                delta=delta,
            )
            for name, delta in sorted(artifact.macro_deltas.items())
        ),
        operational_delta=artifact.operational_delta,
        failure_taxonomy=artifact.failure_taxonomy,
        gates=(artifact.gates[0], artifact.gates[1], artifact.gates[2]),
        reasons=artifact.reasons,
        cases=cases,
    )


def export_dashboard_artifact(
    comparison_path: Path,
    output_path: Path,
    *,
    dataset_manifest_path: Path,
) -> DashboardExportDocument:
    replay_comparison_artifact(comparison_path)
    artifact = ComparisonArtifact.model_validate_json(comparison_path.read_text(encoding="utf-8"))
    document = _dashboard_document(
        artifact,
        _load_dataset_manifest(dataset_manifest_path),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as output_file:
        output_file.write(
            json.dumps(
                document.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    return document
