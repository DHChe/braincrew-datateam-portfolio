from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from typing import Literal

from braincrew.contracts import (
    EvaluationResult,
    FixtureCase,
    NormalizedObservation,
    ParsingAggregate,
    ParsingAggregateMetric,
    ParsingCase,
    ParsingCaseEvaluation,
    ParsingCoverage,
    ParsingDatasetDocument,
    ParsingMetricScore,
    ParsingObservation,
    ParsingObservationBatch,
    ParsingRunEvaluation,
)


def evaluate_exact_answer(
    case: FixtureCase,
    observation: NormalizedObservation,
) -> EvaluationResult:
    score: Literal[0, 1] = 1 if observation.answer == case.expected_answer else 0
    return EvaluationResult(
        schema_version="evaluation-result-v1",
        evaluator_version="exact-answer-v1",
        numerator=score,
        denominator=1,
        score=score,
    )


def _metric_score(numerator: int, denominator: int) -> ParsingMetricScore:
    display_value = (Decimal(numerator) / Decimal(denominator)).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_EVEN,
    )
    return ParsingMetricScore(
        numerator=numerator,
        denominator=denominator,
        display_value=f"{display_value:.4f}",
    )


def evaluate_parsing_case(
    case: ParsingCase,
    observation: ParsingObservation,
) -> ParsingCaseEvaluation:
    if not observation.parse_available:
        return ParsingCaseEvaluation(
            schema_version="parsing-case-evaluation-v1",
            evaluator_version="parsing-quality-v1",
            case_id=case.id,
            status="INVALID",
            invalid_reasons=[observation.failure_code or "PARSE_OBSERVATION_UNAVAILABLE"],
            evidence_span_recovery=None,
            structure_preservation=None,
            metadata_completeness=None,
            table_preservation=None,
            list_preservation=None,
        )

    expected_spans = {
        (
            span.id,
            span.text,
            span.start_char,
            span.end_char,
            span.source_text_digest,
        )
        for span in case.expected.evidence_spans
    }
    observed_spans = {
        (
            span.id,
            span.text,
            span.start_char,
            span.end_char,
            span.source_text_digest,
        )
        for span in observation.evidence_spans
    }
    recovered_spans = len(expected_spans & observed_spans)
    matching_metadata = sum(
        observation.metadata.get(key) == value for key, value in case.expected.metadata.items()
    )
    table_preservation = None
    if case.expected.table is not None:
        table_preservation = _metric_score(int(observation.table == case.expected.table), 1)
    list_preservation = None
    if case.expected.list is not None:
        list_preservation = _metric_score(int(observation.list == case.expected.list), 1)

    return ParsingCaseEvaluation(
        schema_version="parsing-case-evaluation-v1",
        evaluator_version="parsing-quality-v1",
        case_id=case.id,
        status="SCORED",
        invalid_reasons=[],
        evidence_span_recovery=_metric_score(recovered_spans, len(expected_spans)),
        structure_preservation=_metric_score(
            int(observation.headings == case.expected.structure.headings),
            1,
        ),
        metadata_completeness=_metric_score(matching_metadata, len(case.expected.metadata)),
        table_preservation=table_preservation,
        list_preservation=list_preservation,
    )


def _aggregate_metric(scores: list[ParsingMetricScore]) -> ParsingAggregateMetric:
    case_total = sum(
        (Fraction(score.numerator, score.denominator) for score in scores),
        start=Fraction(0, 1),
    )
    macro_score = case_total / len(scores)
    display_value = (Decimal(macro_score.numerator) / Decimal(macro_score.denominator)).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_EVEN,
    )
    return ParsingAggregateMetric(
        numerator=macro_score.numerator,
        denominator=macro_score.denominator,
        case_count=len(scores),
        display_value=f"{display_value:.4f}",
    )


def evaluate_parsing_run(
    dataset: ParsingDatasetDocument,
    batch: ParsingObservationBatch,
) -> ParsingRunEvaluation:
    observations_by_case = {observation.case_id: observation for observation in batch.observations}
    case_results: list[ParsingCaseEvaluation] = []
    invalid_reasons: list[str] = []
    verification_evidence_span_cases = 0
    dataset_case_ids = {case.id for case in dataset.cases}

    for case in dataset.cases:
        observation = observations_by_case.get(case.id)
        if observation is None:
            case_result = ParsingCaseEvaluation(
                schema_version="parsing-case-evaluation-v1",
                evaluator_version="parsing-quality-v1",
                case_id=case.id,
                status="INVALID",
                invalid_reasons=["PARSE_OBSERVATION_MISSING"],
                evidence_span_recovery=None,
                structure_preservation=None,
                metadata_completeness=None,
                table_preservation=None,
                list_preservation=None,
            )
        else:
            case_result = evaluate_parsing_case(case, observation)
        case_results.append(case_result)
        if case_result.status == "INVALID":
            invalid_reasons.extend(f"{case.id}:{reason}" for reason in case_result.invalid_reasons)
        elif case.split == "verification":
            verification_evidence_span_cases += 1

    invalid_reasons.extend(
        f"{case_id}:PARSE_OBSERVATION_UNEXPECTED"
        for case_id in sorted(observations_by_case.keys() - dataset_case_ids)
    )

    if verification_evidence_span_cases < 6:
        invalid_reasons.append("VERIFICATION_EVIDENCE_SPAN_DENOMINATOR_BELOW_6")

    scored_results = [result for result in case_results if result.status == "SCORED"]
    coverage = ParsingCoverage(
        total_cases=len(dataset.cases),
        scored_cases=len(scored_results),
        calibration_cases=sum(case.split == "calibration" for case in dataset.cases),
        verification_cases=sum(case.split == "verification" for case in dataset.cases),
        verification_evidence_span_cases=verification_evidence_span_cases,
    )
    if invalid_reasons:
        return ParsingRunEvaluation(
            schema_version="parsing-run-evaluation-v1",
            evaluator_version="parsing-quality-v1",
            state="INVALID",
            invalid_reasons=invalid_reasons,
            coverage=coverage,
            case_results=case_results,
            aggregate=None,
        )

    return ParsingRunEvaluation(
        schema_version="parsing-run-evaluation-v1",
        evaluator_version="parsing-quality-v1",
        state="COMPLETED",
        invalid_reasons=[],
        coverage=coverage,
        case_results=case_results,
        aggregate=ParsingAggregate(
            evidence_span_recovery=_aggregate_metric(
                [
                    result.evidence_span_recovery
                    for result in scored_results
                    if result.evidence_span_recovery is not None
                ]
            ),
            structure_preservation=_aggregate_metric(
                [
                    result.structure_preservation
                    for result in scored_results
                    if result.structure_preservation is not None
                ]
            ),
            metadata_completeness=_aggregate_metric(
                [
                    result.metadata_completeness
                    for result in scored_results
                    if result.metadata_completeness is not None
                ]
            ),
            table_preservation=_aggregate_metric(
                [
                    result.table_preservation
                    for result in scored_results
                    if result.table_preservation is not None
                ]
            ),
            list_preservation=_aggregate_metric(
                [
                    result.list_preservation
                    for result in scored_results
                    if result.list_preservation is not None
                ]
            ),
        ),
    )
