from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from braincrew import contracts
from braincrew.contracts import (
    RetrievalCase,
    RetrievalCaseEvaluation,
    RetrievalDatasetDocument,
    RetrievalObservation,
    RetrievalObservationBatch,
    RetrievalRunEvaluation,
)
from braincrew.evaluator import evaluate_retrieval_case, evaluate_retrieval_run

DATASET_PATH = Path(__file__).parents[2] / "datasets" / "retrieval" / "retrieval_cases_v1.json"
OBSERVATIONS_PATH = Path(__file__).parents[1] / "fixtures" / "retrieval_observations_v1.json"


def dataset_case(case_id: str) -> RetrievalCase:
    dataset = RetrievalDatasetDocument.model_validate_json(DATASET_PATH.read_text(encoding="utf-8"))
    return next(case for case in dataset.cases if case.id == case_id)


def dataset_document() -> RetrievalDatasetDocument:
    return RetrievalDatasetDocument.model_validate_json(DATASET_PATH.read_text(encoding="utf-8"))


def observation_batch() -> RetrievalObservationBatch:
    return RetrievalObservationBatch.model_validate_json(
        OBSERVATIONS_PATH.read_text(encoding="utf-8")
    )


def retrieval_observation_model() -> type[RetrievalObservation]:
    return RetrievalObservation


def retrieval_evaluator() -> Callable[
    [RetrievalCase, RetrievalObservation], RetrievalCaseEvaluation
]:
    return evaluate_retrieval_case


def retrieval_run_evaluator() -> Callable[
    [RetrievalDatasetDocument, RetrievalObservationBatch], RetrievalRunEvaluation
]:
    return evaluate_retrieval_run


def test_live_retrieval_run_scores_only_the_nine_verification_observations() -> None:
    dataset = dataset_document()
    batch = observation_batch()
    verification_ids = {case.id for case in dataset.cases if case.split == "verification"}
    live_batch = RetrievalObservationBatch.model_validate(
        {
            **batch.model_dump(mode="json"),
            "adapter_version": "ax-sut-http-v1",
            "observations": [
                observation.model_dump(mode="json")
                for observation in batch.observations
                if observation.case_id in verification_ids
            ],
        }
    )

    result = evaluate_retrieval_run(dataset, live_batch)

    assert result.state == "COMPLETED"
    assert result.invalid_reasons == []
    assert len(result.case_results) == 9
    assert result.coverage.total_cases == 9
    assert result.coverage.scored_cases == 9
    assert result.coverage.calibration_cases == 0
    assert result.coverage.verification_cases == 9


def candidate(
    *,
    rank: int,
    record_kind: str,
    record_id: str,
    evidence_span_id: str | None,
    source_text_digest: str | None,
    authority_level: int | None,
) -> dict[str, object]:
    return {
        "rank": rank,
        "record_kind": record_kind,
        "record_id": record_id,
        "evidence_span_id": evidence_span_id,
        "source_text_digest": source_text_digest,
        "authority_level": authority_level,
        "visibility_allowed": True,
        "visibility_reason": "role_scope_allowed",
    }


def test_retrieval_metric_golden_preserves_rank_deduplication_and_exact_counts() -> None:
    case = dataset_case("retrieval-005")
    expected_groups = case.expected.evidence_groups
    primary = expected_groups[0].alternatives[0]
    secondary = expected_groups[1].alternatives[0]
    observation = retrieval_observation_model().model_validate(
        {
            "schema_version": "retrieval-observation-v1",
            "case_id": case.id,
            "query": case.query,
            "retrieval_available": True,
            "failure_code": None,
            "candidates": [
                candidate(
                    rank=1,
                    record_kind="company_rule",
                    record_id="irrelevant-source",
                    evidence_span_id="irrelevant-span",
                    source_text_digest=None,
                    authority_level=3,
                ),
                candidate(rank=2, **secondary.model_dump(mode="python")),
                candidate(rank=3, **secondary.model_dump(mode="python")),
                candidate(rank=4, **primary.model_dump(mode="python")),
            ],
        }
    )

    result = retrieval_evaluator()(case, observation)

    assert result.status == "SCORED"
    assert result.evaluator_version == "retrieval-quality-v1"
    assert result.recall_at_5 is not None
    assert result.mrr_at_10 is not None
    assert result.authority_priority is not None
    assert result.forbidden_visibility is not None
    assert result.recall_at_5.model_dump(mode="json") == {
        "numerator": 2,
        "denominator": 2,
        "display_value": "1.0000",
    }
    assert result.mrr_at_10.model_dump(mode="json") == {
        "numerator": 1,
        "denominator": 2,
        "display_value": "0.5000",
    }
    assert result.authority_priority.model_dump(mode="json") == {
        "numerator": 0,
        "denominator": 1,
        "display_value": "0.0000",
    }
    assert result.forbidden_visibility.model_dump(mode="json") == {
        "numerator": 0,
        "denominator": 1,
        "display_value": "0.0000",
    }
    assert result.failure_codes == ["R-AUTHORITY-ORDER-INVERSION"]
    assert result.hard_failure is False


