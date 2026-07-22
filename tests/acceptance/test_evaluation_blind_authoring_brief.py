import hashlib
import re
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BRIEF_PATH = REPOSITORY_ROOT / "docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md"
BRIEF_DIGEST_PATH = BRIEF_PATH.with_suffix(".sha256")
REVIEW_EVIDENCE_PATH = (
    REPOSITORY_ROOT
    / "docs/reviews/2026-07-22-braincrew-evaluation-corpus-v2-authoring-brief-leakage-review.md"
)
APPROVED_BRIEF_DIGEST = "sha256:121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3"
APPROVED_BRIEF_SIZE_BYTES = 10680
REVIEW_BASE_HEAD = "c387e2a0e44626db43c16d4fbbbffc33cbe110e4"
REPAIR_COMMIT = "0d4c0ae8876ad13d37acaa3bca81e2870c1d85d9"
CONTENT_SCHEMA_PATH = "schemas/ax-synthetic-seed-content-v1.schema.json"
CONTENT_SCHEMA_DIGEST = "sha256:372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb"
PACK_SCHEMA_PATH = "schemas/ax-synthetic-seed-pack-v1.schema.json"
PACK_SCHEMA_DIGEST = "sha256:4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa"
AX_ROLE_CONTRACT_REPOSITORY = "https://github.com/DHChe/AX_portfolio"
AX_ROLE_CONTRACT_REF = "47673b83a9fb431f2bad550781db18c7bee8b67e"
AX_ROLE_CONTRACT_PATH = "backend/src/ax_engine/seed/pack_contract.py"
AX_ROLE_CONTRACT_VERSION = "ax-synthetic-seed-content-v1"
AX_ROLE_CONTRACT_DIGEST = "sha256:09fe230ca2e976bec156d72987b5cf1f39419c34829e323222d11bef35e1fc2a"
ALLOWED_AX_VISIBILITY_ROLES = (
    "Executive",
    "HRAdmin",
    "HRPractitioner",
    "Employee",
)

REQUIRED_GENERIC_POLICY_SECTIONS = (
    "## Pinned AX schema contract",
    "## Generic HR/labor domain families",
    "## Source-authority guidance",
    "## Synthetic and demo policy",
    "## CC0 policy",
    "## Allowed AX visibility roles",
    "## Language bounds",
    "## Format bounds",
    "## Distractor policy",
    "## Independent review and authoring gate",
)

EVALUATION_DERIVED_HINT_PATTERNS = {
    "machine-readable evaluation fields": re.compile(
        r"\b(?:case_id|expected_(?:source_ids?|source_digests?|answer|evidence)|"
        r"case_to_answer|split_label)\b",
        re.IGNORECASE,
    ),
    "concrete case or query identifiers": re.compile(
        r"\b(?:case|query)[_-](?:[a-z]*\d+[a-z0-9_-]*|\d+)\b",
        re.IGNORECASE,
    ),
    "numeric benchmark results": re.compile(
        r"\b(?:score|accuracy|precision|recall|f1|mrr|ndcg|hits?@\d+)\s*[:=]\s*"
        r"\d+(?:\.\d+)?\b",
        re.IGNORECASE,
    ),
    "case-to-answer mapping tables": re.compile(
        r"^\s*\|\s*(?:case|query)(?:[_ -]?id)?\s*\|\s*"
        r"(?:expected[_ -]?)?(?:answer|evidence|source)",
        re.IGNORECASE | re.MULTILINE,
    ),
}


def _read_brief() -> str:
    assert BRIEF_PATH.is_file(), f"authoring brief is missing: {BRIEF_PATH}"
    return BRIEF_PATH.read_text(encoding="utf-8")


def _section_body(markdown: str, heading: str) -> str:
    _, separator, remainder = markdown.partition(heading)
    assert separator, f"missing required generic policy section: {heading}"
    return remainder.partition("\n## ")[0].strip()


def test_brief_pins_staged_content_schema_and_separates_import_schema() -> None:
    brief = _read_brief()
    normalized_brief = " ".join(brief.split())

    assert CONTENT_SCHEMA_PATH in brief
    assert CONTENT_SCHEMA_DIGEST in brief
    assert PACK_SCHEMA_PATH in brief
    assert PACK_SCHEMA_DIGEST in brief
    assert "The content schema governs staged `corpus-manifest.json` authoring." in normalized_brief
    assert (
        "The pack schema is separately labeled for the post-qualification "
        "`import-manifest.json` only." in normalized_brief
    )
    for heading in REQUIRED_GENERIC_POLICY_SECTIONS:
        assert _section_body(brief, heading), f"generic policy section is empty: {heading}"


