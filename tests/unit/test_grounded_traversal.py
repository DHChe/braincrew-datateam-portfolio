from __future__ import annotations

import importlib
from types import ModuleType

import pytest


def grounded_module() -> ModuleType:
    try:
        return importlib.import_module("braincrew.grounded_evaluator")
    except ModuleNotFoundError:
        pytest.fail("claim-traversal-v1 is not implemented")


def contracts_module() -> ModuleType:
    try:
        return importlib.import_module("braincrew.grounded_contracts")
    except ModuleNotFoundError:
        pytest.fail("claim-proposition-v1 contracts are not implemented")


def test_claim_normalization_is_deterministic_without_erasing_negation_or_modality() -> None:
    grounded = grounded_module()

    normalized = grounded.normalize_claim_text("  즉시\r\n  해고하면   안   됩니다. e\u0301  ")

    assert normalized == "즉시\n해고하면 안 됩니다. é"


def test_claim_traversal_enumerates_every_generated_output_path() -> None:
    grounded = grounded_module()
    contracts = contracts_module()
    answer = contracts.GroundedStructuredAnswer(
        summary="요약입니다.",
        answer="답변입니다!",
        grounds=["근거 하나입니다。", "근거 둘입니다？"],
        review_points=["검토 사항입니다?"],
        additional_checks=["추가 확인입니다！"],
        risk_warning="위험 경고입니다.",
    )

    atoms = grounded.traverse_claims(answer, required_output_paths=())

    assert [atom.claim_path for atom in atoms] == [
        "summary",
        "answer",
        "grounds[0]",
        "grounds[1]",
        "review_points[0]",
        "additional_checks[0]",
        "risk_warning",
    ]
    assert all(atom.atom_index == 0 for atom in atoms)
    assert all(atom.placeholder is False for atom in atoms)


def test_claim_atom_identity_uses_path_index_and_normalized_text_digest() -> None:
    grounded = grounded_module()
    contracts = contracts_module()
    answer = contracts.GroundedStructuredAnswer(
        summary="동일한 주장. 동일한 주장.",
        answer="",
        grounds=[],
        review_points=[],
        additional_checks=[],
        risk_warning="",
    )

    first_run = grounded.traverse_claims(answer, required_output_paths=())
    second_run = grounded.traverse_claims(answer, required_output_paths=())

    assert first_run == second_run
    assert [atom.atom_index for atom in first_run] == [0, 1]
    assert first_run[0].normalized_text_digest == first_run[1].normalized_text_digest
    assert first_run[0].stable_identity != first_run[1].stable_identity


def test_missing_required_output_path_adds_one_zero_score_placeholder() -> None:
    grounded = grounded_module()
    contracts = contracts_module()
    answer = contracts.GroundedStructuredAnswer(
        summary="요약입니다.",
        answer="",
        grounds=[],
        review_points=[],
        additional_checks=[],
        risk_warning="",
    )

    atoms = grounded.traverse_claims(
        answer,
        required_output_paths=("answer", "risk_warning"),
    )

    assert [(atom.claim_path, atom.placeholder) for atom in atoms] == [
        ("summary", False),
        ("answer", True),
        ("risk_warning", True),
    ]
