from __future__ import annotations

import hashlib
import re
import unicodedata
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, Literal

from braincrew.grounded_contracts import (
    ClaimAtom,
    ClaimAtomEvaluation,
    ClaimOutcome,
    ClaimProposition,
    EvidenceAlternative,
    GroundedCase,
    GroundedCaseEvaluation,
    GroundedCitation,
    GroundedMetricScore,
    GroundedObservation,
    GroundedStructuredAnswer,
    SourceTextResolution,
    SurfaceMatcher,
)

CLAIM_TRAVERSAL_VERSION: Final[Literal["claim-traversal-v1"]] = "claim-traversal-v1"
CLAIM_ATOMIZER_VERSION: Final[Literal["claim-atomizer-v1"]] = "claim-atomizer-v1"
CLAIM_NORMALIZER_VERSION: Final[Literal["claim-normalizer-v1"]] = "claim-normalizer-v1"
CLAIM_MATCHER_SET_VERSION: Final[Literal["claim-matcher-set-v1"]] = "claim-matcher-set-v1"
CLAIM_PROPOSITION_VERSION: Final[Literal["claim-proposition-v1"]] = "claim-proposition-v1"
PROPOSITION_CATALOG_VERSION: Final[Literal["claim-proposition-catalog-v1"]] = (
    "claim-proposition-catalog-v1"
)
SOURCE_RESOLUTION_VERSION: Final[Literal["source-text-resolution-v1"]] = "source-text-resolution-v1"
HIGH_RISK_GUARD_VERSION: Final[Literal["high-risk-guard-v1"]] = "high-risk-guard-v1"
GROUNDED_EVALUATOR_VERSION: Final[Literal["grounded-answer-v1"]] = "grounded-answer-v1"

_ATOM_BOUNDARY = re.compile(r"[\n.?!。？！]+")
_INLINE_WHITESPACE = re.compile(r"[^\S\n]+")


def normalize_claim_text(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))
    lines = [_INLINE_WHITESPACE.sub(" ", line).strip() for line in normalized.split("\n")]
    return "\n".join(lines).strip()


def _text_digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _generated_values(answer: GroundedStructuredAnswer) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = [
        ("summary", answer.summary),
        ("answer", answer.answer),
    ]
    values.extend((f"grounds[{index}]", value) for index, value in enumerate(answer.grounds))
    values.extend(
        (f"review_points[{index}]", value) for index, value in enumerate(answer.review_points)
    )
    values.extend(
        (f"additional_checks[{index}]", value)
        for index, value in enumerate(answer.additional_checks)
    )
    values.append(("risk_warning", answer.risk_warning))
    return tuple(values)


def traverse_claims(
    answer: GroundedStructuredAnswer,
    *,
    required_output_paths: tuple[str, ...],
) -> tuple[ClaimAtom, ...]:
    atoms: list[ClaimAtom] = []
    populated_paths: set[str] = set()
    for claim_path, value in _generated_values(answer):
        normalized = normalize_claim_text(value)
        parts = [part.strip() for part in _ATOM_BOUNDARY.split(normalized) if part.strip()]
        if parts:
            populated_paths.add(claim_path)
        for atom_index, part in enumerate(parts):
            digest = _text_digest(part)
            atoms.append(
                ClaimAtom(
                    claim_path=claim_path,
                    atom_index=atom_index,
                    normalized_text=part,
                    normalized_text_digest=digest,
                    stable_identity=f"{claim_path}:{atom_index}:{digest}",
                )
            )
    for claim_path in required_output_paths:
        if claim_path not in populated_paths:
            digest = _text_digest("")
            atoms.append(
                ClaimAtom(
                    claim_path=claim_path,
                    atom_index=0,
                    normalized_text="",
                    normalized_text_digest=digest,
                    stable_identity=f"{claim_path}:0:{digest}",
                    placeholder=True,
                )
            )
    return tuple(atoms)


def _surface_matches(matcher: SurfaceMatcher, normalized_atom: str) -> bool:
    if matcher.kind == "literal":
        return normalize_claim_text(matcher.pattern) == normalized_atom
    return re.fullmatch(matcher.pattern, normalized_atom) is not None


def _source_matches(matcher: SurfaceMatcher, source_text: str) -> bool:
    if matcher.kind == "literal":
        return normalize_claim_text(matcher.pattern) in normalize_claim_text(source_text)
    return re.search(matcher.pattern, normalize_claim_text(source_text)) is not None


