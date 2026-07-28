from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from braincrew.contracts import (
    ParsingCase,
    ParsingDatasetDocument,
    ParsingObservation,
    ParsingObservationBatch,
)
from braincrew.evaluator import evaluate_parsing_case, evaluate_parsing_run

DATASET_PATH = Path(__file__).parents[2] / "datasets" / "parsing" / "parsing_cases_v1.json"


def dataset_case(case_id: str) -> ParsingCase:
    raw_dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    document = ParsingDatasetDocument.model_validate(raw_dataset)
    return next(case for case in document.cases if case.id == case_id)


def dataset_document() -> ParsingDatasetDocument:
    raw_dataset = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    return ParsingDatasetDocument.model_validate(raw_dataset)


def observation(**overrides: object) -> ParsingObservation:
    payload: dict[str, object] = {
        "schema_version": "parsing-observation-v1",
        "case_id": "parsing-006",
        "parse_available": True,
        "parser_version": "fixture-parser-v1",
        "failure_code": None,
        "evidence_spans": [],
        "headings": ["제4조 휴게"],
        "metadata": {"document_type": "근무규정", "department": "wrong"},
        "table": None,
        "list": None,
    }
    payload.update(overrides)
    return ParsingObservation.model_validate(payload)


def perfect_observation_payload(case: ParsingCase) -> dict[str, object]:
    return {
        "schema_version": "parsing-observation-v1",
        "case_id": case.id,
        "parse_available": True,
        "parser_version": "fixture-parser-v1",
        "failure_code": None,
        "evidence_spans": [span.model_dump(mode="json") for span in case.expected.evidence_spans],
        "headings": case.expected.structure.headings,
        "metadata": case.expected.metadata,
        "table": None
        if case.expected.table is None
        else case.expected.table.model_dump(mode="json"),
        "list": None if case.expected.list is None else case.expected.list.model_dump(mode="json"),
    }


def observation_batch(dataset: ParsingDatasetDocument) -> ParsingObservationBatch:
    return ParsingObservationBatch.model_validate(
        {
            "schema_version": "parsing-observation-batch-v1",
            "adapter_version": "fixture-parsing-sut-v1",
            "parser_version": "fixture-parser-v1",
            "observations": [perfect_observation_payload(case) for case in dataset.cases],
        }
    )


def test_parsing_metric_golden_preserves_hand_calculated_exact_counts() -> None:
    case = dataset_case("parsing-006")
    result = evaluate_parsing_case(
        case,
        observation(evidence_spans=[case.expected.evidence_spans[0].model_dump(mode="json")]),
    )

    assert result.status == "SCORED"
    assert result.evaluator_version == "parsing-quality-v1"
    assert result.evidence_span_recovery is not None
    assert result.structure_preservation is not None
    assert result.metadata_completeness is not None
    assert result.evidence_span_recovery.model_dump(mode="json") == {
        "numerator": 1,
        "denominator": 2,
        "display_value": "0.5000",
    }
    assert result.structure_preservation.model_dump(mode="json") == {
        "numerator": 1,
        "denominator": 1,
        "display_value": "1.0000",
    }
    assert result.metadata_completeness.model_dump(mode="json") == {
        "numerator": 1,
        "denominator": 2,
        "display_value": "0.5000",
    }
    assert result.table_preservation is None
    assert result.list_preservation is None
    assert result.invalid_reasons == []


def test_table_and_list_metrics_are_scored_only_when_applicable() -> None:
    case = dataset_case("parsing-020")
    assert case.expected.table is not None
    result = evaluate_parsing_case(
        case,
        observation(
            case_id="parsing-020",
            evidence_spans=[span.model_dump(mode="json") for span in case.expected.evidence_spans],
            headings=case.expected.structure.headings,
            metadata=case.expected.metadata,
            table=case.expected.table.model_dump(mode="json"),
            list={"items": ["온라인"], "ordered": False},
        ),
    )

    assert result.table_preservation is not None
    assert result.list_preservation is not None
    assert result.table_preservation.numerator == 1
    assert result.table_preservation.denominator == 1
    assert result.list_preservation.numerator == 0
    assert result.list_preservation.denominator == 1


