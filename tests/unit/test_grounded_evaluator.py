from __future__ import annotations

import hashlib
import json

from braincrew import grounded_evaluator
from braincrew.grounded_contracts import (
    GroundedCase,
    GroundedCaseEvaluation,
    GroundedCitation,
    GroundedObservation,
    SourceTextResolution,
)


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


def evidence(group_id: str, record_id: str, text: str, matcher: str) -> dict[str, object]:
    return {
        "group_id": group_id,
        "alternatives": [
            {
                "record_kind": "company_rule",
                "record_id": record_id,
                "evidence_span_id": f"span-{record_id}",
                "source_text_digest": digest(text),
                "source_matcher": {"kind": "literal", "pattern": matcher},
            }
        ],
    }


SUPPORT_TEXT = "제15조: 즉시 해고는 금지됩니다."
CONTRADICT_TEXT = "제20조: 긴급한 경우 즉시 해고할 수 있습니다."


def proposition(
    proposition_id: str,
    matcher: str,
    *,
    modality: str = "must_not",
    forbidden: bool = False,
    conclusive: bool = True,
    support_record: str = "rule-15",
    support_text: str = SUPPORT_TEXT,
    support_matcher: str = "즉시 해고는 금지됩니다",
    contradict_record: str = "rule-20",
    contradict_text: str = CONTRADICT_TEXT,
    contradict_matcher: str = "즉시 해고할 수 있습니다",
) -> dict[str, object]:
    return {
        "proposition_id": proposition_id,
        "subject": "immediate dismissal",
        "predicate": "is",
        "object": modality,
        "polarity": "affirmed",
        "modality": modality,
        "risk_level": "high",
        "conclusive": conclusive,
        "forbidden": forbidden,
        "allowed_answer_modes": ["direct_grounded", "conditional_grounded"],
        "surface_matchers": [
            {
                "kind": "literal",
                "pattern": matcher,
                "matcher_digest": matcher_digest("literal", matcher),
            }
        ],
        "supporting_evidence_groups": [
            evidence("support", support_record, support_text, support_matcher)
        ],
        "contradicting_evidence_groups": [
            evidence("contradict", contradict_record, contradict_text, contradict_matcher)
        ],
    }


def grounded_case(
    propositions: list[dict[str, object]],
    *,
    risk_level: str = "standard",
    required_output_paths: tuple[str, ...] = (),
) -> GroundedCase:
    return GroundedCase.model_validate(
        {
            "case_id": "GA-001",
            "split": "Verification",
            "risk_level": risk_level,
            "query": "즉시 해고할 수 있나요?",
            "role": "hr_manager",
            "expected_answer_mode": "direct_grounded",
            "required_output_paths": required_output_paths,
            "propositions": propositions,
            "applicability": {
                "claim_support_precision": True,
                "citation_precision": True,
                "citation_coverage": True,
            },
        }
    )


def citation(record_id: str, text: str, path: str = "summary") -> GroundedCitation:
    return GroundedCitation(
        record_kind="company_rule",
        record_id=record_id,
        evidence_span_id=f"span-{record_id}",
        source_text_digest=digest(text),
        claim_paths=(path,),
    )


def source(record_id: str, text: str) -> SourceTextResolution:
    return SourceTextResolution(
        record_kind="company_rule",
        record_id=record_id,
        text=text,
        source_text_digest=digest(text),
    )


def observation(
    *,
    summary: str,
    answer: str = "",
    grounds: tuple[str, ...] = (),
    review_points: tuple[str, ...] = (),
    additional_checks: tuple[str, ...] = (),
    risk_warning: str = "",
    citations: tuple[GroundedCitation, ...] = (),
    source_texts: tuple[SourceTextResolution, ...] = (),
    answer_mode: str = "direct_grounded",
) -> GroundedObservation:
    return GroundedObservation.model_validate(
        {
            "case_id": "GA-001",
            "available": True,
            "error": None,
            "answer_mode": answer_mode,
            "structured_answer": {
                "summary": summary,
                "answer": answer,
                "grounds": grounds,
                "review_points": review_points,
                "additional_checks": additional_checks,
                "risk_warning": risk_warning,
            },
            "citations": citations,
            "source_texts": source_texts,
        }
    )


