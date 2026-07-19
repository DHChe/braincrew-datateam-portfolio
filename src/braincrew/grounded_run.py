from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction
from pathlib import Path

from braincrew.ax_http_adapter import AxHttpAdapter, AxRequestContext
from braincrew.grounded_contracts import (
    GroundedAggregate,
    GroundedAggregateMetric,
    GroundedCaseEvaluation,
    GroundedCitation,
    GroundedCoverage,
    GroundedDatasetDocument,
    GroundedMetricScore,
    GroundedObservationBatch,
    GroundedRunEvaluation,
    SourceTextResolution,
)
from braincrew.grounded_evaluator import (
    CLAIM_NORMALIZER_VERSION,
    CLAIM_PROPOSITION_VERSION,
    CLAIM_TRAVERSAL_VERSION,
    GROUNDED_EVALUATOR_VERSION,
    HIGH_RISK_GUARD_VERSION,
    SOURCE_RESOLUTION_VERSION,
    evaluate_grounded_case,
)


def load_grounded_dataset(path: Path) -> GroundedDatasetDocument:
    return GroundedDatasetDocument.model_validate_json(path.read_text(encoding="utf-8"))


def load_grounded_observations(path: Path) -> GroundedObservationBatch:
    return GroundedObservationBatch.model_validate_json(path.read_text(encoding="utf-8"))


def resolve_cited_source_texts(
    *,
    adapter: AxHttpAdapter,
    context: AxRequestContext,
    citations: tuple[GroundedCitation, ...],
) -> tuple[SourceTextResolution, ...]:
    citation_by_source: dict[tuple[str, str], GroundedCitation] = {}
    for citation in citations:
        source_identity = (citation.record_kind, citation.record_id)
        prior = citation_by_source.get(source_identity)
        if prior is not None and prior.source_text_digest != citation.source_text_digest:
            raise ValueError("citations for one source disagree on source text digest")
        citation_by_source.setdefault(source_identity, citation)

    resolutions: list[SourceTextResolution] = []
    for citation in citation_by_source.values():
        observation = adapter.source_text(
            context=context,
            record_kind=citation.record_kind,
            record_id=citation.record_id,
        )
        resolutions.append(
            SourceTextResolution(
                record_kind=observation.response.record_kind,
                record_id=observation.response.record_id,
                text=observation.response.text,
                source_text_digest=citation.source_text_digest,
            )
        )
    return tuple(resolutions)


def _aggregate_metric(scores: tuple[GroundedMetricScore, ...]) -> GroundedAggregateMetric:
    total = sum(
        (
            (Fraction(score.numerator, score.denominator) if score.denominator else Fraction(0, 1))
            for score in scores
        ),
        start=Fraction(0, 1),
    )
    mean = total / len(scores)
    value = Decimal(mean.numerator) / Decimal(mean.denominator)
    display = value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
    return GroundedAggregateMetric(
        applicable_cases=len(scores),
        exact=f"{mean.numerator}/{mean.denominator}",
        value=str(value),
        display=f"{display:.4f}",
    )


def _invalid_run(
    dataset: GroundedDatasetDocument,
    *,
    verification_claim_support_cases: int,
    verification_citation_precision_cases: int,
    verification_answer_mode_cases: int,
    verification_abstention_cases: int,
    case_evaluations: tuple[GroundedCaseEvaluation, ...] = (),
) -> GroundedRunEvaluation:
    case_failure_codes = tuple(
        failure for result in case_evaluations for failure in result.failure_codes
    )
    return GroundedRunEvaluation(
        evaluator_version=GROUNDED_EVALUATOR_VERSION,
        proposition_contract_version=CLAIM_PROPOSITION_VERSION,
        traversal_contract_version=CLAIM_TRAVERSAL_VERSION,
        normalizer_version=CLAIM_NORMALIZER_VERSION,
        source_resolution_version=SOURCE_RESOLUTION_VERSION,
        guard_version=HIGH_RISK_GUARD_VERSION,
        state="INVALID",
        case_evaluations=case_evaluations,
        coverage=GroundedCoverage(
            total_cases=len(dataset.cases),
            verification_cases=sum(case.split == "Verification" for case in dataset.cases),
            verification_claim_support_cases=verification_claim_support_cases,
            verification_citation_precision_cases=verification_citation_precision_cases,
            verification_answer_mode_cases=verification_answer_mode_cases,
            verification_abstention_cases=verification_abstention_cases,
        ),
        aggregate=None,
        failure_codes=tuple(dict.fromkeys(("SYS-GROUNDED-COVERAGE-INVALID", *case_failure_codes))),
        hard_failure_cases=tuple(
            result.case_id for result in case_evaluations if result.hard_failure_codes
        ),
    )


