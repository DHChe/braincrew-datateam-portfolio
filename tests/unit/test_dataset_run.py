from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest

from braincrew.dataset_registry import validate_dataset_bundle

MANIFEST_PATH = Path("datasets/dataset_manifest_v1.json")
PARSING_OBSERVATIONS = Path("tests/fixtures/parsing_observations_v1.json")
RETRIEVAL_OBSERVATIONS = Path("tests/fixtures/retrieval_observations_v1.json")
GROUNDED_OBSERVATIONS = Path("tests/fixtures/grounded_observations_v1.json")


def test_full_fixture_executes_all_one_hundred_cases_with_component_aggregates() -> None:
    assert importlib.util.find_spec("braincrew.dataset_run") is not None, (
        "Issue #12 must provide the integrated dataset fixture runner"
    )
    dataset_run = importlib.import_module("braincrew.dataset_run")
    load_observations = getattr(dataset_run, "load_dataset_observations", None)
    execute_fixture = getattr(dataset_run, "execute_dataset_fixture", None)
    assert callable(load_observations)
    assert callable(execute_fixture)
    validation = validate_dataset_bundle(MANIFEST_PATH)
    observations = load_observations(
        parsing_path=PARSING_OBSERVATIONS,
        retrieval_path=RETRIEVAL_OBSERVATIONS,
        grounded_path=GROUNDED_OBSERVATIONS,
    )

    result = execute_fixture(validation, observations)

    assert result.schema_version == "dataset-run-evaluation-v1"
    assert result.state == "COMPLETED"
    assert result.invalid_reasons == ()
    assert result.total_cases == 100
    assert result.scored_cases == 100
    assert result.parsing is not None
    assert result.retrieval is not None
    assert result.grounded is not None
    assert len(result.parsing.case_results) == 20
    assert len(result.retrieval.case_results) == 30
    assert len(result.grounded.case_evaluations) == 50
    assert result.parsing.aggregate is not None
    assert result.retrieval.aggregate is not None
    assert result.grounded.aggregate is not None
    assert result.parsing.coverage.verification_evidence_span_cases == 6
    assert result.retrieval.coverage.verification_recall_at_5_cases == 9
    assert result.grounded.coverage.verification_claim_support_cases == 10
    assert result.grounded.coverage.verification_citation_precision_cases == 10
    assert result.grounded.coverage.verification_answer_mode_cases == 15
    assert result.grounded.coverage.verification_abstention_cases == 5


@pytest.mark.parametrize("component", ["parsing", "retrieval", "grounded"])
def test_integrated_run_is_invalid_when_a_component_observation_is_missing(
    component: str,
) -> None:
    dataset_run = importlib.import_module("braincrew.dataset_run")
    validation = validate_dataset_bundle(MANIFEST_PATH)
    observations = dataset_run.load_dataset_observations(
        parsing_path=PARSING_OBSERVATIONS,
        retrieval_path=RETRIEVAL_OBSERVATIONS,
        grounded_path=GROUNDED_OBSERVATIONS,
    )
    batch = getattr(observations, component)
    missing_batch = batch.model_copy(update={"observations": batch.observations[:-1]})
    drifted = observations.model_copy(update={component: missing_batch})

    result = dataset_run.execute_dataset_fixture(validation, drifted)

    assert result.state == "INVALID"
    assert result.scored_cases == 99
    assert "DATASET_CASE_COVERAGE_INVALID" in result.invalid_reasons


def test_integrated_run_is_invalid_when_an_observation_identity_is_duplicated() -> None:
    dataset_run = importlib.import_module("braincrew.dataset_run")
    validation = validate_dataset_bundle(MANIFEST_PATH)
    observations = dataset_run.load_dataset_observations(
        parsing_path=PARSING_OBSERVATIONS,
        retrieval_path=RETRIEVAL_OBSERVATIONS,
        grounded_path=GROUNDED_OBSERVATIONS,
    )
    parsing_items = observations.parsing.observations
    duplicate_batch = observations.parsing.model_copy(
        update={"observations": [*parsing_items[:-1], parsing_items[0]]}
    )
    drifted = observations.model_copy(update={"parsing": duplicate_batch})

    result = dataset_run.execute_dataset_fixture(validation, drifted)

    assert result.state == "INVALID"
    assert result.scored_cases == 99
    assert "DATASET_CASE_COVERAGE_INVALID" in result.invalid_reasons
