"""Derive create-only comparison inputs from replayable run artifacts."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import cast

from braincrew.comparison import (
    CRITICAL_FAILURE_CODES,
    ExperimentCaseResult,
    ExperimentProvenance,
    ExperimentRunSummary,
    FailureIdentity,
    _quantize_parquet_decimal,
)
from braincrew.contracts import (
    ParsingRunEvaluation,
    RetrievalApplicability,
    RetrievalRunEvaluation,
)
from braincrew.dataset_run import DatasetRunArtifactDocument, replay_dataset_run_artifact
from braincrew.digest import canonical_digest
from braincrew.grounded_contracts import GroundedRunEvaluation
from braincrew.live_experiment import LiveExperimentCaptureManifest
from braincrew.operational_evaluator import (
    LatencyDefinition,
    evaluate_operational_measurement,
)

INAPPLICABLE_RETRIEVAL = RetrievalApplicability(
    recall_at_5=False,
    mrr_at_10=False,
    authority_ordering=False,
    forbidden_visibility=False,
)


def _score(numerator: int, denominator: int) -> Decimal:
    return _quantize_parquet_decimal(Decimal(numerator) / Decimal(denominator))


def _failures(
    codes: list[str] | tuple[str, ...],
    evaluator_version: str,
) -> tuple[FailureIdentity, ...]:
    return tuple(
        FailureIdentity(
            code=code,
            severity="critical" if code in CRITICAL_FAILURE_CODES else "major",
            evaluator_version=evaluator_version,
        )
        for code in dict.fromkeys(codes)
    )


def _validate_inputs(
    manifest: LiveExperimentCaptureManifest,
    artifact: DatasetRunArtifactDocument,
) -> None:
    if (
        canonical_digest(manifest.model_dump(mode="json", exclude={"logical_digest"}))
        != manifest.logical_digest
    ):
        raise ValueError("capture manifest logical digest does not reproduce")
    replay_dataset_run_artifact(artifact.model_dump(mode="json"))
    if artifact.run.run_id != manifest.run_id:
        raise ValueError("run artifact ID does not match the capture manifest")
    provenance = manifest.provenance
    artifact_provenance = artifact.provenance
    if (
        artifact.run.execution_mode != "live"
        or artifact_provenance.adapter.execution_mode != "live"
        or artifact_provenance.evaluation_plane.commit_sha != provenance.evaluation_plane_sha
        or artifact_provenance.evaluation_plane.dirty_worktree != provenance.evaluation_plane_dirty
        or artifact_provenance.sut.commit_sha != provenance.sut_sha
        or artifact_provenance.sut.dirty_worktree != provenance.sut_dirty
        or artifact_provenance.sut.executed is not True
        or artifact_provenance.prompt.id != provenance.prompt_id
        or artifact_provenance.prompt.hash != provenance.prompt_hash
        or artifact_provenance.model.provider != provenance.model_provider
        or artifact_provenance.model.name != provenance.model_name
        or artifact_provenance.model.parameters != provenance.model_parameters
    ):
        raise ValueError("run artifact provenance does not match the live capture")
    if {
        "parsing": artifact_provenance.adapter.parsing_version,
        "retrieval": artifact_provenance.adapter.retrieval_version,
        "grounded": artifact_provenance.adapter.grounded_version,
    } != provenance.adapter_versions:
        raise ValueError("run artifact adapter versions do not match the live capture")
    if {
        "parsing": artifact_provenance.evaluator.parsing_version,
        "retrieval": artifact_provenance.evaluator.retrieval_version,
        "grounded": artifact_provenance.evaluator.grounded_version,
        "operational": artifact_provenance.evaluator.operational_version,
    } != provenance.evaluator_versions:
        raise ValueError("run artifact evaluator versions do not match the live capture")
    evaluation = artifact.logical_result.evaluation
    if (
        evaluation.state != "COMPLETED"
        or evaluation.total_cases != 30
        or evaluation.scored_cases != 30
    ):
        raise ValueError("run artifact must contain one completed 30-case Verification evaluation")
    snapshot = artifact.logical_result.dataset_snapshot
    if (
        snapshot.manifest.dataset_id != manifest.provenance.dataset_id
        or snapshot.manifest.dataset_version != manifest.provenance.dataset_version
        or snapshot.dataset_digest != manifest.provenance.dataset_digest
    ):
        raise ValueError("run artifact dataset identity does not match capture provenance")
    observations = artifact.logical_result.observation_snapshot
    if (
        canonical_digest(observations.retrieval.model_dump(mode="json"))
        != manifest.retrieval_observations.content_digest
        or len(observations.retrieval.observations) != manifest.retrieval_observations.case_count
    ):
        raise ValueError("retrieval observations do not match the capture manifest")
    if (
        canonical_digest(observations.grounded.model_dump(mode="json"))
        != manifest.grounded_observations.content_digest
        or len(observations.grounded.observations) != manifest.grounded_observations.case_count
    ):
        raise ValueError("grounded observations do not match the capture manifest")


def build_experiment_run_summary(
    manifest: LiveExperimentCaptureManifest,
    artifact: DatasetRunArtifactDocument,
) -> ExperimentRunSummary:
    """Build the 30-case Verification summary without operator-entered result fields."""
    _validate_inputs(manifest, artifact)
    logical = artifact.logical_result
    evaluation = logical.evaluation
    parsing = cast(ParsingRunEvaluation, evaluation.parsing)
    retrieval = cast(RetrievalRunEvaluation, evaluation.retrieval)
    grounded = cast(GroundedRunEvaluation, evaluation.grounded)

    parsing_by_id = {result.case_id: result for result in parsing.case_results}
    retrieval_by_id = {result.case_id: result for result in retrieval.case_results}
    grounded_by_id = {result.case_id: result for result in grounded.case_evaluations}
    retrieval_case_by_id = {
        case.id: case for case in logical.dataset_snapshot.retrieval_dataset.cases
    }
    retrieval_observation_by_id = {
        item.case_id: item for item in logical.observation_snapshot.retrieval.observations
    }
    grounded_observation_by_id = {
        item.case_id: item for item in logical.observation_snapshot.grounded.observations
    }
    grounded_case_by_id = {
        case.case_id: case for case in logical.dataset_snapshot.grounded_dataset.cases
    }

    cases: dict[str, ExperimentCaseResult] = {}
    latency_definitions: set[LatencyDefinition] = set()
    for case_id in manifest.fixture_case_ids:
        parsing_result = parsing_by_id.get(case_id)
        if (
            parsing_result is None
            or parsing_result.status != "SCORED"
            or parsing_result.evidence_span_recovery is None
        ):
            raise ValueError("parsing Verification result is missing or invalid")
        evidence_span_recovery = parsing_result.evidence_span_recovery
        cases[case_id] = ExperimentCaseResult(
            case_id=case_id,
            metrics={
                "evidence_span_recovery": _score(
                    evidence_span_recovery.numerator,
                    evidence_span_recovery.denominator,
                )
            },
            retrieval_metrics={},
            applicability=INAPPLICABLE_RETRIEVAL,
            latency_ms=None,
            cost_usd=None,
            failures=(),
        )

    for case_id, retrieval_result in retrieval_by_id.items():
        retrieval_observation = retrieval_observation_by_id.get(case_id)
        if retrieval_observation is None or retrieval_observation.operational is None:
            raise ValueError("live retrieval result requires an operational measurement")
        operational = evaluate_operational_measurement(retrieval_observation.operational)
        latency_definitions.add(operational.latency_definition)
        retrieval_primary_metrics: dict[str, Decimal] = {}
        retrieval_metrics: dict[str, Decimal] = {}
        if retrieval_result.recall_at_5 is not None:
            retrieval_primary_metrics["recall_at_5"] = _score(
                retrieval_result.recall_at_5.numerator,
                retrieval_result.recall_at_5.denominator,
            )
        if retrieval_result.mrr_at_10 is not None:
            retrieval_metrics["mrr_at_10"] = _score(
                retrieval_result.mrr_at_10.numerator,
                retrieval_result.mrr_at_10.denominator,
            )
        if retrieval_result.authority_priority is not None:
            retrieval_metrics["authority_priority"] = _score(
                retrieval_result.authority_priority.numerator,
                retrieval_result.authority_priority.denominator,
            )
        cases[case_id] = ExperimentCaseResult(
            case_id=case_id,
            metrics=retrieval_primary_metrics,
            retrieval_metrics=retrieval_metrics,
            applicability=retrieval_case_by_id[case_id].applicability,
            latency_ms=operational.latency_ms,
            cost_usd=operational.cost_usd,
            failures=_failures(
                retrieval_result.failure_codes,
                retrieval_result.evaluator_version,
            ),
        )

    for case_id, grounded_result in grounded_by_id.items():
        grounded_observation = grounded_observation_by_id.get(case_id)
        if grounded_observation is None or grounded_observation.operational is None:
            raise ValueError("live grounded result requires an operational measurement")
        operational = evaluate_operational_measurement(grounded_observation.operational)
        latency_definitions.add(operational.latency_definition)
        grounded_case = grounded_case_by_id[case_id]
        grounded_metrics: dict[str, Decimal] = {}
        for name in (
            "claim_support_precision",
            "citation_precision",
            "answer_mode_accuracy",
            "abstention_accuracy",
        ):
            score = getattr(grounded_result, name)
            if getattr(grounded_case.applicability, name):
                grounded_metrics[name] = _quantize_parquet_decimal(Decimal(score.value))
        cases[case_id] = ExperimentCaseResult(
            case_id=case_id,
            metrics=grounded_metrics,
            retrieval_metrics={},
            applicability=INAPPLICABLE_RETRIEVAL,
            latency_ms=operational.latency_ms,
            cost_usd=operational.cost_usd,
            failures=_failures(
                grounded_result.failure_codes,
                grounded_result.evaluator_version,
            ),
        )

    if set(cases) != set(manifest.verification_case_ids):
        raise ValueError("summary cases do not match the captured Verification partition")
    if len(latency_definitions) != 1:
        raise ValueError("summary operational measurements require one latency definition")
    cost_measurement_status = (
        "measured" if any(case.cost_usd is not None for case in cases.values()) else "unmeasured"
    )
    provenance = ExperimentProvenance.model_validate(
        {
            **manifest.provenance.model_dump(mode="json"),
            "latency_definition": latency_definitions.pop(),
            "cost_measurement_status": cost_measurement_status,
        }
    )
    return ExperimentRunSummary(
        schema_version="experiment-run-summary-v1",
        run_id=manifest.run_id,
        role=manifest.role,
        split="verification",
        state="COMPLETED",
        candidate_plan_version="candidate-plan-v1",
        provenance=provenance,
        cases=tuple(cases[case_id] for case_id in manifest.verification_case_ids),
    )


def write_experiment_run_summary(
    summary: ExperimentRunSummary,
    output_path: Path,
) -> Path:
    """Write one comparison input without replacing existing evidence."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("x", encoding="utf-8") as output_file:
        output_file.write(
            json.dumps(
                summary.model_dump(mode="json"),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    return output_path