def test_brief_pins_canonical_ax_role_contract() -> None:
    brief = _read_brief()

    required_contract_pins = (
        AX_ROLE_CONTRACT_REPOSITORY,
        AX_ROLE_CONTRACT_REF,
        AX_ROLE_CONTRACT_PATH,
        AX_ROLE_CONTRACT_VERSION,
        AX_ROLE_CONTRACT_DIGEST,
    )
    missing_contract_pins = [pin for pin in required_contract_pins if pin not in brief]
    assert not missing_contract_pins, (
        f"missing canonical AX role contract pins: {missing_contract_pins}"
    )


def test_brief_uses_exact_ax_visibility_role_vocabulary() -> None:
    role_section = _section_body(_read_brief(), "## Allowed AX visibility roles")

    documented_roles = set(re.findall(r"(?m)^- `([^`]+)`(?:\s|$)", role_section))
    assert documented_roles == set(ALLOWED_AX_VISIBILITY_ROLES), (
        "AX visibility roles must exactly match the canonical closed vocabulary; "
        f"found {sorted(documented_roles)}"
    )


def test_source_policy_requires_new_synthetic_cc0_reviewed_content_only() -> None:
    brief = _read_brief()
    synthetic_section = " ".join(_section_body(brief, "## Synthetic and demo policy").split())
    cc0_section = " ".join(_section_body(brief, "## CC0 policy").split())
    source_policy = f"{synthetic_section} {cc0_section}"
    required_contracts = (
        "Every future corpus source must be newly authored synthetic/demo content.",
        "This synthetic-only branch keeps pack-wide `synthetic=true` truthful.",
        "Every future corpus source must be licensed `CC0-1.0`.",
        (
            "Every future corpus source must have an independently reviewed provenance "
            "decision before it is eligible."
        ),
        "Missing or pending provenance must block authoring approval and pack inclusion.",
        (
            "Public-source ingestion or adaptation is prohibited in this version, including "
            "externally published `CC0-1.0` material."
        ),
    )
    prohibited_allowances = (
        "CC0 material may inform",
        "Clearly label adaptations.",
        "eligible, independently verified `CC0-1.0` source",
    )

    violations: dict[str, list[str]] = {}
    missing_contracts = [
        contract for contract in required_contracts if contract not in source_policy
    ]
    if missing_contracts:
        violations["missing synthetic-only source contracts"] = missing_contracts
    retained_allowances = [
        allowance for allowance in prohibited_allowances if allowance in source_policy
    ]
    if retained_allowances:
        violations["retained public-source allowances"] = retained_allowances

    assert not violations, f"source policy is not synthetic-only and fail-closed: {violations}"


def test_format_bounds_pin_canonical_text_bytes_and_source_paths() -> None:
    format_section = " ".join(_section_body(_read_brief(), "## Format bounds").split())
    required_format_contracts = (
        "Source bytes must be BOM-free UTF-8, use Unicode NFC normalization, and use "
        "LF-only line endings.",
        "Source paths must be normalized relative POSIX paths with no empty, `.`, or `..` "
        "segments.",
    )

    missing_contracts = [
        contract for contract in required_format_contracts if contract not in format_section
    ]
    assert not missing_contracts, (
        f"format bounds omit canonical AX constraints: {missing_contracts}"
    )


def test_brief_contains_no_evaluation_derived_identifiers_or_hints() -> None:
    brief = _read_brief()

    digests = set(re.findall(r"sha256:[0-9a-f]{64}", brief, flags=re.IGNORECASE))
    assert digests == {
        CONTENT_SCHEMA_DIGEST,
        PACK_SCHEMA_DIGEST,
        AX_ROLE_CONTRACT_DIGEST,
    }, (
        "only the reviewed AX schema and role-contract digests may appear in the brief; "
        f"found {sorted(digests)}"
    )

    leaked_hints = {
        label: sorted(set(pattern.findall(brief)))
        for label, pattern in EVALUATION_DERIVED_HINT_PATTERNS.items()
        if pattern.search(brief)
    }
    assert not leaked_hints, f"evaluation-derived identifiers or hints found: {leaked_hints}"


def test_approved_digest_lock_matches_the_exact_frozen_brief_bytes() -> None:
    brief_bytes = BRIEF_PATH.read_bytes()
    recomputed_digest = f"sha256:{hashlib.sha256(brief_bytes).hexdigest()}"

    assert recomputed_digest == APPROVED_BRIEF_DIGEST
    assert len(brief_bytes) == APPROVED_BRIEF_SIZE_BYTES
    assert BRIEF_DIGEST_PATH.is_file(), f"brief digest lock is missing: {BRIEF_DIGEST_PATH}"
    assert BRIEF_DIGEST_PATH.read_bytes() == f"{APPROVED_BRIEF_DIGEST}\n".encode("ascii")


