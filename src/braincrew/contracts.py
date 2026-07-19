from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class ParsingDocument(StrictContract):
    id: str
    version: str
    canonical_text: str = Field(min_length=1)


class EvidenceSpanExpectation(StrictContract):
    id: str
    text: str = Field(min_length=1)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    source_text_digest: LogicalDigest


class ParsingStructureExpectation(StrictContract):
    headings: list[str] = Field(min_length=1)


class ParsingTableExpectation(StrictContract):
    columns: list[str] = Field(min_length=1)
    rows: list[list[str]] = Field(min_length=1)

    @model_validator(mode="after")
    def require_rectangular_rows(self) -> ParsingTableExpectation:
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("table rows must match the declared column count")
        return self


class ParsingListExpectation(StrictContract):
    items: list[str] = Field(min_length=1)
    ordered: bool


class ParsingExpected(StrictContract):
    evidence_spans: list[EvidenceSpanExpectation] = Field(min_length=1)
    structure: ParsingStructureExpectation
    metadata: dict[str, str] = Field(min_length=1)
    table: ParsingTableExpectation | None
    list: ParsingListExpectation | None


class ParsingReview(StrictContract):
    status: Literal["reviewed"]
    reviewer: str


class ParsingCase(StrictContract):
    id: str
    split: Literal["calibration", "verification"]
    primary_focus: Literal["parsing"]
    tags: list[str]
    document: ParsingDocument
    expected: ParsingExpected
    provenance: FixtureProvenance
    review: ParsingReview

    @model_validator(mode="after")
    def validate_evidence_span_coordinates(self) -> ParsingCase:
        canonical_text = self.document.canonical_text
        source_digest = f"sha256:{hashlib.sha256(canonical_text.encode('utf-8')).hexdigest()}"
        for span in self.expected.evidence_spans:
            if canonical_text[span.start_char : span.end_char] != span.text:
                raise ValueError("EvidenceSpan text and Unicode offsets must match source text")
            if span.source_text_digest != source_digest:
                raise ValueError("EvidenceSpan source digest must match canonical source text")
        return self


class ParsingDatasetDocument(StrictContract):
    schema_version: Literal["parsing-dataset-v1"]
    dataset: DatasetIdentity
    provenance: FixtureProvenance
    cases: list[ParsingCase]

    @model_validator(mode="after")
    def validate_case_set(self) -> ParsingDatasetDocument:
        case_ids = [case.id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case IDs must be unique")
        calibration_count = sum(case.split == "calibration" for case in self.cases)
        verification_count = sum(case.split == "verification" for case in self.cases)
        if len(self.cases) != 20 or calibration_count != 14 or verification_count != 6:
            raise ValueError("parsing dataset must contain 14 calibration and 6 verification cases")
        return self


class ParsingObservation(StrictContract):
    schema_version: Literal["parsing-observation-v1"]
    case_id: str
    parse_available: bool
    parser_version: str | None
    failure_code: str | None
    evidence_spans: list[EvidenceSpanExpectation]
    headings: list[str]
    metadata: dict[str, str]
    table: ParsingTableExpectation | None
    list: ParsingListExpectation | None

    @model_validator(mode="after")
    def validate_availability_contract(self) -> ParsingObservation:
        if self.parse_available and (self.parser_version is None or self.failure_code is not None):
            raise ValueError("available parsing requires a parser version and no failure code")
        if not self.parse_available and self.failure_code is None:
            raise ValueError("unavailable parsing requires an explicit failure code")
        return self


class ParsingMetricScore(StrictContract):
    numerator: int = Field(ge=0)
    denominator: int = Field(gt=0)
    display_value: str = Field(pattern=r"^(0|1)\.[0-9]{4}$")


class ParsingCaseEvaluation(StrictContract):
    schema_version: Literal["parsing-case-evaluation-v1"]
    evaluator_version: Literal["parsing-quality-v1"]
    case_id: str
    status: Literal["SCORED", "INVALID"]
    invalid_reasons: list[str]
    evidence_span_recovery: ParsingMetricScore | None
    structure_preservation: ParsingMetricScore | None
    metadata_completeness: ParsingMetricScore | None
    table_preservation: ParsingMetricScore | None
    list_preservation: ParsingMetricScore | None


class ParsingObservationBatch(StrictContract):
    schema_version: Literal["parsing-observation-batch-v1"]
    adapter_version: Literal["fixture-parsing-sut-v1"]
    parser_version: str
    observations: list[ParsingObservation]

    @model_validator(mode="after")
    def require_unique_case_observations(self) -> ParsingObservationBatch:
        case_ids = [observation.case_id for observation in self.observations]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("parsing observation case IDs must be unique")
        if any(
            observation.parse_available and observation.parser_version != self.parser_version
            for observation in self.observations
        ):
            raise ValueError("available observation parser version must match the batch")
        return self


class ParsingCoverage(StrictContract):
    total_cases: int = Field(ge=0)
    scored_cases: int = Field(ge=0)
    calibration_cases: int = Field(ge=0)
    verification_cases: int = Field(ge=0)
    verification_evidence_span_cases: int = Field(ge=0)


class ParsingAggregateMetric(ParsingMetricScore):
    case_count: int = Field(gt=0)


class ParsingAggregate(StrictContract):
    evidence_span_recovery: ParsingAggregateMetric
    structure_preservation: ParsingAggregateMetric
    metadata_completeness: ParsingAggregateMetric
    table_preservation: ParsingAggregateMetric
    list_preservation: ParsingAggregateMetric


class ParsingRunEvaluation(StrictContract):
    schema_version: Literal["parsing-run-evaluation-v1"]
    evaluator_version: Literal["parsing-quality-v1"]
    state: Literal["COMPLETED", "INVALID"]
    invalid_reasons: list[str]
    coverage: ParsingCoverage
    case_results: list[ParsingCaseEvaluation]
    aggregate: ParsingAggregate | None


class ParsingAdapterProvenance(StrictContract):
    version: Literal["fixture-parsing-sut-v1"]
    parser_version: str
    execution_mode: Literal["fixture"]


class ParsingEvaluatorProvenance(StrictContract):
    version: Literal["parsing-quality-v1"]


class ParsingArtifactProvenance(StrictContract):
    evaluation_plane: EvaluationPlaneProvenance
    sut: SutProvenance
    dataset: DatasetArtifactProvenance
    adapter: ParsingAdapterProvenance
    evaluator: ParsingEvaluatorProvenance
    prompt: PromptIdentity
    model: ModelIdentity


class ParsingLogicalResult(StrictContract):
    dataset_snapshot: ParsingDatasetDocument
    observation_snapshot: ParsingObservationBatch
    evaluation: ParsingRunEvaluation


class ParsingRunArtifactDocument(StrictContract):
    schema_version: Literal["parsing-run-artifact-v1"]
    run: RunEnvelope
    provenance: ParsingArtifactProvenance
    logical_result: ParsingLogicalResult
    logical_digest: LogicalDigest


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
