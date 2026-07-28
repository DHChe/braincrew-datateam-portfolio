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
    RetrievalAggregate,
    RetrievalAggregateMetric,
    RetrievalCandidateObservation,
    RetrievalCase,
    RetrievalCaseEvaluation,
    RetrievalCoverage,
    RetrievalDatasetDocument,
    RetrievalMetricScore,
    RetrievalObservation,
    RetrievalObservationBatch,
    RetrievalRunEvaluation,
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


def _retrieval_metric_score(numerator: int, denominator: int) -> RetrievalMetricScore:
    display_value = (Decimal(numerator) / Decimal(denominator)).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_EVEN,
    )
    return RetrievalMetricScore(
        numerator=numerator,
        denominator=denominator,
        display_value=f"{display_value:.4f}",
    )


def _retrieval_identity(
    source: RetrievalCandidateObservation,
) -> tuple[str, str, str | None, str | None]:
    return (
        source.record_kind,
        source.record_id,
        source.evidence_span_id,
        source.source_text_digest,
    )


def _invalid_retrieval_case(
    case: RetrievalCase,
    *reasons: str,
    forbidden_visible: bool = False,
) -> RetrievalCaseEvaluation:
    return RetrievalCaseEvaluation(
        schema_version="retrieval-case-evaluation-v1",
        evaluator_version="retrieval-quality-v1",
        case_id=case.id,
        status="INVALID",
        invalid_reasons=list(reasons),
        failure_codes=["R-FORBIDDEN-VISIBILITY"] if forbidden_visible else [],
        hard_failure=forbidden_visible,
        recall_at_5=None,
        mrr_at_10=None,
        authority_priority=None,
        forbidden_visibility=None,
    )


def _has_forbidden_retrieval_source(
    case: RetrievalCase,
    candidates: list[RetrievalCandidateObservation],
) -> bool:
    forbidden_identities = {
        (
            source.record_kind,
            source.record_id,
            source.evidence_span_id,
            source.source_text_digest,
        )
        for source in case.expected.forbidden_sources
    }
    return any(_retrieval_identity(candidate) in forbidden_identities for candidate in candidates)


def evaluate_retrieval_case(
    case: RetrievalCase,
    observation: RetrievalObservation,
) -> RetrievalCaseEvaluation:
    forbidden_visible = _has_forbidden_retrieval_source(case, observation.candidates)
    if not observation.retrieval_available:
        return _invalid_retrieval_case(
            case,
            observation.failure_code or "RETRIEVAL_OBSERVATION_UNAVAILABLE",
            forbidden_visible=forbidden_visible,
        )
    if observation.query != case.query:
        return _invalid_retrieval_case(
            case,
            "RETRIEVAL_QUERY_MISMATCH",
            forbidden_visible=forbidden_visible,
        )
    if (
        case.expected.source_identity_status != "resolved"
        and case.expected.unresolved_identity_policy == "invalid"
    ):
        return _invalid_retrieval_case(
            case,
            f"EXPECTED_SOURCE_IDENTITY_{case.expected.source_identity_status.upper()}",
            forbidden_visible=forbidden_visible,
        )

    unique_candidates: list[RetrievalCandidateObservation] = []
    seen_identities: set[tuple[str, str, str | None, str | None]] = set()
    for candidate in observation.candidates:
        identity = _retrieval_identity(candidate)
        if identity not in seen_identities:
            unique_candidates.append(candidate)
            seen_identities.add(identity)

    expected_groups = [
        {
            (
                alternative.record_kind,
                alternative.record_id,
                alternative.evidence_span_id,
                alternative.source_text_digest,
            )
            for alternative in group.alternatives
        }
        for group in case.expected.evidence_groups
    ]
    first_five_identities = {_retrieval_identity(candidate) for candidate in unique_candidates[:5]}
    matched_groups = sum(bool(group & first_five_identities) for group in expected_groups)

    first_relevant = next(
        (
            candidate
            for candidate in unique_candidates
            if candidate.rank <= 10
            and any(_retrieval_identity(candidate) in group for group in expected_groups)
        ),
        None,
    )
    recall_at_5 = (
        _retrieval_metric_score(matched_groups, len(expected_groups))
        if case.applicability.recall_at_5
        else None
    )
    mrr_at_10 = None
    if case.applicability.mrr_at_10:
        mrr_at_10 = (
            _retrieval_metric_score(0, 1)
            if first_relevant is None
            else _retrieval_metric_score(1, first_relevant.rank)
        )
    authority_priority = None
    if case.applicability.authority_ordering:
        authority_priority = _retrieval_metric_score(
            int(
                first_relevant is not None
                and first_relevant.authority_level == case.expected.preferred_authority_level
            ),
            1,
        )

    forbidden_matches = int(_has_forbidden_retrieval_source(case, unique_candidates))
    forbidden_visibility = (
        _retrieval_metric_score(int(forbidden_matches > 0), 1)
        if case.applicability.forbidden_visibility
        else None
    )

    failure_codes: list[str] = []
    if case.expected.source_identity_status != "resolved":
        failure_codes.append("R-EXPECTED-SOURCE-IDENTITY-UNRESOLVED")
    elif recall_at_5 is not None and recall_at_5.numerator < recall_at_5.denominator:
        failure_codes.append("R-RELEVANT-EVIDENCE-MISS")
    if authority_priority is not None and authority_priority.numerator == 0:
        failure_codes.append("R-AUTHORITY-ORDER-INVERSION")
    if forbidden_matches:
        failure_codes.append("R-FORBIDDEN-VISIBILITY")

    return RetrievalCaseEvaluation(
        schema_version="retrieval-case-evaluation-v1",
        evaluator_version="retrieval-quality-v1",
        case_id=case.id,
        status="SCORED",
        invalid_reasons=[],
        failure_codes=failure_codes,
        hard_failure=forbidden_matches > 0,
        recall_at_5=recall_at_5,
        mrr_at_10=mrr_at_10,
        authority_priority=authority_priority,
        forbidden_visibility=forbidden_visibility,
    )