def test_unobservable_parse_is_invalid_and_emits_no_quality_scores() -> None:
    case = dataset_case("parsing-015")
    result = evaluate_parsing_case(
        case,
        observation(
            case_id="parsing-015",
            parse_available=False,
            parser_version=None,
            failure_code="AX_PARSE_OBSERVABILITY_UNAVAILABLE",
            headings=[],
            metadata={},
        ),
    )

    assert result.status == "INVALID"
    assert result.invalid_reasons == ["AX_PARSE_OBSERVABILITY_UNAVAILABLE"]
    assert result.evidence_span_recovery is None
    assert result.structure_preservation is None
    assert result.metadata_completeness is None
    assert result.table_preservation is None
    assert result.list_preservation is None


def test_twenty_case_run_macro_aggregates_exact_scores_and_verification_coverage() -> None:
    dataset = dataset_document()

    result = evaluate_parsing_run(dataset, observation_batch(dataset))

    assert result.state == "COMPLETED"
    assert result.invalid_reasons == []
    assert len(result.case_results) == 20
    assert result.coverage.model_dump(mode="json") == {
        "total_cases": 20,
        "scored_cases": 20,
        "calibration_cases": 14,
        "verification_cases": 6,
        "verification_evidence_span_cases": 6,
    }
    assert result.aggregate is not None
    assert result.aggregate.evidence_span_recovery.model_dump(mode="json") == {
        "numerator": 1,
        "denominator": 1,
        "case_count": 20,
        "display_value": "1.0000",
    }
    assert result.aggregate.structure_preservation.case_count == 20
    assert result.aggregate.metadata_completeness.case_count == 20
    if result.aggregate.table_preservation is None:
        pytest.fail("full parsing evaluation must retain table applicability")
    if result.aggregate.list_preservation is None:
        pytest.fail("full parsing evaluation must retain list applicability")
    assert result.aggregate.table_preservation.case_count == 5
    assert result.aggregate.list_preservation.case_count == 5


def test_run_is_invalid_without_parse_observability_and_publishes_no_aggregate() -> None:
    dataset = dataset_document()
    batch_payload = observation_batch(dataset).model_dump(mode="json")
    batch_payload["observations"][14] = {
        **batch_payload["observations"][14],
        "parse_available": False,
        "parser_version": None,
        "failure_code": "AX_PARSE_OBSERVABILITY_UNAVAILABLE",
        "evidence_spans": [],
        "headings": [],
        "metadata": {},
        "table": None,
        "list": None,
    }
    batch = ParsingObservationBatch.model_validate(batch_payload)

    result = evaluate_parsing_run(dataset, batch)

    assert result.state == "INVALID"
    assert result.invalid_reasons == [
        "parsing-015:AX_PARSE_OBSERVABILITY_UNAVAILABLE",
        "VERIFICATION_EVIDENCE_SPAN_DENOMINATOR_BELOW_6",
    ]
    assert result.coverage.scored_cases == 19
    assert result.coverage.verification_evidence_span_cases == 5
    assert result.aggregate is None


def test_run_is_invalid_when_an_expected_case_observation_is_missing() -> None:
    dataset = dataset_document()
    batch_payload = observation_batch(dataset).model_dump(mode="json")
    batch_payload["observations"].pop()
    batch = ParsingObservationBatch.model_validate(batch_payload)

    result = evaluate_parsing_run(dataset, batch)

    assert result.state == "INVALID"
    assert result.invalid_reasons == [
        "parsing-020:PARSE_OBSERVATION_MISSING",
        "VERIFICATION_EVIDENCE_SPAN_DENOMINATOR_BELOW_6",
    ]
    assert result.aggregate is None


def test_observation_batch_rejects_per_case_parser_version_drift() -> None:
    dataset = dataset_document()
    batch_payload = observation_batch(dataset).model_dump(mode="json")
    batch_payload["observations"][0]["parser_version"] = "different-parser-v2"

    with pytest.raises(ValidationError, match="parser version must match the batch"):
        ParsingObservationBatch.model_validate(batch_payload)


def test_run_is_invalid_when_the_fixture_contains_an_unknown_case() -> None:
    dataset = dataset_document()
    batch_payload = observation_batch(dataset).model_dump(mode="json")
    unknown = dict(batch_payload["observations"][0])
    unknown["case_id"] = "parsing-unknown"
    batch_payload["observations"].append(unknown)
    batch = ParsingObservationBatch.model_validate(batch_payload)

    result = evaluate_parsing_run(dataset, batch)

    assert result.state == "INVALID"
    assert result.invalid_reasons == ["parsing-unknown:PARSE_OBSERVATION_UNEXPECTED"]
    assert result.aggregate is None
