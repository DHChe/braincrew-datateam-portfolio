from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

CommitSha = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
LogicalDigest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
RunId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DatasetIdentity(StrictContract):
    id: str
    version: str
    corpus_id: str


class FixtureCase(StrictContract):
    id: str
    split: Literal["fixture"]
    query: str
    expected_answer: str


class FixtureSutResponse(StrictContract):
    answer: str
    answer_mode: Literal["answer", "abstain", "review_required"]


class PromptIdentity(StrictContract):
    id: str
    hash: str


class ModelIdentity(StrictContract):
    provider: str
    name: str
    parameters: dict[str, object]


class FixtureProvenance(StrictContract):
    source_type: Literal["public", "synthetic"]
    license: str


class FixtureCaseDocument(StrictContract):
    schema_version: Literal["fixture-case-v1"]
    dataset: DatasetIdentity
    case: FixtureCase
    fixture_sut: FixtureSutResponse
    prompt: PromptIdentity
    model: ModelIdentity
    provenance: FixtureProvenance


class RunEnvelope(StrictContract):
    run_id: RunId
    execution_mode: Literal["fixture"]
    created_at: datetime


class EvaluationPlaneProvenance(StrictContract):
    commit_sha: CommitSha
    dirty_worktree: bool
    executed: Literal[True]


class SutProvenance(StrictContract):
    commit_sha: CommitSha
    dirty_worktree: None
    executed: Literal[False]
    claim: Literal["identity placeholder only; live AX was not called"]


class DatasetArtifactProvenance(DatasetIdentity, FixtureProvenance):
    content_digest: LogicalDigest


class AdapterProvenance(StrictContract):
    version: Literal["fixture-sut-v1"]
    execution_mode: Literal["fixture"]


class EvaluatorProvenance(StrictContract):
    version: Literal["exact-answer-v1"]


class ArtifactProvenance(StrictContract):
    evaluation_plane: EvaluationPlaneProvenance
    sut: SutProvenance
    dataset: DatasetArtifactProvenance
    adapter: AdapterProvenance
    evaluator: EvaluatorProvenance
    prompt: PromptIdentity
    model: ModelIdentity


class CaseSnapshot(StrictContract):
    dataset: DatasetIdentity
    case: FixtureCase


class NormalizedObservation(StrictContract):
    schema_version: Literal["normalized-observation-v1"]
    case_id: str
    answer: str
    answer_mode: Literal["answer", "abstain", "review_required"]


class EvaluationResult(StrictContract):
    schema_version: Literal["evaluation-result-v1"]
    evaluator_version: Literal["exact-answer-v1"]
    numerator: Literal[0, 1]
    denominator: Literal[1]
    score: Literal[0, 1]


class GateDecision(StrictContract):
    schema_version: Literal["gate-decision-v1"]
    gate_version: Literal["fixture-exact-answer-gate-v1"]
    decision: Literal["PASS", "FAIL"]
    reasons: list[str]


class LogicalResult(StrictContract):
    case_snapshot: CaseSnapshot
    observation: NormalizedObservation
    evaluation: EvaluationResult
    gate: GateDecision


class RunArtifactDocument(StrictContract):
    schema_version: Literal["run-artifact-v1"]
    run: RunEnvelope
    provenance: ArtifactProvenance
    logical_result: LogicalResult
    logical_digest: LogicalDigest
