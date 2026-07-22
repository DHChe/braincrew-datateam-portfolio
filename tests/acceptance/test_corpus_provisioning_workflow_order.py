from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESIGN_PATH = (
    PROJECT_ROOT
    / "docs/superpowers/specs/2026-07-20-independent-evaluation-corpus-provisioning-design.md"
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
REPAIR_COMMIT = "0d4c0ae8876ad13d37acaa3bca81e2870c1d85d9"


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


def test_issue_36_stays_blocked_on_authoring_contract_repairs() -> None:
    design = DESIGN_PATH.read_text(encoding="utf-8")
    issue_draft = ISSUE_DRAFT_PATH.read_text(encoding="utf-8")
    interview = INTERVIEW_PATH.read_text(encoding="utf-8")
    normalized_design = " ".join(design.split())

    for document in (design, issue_draft, interview):
        normalized_document = " ".join(document.split())
        assert "schemas/ax-synthetic-seed-content-v1.schema.json" in document
        assert CONTENT_SCHEMA_DIGEST in document
        assert "schemas/ax-synthetic-seed-pack-v1.schema.json" in document
        assert PACK_SCHEMA_DIGEST in document
        assert "source-first evaluation freeze" in document
        assert "Issue #36 remains blocked" in document
        assert "current Issue #32 launcher" in normalized_document

    assert "provenance sidecar" in design
    assert "sealer support for accepting, preserving, and replaying" in design
    assert "provenance sidecar" in issue_draft
    assert "provenance sidecar" in interview
    normalized_interview = " ".join(interview.split())
    assert "post-commit byte equality is **PASS**" in normalized_interview
    assert "Issue #46, Issue #47, and the separate data-creation proposal gate remain" in (
        normalized_interview
    )
    assert "remains blocked until post-commit byte equality passes" not in normalized_interview

    assert "The current Issue #32 launcher still copies the pack schema" in normalized_design
    assert "the launcher was pinned to" not in normalized_design
    assert "must be repaired in a separate prerequisite before Issue #36" in normalized_design

    execution_order = _section(
        design,
        "## 11. Execution and stop order",
        "### Issue #31 schema-sealing implementation lock",
    )
    assert "in a fresh restricted context, run Braincrew #36" not in execution_order
    assert "qualification feedback" in execution_order


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
    assert "Active canonical phase: Issue #46 implementation" in current_checkpoint
    assert "Issue #36 is `BLOCKED`" in current_checkpoint
    assert "Issue #47" in current_checkpoint
    assert "separate data-creation proposal gate" in current_checkpoint
    assert "Issue #36 is `BLOCKED`, has no `ready-for-agent` label" in current_checkpoint


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
    assert REPAIR_COMMIT in current_checkpoint
    assert APPROVED_BRIEF_DIGEST in current_checkpoint
    assert "10,680-byte brief" in current_checkpoint
    assert "`/root/sanitized_blind_reviewer`" in current_checkpoint
    assert "`/root/fresh_blind_final_review`" not in current_checkpoint
    assert "PR #45" in current_checkpoint
    assert "Issue #46" in current_checkpoint
    assert "Issue #47" in current_checkpoint
    assert "Issue #36 is `BLOCKED`" in current_checkpoint
    assert "308 passed" in current_checkpoint
    assert "publish this status-only commit" not in current_checkpoint

    assert "8,531-byte brief" not in current_checkpoint
    assert "only the clean-commit" not in current_checkpoint.casefold()