def execute_grounded_fixture(
    dataset: GroundedDatasetDocument,
    observations: GroundedObservationBatch,
) -> GroundedRunEvaluation:
    try:
        GroundedDatasetDocument.model_validate(dataset.model_dump(mode="json"))
        dataset_contract_valid = True
    except ValueError:
        dataset_contract_valid = False
    case_by_id = {case.case_id: case for case in dataset.cases}
    observation_by_id = {item.case_id: item for item in observations.observations}
    expected_ids = set(case_by_id)
    observed_ids = set(observation_by_id)
    available_verification_ids = {
        case_id
        for case_id, case in case_by_id.items()
        if case.split == "Verification"
        and case_id in observation_by_id
        and observation_by_id[case_id].available
    }
    claim_support_coverage = sum(
        case_by_id[case_id].applicability.claim_support_precision
        for case_id in available_verification_ids
    )
    citation_precision_coverage = sum(
        case_by_id[case_id].applicability.citation_precision
        for case_id in available_verification_ids
    )
    answer_mode_coverage = sum(
        case_by_id[case_id].applicability.answer_mode_accuracy
        for case_id in available_verification_ids
    )
    abstention_coverage = sum(
        case_by_id[case_id].applicability.abstention_accuracy
        for case_id in available_verification_ids
    )
    case_evaluations = tuple(
        evaluate_grounded_case(case, observation_by_id[case.case_id])
        for case in dataset.cases
        if case.case_id in observation_by_id
    )
    if (
        not dataset_contract_valid
        or observed_ids != expected_ids
        or claim_support_coverage < 10
        or citation_precision_coverage < 10
        or answer_mode_coverage < 15
        or abstention_coverage < 5
    ):
        return _invalid_run(
            dataset,
            verification_claim_support_cases=claim_support_coverage,
            verification_citation_precision_cases=citation_precision_coverage,
            verification_answer_mode_cases=answer_mode_coverage,
            verification_abstention_cases=abstention_coverage,
            case_evaluations=case_evaluations,
        )

    if any(result.state != "COMPLETED" for result in case_evaluations):
        return _invalid_run(
            dataset,
            verification_claim_support_cases=claim_support_coverage,
            verification_citation_precision_cases=citation_precision_coverage,
            verification_answer_mode_cases=answer_mode_coverage,
            verification_abstention_cases=abstention_coverage,
            case_evaluations=case_evaluations,
        )
    claim_scores = tuple(
        result.claim_support_precision
        for case, result in zip(dataset.cases, case_evaluations, strict=True)
        if case.applicability.claim_support_precision
    )
    citation_scores = tuple(
        result.citation_precision
        for case, result in zip(dataset.cases, case_evaluations, strict=True)
        if case.applicability.citation_precision
    )
    coverage_scores = tuple(
        result.citation_coverage
        for case, result in zip(dataset.cases, case_evaluations, strict=True)
        if case.applicability.citation_coverage
    )
    answer_mode_scores = tuple(
        result.answer_mode_accuracy
        for case, result in zip(dataset.cases, case_evaluations, strict=True)
        if case.applicability.answer_mode_accuracy
    )
    abstention_scores = tuple(
        result.abstention_accuracy
        for case, result in zip(dataset.cases, case_evaluations, strict=True)
        if case.applicability.abstention_accuracy
    )
    if (
        not claim_scores
        or not citation_scores
        or not coverage_scores
        or not answer_mode_scores
        or not abstention_scores
    ):
        return _invalid_run(
            dataset,
            verification_claim_support_cases=claim_support_coverage,
            verification_citation_precision_cases=citation_precision_coverage,
            verification_answer_mode_cases=answer_mode_coverage,
            verification_abstention_cases=abstention_coverage,
            case_evaluations=case_evaluations,
        )
    failure_codes = tuple(
        dict.fromkeys(failure for result in case_evaluations for failure in result.failure_codes)
    )
    return GroundedRunEvaluation(
        evaluator_version=GROUNDED_EVALUATOR_VERSION,
        proposition_contract_version=CLAIM_PROPOSITION_VERSION,
        traversal_contract_version=CLAIM_TRAVERSAL_VERSION,
        normalizer_version=CLAIM_NORMALIZER_VERSION,
        source_resolution_version=SOURCE_RESOLUTION_VERSION,
        guard_version=HIGH_RISK_GUARD_VERSION,
        state="COMPLETED",
        case_evaluations=case_evaluations,
        coverage=GroundedCoverage(
            total_cases=len(dataset.cases),
            verification_cases=sum(case.split == "Verification" for case in dataset.cases),
            verification_claim_support_cases=claim_support_coverage,
            verification_citation_precision_cases=citation_precision_coverage,
            verification_answer_mode_cases=answer_mode_coverage,
            verification_abstention_cases=abstention_coverage,
        ),
        aggregate=GroundedAggregate(
            claim_support_precision=_aggregate_metric(claim_scores),
            citation_precision=_aggregate_metric(citation_scores),
            citation_coverage=_aggregate_metric(coverage_scores),
            answer_mode_accuracy=_aggregate_metric(answer_mode_scores),
            abstention_accuracy=_aggregate_metric(abstention_scores),
        ),
        failure_codes=failure_codes,
        hard_failure_cases=tuple(
            result.case_id for result in case_evaluations if result.hard_failure_codes
        ),
    )