def test_recall_at_five_uses_the_first_five_unique_identities() -> None:
    case = dataset_case("retrieval-005")
    relevant = case.expected.evidence_groups[1].alternatives[0]
    candidates = [
        candidate(
            rank=1,
            record_kind="company_rule",
            record_id="duplicate-source",
            evidence_span_id="duplicate-span",
            source_text_digest=None,
            authority_level=3,
        ),
        candidate(
            rank=2,
            record_kind="company_rule",
            record_id="duplicate-source",
            evidence_span_id="duplicate-span",
            source_text_digest=None,
            authority_level=3,
        ),
    ]
    candidates.extend(
        candidate(
            rank=rank,
            record_kind="company_rule",
            record_id=f"irrelevant-{rank}",
            evidence_span_id=f"irrelevant-span-{rank}",
            source_text_digest=None,
            authority_level=3,
        )
        for rank in range(3, 6)
    )
    candidates.append(candidate(rank=6, **relevant.model_dump(mode="python")))
    observation = retrieval_observation_model().model_validate(
        {
            "schema_version": "retrieval-observation-v1",
            "case_id": case.id,
            "query": case.query,
            "retrieval_available": True,
            "failure_code": None,
            "candidates": candidates,
        }
    )

    result = retrieval_evaluator()(case, observation)

    assert result.recall_at_5 is not None
    assert result.recall_at_5.model_dump(mode="json") == {
        "numerator": 1,
        "denominator": 2,
        "display_value": "0.5000",
    }


def test_missing_expected_identity_remains_in_recall_and_mrr_denominators() -> None:
    case = dataset_case("retrieval-019")
    observation = retrieval_observation_model().model_validate(
        {
            "schema_version": "retrieval-observation-v1",
            "case_id": case.id,
            "query": case.query,
            "retrieval_available": True,
            "failure_code": None,
            "candidates": [],
        }
    )

    result = retrieval_evaluator()(case, observation)

    assert result.status == "SCORED"
    assert result.recall_at_5 is not None
    assert result.mrr_at_10 is not None
    assert result.recall_at_5.model_dump(mode="json") == {
        "numerator": 0,
        "denominator": 1,
        "display_value": "0.0000",
    }
    assert result.mrr_at_10.model_dump(mode="json") == {
        "numerator": 0,
        "denominator": 1,
        "display_value": "0.0000",
    }
    assert result.authority_priority is None
    assert result.failure_codes == ["R-EXPECTED-SOURCE-IDENTITY-UNRESOLVED"]


def test_ambiguous_expected_identity_can_invalidate_instead_of_leaving_the_denominator() -> None:
    dataset_case_with_denominator = dataset_case("retrieval-020")
    case_payload = dataset_case_with_denominator.model_dump(mode="json")
    case_payload["expected"]["unresolved_identity_policy"] = "invalid"
    case = type(dataset_case_with_denominator).model_validate(case_payload)
    observation = retrieval_observation_model().model_validate(
        {
            "schema_version": "retrieval-observation-v1",
            "case_id": case.id,
            "query": case.query,
            "retrieval_available": True,
            "failure_code": None,
            "candidates": [],
        }
    )

    result = retrieval_evaluator()(case, observation)

    assert result.status == "INVALID"
    assert result.invalid_reasons == ["EXPECTED_SOURCE_IDENTITY_AMBIGUOUS"]
    assert result.recall_at_5 is None
    assert result.mrr_at_10 is None
    assert result.authority_priority is None
    assert result.forbidden_visibility is None