def evaluate(case: GroundedCase, observed: GroundedObservation) -> GroundedCaseEvaluation:
    assert hasattr(grounded_evaluator, "evaluate_grounded_case"), (
        "grounded evaluator is not implemented"
    )
    return grounded_evaluator.evaluate_grounded_case(case, observed)


def test_supported_claim_requires_matching_source_text_and_exact_path_citation() -> None:
    case = grounded_case([proposition("dismissal-prohibited", "즉시 해고는 금지됩니다")])
    observed = observation(
        summary="즉시 해고는 금지됩니다.",
        citations=(citation("rule-15", SUPPORT_TEXT),),
        source_texts=(source("rule-15", SUPPORT_TEXT),),
    )

    result = evaluate(case, observed)

    assert result.atom_evaluations[0].outcome == "supported"
    assert result.claim_support_precision.exact == "1/1"
    assert result.citation_precision.exact == "1/1"
    assert result.citation_coverage.exact == "1/1"


def test_same_path_support_and_contradiction_cannot_cancel_each_other() -> None:
    case = grounded_case([proposition("dismissal-prohibited", "즉시 해고는 금지됩니다")])
    observed = observation(
        summary="즉시 해고는 금지됩니다.",
        citations=(
            citation("rule-15", SUPPORT_TEXT),
            citation("rule-20", CONTRADICT_TEXT),
        ),
        source_texts=(source("rule-15", SUPPORT_TEXT), source("rule-20", CONTRADICT_TEXT)),
    )

    result = evaluate(case, observed)

    assert result.atom_evaluations[0].outcome == "contradicted"
    assert "A-CONTRADICTED-CLAIM" in result.atom_evaluations[0].failure_codes
    assert result.claim_support_precision.exact == "0/1"
    assert result.citation_precision.exact == "1/2"


def test_unmapped_and_ambiguous_atoms_remain_in_the_claim_denominator() -> None:
    single = proposition("dismissal-prohibited", "즉시 해고는 금지됩니다")
    duplicate = proposition("dismissal-prohibited-duplicate", "즉시 해고는 금지됩니다")

    unmapped = evaluate(grounded_case([single]), observation(summary="관련 규정을 확인하세요."))
    ambiguous = evaluate(
        grounded_case([single, duplicate]),
        observation(summary="즉시 해고는 금지됩니다."),
    )

    assert unmapped.atom_evaluations[0].outcome == "unmapped"
    assert unmapped.atom_evaluations[0].failure_codes == ("A-UNMAPPED-CLAIM",)
    assert unmapped.claim_support_precision.exact == "0/1"
    assert ambiguous.atom_evaluations[0].outcome == "ambiguous"
    assert ambiguous.atom_evaluations[0].failure_codes == ("A-AMBIGUOUS-CLAIM",)
    assert ambiguous.claim_support_precision.exact == "0/1"


def test_negated_or_permitted_forbidden_proposition_fails_closed_at_high_risk() -> None:
    allowed = proposition(
        "dismissal-allowed",
        "즉시 해고할 수 있습니다",
        modality="may",
        forbidden=True,
        support_record="rule-20",
        support_text=CONTRADICT_TEXT,
        support_matcher="즉시 해고할 수 있습니다",
        contradict_record="rule-15",
        contradict_text=SUPPORT_TEXT,
        contradict_matcher="즉시 해고는 금지됩니다",
    )
    case = grounded_case([allowed], risk_level="high")
    observed = observation(
        summary="즉시 해고할 수 있습니다.",
        citations=(citation("rule-15", SUPPORT_TEXT),),
        source_texts=(source("rule-15", SUPPORT_TEXT),),
    )

    result = evaluate(case, observed)

    assert result.atom_evaluations[0].proposition_id == "dismissal-allowed"
    assert result.atom_evaluations[0].outcome == "contradicted"
    assert "A-FORBIDDEN-PROPOSITION" in result.failure_codes
    assert "A-UNSUPPORTED-HIGH-RISK-CONCLUSION" in result.failure_codes
    assert result.hard_failure_atom_ids == (result.atom_evaluations[0].atom.stable_identity,)


