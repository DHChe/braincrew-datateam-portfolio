from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DESIGN_PATH = (
    PROJECT_ROOT
    / "docs/superpowers/specs/2026-07-20-independent-evaluation-corpus-provisioning-design.md"
)


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
    assert "Braincrew #35's only blocker is Braincrew #32" in execution_order
    assert "AX #36 may proceed independently of the Braincrew #35 commit lane" in execution_order
    assert "AX #36 must be complete before operator load" in execution_order
    assert execution_order.index("require AX #36") < execution_order.index(
        "perform the approved atomic AX load"
    )

    assert "AX #36 remains open" in progress
    assert "Braincrew #35 is active" in progress
