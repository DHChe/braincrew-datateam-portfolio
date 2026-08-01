from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from braincrew.operational_evaluator import OperationalMeasurement

CommitSha = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
LogicalDigest = Annotated[str, Field(pattern=r"^sha256:[0-9a-f]{64}$")]
RunId = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")]
ParsingEvaluatorVersion = Literal["parsing-quality-v1", "parsing-quality-v2"]
PARSING_EVALUATOR_V1: ParsingEvaluatorVersion = "parsing-quality-v1"
PARSING_EVALUATOR_V2: ParsingEvaluatorVersion = "parsing-quality-v2"


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


class RetrievalCorpusIdentity(StrictContract):
    id: str
    version: str


class RetrievalSourceExpectation(StrictContract):
    record_kind: str
    record_id: str
    evidence_span_id: str | None
    source_text_digest: LogicalDigest | None
    authority_level: int | None = Field(ge=1)


class RetrievalEvidenceGroup(StrictContract):
    id: str
    alternatives: list[RetrievalSourceExpectation]


class RetrievalExpected(StrictContract):
    source_identity_status: Literal["resolved", "missing", "ambiguous"]
    unresolved_identity_policy: Literal["not_applicable", "denominator_zero", "invalid"]
    evidence_groups: list[RetrievalEvidenceGroup] = Field(min_length=1)
    preferred_authority_level: int | None = Field(ge=1)
    forbidden_sources: list[RetrievalSourceExpectation] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_expected_source_identity_policy(self) -> RetrievalExpected:
        alternatives = [
            alternative for group in self.evidence_groups for alternative in group.alternatives
        ]
        if self.source_identity_status == "resolved":
            if any(not group.alternatives for group in self.evidence_groups):
                raise ValueError("resolved expected source identities require alternatives")
            if self.unresolved_identity_policy != "not_applicable":
                raise ValueError(
                    "resolved expected source identities require not_applicable policy"
                )
        else:
            if alternatives:
                raise ValueError(
                    "unresolved expected source identities cannot declare alternatives"
                )
            if self.unresolved_identity_policy == "not_applicable":
                raise ValueError("unresolved expected source identities require an explicit policy")
        return self


class RetrievalApplicability(StrictContract):
    recall_at_5: bool
    mrr_at_10: bool
    authority_ordering: bool
    forbidden_visibility: bool


class RetrievalReview(StrictContract):
    status: Literal["reviewed"]
    reviewer: str


class RetrievalCase(StrictContract):
    id: str
    split: Literal["calibration", "verification"]
    primary_focus: Literal["retrieval"]
    tags: list[str]
    role: Literal["Executive", "HRManager"]
    query: str = Field(min_length=1)
    corpus: RetrievalCorpusIdentity
    expected: RetrievalExpected
    applicability: RetrievalApplicability
    difficulty: Literal["standard", "adversarial"]
    provenance: FixtureProvenance
    review: RetrievalReview

    @model_validator(mode="after")
    def validate_metric_applicability(self) -> RetrievalCase:
        if (
            self.applicability.authority_ordering
            and self.expected.preferred_authority_level is None
        ):
            raise ValueError("authority ordering requires a preferred authority level")
        if (
            self.expected.source_identity_status != "resolved"
            and self.applicability.authority_ordering
        ):
            raise ValueError("unresolved expected source identity cannot score authority ordering")
        return self


class RetrievalDatasetDocument(StrictContract):
    schema_version: Literal["retrieval-dataset-v1"]
    dataset: DatasetIdentity
    provenance: FixtureProvenance
    cases: list[RetrievalCase]

    @model_validator(mode="after")
    def validate_case_set(self) -> RetrievalDatasetDocument:
        case_ids = [case.id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case IDs must be unique")
        calibration_count = sum(case.split == "calibration" for case in self.cases)
        verification_cases = [case for case in self.cases if case.split == "verification"]
        if len(self.cases) != 30 or calibration_count != 21 or len(verification_cases) != 9:
            raise ValueError(
                "retrieval dataset must contain 21 calibration and 9 verification cases"
            )
        if any(
            case.expected.source_identity_status != "resolved" or not case.applicability.recall_at_5
            for case in verification_cases
        ):
            raise ValueError("all 9 verification cases must have resolved Recall@5 ground truth")
        return self


class RetrievalCandidateObservation(StrictContract):
    rank: int = Field(ge=1)
    record_kind: str
    record_id: str
    evidence_span_id: str | None
    source_text_digest: LogicalDigest | None
    authority_level: int | None = Field(ge=1)
    visibility_allowed: bool
    visibility_reason: str


class RetrievalObservation(StrictContract):
    schema_version: Literal["retrieval-observation-v1"]
    case_id: str
    query: str
    retrieval_available: bool
    failure_code: str | None
    candidates: list[RetrievalCandidateObservation]
    operational: OperationalMeasurement | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )

    @model_validator(mode="after")
    def validate_availability_and_rank_contract(self) -> RetrievalObservation:
        if self.retrieval_available and self.failure_code is not None:
            raise ValueError("available retrieval cannot declare a failure code")
        if not self.retrieval_available and self.failure_code is None:
            raise ValueError("unavailable retrieval requires an explicit failure code")
        if [candidate.rank for candidate in self.candidates] != list(
            range(1, len(self.candidates) + 1)
        ):
            raise ValueError("retrieval candidate rank must equal one-based array order")
        return self