def test_brief_defines_future_provenance_sidecar_and_blocks_issue_36() -> None:
    normalized_brief = " ".join(_read_brief().split())
    required_provenance_facts = (
        (
            "The current strict content and pack contracts do not preserve durable evidence "
            "of an independent per-source provenance approval."
        ),
        "The future provenance sidecar is create-only and remains outside the staged pack.",
        "sealed content digest",
        "per-source identifier and content digest",
        "synthetic origin",
        "authoring owner",
        "CC0 assignment",
        "reviewer identity, review date, timezone, and approve-or-reject decision",
        "receipt digest",
        (
            "Issue #36 remains blocked until sealer support for accepting, preserving, and "
            "replaying this evidence is separately implemented and tested."
        ),
        "This ticket creates no provenance sidecar or provenance receipt.",
    )
    missing_provenance_facts = [
        fact for fact in required_provenance_facts if fact not in normalized_brief
    ]
    assert not missing_provenance_facts, (
        f"provenance sidecar boundary is incomplete: {missing_provenance_facts}"
    )


def test_brief_requires_source_order_resolution_without_evaluation_feedback() -> None:
    normalized_brief = " ".join(_read_brief().split())
    required_source_order_facts = (
        (
            "Evaluation-blind authoring cannot be required to match an already-hidden exact "
            "evaluation source contract."
        ),
        "A separately approved source-order architecture resolution must choose either",
        "source-first evaluation freeze",
        "pre-existing, evaluation-independent exact source bytes or generator",
        (
            "Qualification feedback, evaluation identifiers, and evaluation digests must "
            "never enter authoring."
        ),
        "Issue #36 remains blocked until this architecture resolution is approved.",
    )
    missing_source_order_facts = [
        fact for fact in required_source_order_facts if fact not in normalized_brief
    ]
    assert not missing_source_order_facts, (
        f"source-order architecture boundary is incomplete: {missing_source_order_facts}"
    )

    assert (
        "Only the clean-commit and post-commit byte-equality gate remains **pending**."
        not in normalized_brief
    )


def test_brief_defers_exact_byte_approval_state_to_the_separate_review_record() -> None:
    opening = " ".join(_read_brief().partition("\n## ")[0].split())

    assert "pending" not in opening.casefold(), (
        f"brief opening must not embed time-dependent approval state: {opening}"
    )
    assert (
        "The approval state is authoritative only in the separate exact-byte leakage-review "
        "record." in opening
    )
    assert "Any change to these brief bytes requires a new exact-byte review." in opening


