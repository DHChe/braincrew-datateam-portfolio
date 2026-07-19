from __future__ import annotations

import hashlib
import json
import re
from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from braincrew.contracts import (
    DatasetArtifactProvenance,
    EvaluationPlaneProvenance,
    LogicalDigest,
    ModelIdentity,
    PromptIdentity,
    RunEnvelope,
    SutProvenance,
)


class StrictGroundedContract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class GroundedStructuredAnswer(StrictGroundedContract):
    summary: str
    answer: str
    grounds: tuple[str, ...]
    review_points: tuple[str, ...]
    additional_checks: tuple[str, ...]
    risk_warning: str


class ClaimAtom(StrictGroundedContract):
    claim_path: str
    atom_index: int = Field(ge=0)
    normalized_text: str
    normalized_text_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    stable_identity: str
    placeholder: bool = False


ClaimPathRoot = Literal[
    "summary",
    "answer",
    "grounds",
    "review_points",
    "additional_checks",
    "risk_warning",
]

AnswerMode = Literal[
    "direct_grounded",
    "conditional_grounded",
    "insufficient_evidence",
    "out_of_scope",
    "review_required",
]
ClaimOutcome = Literal[
    "supported",
    "unsupported",
    "contradicted",
    "unmapped",
    "ambiguous",
    "missing_required",
]
RiskLevel = Literal["standard", "high"]
PrimaryFocus = Literal["grounded_answer", "visibility_abstention"]
ClaimPolarity = Literal["affirmed", "denied"]
ClaimModality = Literal[
    "must",
    "may",
    "must_not",
    "unknown",
    "review_required",
]

_REQUIRED_PATH_PATTERN = re.compile(
    r"^(summary|answer|risk_warning|(grounds|review_points|additional_checks)\[[0-9]+\])$"
)


