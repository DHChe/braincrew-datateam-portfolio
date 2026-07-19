from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from braincrew.contracts import CaseSnapshot, FixtureCaseDocument, LogicalResult
from braincrew.evaluator import evaluate_exact_answer
from braincrew.fixture_adapter import normalize_fixture_response
from braincrew.gate import decide_fixture_gate


def load_fixture_case(path: Path) -> FixtureCaseDocument:
    raw_case: Any = json.loads(path.read_text(encoding="utf-8"))
    return FixtureCaseDocument.model_validate(raw_case)


def execute_fixture_case(case_document: FixtureCaseDocument) -> LogicalResult:
    observation = normalize_fixture_response(case_document)
    evaluation = evaluate_exact_answer(case_document.case, observation)
    gate = decide_fixture_gate(evaluation)
    return LogicalResult(
        case_snapshot=CaseSnapshot(dataset=case_document.dataset, case=case_document.case),
        observation=observation,
        evaluation=evaluation,
        gate=gate,
    )
