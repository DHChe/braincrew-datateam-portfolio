from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from braincrew.contracts import (
    RetrievalDatasetDocument,
    RetrievalObservationBatch,
    RetrievalRunEvaluation,
)
from braincrew.evaluator import evaluate_retrieval_run


def load_retrieval_dataset(path: Path) -> RetrievalDatasetDocument:
    raw_dataset: Any = json.loads(path.read_text(encoding="utf-8"))
    return RetrievalDatasetDocument.model_validate(raw_dataset)


def load_retrieval_observations(path: Path) -> RetrievalObservationBatch:
    raw_observations: Any = json.loads(path.read_text(encoding="utf-8"))
    return RetrievalObservationBatch.model_validate(raw_observations)


def execute_retrieval_fixture(
    dataset: RetrievalDatasetDocument,
    observations: RetrievalObservationBatch,
) -> RetrievalRunEvaluation:
    return evaluate_retrieval_run(dataset, observations)