class RetrievalObservationBatch(StrictContract):
    schema_version: Literal["retrieval-observation-batch-v1"]
    adapter_version: Literal["fixture-retrieval-sut-v1", "ax-sut-http-v1"]
    observations: list[RetrievalObservation]

    @model_validator(mode="after")
    def require_unique_case_observations(self) -> RetrievalObservationBatch:
        case_ids = [observation.case_id for observation in self.observations]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("retrieval observation case IDs must be unique")
        return self


class RetrievalMetricScore(StrictContract):
    numerator: int = Field(ge=0)
    denominator: int = Field(gt=0)
    display_value: str = Field(pattern=r"^(0|1)\.[0-9]{4}$")

    @model_validator(mode="after")
    def validate_exact_score(self) -> RetrievalMetricScore:
        if self.numerator > self.denominator:
            raise ValueError("retrieval metric numerator cannot exceed denominator")
        expected_display = (Decimal(self.numerator) / Decimal(self.denominator)).quantize(
            Decimal("0.0001"),
            rounding=ROUND_HALF_EVEN,
        )
        if self.display_value != f"{expected_display:.4f}":
            raise ValueError("retrieval metric display must match its exact fraction")
        return self


class RetrievalCaseEvaluation(StrictContract):
    schema_version: Literal["retrieval-case-evaluation-v1"]
    evaluator_version: Literal["retrieval-quality-v1"]
    case_id: str
    status: Literal["SCORED", "INVALID"]
    invalid_reasons: list[str]
    failure_codes: list[str]
    hard_failure: bool
    recall_at_5: RetrievalMetricScore | None
    mrr_at_10: RetrievalMetricScore | None
    authority_priority: RetrievalMetricScore | None
    forbidden_visibility: RetrievalMetricScore | None


class RetrievalCoverage(StrictContract):
    total_cases: int = Field(ge=0)
    scored_cases: int = Field(ge=0)
    calibration_cases: int = Field(ge=0)
    verification_cases: int = Field(ge=0)
    verification_recall_at_5_cases: int = Field(ge=0)
    authority_ordering_cases: int = Field(ge=0)
    forbidden_visibility_cases: int = Field(ge=0)


class RetrievalAggregateMetric(RetrievalMetricScore):
    case_count: int = Field(gt=0)


class RetrievalAggregate(StrictContract):
    recall_at_5: RetrievalAggregateMetric
    mrr_at_10: RetrievalAggregateMetric
    authority_priority: RetrievalAggregateMetric
    forbidden_visibility: RetrievalAggregateMetric


class RetrievalRunEvaluation(StrictContract):
    schema_version: Literal["retrieval-run-evaluation-v1"]
    evaluator_version: Literal["retrieval-quality-v1"]
    state: Literal["COMPLETED", "FAILED", "INVALID"]
    invalid_reasons: list[str]
    hard_failure_cases: list[str]
    coverage: RetrievalCoverage
    case_results: list[RetrievalCaseEvaluation]
    aggregate: RetrievalAggregate | None


class RetrievalAdapterProvenance(StrictContract):
    version: Literal["fixture-retrieval-sut-v1", "ax-sut-http-v1"]
    execution_mode: Literal["fixture", "live"]


class RetrievalEvaluatorProvenance(StrictContract):
    version: Literal["retrieval-quality-v1"]


class RetrievalArtifactProvenance(StrictContract):
    evaluation_plane: EvaluationPlaneProvenance
    sut: SutProvenance
    dataset: DatasetArtifactProvenance
    adapter: RetrievalAdapterProvenance
    evaluator: RetrievalEvaluatorProvenance
    prompt: PromptIdentity
    model: ModelIdentity


class RetrievalLogicalResult(StrictContract):
    dataset_snapshot: RetrievalDatasetDocument
    observation_snapshot: RetrievalObservationBatch
    evaluation: RetrievalRunEvaluation


class RetrievalRunArtifactDocument(StrictContract):
    schema_version: Literal["retrieval-run-artifact-v1"]
    run: RunEnvelope
    provenance: RetrievalArtifactProvenance
    logical_result: RetrievalLogicalResult
    logical_digest: LogicalDigest


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
    evaluator_version: ParsingEvaluatorVersion
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
    table_preservation: ParsingAggregateMetric | None
    list_preservation: ParsingAggregateMetric | None


class ParsingRunEvaluation(StrictContract):
    schema_version: Literal["parsing-run-evaluation-v1"]
    evaluator_version: ParsingEvaluatorVersion
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
    version: ParsingEvaluatorVersion


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
    execution_mode: Literal["fixture", "live"]
    created_at: datetime


class EvaluationPlaneProvenance(StrictContract):
    commit_sha: CommitSha
    dirty_worktree: bool
    executed: Literal[True]


class SutProvenance(StrictContract):
    commit_sha: CommitSha
    dirty_worktree: bool | None
    executed: bool
    claim: Literal[
        "identity placeholder only; live AX was not called",
        "live AX called; clean state warranted by read-only checkout check",
    ]

    @model_validator(mode="after")
    def bind_execution_claim(self) -> SutProvenance:
        if self.executed:
            if self.dirty_worktree is None or self.claim != (
                "live AX called; clean state warranted by read-only checkout check"
            ):
                raise ValueError("live SUT provenance requires a read-only worktree warrant")
        elif self.dirty_worktree is not None or self.claim != (
            "identity placeholder only; live AX was not called"
        ):
            raise ValueError("fixture SUT provenance must retain its non-execution claim")
        return self


class DatasetArtifactProvenance(DatasetIdentity, FixtureProvenance):
    content_digest: LogicalDigest


class AdapterProvenance(StrictContract):
    version: Literal["fixture-sut-v1", "ax-sut-http-v1"]
    execution_mode: Literal["fixture", "live"]


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