def test_forbidden_source_identity_is_a_zero_tolerance_hard_failure() -> None:
    case = dataset_case("retrieval-001")
    forbidden = case.expected.forbidden_sources[0]
    observation = retrieval_observation_model().model_validate(
        {
            "schema_version": "retrieval-observation-v1",
            "case_id": case.id,
            "query": case.query,
            "retrieval_available": True,
            "failure_code": None,
            "candidates": [candidate(rank=1, **forbidden.model_dump(mode="python"))],
        }
    )

    result = retrieval_evaluator()(case, observation)

    assert result.status == "SCORED"
    assert result.forbidden_visibility is not None
    assert result.forbidden_visibility.model_dump(mode="json") == {
        "numerator": 1,
        "denominator": 1,
        "display_value": "1.0000",
    }
    assert "R-FORBIDDEN-VISIBILITY" in result.failure_codes
    assert result.hard_failure is True


def test_query_identity_mismatch_is_invalid_instead_of_scoring_the_wrong_case() -> None:
    case = dataset_case("retrieval-001")
    observation = retrieval_observation_model().model_validate(
        {
            "schema_version": "retrieval-observation-v1",
            "case_id": case.id,
            "query": "다른 질의",
            "retrieval_available": True,
            "failure_code": None,
            "candidates": [],
        }
    )

    result = retrieval_evaluator()(case, observation)

    assert result.status == "INVALID"
    assert result.invalid_reasons == ["RETRIEVAL_QUERY_MISMATCH"]
    assert result.recall_at_5 is None


def test_unavailable_retrieval_is_invalid_and_emits_no_quality_scores() -> None:
    case = dataset_case("retrieval-001")
    observation = retrieval_observation_model().model_validate(
        {
            "schema_version": "retrieval-observation-v1",
            "case_id": case.id,
            "query": case.query,
            "retrieval_available": False,
            "failure_code": "AX_RETRIEVAL_UNAVAILABLE",
            "candidates": [],
        }
    )

    result = retrieval_evaluator()(case, observation)

    assert result.status == "INVALID"
    assert result.invalid_reasons == ["AX_RETRIEVAL_UNAVAILABLE"]
    assert result.recall_at_5 is None
    assert result.mrr_at_10 is None
    assert result.authority_priority is None
    assert result.forbidden_visibility is None


def test_invalid_retrieval_preserves_forbidden_source_hard_failure_evidence() -> None:
    dataset = dataset_document()
    batch_payload = observation_batch().model_dump(mode="json")
    forbidden = dataset.cases[0].expected.forbidden_sources[0]
    batch_payload["observations"][0].update(
        {
            "retrieval_available": False,
            "failure_code": "AX_RETRIEVAL_UNAVAILABLE",
            "candidates": [candidate(rank=1, **forbidden.model_dump(mode="python"))],
        }
    )
    batch = contracts.RetrievalObservationBatch.model_validate(batch_payload)

    result = retrieval_run_evaluator()(dataset, batch)

    invalid_case = result.case_results[0]
    assert result.state == "INVALID"
    assert invalid_case.status == "INVALID"
    assert invalid_case.invalid_reasons == ["AX_RETRIEVAL_UNAVAILABLE"]
    assert invalid_case.failure_codes == ["R-FORBIDDEN-VISIBILITY"]
    assert invalid_case.hard_failure is True
    assert invalid_case.forbidden_visibility is None
    assert result.hard_failure_cases == ["retrieval-001"]


