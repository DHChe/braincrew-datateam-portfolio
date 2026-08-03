from __future__ import annotations

import copy
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import BaseModel, ValidationError

from braincrew import contracts

DATASET_PATH = Path(__file__).parents[2] / "datasets" / "retrieval" / "retrieval_cases_v1.json"
OBSERVATIONS_PATH = Path(__file__).parents[1] / "fixtures" / "retrieval_observations_v1.json"


def load_raw_dataset() -> dict[str, Any]:
    assert DATASET_PATH.is_file(), "Issue #9 must provide the versioned retrieval dataset"
    return cast(dict[str, Any], json.loads(DATASET_PATH.read_text(encoding="utf-8")))


def retrieval_dataset_model() -> type[BaseModel]:
    model = getattr(contracts, "RetrievalDatasetDocument", None)
    assert model is not None, "Issue #9 must define the strict retrieval dataset contract"
    return cast(type[BaseModel], model)


def retrieval_observation_batch_model() -> type[BaseModel]:
    model = getattr(contracts, "RetrievalObservationBatch", None)
    assert model is not None, "Issue #9 must define the strict retrieval observation batch"
    return cast(type[BaseModel], model)


def test_retrieval_dataset_freezes_thirty_cases_and_the_twenty_one_nine_split() -> None:
    dataset = load_raw_dataset()

    assert dataset["schema_version"] == "retrieval-dataset-v1"
    assert dataset["dataset"] == {
        "id": "braincrew-retrieval-quality",
        "version": "1.0.0",
        "corpus_id": "synthetic-hr-v1",
    }
    assert dataset["provenance"] == {
        "source_type": "synthetic",
        "license": "CC0-1.0",
    }
    assert len(dataset["cases"]) == 30
    assert Counter(case["split"] for case in dataset["cases"]) == {
        "calibration": 21,
        "verification": 9,
    }
    assert len({case["id"] for case in dataset["cases"]}) == 30


def test_each_retrieval_case_has_reviewable_identity_authority_and_visibility_ground_truth() -> (
    None
):
    dataset = load_raw_dataset()

    for case in dataset["cases"]:
        assert case["primary_focus"] == "retrieval"
        assert case["role"] in {"Executive", "HRManager"}
        assert case["query"]
        assert case["corpus"] == {"id": "synthetic-hr-v1", "version": "1.0.0"}
        assert case["expected"]["evidence_groups"]
        assert case["expected"]["forbidden_sources"]
        assert case["applicability"]["recall_at_5"] is True
        assert case["applicability"]["mrr_at_10"] is True
        assert case["applicability"]["forbidden_visibility"] is True
        assert case["provenance"] == {"source_type": "synthetic", "license": "CC0-1.0"}
        assert case["review"]["status"] == "reviewed"

    verification_cases = [case for case in dataset["cases"] if case["split"] == "verification"]
    assert len(verification_cases) == 9
    assert all(
        case["expected"]["source_identity_status"] == "resolved" for case in verification_cases
    )


def test_unresolved_expected_source_identity_policy_is_explicit_and_auditable() -> None:
    cases = {case["id"]: case for case in load_raw_dataset()["cases"]}

    assert cases["retrieval-019"]["expected"]["source_identity_status"] == "missing"
    assert cases["retrieval-019"]["expected"]["unresolved_identity_policy"] == "denominator_zero"
    assert cases["retrieval-020"]["expected"]["source_identity_status"] == "ambiguous"
    assert cases["retrieval-020"]["expected"]["unresolved_identity_policy"] == "denominator_zero"
    assert cases["retrieval-019"]["expected"]["evidence_groups"][0]["alternatives"] == []
    assert cases["retrieval-020"]["expected"]["evidence_groups"][0]["alternatives"] == []


def test_retrieval_dataset_round_trips_through_a_strict_versioned_contract() -> None:
    document = retrieval_dataset_model().model_validate(load_raw_dataset())

    assert document.model_dump(mode="json") == load_raw_dataset()


def test_retrieval_dataset_contract_rejects_split_identity_and_unknown_field_drift() -> None:
    split_drift = copy.deepcopy(load_raw_dataset())
    split_drift["cases"][20]["split"] = "verification"
    duplicate_id = copy.deepcopy(load_raw_dataset())
    duplicate_id["cases"][1]["id"] = duplicate_id["cases"][0]["id"]
    missing_resolved_identity = copy.deepcopy(load_raw_dataset())
    missing_resolved_identity["cases"][0]["expected"]["evidence_groups"][0]["alternatives"] = []
    unknown_field = copy.deepcopy(load_raw_dataset())
    unknown_field["cases"][0]["unexpected"] = True

    with pytest.raises(ValidationError, match="21 calibration and 9 verification"):
        retrieval_dataset_model().model_validate(split_drift)
    with pytest.raises(ValidationError, match="case IDs must be unique"):
        retrieval_dataset_model().model_validate(duplicate_id)
    with pytest.raises(
        ValidationError, match="resolved expected source identities require alternatives"
    ):
        retrieval_dataset_model().model_validate(missing_resolved_identity)
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        retrieval_dataset_model().model_validate(unknown_field)


def test_versioned_fixture_observations_cover_the_exact_thirty_dataset_cases() -> None:
    assert OBSERVATIONS_PATH.is_file(), "Issue #9 must provide versioned fixture observations"
    raw_observations = json.loads(OBSERVATIONS_PATH.read_text(encoding="utf-8"))
    dataset_case_ids = [case["id"] for case in load_raw_dataset()["cases"]]

    assert raw_observations["schema_version"] == "retrieval-observation-batch-v1"
    assert raw_observations["adapter_version"] == "fixture-retrieval-sut-v1"
    assert [item["case_id"] for item in raw_observations["observations"]] == dataset_case_ids


def test_retrieval_observation_batch_round_trips_and_rejects_rank_or_identity_drift() -> None:
    raw_observations = json.loads(OBSERVATIONS_PATH.read_text(encoding="utf-8"))

    document = retrieval_observation_batch_model().model_validate(raw_observations)

    assert document.model_dump(mode="json") == raw_observations

    duplicate_case = copy.deepcopy(raw_observations)
    duplicate_case["observations"][1]["case_id"] = duplicate_case["observations"][0]["case_id"]
    rank_drift = copy.deepcopy(raw_observations)
    rank_drift["observations"][4]["candidates"][1]["rank"] = 3
    unknown_field = copy.deepcopy(raw_observations)
    unknown_field["observations"][0]["candidates"][0]["unexpected"] = True

    with pytest.raises(ValidationError, match="retrieval observation case IDs must be unique"):
        retrieval_observation_batch_model().model_validate(duplicate_case)
    with pytest.raises(ValidationError, match="rank must equal one-based array order"):
        retrieval_observation_batch_model().model_validate(rank_drift)
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        retrieval_observation_batch_model().model_validate(unknown_field)