class SurfaceMatcher(StrictGroundedContract):
    kind: Literal["literal", "regex"]
    pattern: str = Field(min_length=1)
    matcher_digest: str | None = Field(default=None, pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def require_bounded_regex(self) -> SurfaceMatcher:
        if self.kind == "regex":
            if not (self.pattern.startswith("^") and self.pattern.endswith("$")):
                raise ValueError("regex surface matcher must be bounded with ^ and $")
            re.compile(self.pattern)
        if self.matcher_digest is not None:
            payload = json.dumps(
                {"kind": self.kind, "pattern": self.pattern},
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            actual = f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"
            if actual != self.matcher_digest:
                raise ValueError("surface matcher digest does not match matcher content")
        return self


class EvidenceAlternative(StrictGroundedContract):
    record_kind: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    evidence_span_id: str = Field(min_length=1)
    source_text_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_matcher: SurfaceMatcher


class EvidenceGroup(StrictGroundedContract):
    group_id: str = Field(min_length=1)
    alternatives: tuple[EvidenceAlternative, ...] = Field(min_length=1)


class ClaimProposition(StrictGroundedContract):
    proposition_id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    predicate: str = Field(min_length=1)
    object: str | None = Field(default=None, min_length=1)
    polarity: ClaimPolarity
    modality: ClaimModality
    risk_level: RiskLevel
    conclusive: bool
    forbidden: bool
    allowed_answer_modes: tuple[AnswerMode, ...] = Field(min_length=1)
    forbidden_answer_modes: tuple[AnswerMode, ...] = ()
    surface_matchers: tuple[SurfaceMatcher, ...] = Field(min_length=1)
    supporting_evidence_groups: tuple[EvidenceGroup, ...] = Field(min_length=1)
    contradicting_evidence_groups: tuple[EvidenceGroup, ...] = ()

    @model_validator(mode="after")
    def validate_answer_modes_and_surface_matchers(self) -> ClaimProposition:
        if set(self.allowed_answer_modes) & set(self.forbidden_answer_modes):
            raise ValueError("allowed and forbidden Answer Modes must be disjoint")
        if any(matcher.matcher_digest is None for matcher in self.surface_matchers):
            raise ValueError("proposition surface matchers require matcher identity digests")
        return self


class GroundedApplicability(StrictGroundedContract):
    claim_support_precision: bool
    citation_precision: bool
    citation_coverage: bool
    answer_mode_accuracy: bool = False
    abstention_accuracy: bool = False


class GroundedCase(StrictGroundedContract):
    case_id: str = Field(pattern=r"^(GA|VA)-[0-9]{3}$")
    primary_focus: PrimaryFocus
    split: Literal["Calibration", "Verification"]
    risk_level: RiskLevel
    query: str = Field(min_length=1)
    role: str = Field(min_length=1)
    expected_answer_mode: AnswerMode
    required_abstention_mode: AnswerMode | None = None
    forbidden_conclusive_proposition_ids: tuple[str, ...] = ()
    protected_identifiers: tuple[str, ...] = ()
    forbidden_role_proposition_ids: tuple[str, ...] = ()
    required_output_paths: tuple[str, ...]
    propositions: tuple[ClaimProposition, ...] = Field(min_length=1)
    applicability: GroundedApplicability

    @field_validator("required_output_paths")
    @classmethod
    def validate_required_output_paths(cls, paths: tuple[str, ...]) -> tuple[str, ...]:
        if len(paths) != len(set(paths)) or any(
            _REQUIRED_PATH_PATTERN.fullmatch(path) is None for path in paths
        ):
            raise ValueError("required_output_paths must contain unique concrete claim paths")
        return paths

    @field_validator("protected_identifiers")
    @classmethod
    def validate_protected_identifiers(cls, values: tuple[str, ...]) -> tuple[str, ...]:
        if len(values) != len(set(values)) or any(not value.strip() for value in values):
            raise ValueError("protected identifiers must be unique non-empty literals")
        return values

    @model_validator(mode="after")
    def require_unique_proposition_ids(self) -> GroundedCase:
        proposition_ids = [item.proposition_id for item in self.propositions]
        if len(proposition_ids) != len(set(proposition_ids)):
            raise ValueError("proposition identities must be unique within a case")
        if not set(self.forbidden_conclusive_proposition_ids) <= set(proposition_ids):
            raise ValueError("forbidden conclusive proposition identities must exist in the case")
        conclusive_ids = {item.proposition_id for item in self.propositions if item.conclusive}
        if not set(self.forbidden_conclusive_proposition_ids) <= conclusive_ids:
            raise ValueError(
                "forbidden conclusive identity must reference a conclusive proposition"
            )
        if not set(self.forbidden_role_proposition_ids) <= set(proposition_ids):
            raise ValueError("forbidden role proposition identities must exist in the case")
        if self.applicability.abstention_accuracy:
            if self.required_abstention_mode not in {"insufficient_evidence", "out_of_scope"}:
                raise ValueError("applicable abstention requires the supported abstention mode")
            if self.expected_answer_mode != self.required_abstention_mode:
                raise ValueError("expected and required abstention modes must match")
        return self


class GroundedDatasetProvenance(StrictGroundedContract):
    source_kind: Literal["synthetic", "public"]
    license: str = Field(min_length=1)
    review_status: Literal["draft", "reviewed", "frozen"]


class GroundedDatasetDocument(StrictGroundedContract):
    schema_version: Literal["grounded-dataset-v1"]
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    case_count: int = Field(ge=1)
    proposition_contract_version: Literal["claim-proposition-v1"]
    traversal_contract_version: Literal["claim-traversal-v1"]
    normalizer_version: Literal["claim-normalizer-v1"]
    source_resolution_version: Literal["source-text-resolution-v1"]
    answer_mode_contract_version: Literal["answer-mode-v1"]
    abstention_contract_version: Literal["abstention-v1"]
    visibility_contract_version: Literal["answer-visibility-v1"]
    cases: tuple[GroundedCase, ...] = Field(min_length=1)
    provenance: GroundedDatasetProvenance

    @model_validator(mode="after")
    def validate_case_set(self) -> GroundedDatasetDocument:
        if self.case_count != len(self.cases):
            raise ValueError("case_count must equal the number of grounded cases")
        case_ids = [case.case_id for case in self.cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("grounded case identities must be unique")
        if self.dataset_id == "braincrew-answer-quality":
            allocation: dict[tuple[PrimaryFocus, str], int] = {}
            for case in self.cases:
                key = (case.primary_focus, case.split)
                allocation[key] = allocation.get(key, 0) + 1
            expected = {
                ("grounded_answer", "Calibration"): 30,
                ("grounded_answer", "Verification"): 10,
                ("visibility_abstention", "Calibration"): 5,
                ("visibility_abstention", "Verification"): 5,
            }
            if allocation != expected:
                raise ValueError("answer-quality case allocation does not match the frozen split")
        return self


class GroundedCitation(StrictGroundedContract):
    record_kind: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    evidence_span_id: str = Field(min_length=1)
    source_text_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    claim_paths: tuple[str, ...] = Field(min_length=1)


class SourceTextResolution(StrictGroundedContract):
    record_kind: str = Field(min_length=1)
    record_id: str = Field(min_length=1)
    text: str
    source_text_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_source_text_digest(self) -> SourceTextResolution:
        actual = f"sha256:{hashlib.sha256(self.text.encode('utf-8')).hexdigest()}"
        if actual != self.source_text_digest:
            raise ValueError("source text digest does not match resolved text")
        return self


class GroundedObservation(StrictGroundedContract):
    case_id: str = Field(pattern=r"^(GA|VA)-[0-9]{3}$")
    executed_role: str = Field(min_length=1)
    available: bool
    error: str | None
    answer_mode: AnswerMode
    structured_answer: GroundedStructuredAnswer
    citations: tuple[GroundedCitation, ...]
    source_texts: tuple[SourceTextResolution, ...]

    @model_validator(mode="after")
    def validate_availability(self) -> GroundedObservation:
        if self.available and self.error is not None:
            raise ValueError("available grounded observation cannot carry an error")
        if not self.available and not self.error:
            raise ValueError("unavailable grounded observation requires an error")
        return self


class GroundedObservationBatch(StrictGroundedContract):
    schema_version: Literal["grounded-observation-batch-v1"]
    adapter_version: Literal["fixture-grounded-sut-v1"]
    sut_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    observations: tuple[GroundedObservation, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def require_unique_case_observations(self) -> GroundedObservationBatch:
        case_ids = [observation.case_id for observation in self.observations]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("grounded observation case identities must be unique")
        return self


class GroundedMetricScore(StrictGroundedContract):
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    exact: str
    value: str
    display: str

    @model_validator(mode="after")
    def validate_exact_score(self) -> GroundedMetricScore:
        if self.numerator > self.denominator or (self.denominator == 0 and self.numerator != 0):
            raise ValueError("grounded metric counts must describe a fraction in [0, 1]")
        if self.exact != f"{self.numerator}/{self.denominator}":
            raise ValueError("grounded metric exact fraction does not match counts")
        expected_value = (
            Decimal(0)
            if self.denominator == 0
            else Decimal(self.numerator) / Decimal(self.denominator)
        )
        try:
            stored_value = Decimal(self.value)
        except InvalidOperation as error:
            raise ValueError("grounded metric value must be decimal") from error
        if stored_value != expected_value:
            raise ValueError("grounded metric value does not match counts")
        expected_display = expected_value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
        if self.display != f"{expected_display:.4f}":
            raise ValueError("grounded metric display does not match counts")
        return self


class ClaimAtomEvaluation(StrictGroundedContract):
    atom: ClaimAtom
    outcome: ClaimOutcome
    proposition_id: str | None
    failure_codes: tuple[str, ...]


class GroundedCaseEvaluation(StrictGroundedContract):
    evaluator_version: Literal["grounded-answer-v1"]
    proposition_contract_version: Literal["claim-proposition-v1"]
    traversal_contract_version: Literal["claim-traversal-v1"]
    normalizer_version: Literal["claim-normalizer-v1"]
    source_resolution_version: Literal["source-text-resolution-v1"]
    guard_version: Literal["high-risk-guard-v1"]
    case_id: str
    state: Literal["COMPLETED", "INVALID"]
    atom_evaluations: tuple[ClaimAtomEvaluation, ...]
    claim_support_precision: GroundedMetricScore
    citation_precision: GroundedMetricScore
    citation_coverage: GroundedMetricScore
    answer_mode_accuracy: GroundedMetricScore
    abstention_accuracy: GroundedMetricScore
    failure_codes: tuple[str, ...]
    hard_failure_atom_ids: tuple[str, ...]
    hard_failure_codes: tuple[str, ...]


class GroundedCoverage(StrictGroundedContract):
    total_cases: int = Field(ge=0)
    verification_cases: int = Field(ge=0)
    verification_claim_support_cases: int = Field(ge=0)
    verification_citation_precision_cases: int = Field(ge=0)
    verification_answer_mode_cases: int = Field(ge=0)
    verification_abstention_cases: int = Field(ge=0)


class GroundedAggregateMetric(StrictGroundedContract):
    applicable_cases: int = Field(ge=0)
    exact: str
    value: str
    display: str


class GroundedAggregate(StrictGroundedContract):
    claim_support_precision: GroundedAggregateMetric
    citation_precision: GroundedAggregateMetric
    citation_coverage: GroundedAggregateMetric
    answer_mode_accuracy: GroundedAggregateMetric
    abstention_accuracy: GroundedAggregateMetric


class GroundedRunEvaluation(StrictGroundedContract):
    evaluator_version: Literal["grounded-answer-v1"]
    proposition_contract_version: Literal["claim-proposition-v1"]
    traversal_contract_version: Literal["claim-traversal-v1"]
    normalizer_version: Literal["claim-normalizer-v1"]
    source_resolution_version: Literal["source-text-resolution-v1"]
    guard_version: Literal["high-risk-guard-v1"]
    state: Literal["COMPLETED", "INVALID"]
    case_evaluations: tuple[GroundedCaseEvaluation, ...]
    coverage: GroundedCoverage
    aggregate: GroundedAggregate | None
    failure_codes: tuple[str, ...]
    hard_failure_cases: tuple[str, ...]


class GroundedAdapterProvenance(StrictGroundedContract):
    version: Literal["fixture-grounded-sut-v1"]
    execution_mode: Literal["fixture"]


class GroundedCompatibilityProvenance(StrictGroundedContract):
    evaluator_version: Literal["grounded-answer-v1"]
    proposition_contract_version: Literal["claim-proposition-v1"]
    traversal_contract_version: Literal["claim-traversal-v1"]
    atomizer_version: Literal["claim-atomizer-v1"]
    atomizer_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    normalizer_version: Literal["claim-normalizer-v1"]
    normalizer_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    matcher_set_version: Literal["claim-matcher-set-v1"]
    matcher_set_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    proposition_catalog_version: Literal["claim-proposition-catalog-v1"]
    proposition_catalog_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    case_catalog_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    source_resolution_version: Literal["source-text-resolution-v1"]
    guard_version: Literal["high-risk-guard-v1"]
    answer_mode_contract_version: Literal["answer-mode-v1"]
    answer_mode_contract_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    abstention_contract_version: Literal["abstention-v1"]
    abstention_contract_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    visibility_contract_version: Literal["answer-visibility-v1"]
    visibility_contract_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class GroundedArtifactProvenance(StrictGroundedContract):
    evaluation_plane: EvaluationPlaneProvenance
    sut: SutProvenance
    dataset: DatasetArtifactProvenance
    adapter: GroundedAdapterProvenance
    compatibility: GroundedCompatibilityProvenance
    prompt: PromptIdentity
    model: ModelIdentity


class GroundedLogicalResult(StrictGroundedContract):
    dataset_snapshot: GroundedDatasetDocument
    observation_snapshot: GroundedObservationBatch
    evaluation: GroundedRunEvaluation


class GroundedRunArtifactDocument(StrictGroundedContract):
    schema_version: Literal["grounded-run-artifact-v1"]
    run: RunEnvelope
    provenance: GroundedArtifactProvenance
    logical_result: GroundedLogicalResult
    logical_digest: LogicalDigest