def test_independent_review_evidence_records_the_blind_boundary_and_completed_gate() -> None:
    assert REVIEW_EVIDENCE_PATH.is_file(), (
        f"independent review evidence is missing: {REVIEW_EVIDENCE_PATH}"
    )
    review = REVIEW_EVIDENCE_PATH.read_text(encoding="utf-8")
    normalized_review = " ".join(review.split())
    required_review_facts = (
        "Reviewer identity: `/root/sanitized_blind_reviewer`",
        "Reviewer role: `code-reviewer`",
        "Review date: `2026-07-23`",
        "Review timezone: `Asia/Seoul`",
        "Decision: **APPROVE**",
        "Material findings: **0**",
        f"Reviewed brief digest: `{APPROVED_BRIEF_DIGEST}`",
        f"Reviewed brief size: `{APPROVED_BRIEF_SIZE_BYTES} bytes`",
        f"Review base HEAD: `{REVIEW_BASE_HEAD}`",
        "Reviewed source policy: **newly authored synthetic/demo content only**.",
        "Reviewed license policy: **every source uses `CC0-1.0`**.",
        (
            "Reviewed provenance policy: **independently reviewed for every source; missing "
            "or pending blocks authoring**."
        ),
        (
            "Public-source ingestion or adaptation: **prohibited, including externally "
            "published `CC0-1.0` material**."
        ),
        "Pack-wide `synthetic=true`: **preserved by the synthetic-only branch**.",
        (
            "Reviewed staged schema: **the content schema governs staged "
            "`corpus-manifest.json` authoring**."
        ),
        (
            "Reviewed post-qualification schema: **the pack schema governs only the later "
            "`import-manifest.json`**."
        ),
        (
            "Current strict provenance evidence: **not durable; `provenance_status` alone "
            "does not preserve independent approval evidence**."
        ),
        (
            "Future provenance sidecar: **create-only, outside the staged pack, and not "
            "created by Issue #35**."
        ),
        (
            "Evaluation feedback boundary: **qualification feedback, evaluation identifiers, "
            "and evaluation digests cannot enter authoring**."
        ),
    )
    missing_review_facts = [fact for fact in required_review_facts if fact not in normalized_review]
    assert not missing_review_facts, (
        f"independent review evidence omits required facts: {missing_review_facts}"
    )

    allowed_sources = _section_body(review, "## Allowed review sources")
    required_allowed_sources = (
        "`AGENTS.md`",
        "GitHub Issue `#35` body",
        "`schemas/ax-synthetic-seed-content-v1.schema.json`",
        "`schemas/ax-synthetic-seed-content-v1.schema.sha256`",
        "`schemas/ax-synthetic-seed-pack-v1.schema.json`",
        "`schemas/ax-synthetic-seed-pack-v1.schema.sha256`",
        "`pyproject.toml` and `uv.lock` execution settings",
        "current Issue #35 authoring brief",
        (f"`git show {AX_ROLE_CONTRACT_REF}:{AX_ROLE_CONTRACT_PATH}` from `AX_portfolio`"),
    )
    missing_allowed_sources = [
        source for source in required_allowed_sources if source not in allowed_sources
    ]
    assert not missing_allowed_sources, (
        f"review evidence omits allowed source boundaries: {missing_allowed_sources}"
    )
    assert "tests/" not in allowed_sources

    prohibited_sources = _section_body(review, "## Prohibited review sources")
    required_prohibited_sources = (
        "`datasets/**`",
        "`tests/fixtures/**`",
        "evaluation cases, queries, answers, evidence, scores, or split labels",
        "benchmark artifacts or results",
        "PR `#29`",
        "`feat/issue-15-live-verification`",
        "Braincrew `corpus_sealing.py`",
        "Braincrew `corpus_qualification.py`",
        "`tests/**`",
        "the adjacent brief digest and all pre-existing leakage-review evidence",
        "Git history, diffs, or pull-request review material",
        "downstream design, draft, interview, or status documents",
    )
    missing_prohibited_sources = [
        source for source in required_prohibited_sources if source not in prohibited_sources
    ]
    assert not missing_prohibited_sources, (
        f"review evidence omits prohibited source boundaries: {missing_prohibited_sources}"
    )

    issue_36_blockers = " ".join(_section_body(review, "## Issue #36 blockers").split())
    required_issue_36_blockers = (
        (
            "Source-order architecture: **blocked** until a separately approved resolution "
            "chooses a source-first evaluation freeze or pre-existing, evaluation-independent "
            "exact source bytes or generator."
        ),
        (
            "Provenance-sidecar sealer support: **blocked** until accepting, preserving, and "
            "replaying the sidecar evidence is separately implemented and tested."
        ),
        "This exact-byte approval clears neither Issue #36 blocker.",
    )
    missing_issue_36_blockers = [
        blocker for blocker in required_issue_36_blockers if blocker not in issue_36_blockers
    ]
    assert not missing_issue_36_blockers, (
        f"review evidence omits Issue #36 blockers: {missing_issue_36_blockers}"
    )

    completed_gate = " ".join(_section_body(review, "## Completed post-commit gate").split())
    required_gate_statements = (
        "Approval applies only to the reviewed brief bytes.",
        f"Repaired-brief clean commit: `{REPAIR_COMMIT}`.",
        "Post-commit byte-equality verification: **PASS**.",
        f"Verified committed brief digest: `{APPROVED_BRIEF_DIGEST}`.",
        f"Verified committed brief size: `{APPROVED_BRIEF_SIZE_BYTES} bytes`.",
        (
            "The committed brief bytes at the repaired-brief clean commit match the reviewed "
            "digest and size."
        ),
        (
            "Corpus authoring remains blocked by Issue #46, Issue #47, and a separate "
            "data-creation proposal gate."
        ),
    )
    missing_gate_statements = [
        statement for statement in required_gate_statements if statement not in completed_gate
    ]
    assert not missing_gate_statements, (
        f"review evidence omits the completed post-commit gate: {missing_gate_statements}"
    )


def test_authoring_gate_requires_digest_bound_independent_review_evidence() -> None:
    gate_section = _section_body(_read_brief(), "## Independent review and authoring gate")
    normalized_gate = " ".join(gate_section.split())

    required_gate = (
        "The independent review evidence must record the exact brief SHA-256 and a post-commit "
        "byte-equality verification before corpus authoring may open."
    )
    assert required_gate in normalized_gate
