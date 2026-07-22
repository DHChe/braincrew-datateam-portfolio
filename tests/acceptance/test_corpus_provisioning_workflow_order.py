from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESIGN_PATH = (
    PROJECT_ROOT
    / "docs/superpowers/specs/2026-07-20-independent-evaluation-corpus-provisioning-design.md"
)
CANONICAL_DESIGN_PATH = (
    PROJECT_ROOT / "docs/superpowers/specs/2026-07-18-evidence-first-evaluation-plane-design.md"
)
ISSUE_DRAFT_PATH = (
    PROJECT_ROOT
    / "docs/superpowers/specs/2026-07-21-independent-evaluation-corpus-provisioning-issue-draft.md"
)
INTERVIEW_PATH = PROJECT_ROOT / "docs/interview/braincrew-data-portfolio-defense.md"
STATUS_PATH = PROJECT_ROOT / "docs/status/braincrew-delivery-workflow.md"

CONTENT_SCHEMA_DIGEST = "372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb"
PACK_SCHEMA_DIGEST = "4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa"
APPROVED_BRIEF_DIGEST = "121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3"
ISSUE_47_MERGE_COMMIT = "4d80b9b8950f4d7356a9aa9806f492ae79126dab"
DATA_CREATION_APPROVAL_BASE = "5cec187af3e2d5b95b35f6e6f81fee55a73d5409"
AUTHORING_OWNER = "codex-issue-36-authoring-agent"
PROVENANCE_REVIEWER = "DHChe-corpus-provenance-reviewer"
AUTHORING_ROOT = "/Users/astralpig/braincrew-issue-36-authoring"
AUTHORIZATION_RECORD = f"{AUTHORING_ROOT}/authorization/data-creation-authorization.json"
TOOL_PATH = f"{AUTHORING_ROOT}/tool/author-corpus"
STAGING_PATH = f"{AUTHORING_ROOT}/staging"
AUTHORING_RECEIPT_PATH = f"{AUTHORING_ROOT}/receipts/authoring-independence-receipt.json"
PROVENANCE_SIDECAR_PATH = f"{AUTHORING_ROOT}/review/provenance-review.json"
SEALED_OUTPUT_PATH = f"{AUTHORING_ROOT}/sealed"
SCHEMA_DECLARATION_DIGEST = "c9dae9c47ce20f2e4b5c954dbd467e051ebf33081e13a033cc23f9b418897dff"
INPUT_INVENTORY_DIGEST = "e707333d28fb9452b2823d1b6c125a1b6dcc3a0d5b118069e8bf7b502854061e"


def _section(document: str, heading: str, next_heading: str) -> str:
    return document.split(heading, maxsplit=1)[1].split(next_heading, maxsplit=1)[0]


def test_issue_35_commit_and_ax_36_proof_converge_only_before_operator_load() -> None:
    design = DESIGN_PATH.read_text(encoding="utf-8")
    execution_order = _section(
        design,
        "## 11. Execution and stop order",
        "### Issue #31 schema-sealing implementation lock",
    )
    progress = _section(
        design,
        "## 14. Implementation progress checkpoint",
        "## 15. Completion criteria",
    )

    assert "The required sequence is:" not in execution_order
    assert (
        "The operator path below records dependency and convergence gates, not a strict start "
        "order:" in execution_order
    )
    assert "Braincrew #35's only blocker is Braincrew #32" not in execution_order
    assert "PR #45 review discovered two" in execution_order
    assert "Braincrew Issue #36 remains blocked" in execution_order
    assert "AX #36 may proceed independently of the Braincrew #35 commit lane" in execution_order
    assert "AX #36 must be complete before operator load" in execution_order
    assert execution_order.index("require AX #36") < execution_order.index(
        "perform the approved atomic AX load"
    )

    assert "AX #36 remains open" in progress
    assert "Braincrew #35 is closed after PR #45 merged" in progress


