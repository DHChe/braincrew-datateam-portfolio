from __future__ import annotations

import hashlib
import importlib
import json
from types import ModuleType

import pytest
from pydantic import ValidationError


def contracts_module() -> ModuleType:
    try:
        return importlib.import_module("braincrew.grounded_contracts")
    except ModuleNotFoundError:
        pytest.fail("claim-proposition-v1 contracts are not implemented")


def digest(text: str) -> str:
    return f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"


def matcher_digest(kind: str, pattern: str) -> str:
    payload = json.dumps(
        {"kind": kind, "pattern": pattern},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return digest(payload)


def evidence(group_id: str, text: str) -> dict[str, object]:
    return {
        "group_id": group_id,
        "alternatives": [
            {
                "record_kind": "company_rule",
                "record_id": "rule-15",
                "evidence_span_id": f"span-{group_id}",
                "source_text_digest": digest(text),
                "source_matcher": {"kind": "literal", "pattern": "즉시 해고는 금지됩니다"},
            }
        ],
    }


def case_payload() -> dict[str, object]:
    supporting_text = "제15조: 즉시 해고는 금지됩니다."
    contradicting_text = "제20조: 긴급한 경우 즉시 해고할 수 있습니다."
    return {
        "case_id": "GA-001",
        "split": "Verification",
        "risk_level": "high",
        "query": "즉시 해고할 수 있나요?",
        "role": "hr_manager",
        "expected_answer_mode": "direct_grounded",
        "required_output_paths": ["summary", "answer", "risk_warning"],
        "propositions": [
            {
                "proposition_id": "dismissal-immediate-prohibited",
                "subject": "immediate dismissal",
                "predicate": "is",
                "object": "prohibited",
                "polarity": "affirmed",
                "modality": "must_not",
                "risk_level": "high",
                "conclusive": True,
                "forbidden": False,
                "allowed_answer_modes": ["direct_grounded", "conditional_grounded"],
                "surface_matchers": [
                    {
                        "kind": "literal",
                        "pattern": "즉시 해고는 금지됩니다",
                        "matcher_digest": matcher_digest("literal", "즉시 해고는 금지됩니다"),
                    }
                ],
                "supporting_evidence_groups": [evidence("support", supporting_text)],
                "contradicting_evidence_groups": [evidence("contradict", contradicting_text)],
            },
            {
                "proposition_id": "dismissal-immediate-allowed",
                "subject": "immediate dismissal",
                "predicate": "is",
                "object": "allowed",
                "polarity": "affirmed",
                "modality": "may",
                "risk_level": "high",
                "conclusive": True,
                "forbidden": True,
                "allowed_answer_modes": ["direct_grounded"],
                "surface_matchers": [
                    {
                        "kind": "literal",
                        "pattern": "즉시 해고할 수 있습니다",
                        "matcher_digest": matcher_digest("literal", "즉시 해고할 수 있습니다"),
                    }
                ],
                "supporting_evidence_groups": [evidence("contradict", contradicting_text)],
                "contradicting_evidence_groups": [evidence("support", supporting_text)],
            },
        ],
        "applicability": {
            "claim_support_precision": True,
            "citation_precision": True,
            "citation_coverage": True,
        },
    }


def dataset_payload() -> dict[str, object]:
    return {
        "schema_version": "grounded-dataset-v1",
        "dataset_id": "braincrew-grounded-answer-initial",
        "dataset_version": "1.0.0",
        "case_count": 1,
        "proposition_contract_version": "claim-proposition-v1",
        "traversal_contract_version": "claim-traversal-v1",
        "normalizer_version": "claim-normalizer-v1",
        "source_resolution_version": "source-text-resolution-v1",
        "cases": [case_payload()],
        "provenance": {
            "source_kind": "synthetic",
            "license": "CC0-1.0",
            "review_status": "reviewed",
        },
    }


def test_claim_proposition_contract_preserves_polarity_modality_and_allowed_modes() -> None:
    contracts = contracts_module()

    dataset = contracts.GroundedDatasetDocument.model_validate(dataset_payload())
    proposition = dataset.cases[0].propositions[0]

    assert proposition.polarity == "affirmed"
    assert proposition.modality == "must_not"
    assert proposition.allowed_answer_modes == ("direct_grounded", "conditional_grounded")
    assert (
        proposition.supporting_evidence_groups[0]
        .alternatives[0]
        .source_text_digest.startswith("sha256:")
    )


def test_claim_proposition_contract_uses_canonical_modality_and_matcher_identity() -> None:
    contracts = contracts_module()
    payload = case_payload()["propositions"][0].copy()  # type: ignore[index]
    payload.pop("object")
    payload["modality"] = "must_not"
    payload["forbidden_answer_modes"] = ["insufficient_evidence"]
    payload["surface_matchers"] = [
        {
            "kind": "literal",
            "pattern": "즉시 해고는 금지됩니다",
            "matcher_digest": matcher_digest("literal", "즉시 해고는 금지됩니다"),
        }
    ]

    proposition = contracts.ClaimProposition.model_validate(payload)

    assert proposition.object is None
    assert proposition.modality == "must_not"
    assert proposition.forbidden_answer_modes == ("insufficient_evidence",)
    assert proposition.surface_matchers[0].matcher_digest.startswith("sha256:")


def test_case_authors_cannot_narrow_claim_traversal_paths() -> None:
    contracts = contracts_module()
    payload = dataset_payload()
    payload["cases"][0]["traversal_paths"] = ["summary"]  # type: ignore[index]

    with pytest.raises(ValidationError, match="traversal_paths"):
        contracts.GroundedDatasetDocument.model_validate(payload)


def test_required_output_paths_reject_unknown_or_wildcard_only_paths() -> None:
    contracts = contracts_module()
    payload = dataset_payload()
    payload["cases"][0]["required_output_paths"] = ["grounds[*]"]  # type: ignore[index]

    with pytest.raises(ValidationError, match="required_output_paths"):
        contracts.GroundedDatasetDocument.model_validate(payload)


def test_source_text_resolution_rejects_digest_drift() -> None:
    contracts = contracts_module()

    with pytest.raises(ValidationError, match="source text digest"):
        contracts.SourceTextResolution(
            record_kind="company_rule",
            record_id="rule-15",
            text="제15조: 즉시 해고는 금지됩니다.",
            source_text_digest=digest("다른 원문"),
        )


def test_grounded_observation_requires_unique_case_identities() -> None:
    contracts = contracts_module()
    observation = {
        "case_id": "GA-001",
        "available": True,
        "error": None,
        "answer_mode": "direct_grounded",
        "structured_answer": {
            "summary": "즉시 해고는 금지됩니다.",
            "answer": "즉시 해고는 금지됩니다.",
            "grounds": [],
            "review_points": [],
            "additional_checks": [],
            "risk_warning": "",
        },
        "citations": [],
        "source_texts": [],
    }

    with pytest.raises(ValidationError, match="unique"):
        contracts.GroundedObservationBatch(
            schema_version="grounded-observation-batch-v1",
            adapter_version="fixture-grounded-sut-v1",
            sut_commit_sha="a" * 40,
            observations=[observation, observation],
        )


def test_grounded_metric_contract_rejects_impossible_or_mismatched_scores() -> None:
    contracts = contracts_module()

    with pytest.raises(ValidationError, match="grounded metric"):
        contracts.GroundedMetricScore(
            numerator=2,
            denominator=1,
            exact="2/1",
            value="2",
            display="2.0000",
        )

    with pytest.raises(ValidationError, match="grounded metric"):
        contracts.GroundedMetricScore(
            numerator=1,
            denominator=2,
            exact="1/2",
            value="0.5",
            display="0.9999",
        )