def test_required_missing_path_and_non_high_risk_additional_check_keep_denominators() -> None:
    safe = proposition("dismissal-prohibited", "즉시 해고는 금지됩니다")
    check = proposition(
        "check-collective-agreement",
        "단체협약도 확인해야 합니다",
        modality="must",
        conclusive=False,
    )
    case = grounded_case([safe, check], required_output_paths=("answer",))
    observed = observation(
        summary="즉시 해고는 금지됩니다.",
        additional_checks=("단체협약도 확인해야 합니다.",),
        citations=(citation("rule-15", SUPPORT_TEXT),),
        source_texts=(source("rule-15", SUPPORT_TEXT),),
    )

    result = evaluate(case, observed)

    assert [item.outcome for item in result.atom_evaluations] == [
        "supported",
        "unsupported",
        "missing_required",
    ]
    assert result.claim_support_precision.exact == "1/3"
    assert result.citation_coverage.exact == "1/3"
    assert result.hard_failure_atom_ids == ()


def test_missing_required_path_cannot_gain_coverage_from_a_dangling_citation() -> None:
    case = grounded_case(
        [proposition("dismissal-prohibited", "즉시 해고는 금지됩니다")],
        required_output_paths=("answer",),
    )
    observed = observation(
        summary="즉시 해고는 금지됩니다.",
        citations=(
            citation("rule-15", SUPPORT_TEXT),
            citation("rule-20", CONTRADICT_TEXT, path="answer"),
        ),
        source_texts=(source("rule-15", SUPPORT_TEXT), source("rule-20", CONTRADICT_TEXT)),
    )

    result = evaluate(case, observed)

    assert result.citation_coverage.exact == "1/2"


def test_high_risk_unmapped_atom_and_disallowed_answer_mode_fail_closed() -> None:
    case = grounded_case(
        [proposition("dismissal-prohibited", "즉시 해고는 금지됩니다")],
        risk_level="high",
    )
    observed = observation(
        summary="즉시 해고는 금지됩니다. 다른 절차도 가능합니다.",
        citations=(citation("rule-15", SUPPORT_TEXT),),
        source_texts=(source("rule-15", SUPPORT_TEXT),),
        answer_mode="review_required",
    )

    result = evaluate(case, observed)

    assert [item.outcome for item in result.atom_evaluations] == ["unsupported", "unmapped"]
    assert result.claim_support_precision.exact == "0/2"
    assert "A-UNSUPPORTED-HIGH-RISK-CONCLUSION" in result.failure_codes
    assert len(result.hard_failure_atom_ids) == 2


def test_matching_citation_identity_is_not_support_without_resolved_source_match() -> None:
    case = grounded_case(
        [
            proposition(
                "dismissal-prohibited",
                "즉시 해고는 금지됩니다",
                support_matcher="존재하지 않는 근거 문구",
            )
        ]
    )
    observed = observation(
        summary="즉시 해고는 금지됩니다.",
        citations=(citation("rule-15", SUPPORT_TEXT),),
        source_texts=(source("rule-15", SUPPORT_TEXT),),
    )

    result = evaluate(case, observed)

    assert result.atom_evaluations[0].outcome == "unsupported"
    assert result.atom_evaluations[0].failure_codes == ("A-UNSUPPORTED-CLAIM",)
    assert result.claim_support_precision.exact == "0/1"
    assert result.citation_precision.exact == "0/1"


def test_high_risk_source_resolution_failure_preserves_critical_identity() -> None:
    case = grounded_case(
        [
            proposition(
                "dismissal-prohibited",
                "즉시 해고는 금지됩니다",
                support_matcher="존재하지 않는 근거 문구",
            )
        ],
        risk_level="high",
    )
    observed = observation(
        summary="즉시 해고는 금지됩니다.",
        citations=(citation("rule-15", SUPPORT_TEXT),),
        source_texts=(source("rule-15", SUPPORT_TEXT),),
    )

    result = evaluate(case, observed)

    assert result.atom_evaluations[0].outcome == "unsupported"
    assert result.atom_evaluations[0].failure_codes == (
        "A-UNSUPPORTED-CLAIM",
        "A-UNSUPPORTED-HIGH-RISK-CONCLUSION",
    )
    assert result.hard_failure_atom_ids == (result.atom_evaluations[0].atom.stable_identity,)