def test_thirty_case_run_macro_aggregates_exact_scores_and_verification_coverage() -> None:
    result = retrieval_run_evaluator()(dataset_document(), observation_batch())

    assert result.state == "COMPLETED"
    assert result.invalid_reasons == []
    assert result.hard_failure_cases == []
    assert len(result.case_results) == 30
    assert result.coverage.model_dump(mode="json") == {
        "total_cases": 30,
        "scored_cases": 30,
        "calibration_cases": 21,
        "verification_cases": 9,
        "verification_recall_at_5_cases": 9,
        "authority_ordering_cases": 28,
        "forbidden_visibility_cases": 30,
    }
    assert result.aggregate is not None
    assert result.aggregate.recall_at_5.model_dump(mode="json") == {
        "numerator": 14,
        "denominator": 15,
        "case_count": 30,
        "display_value": "0.9333",
    }
    assert result.aggregate.mrr_at_10.model_dump(mode="json") == {
        "numerator": 14,
        "denominator": 15,
        "case_count": 30,
        "display_value": "0.9333",
    }
    assert result.aggregate.authority_priority.model_dump(mode="json") == {
        "numerator": 1,
        "denominator": 1,
        "case_count": 28,
        "display_value": "1.0000",
    }
    assert result.aggregate.forbidden_visibility.model_dump(mode="json") == {
        "numerator": 0,
        "denominator": 1,
        "case_count": 30,
        "display_value": "0.0000",
    }


def test_complete_run_preserves_any_forbidden_source_as_a_hard_failure() -> None:
    dataset = dataset_document()
    batch_payload = observation_batch().model_dump(mode="json")
    forbidden = dataset.cases[0].expected.forbidden_sources[0]
    batch_payload["observations"][0]["candidates"] = [
        candidate(rank=1, **forbidden.model_dump(mode="python"))
    ]
    batch = contracts.RetrievalObservationBatch.model_validate(batch_payload)

    result = retrieval_run_evaluator()(dataset, batch)

    assert result.state == "COMPLETED"
    assert result.hard_failure_cases == ["retrieval-001"]
    assert result.invalid_reasons == []
    assert result.aggregate is not None
    assert result.aggregate.forbidden_visibility.model_dump(mode="json") == {
        "numerator": 1,
        "denominator": 30,
        "case_count": 30,
        "display_value": "0.0333",
    }


def test_run_is_invalid_when_a_verification_observation_is_missing() -> None:
    dataset = dataset_document()
    batch_payload = observation_batch().model_dump(mode="json")
    batch_payload["observations"].pop()
    batch = contracts.RetrievalObservationBatch.model_validate(batch_payload)

    try:
        result = retrieval_run_evaluator()(dataset, batch)
    except KeyError:
        pytest.fail("missing observations must produce an INVALID result, not a KeyError")

    assert result.state == "INVALID"
    assert result.invalid_reasons == [
        "retrieval-030:RETRIEVAL_OBSERVATION_MISSING",
        "VERIFICATION_RECALL_AT_5_DENOMINATOR_BELOW_9",
    ]
    assert result.coverage.scored_cases == 29
    assert result.coverage.verification_recall_at_5_cases == 8
    assert result.aggregate is None


def test_run_is_invalid_when_the_fixture_contains_an_unknown_case() -> None:
    dataset = dataset_document()
    batch_payload = observation_batch().model_dump(mode="json")
    unknown = dict(batch_payload["observations"][0])
    unknown["case_id"] = "retrieval-unknown"
    batch_payload["observations"].append(unknown)
    batch = contracts.RetrievalObservationBatch.model_validate(batch_payload)

    result = retrieval_run_evaluator()(dataset, batch)

    assert result.state == "INVALID"
    assert result.invalid_reasons == ["retrieval-unknown:RETRIEVAL_OBSERVATION_UNEXPECTED"]
    assert result.aggregate is None


def test_run_is_invalid_when_an_aggregate_metric_has_no_applicable_cases() -> None:
    dataset_payload = dataset_document().model_dump(mode="json")
    for case in dataset_payload["cases"]:
        case["applicability"]["authority_ordering"] = False
        case["expected"]["preferred_authority_level"] = None
    dataset = contracts.RetrievalDatasetDocument.model_validate(dataset_payload)

    result = retrieval_run_evaluator()(dataset, observation_batch())

    assert result.state == "INVALID"
    assert result.invalid_reasons == ["AUTHORITY_ORDERING_DENOMINATOR_ZERO"]
    assert result.aggregate is None


def test_retrieval_metric_contract_rejects_impossible_or_mismatched_scores() -> None:
    with pytest.raises(ValueError):
        contracts.RetrievalMetricScore.model_validate(
            {"numerator": 2, "denominator": 1, "display_value": "1.0000"}
        )
    with pytest.raises(ValueError):
        contracts.RetrievalMetricScore.model_validate(
            {"numerator": 1, "denominator": 2, "display_value": "0.6000"}
        )