def _citation_identity(citation: GroundedCitation) -> tuple[str, str, str, str]:
    return (
        citation.record_kind,
        citation.record_id,
        citation.evidence_span_id,
        citation.source_text_digest,
    )


def _alternative_identity(alternative: EvidenceAlternative) -> tuple[str, str, str, str]:
    return (
        alternative.record_kind,
        alternative.record_id,
        alternative.evidence_span_id,
        alternative.source_text_digest,
    )


def _resolved_source(
    alternative: EvidenceAlternative,
    sources: tuple[SourceTextResolution, ...],
) -> bool:
    for source in sources:
        if (
            source.record_kind == alternative.record_kind
            and source.record_id == alternative.record_id
            and source.source_text_digest == alternative.source_text_digest
            and _source_matches(alternative.source_matcher, source.text)
        ):
            return True
    return False


def _citation_matches_alternative(
    citation: GroundedCitation,
    alternative: EvidenceAlternative,
    sources: tuple[SourceTextResolution, ...],
) -> bool:
    return _citation_identity(citation) == _alternative_identity(alternative) and _resolved_source(
        alternative, sources
    )


def _citation_matches_groups(
    citation: GroundedCitation,
    proposition: ClaimProposition,
    sources: tuple[SourceTextResolution, ...],
    *,
    contradicting: bool,
) -> bool:
    groups = (
        proposition.contradicting_evidence_groups
        if contradicting
        else proposition.supporting_evidence_groups
    )
    return any(
        _citation_matches_alternative(citation, alternative, sources)
        for group in groups
        for alternative in group.alternatives
    )


def _metric(numerator: int, denominator: int) -> GroundedMetricScore:
    value = Decimal(0) if denominator == 0 else Decimal(numerator) / Decimal(denominator)
    display = value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
    return GroundedMetricScore(
        numerator=numerator,
        denominator=denominator,
        exact=f"{numerator}/{denominator}",
        value=str(value),
        display=f"{display:.4f}",
    )


def _matched_propositions(
    atom: ClaimAtom,
    propositions: tuple[ClaimProposition, ...],
) -> tuple[ClaimProposition, ...]:
    if atom.placeholder:
        return ()
    return tuple(
        proposition
        for proposition in propositions
        if any(
            _surface_matches(matcher, atom.normalized_text)
            for matcher in proposition.surface_matchers
        )
    )