def test_issue_36_data_creation_gate_is_approved_for_a_new_session() -> None:
    design = DESIGN_PATH.read_text(encoding="utf-8")
    issue_draft = ISSUE_DRAFT_PATH.read_text(encoding="utf-8")
    interview = INTERVIEW_PATH.read_text(encoding="utf-8")
    status = STATUS_PATH.read_text(encoding="utf-8")
    normalized_design = " ".join(design.split())

    for document in (design, issue_draft, interview):
        normalized_document = " ".join(document.split())
        assert "schemas/ax-synthetic-seed-content-v1.schema.json" in document
        assert CONTENT_SCHEMA_DIGEST in document
        assert "schemas/ax-synthetic-seed-pack-v1.schema.json" in document
        assert PACK_SCHEMA_DIGEST in document
        assert "source-first evaluation freeze" in document
        assert "Issue #47" in normalized_document

    approved_gate_facts = (
        "Data-creation proposal gate: **APPROVED_FOR_NEW_SESSION**.",
        f"Approval baseline: `{DATA_CREATION_APPROVAL_BASE}`.",
        f"Authoring owner: `{AUTHORING_OWNER}`.",
        f"Manual provenance reviewer: `{PROVENANCE_REVIEWER}`.",
        f"External lifecycle root: `{AUTHORING_ROOT}`.",
        "Create-only authorization record:",
        "`corpus-data-creation-authorization-v1`",
        (
            "No source byte may be created before the clean execution SHA and external authoring "
            "tool SHA-256 are recorded"
        ),
        (
            "authoring brief, content schema, schema digest declaration, and canonical "
            "input-digest inventory"
        ),
        "Author, then review, then seal, then replay",
        "No automatic retry",
        "RED contract tests must first prove",
    )
    exact_targets = (
        AUTHORIZATION_RECORD,
        TOOL_PATH,
        STAGING_PATH,
        AUTHORING_RECEIPT_PATH,
        PROVENANCE_SIDECAR_PATH,
        SEALED_OUTPUT_PATH,
    )
    exact_inputs = (
        (
            "docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md",
            APPROVED_BRIEF_DIGEST,
        ),
        ("schemas/ax-synthetic-seed-content-v1.schema.json", CONTENT_SCHEMA_DIGEST),
        (
            "schemas/ax-synthetic-seed-content-v1.schema.sha256",
            SCHEMA_DECLARATION_DIGEST,
        ),
        ("input-digests.json", INPUT_INVENTORY_DIGEST),
    )
    authorization_bindings = (
        "approval authority",
        "exact execution SHA",
        "authoring-tool SHA-256",
        "four exact input digests",
        "all lifecycle target paths",
    )
    for document in (design, interview, status):
        normalized_document = " ".join(document.split())
        normalized_casefold = normalized_document.casefold()
        missing_facts = [
            fact
            for fact in approved_gate_facts
            if " ".join(fact.split()) not in normalized_document
        ]
        assert not missing_facts, (
            f"Issue #36 approved data-creation gate is incomplete: {missing_facts}"
        )
        assert AUTHORING_OWNER != PROVENANCE_REVIEWER
        assert "must differ from the authoring owner" in normalized_document
        missing_targets = [target for target in exact_targets if target not in document]
        assert not missing_targets, f"Issue #36 lifecycle targets are incomplete: {missing_targets}"
        for input_path, input_digest in exact_inputs:
            assert input_path in document
            assert input_digest in document
        missing_bindings = [
            binding for binding in authorization_bindings if binding not in normalized_document
        ]
        assert not missing_bindings, (
            f"Issue #36 authorization record bindings are incomplete: {missing_bindings}"
        )
        assert "authorization record is create-only" in normalized_casefold
        assert "launch must reject any authorization-record mismatch" in normalized_casefold
        assert "staging target must be empty" in normalized_casefold
        assert "all other create-only targets must be absent" in normalized_casefold
        assert "all targets must be outside the repository and must not be symbolic links" in (
            normalized_casefold
        )
        assert "independence receipt and provenance sidecar are create-only" in normalized_casefold
        assert "manual reviewer approves every exact source digest" in normalized_casefold
        assert "before any source-byte authoring attempt" in normalized_casefold
        assert normalized_document.index("Author, then review, then seal, then replay") < (
            normalized_document.index("qualification remains")
        )
        for stop_condition in (
            "non-empty staging",
            "existing target",
            "nonzero authoring exit",
            "manual rejection",
            "sealing failure",
            "replay failure",
        ):
            assert stop_condition in normalized_casefold

    assert "provenance sidecar" in design
    assert "sealer support for accepting, preserving, and replaying" in normalized_design
    assert "provenance sidecar" in issue_draft
    assert "provenance sidecar" in interview
    normalized_interview = " ".join(interview.split())
    assert "post-commit byte equality is **PASS**" in normalized_interview
    assert (
        "PR #49 merged Issue #47 into `develop` as `4d80b9b8950f4d7356a9aa9806f492ae79126dab`"
        in normalized_interview
    )
    assert "checks succeeded, and Issue #47 is closed" in normalized_interview
    assert "The separate data-creation proposal gate must still pass" not in normalized_interview
    assert "remains blocked until post-commit byte equality passes" not in normalized_interview

    assert "Issue #47 repaired staged authoring to expose the content schema" in normalized_design
    assert "The merged launcher still requires Issue #47 repair" not in normalized_design
    assert "PR #49 merged and verified Issue #47" in normalized_design
    normalized_issue_draft = " ".join(issue_draft.split())
    assert "Issue #47 is merged and verified" in normalized_issue_draft
    assert "Issue #36 remains blocked until sealer support can accept" not in normalized_issue_draft
    assert "blocked until sealer support" not in normalized_issue_draft
    assert (
        "#47 and the separate data-creation proposal gate are complete"
        not in normalized_issue_draft
    )

    execution_order = _section(
        design,
        "## 11. Execution and stop order",
        "### Issue #31 schema-sealing implementation lock",
    )
    assert "in a fresh restricted context, run Braincrew #36" in execution_order
    assert "qualification feedback" in execution_order


