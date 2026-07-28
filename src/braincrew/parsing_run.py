from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from braincrew.contracts import (
    ParsingDatasetDocument,
    ParsingObservationBatch,
    ParsingRunEvaluation,
)
from braincrew.evaluator import evaluate_parsing_run


def load_parsing_dataset(path: Path) -> ParsingDatasetDocument:
    raw_dataset: Any = json.loads(path.read_text(encoding="utf-8"))
    return ParsingDatasetDocument.model_validate(raw_dataset)


def load_parsing_observations(path: Path) -> ParsingObservationBatch:
    raw_observations: Any = json.loads(path.read_text(encoding="utf-8"))
    return ParsingObservationBatch.model_validate(raw_observations)


def execute_parsing_fixture(
    dataset: ParsingDatasetDocument,
    observations: ParsingObservationBatch,
    *,
    verification_only: bool = False,
) -> ParsingRunEvaluation:
    return evaluate_parsing_run(
        dataset,
        observations,
        verification_only=verification_only,
    )
