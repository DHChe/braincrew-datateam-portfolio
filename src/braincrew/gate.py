from __future__ import annotations

from braincrew.contracts import EvaluationResult, GateDecision


def decide_fixture_gate(evaluation: EvaluationResult) -> GateDecision:
    if evaluation.score == 1:
        return GateDecision(
            schema_version="gate-decision-v1",
            gate_version="fixture-exact-answer-gate-v1",
            decision="PASS",
            reasons=[],
        )
    return GateDecision(
        schema_version="gate-decision-v1",
        gate_version="fixture-exact-answer-gate-v1",
        decision="FAIL",
        reasons=["FIXTURE_ANSWER_MISMATCH"],
    )