def test_canonical_design_records_the_issue_47_sealing_and_authoring_boundary() -> None:
    design = CANONICAL_DESIGN_PATH.read_text(encoding="utf-8")
    normalized_design = " ".join(design.split())

    assert "corpus-sealing-receipt-v2" in design
    assert "provenance-review.json" in design
    assert "corpus-sealing-receipt-v1" in design
    assert "emits a create-only `corpus-sealing-receipt-v1`" not in design
    assert "Historical Historical" not in normalized_design
    assert "ax-synthetic-seed-content-v1.schema.json" in design
    assert "The later `ax-synthetic-seed-pack-v1.schema.json` is not mounted" in normalized_design
    assert (
        "requires a clean Braincrew Git source, one committed approved brief, the Issue #31 "
        "digest-pinned AX pack schema"
    ) not in normalized_design


def test_issue_47_documents_independent_review_and_portable_replay() -> None:
    documents = (
        CANONICAL_DESIGN_PATH.read_text(encoding="utf-8"),
        INTERVIEW_PATH.read_text(encoding="utf-8"),
        STATUS_PATH.read_text(encoding="utf-8"),
    )

    for document in documents:
        normalized_document = " ".join(document.split()).casefold()
        assert "reviewer identity must differ from the authoring owner" in normalized_document
        assert (
            "replay validates canonical bytes and digest independent of normalized filesystem "
            "write bits"
        ) in normalized_document