def evaluate_grounded_case(
    case: GroundedCase,
    observation: GroundedObservation,
) -> GroundedCaseEvaluation:
    if observation.case_id != case.case_id or not observation.available:
        return GroundedCaseEvaluation(
            evaluator_version=GROUNDED_EVALUATOR_VERSION,
            proposition_contract_version=CLAIM_PROPOSITION_VERSION,
            traversal_contract_version=CLAIM_TRAVERSAL_VERSION,
            normalizer_version=CLAIM_NORMALIZER_VERSION,
            source_resolution_version=SOURCE_RESOLUTION_VERSION,
            guard_version=HIGH_RISK_GUARD_VERSION,
            case_id=case.case_id,
            state="INVALID",
            atom_evaluations=(),
            claim_support_precision=_metric(0, 0),
            citation_precision=_metric(0, 0),
            citation_coverage=_metric(0, 0),
            failure_codes=("SYS-GROUNDED-OBSERVATION-INVALID",),
            hard_failure_atom_ids=(),
        )

    atoms = traverse_claims(
        observation.structured_answer,
        required_output_paths=case.required_output_paths,
    )
    atom_evaluations: list[ClaimAtomEvaluation] = []
    failures: list[str] = []
    hard_failure_atom_ids: list[str] = []
    unique_citations: dict[tuple[str, str, str, str], GroundedCitation] = {}
    for citation in observation.citations:
        identity = _citation_identity(citation)
        if identity in unique_citations:
            prior = unique_citations[identity]
            unique_citations[identity] = prior.model_copy(
                update={
                    "claim_paths": tuple(dict.fromkeys((*prior.claim_paths, *citation.claim_paths)))
                }
            )
        else:
            unique_citations[identity] = citation

    atom_matches: dict[str, tuple[ClaimProposition, ...]] = {}
    supported_count = 0
    for atom in atoms:
        matched = _matched_propositions(atom, case.propositions)
        atom_matches[atom.stable_identity] = matched
        proposition_id: str | None = matched[0].proposition_id if len(matched) == 1 else None
        atom_failures: list[str] = []
        outcome: ClaimOutcome
        if atom.placeholder:
            outcome = "missing_required"
            atom_failures.append("A-REQUIRED-OUTPUT-MISSING")
        elif not matched:
            outcome = "unmapped"
            atom_failures.append("A-UNMAPPED-CLAIM")
        elif len(matched) > 1:
            outcome = "ambiguous"
            atom_failures.append("A-AMBIGUOUS-CLAIM")
        else:
            proposition = matched[0]
            path_citations = tuple(
                citation
                for citation in unique_citations.values()
                if atom.claim_path in citation.claim_paths
            )
            has_support = any(
                _citation_matches_groups(
                    citation,
                    proposition,
                    observation.source_texts,
                    contradicting=False,
                )
                for citation in path_citations
            )
            has_contradiction = any(
                _citation_matches_groups(
                    citation,
                    proposition,
                    observation.source_texts,
                    contradicting=True,
                )
                for citation in path_citations
            )
            if proposition.forbidden:
                atom_failures.append("A-FORBIDDEN-PROPOSITION")
            if has_contradiction:
                outcome = "contradicted"
                atom_failures.append("A-CONTRADICTED-CLAIM")
            elif (
                not has_support
                or observation.answer_mode not in proposition.allowed_answer_modes
                or proposition.forbidden
            ):
                outcome = "unsupported"
                atom_failures.append("A-UNSUPPORTED-CLAIM")
            else:
                outcome = "supported"
                supported_count += 1

        high_risk_failure = False
        if case.risk_level == "high":
            if outcome in {"unmapped", "ambiguous", "missing_required"}:
                high_risk_failure = True
            elif len(matched) == 1 and matched[0].conclusive and outcome != "supported":
                high_risk_failure = True
            if len(matched) == 1 and matched[0].conclusive and matched[0].forbidden:
                high_risk_failure = True
        if high_risk_failure:
            atom_failures.append("A-UNSUPPORTED-HIGH-RISK-CONCLUSION")
            hard_failure_atom_ids.append(atom.stable_identity)
        for failure in atom_failures:
            if failure not in failures:
                failures.append(failure)
        atom_evaluations.append(
            ClaimAtomEvaluation(
                atom=atom,
                outcome=outcome,
                proposition_id=proposition_id,
                failure_codes=tuple(dict.fromkeys(atom_failures)),
            )
        )

    precise_citations = 0
    existing_paths = {atom.claim_path for atom in atoms}
    generated_paths = {atom.claim_path for atom in atoms if not atom.placeholder}
    for citation in unique_citations.values():
        precise = False
        for atom in atoms:
            matched = atom_matches[atom.stable_identity]
            if (
                atom.claim_path in citation.claim_paths
                and atom.claim_path in existing_paths
                and len(matched) == 1
                and _citation_matches_groups(
                    citation,
                    matched[0],
                    observation.source_texts,
                    contradicting=False,
                )
            ):
                precise = True
                break
        if precise:
            precise_citations += 1

    cited_paths = {
        path
        for citation in unique_citations.values()
        for path in citation.claim_paths
        if path in generated_paths
    }
    return GroundedCaseEvaluation(
        evaluator_version=GROUNDED_EVALUATOR_VERSION,
        proposition_contract_version=CLAIM_PROPOSITION_VERSION,
        traversal_contract_version=CLAIM_TRAVERSAL_VERSION,
        normalizer_version=CLAIM_NORMALIZER_VERSION,
        source_resolution_version=SOURCE_RESOLUTION_VERSION,
        guard_version=HIGH_RISK_GUARD_VERSION,
        case_id=case.case_id,
        state="COMPLETED",
        atom_evaluations=tuple(atom_evaluations),
        claim_support_precision=_metric(supported_count, len(atoms)),
        citation_precision=_metric(precise_citations, max(1, len(unique_citations))),
        citation_coverage=_metric(len(cited_paths), len(existing_paths)),
        failure_codes=tuple(failures),
        hard_failure_atom_ids=tuple(dict.fromkeys(hard_failure_atom_ids)),
    )
