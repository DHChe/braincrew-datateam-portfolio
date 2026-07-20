from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, cast

import pytest
from pydantic import ValidationError

from braincrew import contracts, grounded_contracts
from braincrew.dataset_registry import DatasetManifest, validate_dataset_bundle

DATASET_ROOT = Path(__file__).parents[2] / "datasets"
V1_MANIFEST_PATH = DATASET_ROOT / "dataset_manifest_v1.json"
V2_MANIFEST_PATH = DATASET_ROOT / "dataset_manifest_v2.json"
V2_PARSING_PATH = DATASET_ROOT / "parsing" / "parsing_cases_v2.json"
V2_RETRIEVAL_PATH = DATASET_ROOT / "retrieval" / "retrieval_cases_v2.json"
V2_GROUNDED_PATH = DATASET_ROOT / "grounded" / "grounded_cases_v2.json"

AX_AUTHORIZATION_ROLES = {"Executive", "HRAdmin", "HRPractitioner", "Employee"}
PERSONAS = {
    "executive",
    "hr_manager",
    "recruiter",
    "investigator",
    "employee",
    "manager",
    "interviewer",
    "it_admin",
}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return cast(dict[str, Any], payload)


def test_v2_bundle_is_new_and_v1_remains_frozen_and_valid() -> None:
    v1 = validate_dataset_bundle(V1_MANIFEST_PATH)

    assert v1.state == "VALID"
    assert v1.snapshot is not None
    assert v1.snapshot.manifest.dataset_version == "1.0.0"
    assert v1.snapshot.dataset_digest == (
        "sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b"
    )
    assert V2_MANIFEST_PATH.is_file()

    v2 = validate_dataset_bundle(V2_MANIFEST_PATH)

    assert v2.state == "VALID"
    assert v2.snapshot is not None
    assert v2.snapshot.manifest.schema_version == "dataset-manifest-v2"
    assert v2.snapshot.manifest.dataset_version == "2.0.0"
    assert v2.snapshot.dataset_digest != v1.snapshot.dataset_digest
    assert len(v2.snapshot.case_records) == 100


def test_v2_manifest_schema_rejects_a_different_dataset_version() -> None:
    payload = read_json(V2_MANIFEST_PATH)
    payload["dataset_version"] = "3.0.0"

    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(payload)


@pytest.mark.parametrize(
    ("path", "schema_version", "model_name"),
    (
        (V2_PARSING_PATH, "parsing-dataset-v2", "ParsingDatasetDocumentV2"),
        (V2_RETRIEVAL_PATH, "retrieval-dataset-v2", "RetrievalDatasetDocumentV2"),
        (V2_GROUNDED_PATH, "grounded-dataset-v2", "GroundedDatasetDocumentV2"),
    ),
)
def test_v2_components_strictly_separate_authorization_role_and_persona(
    path: Path,
    schema_version: str,
    model_name: str,
) -> None:
    payload = read_json(path)
    model = getattr(
        grounded_contracts if "Grounded" in model_name else contracts,
        model_name,
    )

    document = model.model_validate(payload)

    assert document.schema_version == schema_version
    assert payload["schema_version"] == schema_version
    for case in payload["cases"]:
        assert "role" not in case
        assert case["authorization_role"] in AX_AUTHORIZATION_ROLES
        assert case["persona"] in PERSONAS


def test_v2_contract_does_not_derive_authorization_from_persona() -> None:
    payload = read_json(V2_RETRIEVAL_PATH)
    original_authorization_role = payload["cases"][0]["authorization_role"]
    payload["cases"][0]["persona"] = "employee"

    document = contracts.RetrievalDatasetDocumentV2.model_validate(payload)

    assert document.cases[0].persona == "employee"
    assert document.cases[0].authorization_role == original_authorization_role


def test_v2_verification_roles_are_exact_ax_authorization_roles() -> None:
    retrieval = read_json(V2_RETRIEVAL_PATH)
    grounded = read_json(V2_GROUNDED_PATH)
    parsing = read_json(V2_PARSING_PATH)
    verification_roles = (
        {case["authorization_role"] for case in parsing["cases"] if case["split"] == "verification"}
        | {
            case["authorization_role"]
            for case in retrieval["cases"]
            if case["split"] == "verification"
        }
        | {
            case["authorization_role"]
            for case in grounded["cases"]
            if case["split"] == "Verification"
        }
    )

    assert verification_roles == {"Executive", "HRPractitioner", "Employee"}


@pytest.mark.parametrize(
    ("model", "payload"),
    (
        (
            lambda: contracts.ParsingDatasetDocumentV2,
            lambda: read_json(V2_PARSING_PATH),
        ),
        (
            lambda: contracts.RetrievalDatasetDocumentV2,
            lambda: read_json(V2_RETRIEVAL_PATH),
        ),
        (
            lambda: grounded_contracts.GroundedDatasetDocumentV2,
            lambda: read_json(V2_GROUNDED_PATH),
        ),
    ),
)
def test_v2_contract_rejects_legacy_or_unsupported_authorization_fields(
    model: Any,
    payload: Any,
) -> None:
    legacy = copy.deepcopy(payload())
    legacy["cases"][0]["role"] = legacy["cases"][0].pop("authorization_role")
    unsupported = copy.deepcopy(payload())
    unsupported["cases"][0]["authorization_role"] = "Manager"
    missing_persona = copy.deepcopy(payload())
    del missing_persona["cases"][0]["persona"]

    for invalid in (legacy, unsupported, missing_persona):
        with pytest.raises(ValidationError):
            model().model_validate(invalid)