def test_issue_46_locks_source_first_freeze_and_successor_version_boundary() -> None:
    documents = (
        DESIGN_PATH.read_text(encoding="utf-8"),
        ISSUE_DRAFT_PATH.read_text(encoding="utf-8"),
        INTERVIEW_PATH.read_text(encoding="utf-8"),
        STATUS_PATH.read_text(encoding="utf-8"),
    )
    required_contract_facts = (
        "Selected source-order contract: **source-first evaluation freeze**.",
        (
            "Rejected alternative: pre-existing, evaluation-independent exact source bytes or "
            "generator."
        ),
        (
            "Reason: no independently versioned, provenance-bearing artifact predates the "
            "evaluation-specific freeze."
        ),
        (
            "Failure mode: frozen evaluation identifiers, digests, or qualification feedback "
            "reach authoring."
        ),
        (
            "`braincrew-evaluation-dataset@2.0.0` remains immutable and is not a target for "
            "authoring or qualification in this lane."
        ),
        (
            "A successor dataset version greater than `2.0.0` is required after the new corpus "
            "version is sealed."
        ),
        (
            "The successor qualification receipt must bind that successor dataset version and "
            "digest to the unchanged sealed corpus digest."
        ),
        (
            "Qualification remains read-only and cannot return feedback, identifiers, or digests "
            "to authoring."
        ),
    )

    for document in documents:
        normalized_document = " ".join(document.split())
        missing_facts = [
            fact
            for fact in required_contract_facts
            if " ".join(fact.split()) not in normalized_document
        ]
        assert not missing_facts, f"Issue #46 source-first contract is incomplete: {missing_facts}"

    design = documents[0]
    execution_order = _section(
        design,
        "## 11. Execution and stop order",
        "### Issue #31 schema-sealing implementation lock",
    )
    assert "freeze the successor evaluation dataset" in execution_order
    assert (
        "cross-validate the unchanged sealed pack against the successor dataset" in execution_order
    )

    current_checkpoint = _section(documents[3], "## Current checkpoint", "## Transition history")
    assert "Completed predecessor: PR #49 merged Issue #47" in current_checkpoint
    assert "Issue #46 is `CLOSED` after PR #48" in current_checkpoint
    assert (
        "Issue #36 remains `BLOCKED` only until this approval record is merged"
        in current_checkpoint
    )
    assert "Issue #47" in current_checkpoint
    assert "APPROVED_FOR_NEW_SESSION" in current_checkpoint
    assert "still has no `ready-for-agent` label" in current_checkpoint


def test_issue_46_removes_dataset_v2_from_the_future_seal_to_qualification_path() -> None:
    design = DESIGN_PATH.read_text(encoding="utf-8")
    issue_draft = ISSUE_DRAFT_PATH.read_text(encoding="utf-8")
    design_cross_validation = _section(
        design,
        "## 7. Post-seal cross-validation",
        "## 8. Parsing mapping and principal recovery",
    )
    issue_solution = _section(issue_draft, "## Solution", "## User Stories")
    normalized_design = " ".join(design.split())
    normalized_issue_solution = " ".join(issue_solution.split())

    assert "successor evaluation dataset freeze" in design
    assert "cross-validator <---- successor dataset, read only" in design
    assert "both the pack and the successor dataset" in design_cross_validation
    assert "both the pack and dataset v2" not in design_cross_validation
    assert "bind the sealed corpus digest to dataset v2" not in design_cross_validation
    assert "successor dataset version and successful cross-validation receipt" in normalized_design

    assert "successor dataset frozen after sealing" in normalized_issue_solution
    assert "binds the unchanged corpus digest to that successor dataset version and digest" in (
        normalized_issue_solution
    )
    assert "compares the immutable pack with dataset v2" not in issue_solution


def test_delivery_status_records_the_published_review_repair_and_new_frontier() -> None:
    status = STATUS_PATH.read_text(encoding="utf-8")
    current_checkpoint = _section(status, "## Current checkpoint", "## Transition history")

    assert "Last updated: 2026-07-23" in status
    assert ISSUE_47_MERGE_COMMIT in current_checkpoint
    assert APPROVED_BRIEF_DIGEST in current_checkpoint
    assert "10,680-byte brief" in current_checkpoint
    assert "`/root/sanitized_blind_reviewer`" in current_checkpoint
    assert "`/root/fresh_blind_final_review`" not in current_checkpoint
    assert "PR #48" in current_checkpoint
    assert "Issue #46" in current_checkpoint
    assert "Issue #47" in current_checkpoint
    assert (
        "Issue #36 remains `BLOCKED` only until this approval record is merged"
        in current_checkpoint
    )
    assert "7 passed" in current_checkpoint
    assert "publish this status-only commit" not in current_checkpoint

    assert "8,531-byte brief" not in current_checkpoint
    assert "only the clean-commit" not in current_checkpoint.casefold()