def _aggregate_retrieval_metric(
    scores: list[RetrievalMetricScore],
) -> RetrievalAggregateMetric:
    case_total = sum(
        (Fraction(score.numerator, score.denominator) for score in scores),
        start=Fraction(0, 1),
    )
    macro_score = case_total / len(scores)
    display_value = (Decimal(macro_score.numerator) / Decimal(macro_score.denominator)).quantize(
        Decimal("0.0001"),
        rounding=ROUND_HALF_EVEN,
    )
    return RetrievalAggregateMetric(
        numerator=macro_score.numerator,
        denominator=macro_score.denominator,
        case_count=len(scores),
        display_value=f"{display_value:.4f}",
    )


def evaluate_retrieval_run(
    dataset: RetrievalDatasetDocument,
    batch: RetrievalObservationBatch,
) -> RetrievalRunEvaluation:
    observations_by_case = {observation.case_id: observation for observation in batch.observations}
    evaluated_cases = [
        case
        for case in dataset.cases
        if batch.adapter_version != "ax-sut-http-v1" or case.split == "verification"
    ]
    case_results: list[RetrievalCaseEvaluation] = []
    invalid_reasons: list[str] = []
    for case in evaluated_cases:
        observation = observations_by_case.get(case.id)
        if observation is None:
            result = _invalid_retrieval_case(case, "RETRIEVAL_OBSERVATION_MISSING")
        else:
            result = evaluate_retrieval_case(case, observation)
        case_results.append(result)
        if result.status == "INVALID":
            invalid_reasons.extend(f"{case.id}:{reason}" for reason in result.invalid_reasons)
    dataset_case_ids = {case.id for case in evaluated_cases}
    invalid_reasons.extend(
        f"{case_id}:RETRIEVAL_OBSERVATION_UNEXPECTED"
        for case_id in sorted(observations_by_case.keys() - dataset_case_ids)
    )
    scored_results = [result for result in case_results if result.status == "SCORED"]
    hard_failure_cases = [result.case_id for result in case_results if result.hard_failure]
    verification_recall_at_5_cases = sum(
        case.split == "verification" and result.recall_at_5 is not None
        for case, result in zip(evaluated_cases, case_results, strict=True)
    )
    coverage = RetrievalCoverage(
        total_cases=len(evaluated_cases),
        scored_cases=len(scored_results),
        calibration_cases=sum(case.split == "calibration" for case in evaluated_cases),
        verification_cases=sum(case.split == "verification" for case in evaluated_cases),
        verification_recall_at_5_cases=verification_recall_at_5_cases,
        authority_ordering_cases=sum(
            result.authority_priority is not None for result in scored_results
        ),
        forbidden_visibility_cases=sum(
            result.forbidden_visibility is not None for result in scored_results
        ),
    )
    if verification_recall_at_5_cases < 9:
        invalid_reasons.append("VERIFICATION_RECALL_AT_5_DENOMINATOR_BELOW_9")
    if invalid_reasons:
        return RetrievalRunEvaluation(
            schema_version="retrieval-run-evaluation-v1",
            evaluator_version="retrieval-quality-v1",
            state="INVALID",
            invalid_reasons=invalid_reasons,
            hard_failure_cases=hard_failure_cases,
            coverage=coverage,
            case_results=case_results,
            aggregate=None,
        )
    metric_scores = {
        "RECALL_AT_5_DENOMINATOR_ZERO": [
            result.recall_at_5 for result in scored_results if result.recall_at_5 is not None
        ],
        "MRR_AT_10_DENOMINATOR_ZERO": [
            result.mrr_at_10 for result in scored_results if result.mrr_at_10 is not None
        ],
        "AUTHORITY_ORDERING_DENOMINATOR_ZERO": [
            result.authority_priority
            for result in scored_results
            if result.authority_priority is not None
        ],
        "FORBIDDEN_VISIBILITY_DENOMINATOR_ZERO": [
            result.forbidden_visibility
            for result in scored_results
            if result.forbidden_visibility is not None
        ],
    }
    zero_denominator_reasons = [reason for reason, scores in metric_scores.items() if not scores]
    if zero_denominator_reasons:
        return RetrievalRunEvaluation(
            schema_version="retrieval-run-evaluation-v1",
            evaluator_version="retrieval-quality-v1",
            state="INVALID",
            invalid_reasons=zero_denominator_reasons,
            hard_failure_cases=hard_failure_cases,
            coverage=coverage,
            case_results=case_results,
            aggregate=None,
        )
    return RetrievalRunEvaluation(
        schema_version="retrieval-run-evaluation-v1",
        evaluator_version="retrieval-quality-v1",
        state="COMPLETED",
        invalid_reasons=[],
        hard_failure_cases=hard_failure_cases,
        coverage=coverage,
        case_results=case_results,
        aggregate=RetrievalAggregate(
            recall_at_5=_aggregate_retrieval_metric(metric_scores["RECALL_AT_5_DENOMINATOR_ZERO"]),
            mrr_at_10=_aggregate_retrieval_metric(metric_scores["MRR_AT_10_DENOMINATOR_ZERO"]),
            authority_priority=_aggregate_retrieval_metric(
                metric_scores["AUTHORITY_ORDERING_DENOMINATOR_ZERO"]
            ),
            forbidden_visibility=_aggregate_retrieval_metric(
                metric_scores["FORBIDDEN_VISIBILITY_DENOMINATOR_ZERO"]
            ),
        ),
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
    *,
    verification_only: bool = False,
) -> ParsingRunEvaluation:
    observations_by_case = {observation.case_id: observation for observation in batch.observations}
    evaluated_cases = [
        case for case in dataset.cases if not verification_only or case.split == "verification"
    ]
    case_results: list[ParsingCaseEvaluation] = []
    invalid_reasons: list[str] = []
    verification_evidence_span_cases = 0
    dataset_case_ids = {case.id for case in evaluated_cases}

    for case in evaluated_cases:
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
        total_cases=len(evaluated_cases),
        scored_cases=len(scored_results),
        calibration_cases=sum(case.split == "calibration" for case in evaluated_cases),
        verification_cases=sum(case.split == "verification" for case in evaluated_cases),
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
            table_preservation=(
                _aggregate_metric(
                    [
                        result.table_preservation
                        for result in scored_results
                        if result.table_preservation is not None
                    ]
                )
                if any(result.table_preservation is not None for result in scored_results)
                else None
            ),
            list_preservation=(
                _aggregate_metric(
                    [
                        result.list_preservation
                        for result in scored_results
                        if result.list_preservation is not None
                    ]
                )
                if any(result.list_preservation is not None for result in scored_results)
                else None
            ),
        ),
    )
