from __future__ import annotations

import copy
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import BaseModel, ValidationError

from braincrew import contracts

DATASET_PATH = Path(__file__).parents[2] / "datasets" / "parsing" / "parsing_cases_v1.json"
OBSERVATIONS_PATH = Path(__file__).parents[1] / "fixtures" / "parsing_observations_v1.json"


def load_raw_dataset() -> dict[str, Any]:
    assert DATASET_PATH.is_file(), "Issue #8 must provide the versioned parsing dataset"
    return cast(dict[str, Any], json.loads(DATASET_PATH.read_text(encoding="utf-8")))


def parsing_dataset_model() -> type[BaseModel]:
    model = getattr(contracts, "ParsingDatasetDocument", None)
    assert model is not None, "Issue #8 must define the strict parsing dataset contract"
    return cast(type[BaseModel], model)


def test_parsing_dataset_freezes_twenty_cases_and_the_fourteen_six_split() -> None:
    dataset = load_raw_dataset()

    assert dataset["schema_version"] == "parsing-dataset-v1"
    assert dataset["dataset"] == {
        "id": "braincrew-parsing-quality",
        "version": "1.0.0",
        "corpus_id": "synthetic-hr-v1",
    }
    assert dataset["provenance"] == {
        "source_type": "synthetic",
        "license": "CC0-1.0",
    }
    assert len(dataset["cases"]) == 20
    assert Counter(case["split"] for case in dataset["cases"]) == {
        "calibration": 14,
        "verification": 6,
    }
    assert len({case["id"] for case in dataset["cases"]}) == 20


def test_each_parsing_case_has_reviewable_ground_truth_for_every_metric_family() -> None:
    dataset = load_raw_dataset()

    for case in dataset["cases"]:
        assert case["primary_focus"] == "parsing"
        assert case["document"]["id"]
        assert case["document"]["version"] == "1.0.0"
        assert case["document"]["canonical_text"]
        assert case["expected"]["evidence_spans"]
        assert case["expected"]["structure"]["headings"]
        assert case["expected"]["metadata"]
        assert case["provenance"]["source_type"] == "synthetic"
        assert case["provenance"]["license"] == "CC0-1.0"
        assert case["review"]["status"] == "reviewed"

    verification_cases = [case for case in dataset["cases"] if case["split"] == "verification"]
    assert len(verification_cases) == 6
    assert all(case["expected"]["evidence_spans"] for case in verification_cases)


def test_expected_evidence_spans_freeze_unicode_offsets_and_source_digest() -> None:
    dataset = load_raw_dataset()

    for case in dataset["cases"]:
        canonical_text = case["document"]["canonical_text"]
        source_digest = f"sha256:{hashlib.sha256(canonical_text.encode('utf-8')).hexdigest()}"
        for span in case["expected"]["evidence_spans"]:
            assert span["source_text_digest"] == source_digest
            assert canonical_text[span["start_char"] : span["end_char"]] == span["text"]


def test_parsing_dataset_round_trips_through_a_strict_versioned_contract() -> None:
    document = parsing_dataset_model().model_validate(load_raw_dataset())

    assert document.model_dump(mode="json") == load_raw_dataset()


def test_parsing_dataset_contract_rejects_split_drift_and_duplicate_case_ids() -> None:
    split_drift = copy.deepcopy(load_raw_dataset())
    split_drift["cases"][13]["split"] = "verification"
    duplicate_id = copy.deepcopy(load_raw_dataset())
    duplicate_id["cases"][1]["id"] = duplicate_id["cases"][0]["id"]

    with pytest.raises(ValidationError, match="14 calibration and 6 verification"):
        parsing_dataset_model().model_validate(split_drift)
    with pytest.raises(ValidationError, match="case IDs must be unique"):
        parsing_dataset_model().model_validate(duplicate_id)


def test_parsing_dataset_contract_rejects_tampered_span_and_unknown_fields() -> None:
    tampered_span = copy.deepcopy(load_raw_dataset())
    tampered_span["cases"][0]["expected"]["evidence_spans"][0]["start_char"] += 1
    unknown_field = copy.deepcopy(load_raw_dataset())
    unknown_field["cases"][0]["unexpected"] = True

    with pytest.raises(ValidationError, match="EvidenceSpan text and Unicode offsets"):
        parsing_dataset_model().model_validate(tampered_span)
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        parsing_dataset_model().model_validate(unknown_field)


def test_versioned_fixture_observations_cover_the_exact_twenty_dataset_cases() -> None:
    assert OBSERVATIONS_PATH.is_file(), "Issue #8 must provide versioned fixture observations"
    raw_observations = json.loads(OBSERVATIONS_PATH.read_text(encoding="utf-8"))
    observations = contracts.ParsingObservationBatch.model_validate(raw_observations)
    dataset_case_ids = [case["id"] for case in load_raw_dataset()["cases"]]

    assert observations.adapter_version == "fixture-parsing-sut-v1"
    assert observations.parser_version == "fixture-parser-v1"
    assert [observation.case_id for observation in observations.observations] == dataset_case_ids
