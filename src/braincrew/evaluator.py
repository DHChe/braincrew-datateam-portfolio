from __future__ import annotations

from typing import Literal

from braincrew.contracts import EvaluationResult, FixtureCase, NormalizedObservation


def evaluate_exact_answer(
    case: FixtureCase,
    observation: NormalizedObservation,
) -> EvaluationResult:
    score: Literal[0, 1] = 1 if observation.answer == case.expected_answer else 0
    return EvaluationResult(
        schema_version="evaluation-result-v1",
        evaluator_version="exact-answer-v1",
        numerator=score,
        denominator=1,
        score=score,
    )
