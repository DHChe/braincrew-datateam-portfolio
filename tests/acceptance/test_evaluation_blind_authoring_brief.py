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
APPROVED_BRIEF_DIGEST = "sha256:f21f5df1950ec0872e45c956f9c689b09c59362d2cae53dbd2f86635bbb690ae"
APPROVED_BRIEF_SIZE_BYTES = 8531
REVIEW_BASE_HEAD = "67d7c104757f60194e59df20240ac47f8be9c027"
SCHEMA_PATH = "schemas/ax-synthetic-seed-pack-v1.schema.json"
SCHEMA_DIGEST = "sha256:4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa"
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


def test_brief_pins_reviewed_schema_and_defines_only_generic_policy_sections() -> None:
    brief = _read_brief()

    assert SCHEMA_PATH in brief
    assert SCHEMA_DIGEST in brief
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
    assert digests == {SCHEMA_DIGEST, AX_ROLE_CONTRACT_DIGEST}, (
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


def test_brief_records_exact_byte_approval_and_only_post_commit_gate_pending() -> None:
    normalized_brief = " ".join(_read_brief().split())
    required_state_facts = (
        "Independent exact-byte review approval: **recorded**.",
        (
            "The accompanying `.sha256` digest file and independent leakage-review record "
            "hold the approved brief-byte lock."
        ),
        "Only the clean-commit and post-commit byte-equality gate remains **pending**.",
    )
    obsolete_state_phrases = (
        "pending independent review",
        "This brief has no digest lock yet",
        "Gate status: **pending**",
        "reviewed commit",
        "does not create a brief digest lock",
        "or a brief digest lock",
    )

    violations: dict[str, list[str]] = {}
    missing_state_facts = [fact for fact in required_state_facts if fact not in normalized_brief]
    if missing_state_facts:
        violations["missing current approval and gate state"] = missing_state_facts

    retained_obsolete_phrases = [
        phrase for phrase in obsolete_state_phrases if phrase in normalized_brief
    ]
    if retained_obsolete_phrases:
        violations["retained obsolete pre-review state"] = retained_obsolete_phrases

    assert not violations, f"authoring brief approval state is stale: {violations}"


def test_independent_review_evidence_records_the_blind_boundary_and_pending_gate() -> None:
    assert REVIEW_EVIDENCE_PATH.is_file(), (
        f"independent review evidence is missing: {REVIEW_EVIDENCE_PATH}"
    )
    review = REVIEW_EVIDENCE_PATH.read_text(encoding="utf-8")
    normalized_review = " ".join(review.split())
    required_review_facts = (
        "Reviewer identity: `/root/code_reviewer_license_fix`",
        "Reviewer role: `code-reviewer`",
        "Review date: `2026-07-22`",
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
    )
    missing_review_facts = [fact for fact in required_review_facts if fact not in normalized_review]
    assert not missing_review_facts, (
        f"independent review evidence omits required facts: {missing_review_facts}"
    )

    allowed_sources = _section_body(review, "## Allowed review sources")
    required_allowed_sources = (
        "`AGENTS.md`",
        "GitHub Issue `#35` body",
        "`schemas/ax-synthetic-seed-pack-v1.schema.json`",
        "`schemas/ax-synthetic-seed-pack-v1.schema.sha256`",
        "`pyproject.toml` and `uv.lock` execution settings",
        "current Issue #35 authoring brief",
        "`tests/acceptance/test_evaluation_blind_authoring_brief.py`",
        (f"`git show {AX_ROLE_CONTRACT_REF}:{AX_ROLE_CONTRACT_PATH}` from `AX_portfolio`"),
    )
    missing_allowed_sources = [
        source for source in required_allowed_sources if source not in allowed_sources
    ]
    assert not missing_allowed_sources, (
        f"review evidence omits allowed source boundaries: {missing_allowed_sources}"
    )

    prohibited_sources = _section_body(review, "## Prohibited review sources")
    required_prohibited_sources = (
        "`datasets/**`",
        "`tests/fixtures/**`",
        "evaluation content or results",
        "PR `#29`",
        "`feat/issue-15-live-verification`",
        "Braincrew `corpus_sealing.py`",
        "later design, draft, interview, or status documents",
    )
    missing_prohibited_sources = [
        source for source in required_prohibited_sources if source not in prohibited_sources
    ]
    assert not missing_prohibited_sources, (
        f"review evidence omits prohibited source boundaries: {missing_prohibited_sources}"
    )

    pending_gate = " ".join(_section_body(review, "## Pending post-commit gate").split())
    required_gate_statements = (
        "Approval applies only to the reviewed brief bytes.",
        "Post-commit byte-equality verification: **pending**.",
        (
            "Corpus authoring remains blocked until the brief reaches a clean committed "
            "Braincrew SHA and the committed brief bytes match the approved digest."
        ),
    )
    missing_gate_statements = [
        statement for statement in required_gate_statements if statement not in pending_gate
    ]
    assert not missing_gate_statements, (
        f"review evidence omits the pending post-commit gate: {missing_gate_statements}"
    )


def test_authoring_gate_requires_digest_bound_independent_review_evidence() -> None:
    gate_section = _section_body(_read_brief(), "## Independent review and authoring gate")
    normalized_gate = " ".join(gate_section.split())

    required_gate = (
        "The independent review evidence must record the exact brief SHA-256 and a post-commit "
        "byte-equality verification before corpus authoring may open."
    )
    assert required_gate in normalized_gate
