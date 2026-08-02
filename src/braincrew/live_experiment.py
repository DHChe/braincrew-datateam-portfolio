"""Create-only live observation capture for the pinned Verification experiment."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path, PureWindowsPath
from tempfile import TemporaryDirectory
from typing import Literal, cast
from uuid import UUID

import httpx
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

from braincrew.ax_http_adapter import (
    AnswerCitation,
    AxHttpAdapter,
    AxHttpAdapterConfig,
    AxRequestContext,
    RetrievalCandidate,
)
from braincrew.comparison import (
    COST_IMPROVEMENT_MINIMUM,
    COST_REGRESSION_LIMIT,
    LATENCY_IMPROVEMENT_MINIMUM,
    LATENCY_REGRESSION_LIMIT,
    QUALITY_IMPROVEMENT_MINIMUM,
    QUALITY_REGRESSION_LIMIT,
    ExperimentProvenance,
)
from braincrew.contracts import (
    PARSING_EVALUATOR_V2,
    EvidenceSpanExpectation,
    ParsingListExpectation,
    ParsingObservation,
    ParsingObservationBatch,
    ParsingTableExpectation,
    RetrievalCandidateObservation,
    RetrievalCase,
    RetrievalObservation,
    RetrievalObservationBatch,
    RetrievalSourceExpectation,
    StrictContract,
)
from braincrew.dataset_registry import DatasetBundleSnapshot, DatasetValidationReport
from braincrew.digest import canonical_digest
from braincrew.grounded_contracts import (
    AnswerMode,
    AnswerPathHealth,
    EvidenceAlternative,
    GroundedCase,
    GroundedCitation,
    GroundedObservation,
    GroundedObservationBatch,
    GroundedStructuredAnswer,
    SourceTextResolution,
    canonical_ax_role,
)
from braincrew.live_preflight import PINNED_AX_SHA
from braincrew.operational_evaluator import (
    CLIENT_TOTAL_LATENCY_DEFINITION,
    OPERATIONAL_EVALUATOR_VERSION,
    OperationalMeasurement,
)
from braincrew.repository import RepositoryState

TOP_K = 5
EVIDENCE_LIMITS = {"baseline": 3, "candidate": 5}
PROMPT_ID = "ax-answer-runtime-source-v1"
PROMPT_SOURCE = Path("backend/src/ax_engine/answers/service.py")
THRESHOLD_VERSION = "release-thresholds-v1"
EVALUATOR_VERSIONS = {
    "parsing": PARSING_EVALUATOR_V2,
    "retrieval": "retrieval-quality-v1",
    "grounded": "grounded-answer-v1",
    "operational": OPERATIONAL_EVALUATOR_VERSION,
}
ADAPTER_VERSIONS = {
    "parsing": "fixture-parsing-sut-v1",
    "retrieval": "ax-sut-http-v1",
    "grounded": "ax-sut-http-v1",
}
LIVE_RETRIEVAL_CASE_COUNT = 9
LIVE_GROUNDED_CASE_COUNT = 15
LIVE_PARSING_CASE_COUNT = 6
LIVE_PARSING_ROLE = "HRPractitioner"


class ReviewedPrincipalBinding(StrictContract):
    tenant_id: str
    user_id: str

    @field_validator("tenant_id", "user_id")
    @classmethod
    def require_canonical_uuid(cls, value: str) -> str:
        if str(UUID(value)) != value:
            raise ValueError("principal identifiers must be canonical UUIDs")
        return value


class SutStateSubject(StrictContract):
    repository: Literal["AX_portfolio"]
    checkout_path: str = Field(min_length=1)
    checked_at: datetime


class SutStateWarrant(StrictContract):
    schema_version: Literal["sut-state-warrant-v1"]
    method: Literal["read-only-git-check"]
    subject: SutStateSubject
    commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    dirty_worktree: bool


class CaptureArtifactReference(StrictContract):
    file_name: str = Field(min_length=1)
    content_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    case_count: int = Field(ge=1)

    @field_validator("file_name")
    @classmethod
    def require_bare_file_name(cls, file_name: str) -> str:
        if (
            file_name in {".", ".."}
            or Path(file_name).name != file_name
            or PureWindowsPath(file_name).name != file_name
        ):
            raise ValueError("capture artifact file name must be a bare filename")
        return file_name


class LiveExperimentCaptureManifest(StrictContract):
    schema_version: Literal["live-experiment-capture-v1"]
    run_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    role: Literal["baseline", "candidate"]
    captured_at: datetime
    provenance: ExperimentProvenance
    sut_state_warrant: SutStateWarrant
    verification_case_ids: tuple[str, ...] = Field(min_length=30, max_length=30)
    live_case_ids: tuple[str, ...] = Field(min_length=24, max_length=24)
    fixture_case_ids: tuple[str, ...] = Field(min_length=6, max_length=6)
    retrieval_observations: CaptureArtifactReference
    grounded_observations: CaptureArtifactReference
    logical_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def bind_execution_identity(self) -> LiveExperimentCaptureManifest:
        if set(self.live_case_ids) & set(self.fixture_case_ids):
            raise ValueError("live and fixture case identities must be disjoint")
        if set(self.verification_case_ids) != set(self.live_case_ids) | set(self.fixture_case_ids):
            raise ValueError("capture case partition must cover all Verification cases")
        expected_limit = EVIDENCE_LIMITS[self.role]
        if self.provenance.evidence_limit != expected_limit:
            raise ValueError("capture role and evidence limit must agree")
        if self.provenance.execution_mode != "live":
            raise ValueError("live capture provenance must declare live execution")
        if (
            self.provenance.sut_sha != self.sut_state_warrant.commit_sha
            or self.provenance.sut_dirty != self.sut_state_warrant.dirty_worktree
        ):
            raise ValueError("SUT provenance must match the read-only state warrant")
        return self


@dataclass(frozen=True)
class LiveExperimentCapture:
    manifest: LiveExperimentCaptureManifest
    retrieval_observations: RetrievalObservationBatch
    grounded_observations: GroundedObservationBatch


class LiveParsingCaptureManifest(StrictContract):
    """Create-only provenance for live parser observations outside the 24-case capture."""

    schema_version: Literal["live-parsing-capture-v1"]
    run_id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
    captured_at: datetime
    evaluation_plane_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    evaluation_plane_dirty: bool
    dataset_id: Literal["braincrew-evaluation-dataset"]
    dataset_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    dataset_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    sut_state_warrant: SutStateWarrant
    verification_case_ids: tuple[str, ...] = Field(
        min_length=LIVE_PARSING_CASE_COUNT,
        max_length=LIVE_PARSING_CASE_COUNT,
    )
    document_attachment_ids: dict[str, str] = Field(
        min_length=LIVE_PARSING_CASE_COUNT,
        max_length=LIVE_PARSING_CASE_COUNT,
    )
    adapter_version: Literal["ax-sut-http-v1"]
    parser_name: str = Field(min_length=1)
    parser_version: str = Field(min_length=1)
    parsing_observations: CaptureArtifactReference
    logical_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")

    @model_validator(mode="after")
    def bind_live_parsing_identity(self) -> LiveParsingCaptureManifest:
        if self.sut_state_warrant.commit_sha != PINNED_AX_SHA:
            raise ValueError(
                "live parsing capture SUT commit does not match the under-test AX commit"
            )
        if self.sut_state_warrant.dirty_worktree:
            raise ValueError("live parsing capture requires a clean SUT checkout")
        if len(set(self.verification_case_ids)) != LIVE_PARSING_CASE_COUNT:
            raise ValueError("live parsing capture case identities must be unique")
        if len(set(self.document_attachment_ids.values())) != LIVE_PARSING_CASE_COUNT:
            raise ValueError("live parsing capture attachment identities must be unique")
        return self


@dataclass(frozen=True)
class LiveParsingObservationCapture:
    manifest: LiveParsingCaptureManifest
    observations: ParsingObservationBatch


class LiveParsingAttachmentMapping(StrictContract):
    """Operator-supplied v3 document-to-AX attachment identities for one capture."""

    schema_version: Literal["live-parsing-attachment-mapping-v1"]
    document_attachment_ids: dict[str, str] = Field(
        min_length=LIVE_PARSING_CASE_COUNT,
        max_length=LIVE_PARSING_CASE_COUNT,
    )

    @model_validator(mode="after")
    def require_distinct_attachment_ids(self) -> LiveParsingAttachmentMapping:
        if any(not attachment_id for attachment_id in self.document_attachment_ids.values()):
            raise ValueError(
                "live parsing attachment mapping contains an empty attachment identity"
            )
        if len(set(self.document_attachment_ids.values())) != LIVE_PARSING_CASE_COUNT:
            raise ValueError("live parsing attachment mapping must contain distinct attachments")
        return self


def load_reviewed_principal_binding(path: Path) -> ReviewedPrincipalBinding:
    # The reviewed receipt loader owns the digest, SHA, completion, subject, and
    # attachment-binding checks. This command exposes only its reviewed principal.
    from braincrew.live_preflight import _load_reviewed_handoff_binding

    binding = _load_reviewed_handoff_binding(path)
    return ReviewedPrincipalBinding(
        tenant_id=binding.tenant_id,
        user_id=binding.subject_id,
    )


def load_live_parsing_attachment_mapping(path: Path) -> LiveParsingAttachmentMapping:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"live parsing attachment mapping cannot be read: {error}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"live parsing attachment mapping is not valid JSON: {error}") from error
    try:
        return LiveParsingAttachmentMapping.model_validate(payload)
    except ValidationError as error:
        raise ValueError(f"live parsing attachment mapping does not validate: {error}") from error


def _sha256_bytes(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _adapter(
    *,
    base_url: str,
    principal: ReviewedPrincipalBinding,
    role: str,
    transport: httpx.BaseTransport | None,
) -> AxHttpAdapter:
    return AxHttpAdapter(
        AxHttpAdapterConfig(
            base_url=base_url,
            sut_commit_sha=PINNED_AX_SHA,
            tenant_id=principal.tenant_id,
            user_id=principal.user_id,
            roles=(role,),
        ),
        transport=transport,
    )


def _context(run_id: str, case_id: str, operation: str) -> AxRequestContext:
    return AxRequestContext(
        run_id=run_id,
        case_id=case_id,
        eval_correlation_id=f"{run_id}:{case_id}:{operation}",
    )


def _source_texts(snapshot: DatasetBundleSnapshot) -> dict[str, str]:
    return {
        case.document.id: case.document.canonical_text for case in snapshot.parsing_dataset.cases
    }


def _retrieval_expectations(case: RetrievalCase) -> tuple[RetrievalSourceExpectation, ...]:
    return tuple(
        alternative for group in case.expected.evidence_groups for alternative in group.alternatives
    ) + tuple(case.expected.forbidden_sources)


def _normalize_retrieval_candidate(
    candidate: RetrievalCandidate,
    *,
    case: RetrievalCase,
    source_texts: dict[str, str],
    rank: int,
) -> RetrievalCandidateObservation:
    logical = next(
        (
            item
            for item in _retrieval_expectations(case)
            if item.record_id == candidate.source_id
            and item.record_kind == candidate.source_class
            and candidate.snippet in source_texts.get(item.record_id, "")
        ),
        None,
    )
    visibility_allowed = candidate.visibility_decision.get("allowed")
    visibility_reason = candidate.visibility_decision.get("reason")
    if not isinstance(visibility_allowed, bool) or not isinstance(visibility_reason, str):
        raise ValueError("AX retrieval visibility decision is incomplete")
    return RetrievalCandidateObservation(
        rank=rank,
        record_kind=(
            logical.record_kind
            if logical is not None
            else candidate.source_class or candidate.record_kind
        ),
        record_id=(
            logical.record_id if logical is not None else candidate.source_id or candidate.record_id
        ),
        evidence_span_id=(
            logical.evidence_span_id if logical is not None else candidate.evidence_span_id
        ),
        source_text_digest=(logical.source_text_digest if logical is not None else None),
        authority_level=(
            logical.authority_level if logical is not None else candidate.authority_level
        ),
        visibility_allowed=visibility_allowed,
        visibility_reason=visibility_reason,
    )


def _grounded_alternatives(case: GroundedCase) -> tuple[EvidenceAlternative, ...]:
    return tuple(
        alternative
        for proposition in case.propositions
        for group in (
            *proposition.supporting_evidence_groups,
            *proposition.contradicting_evidence_groups,
        )
        for alternative in group.alternatives
    )


def _normalize_grounded_citation(
    citation: AnswerCitation,
    *,
    case: GroundedCase,
    source_texts: dict[str, str],
) -> tuple[GroundedCitation, SourceTextResolution | None]:
    logical = next(
        (
            item
            for item in _grounded_alternatives(case)
            if item.record_id == citation.source_id
            and item.record_kind == citation.source_class
            and citation.snippet in source_texts.get(item.record_id, "")
        ),
        None,
    )
    if logical is None:
        digest = _sha256_bytes(citation.snippet.encode("utf-8"))
        return (
            GroundedCitation(
                record_kind=citation.source_class or citation.record_kind,
                record_id=citation.source_id or citation.record_id,
                evidence_span_id=citation.evidence_span_id or citation.record_id,
                source_text_digest=digest,
                claim_paths=tuple(citation.claim_paths),
            ),
            SourceTextResolution(
                record_kind=citation.source_class or citation.record_kind,
                record_id=citation.source_id or citation.record_id,
                text=citation.snippet,
                source_text_digest=digest,
            ),
        )
    source_text = source_texts[logical.record_id]
    return (
        GroundedCitation(
            record_kind=logical.record_kind,
            record_id=logical.record_id,
            evidence_span_id=logical.evidence_span_id,
            source_text_digest=logical.source_text_digest,
            claim_paths=tuple(citation.claim_paths),
        ),
        SourceTextResolution(
            record_kind=logical.record_kind,
            record_id=logical.record_id,
            text=source_text,
            source_text_digest=logical.source_text_digest,
        ),
    )


def _answer_mode(value: str) -> AnswerMode:
    normalized = {"risk_review": "review_required"}.get(value, value)
    allowed = {
        "direct_grounded",
        "conditional_grounded",
        "insufficient_evidence",
        "out_of_scope",
        "review_required",
    }
    if normalized not in allowed:
        raise ValueError("AX answer mode is not representable by the evaluator contract")
    return cast(AnswerMode, normalized)


def _answer_path_health(provider_metadata: dict[str, object]) -> AnswerPathHealth:
    return AnswerPathHealth.model_validate(
        {
            "llm_call_performed": provider_metadata.get("llm_call_performed"),
            "llm_call_succeeded": provider_metadata.get("llm_call_succeeded"),
            "failure_reason": provider_metadata.get("failure_reason"),
            "citation_contract_violation": provider_metadata.get("citation_contract_violation"),
            "unsafe_provider_output": provider_metadata.get("unsafe_provider_output"),
        }
    )


def _threshold_digest() -> str:
    return canonical_digest(
        {
            "quality_regression_limit": str(QUALITY_REGRESSION_LIMIT),
            "quality_improvement_minimum": str(QUALITY_IMPROVEMENT_MINIMUM),
            "latency_regression_limit": str(LATENCY_REGRESSION_LIMIT),
            "latency_improvement_minimum": str(LATENCY_IMPROVEMENT_MINIMUM),
            "cost_regression_limit": str(COST_REGRESSION_LIMIT),
            "cost_improvement_minimum": str(COST_IMPROVEMENT_MINIMUM),
        }
    )


def _runtime_environment_digest() -> str:
    return canonical_digest(
        {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "executable": Path(sys.executable).name,
        }
    )


def capture_live_experiment(
    *,
    run_id: str,
    role: Literal["baseline", "candidate"],
    captured_at: datetime,
    evaluation_state: RepositoryState,
    sut_state: SutStateWarrant,
    sut_source_root: Path,
    base_url: str,
    principal: ReviewedPrincipalBinding,
    dataset_validation: DatasetValidationReport,
    dependency_lock_path: Path,
    transport: httpx.BaseTransport | None = None,
    clock_ns: Callable[[], int] = time.perf_counter_ns,
) -> LiveExperimentCapture:
    if evaluation_state.dirty_worktree:
        raise ValueError("live capture requires a clean committed Evaluation Plane")
    if sut_state.commit_sha != PINNED_AX_SHA:
        raise ValueError("live capture SUT commit does not match the under-test AX commit")
    if sut_state.dirty_worktree:
        raise ValueError("live capture requires a clean SUT checkout")
    if dataset_validation.state != "VALID" or dataset_validation.snapshot is None:
        raise ValueError("live capture requires the validated frozen dataset")
    snapshot = dataset_validation.snapshot
    source_texts = _source_texts(snapshot)
    verification_records = tuple(
        record for record in snapshot.case_records if record.split == "Verification"
    )
    verification_case_ids = tuple(record.case_id for record in verification_records)
    fixture_case_ids = tuple(
        record.case_id for record in verification_records if record.primary_focus == "parsing"
    )
    live_case_ids = tuple(
        record.case_id for record in verification_records if record.primary_focus != "parsing"
    )
    retrieval_cases = tuple(
        case for case in snapshot.retrieval_dataset.cases if case.split == "verification"
    )
    grounded_cases = tuple(
        case for case in snapshot.grounded_dataset.cases if case.split == "Verification"
    )
    required_roles = frozenset(
        {
            *(canonical_ax_role(case.role) for case in retrieval_cases),
            *(canonical_ax_role(case.role) for case in grounded_cases),
        }
    )
    roles = tuple(sorted(required_roles))

    corpus_ids: set[str] = set()
    corpus_digests_by_role: dict[str, str] = {}
    confirmed_roles_by_request: dict[str, tuple[str, ...]] = {}
    for corpus_role in roles:
        corpus_observation = _adapter(
            base_url=base_url,
            principal=principal,
            role=corpus_role,
            transport=transport,
        ).corpus_identity(context=_context(run_id, f"corpus-{corpus_role}", "corpus-identity"))
        confirmed_roles_by_request[corpus_role] = tuple(corpus_observation.response.principal_roles)
        corpus_ids.add(corpus_observation.response.corpus_id)
        corpus_digests_by_role[corpus_role] = corpus_observation.response.corpus_digest
    expected_role_evidence = {role: (role,) for role in required_roles}
    if confirmed_roles_by_request != expected_role_evidence:
        raise ValueError("AX-confirmed corpus roles do not match required dataset roles")
    if len(corpus_ids) != 1:
        raise ValueError("corpus ID differs across dataset roles")
    corpus_id = corpus_ids.pop()

    retrieval_observations: list[RetrievalObservation] = []
    for retrieval_case in retrieval_cases:
        retrieval_role = canonical_ax_role(retrieval_case.role)
        retrieval_adapter = _adapter(
            base_url=base_url,
            principal=principal,
            role=retrieval_role,
            transport=transport,
        )
        started_ns = clock_ns()
        retrieval_ax_observation = retrieval_adapter.retrieve(
            context=_context(run_id, retrieval_case.id, "retrieve"),
            query=retrieval_case.query,
            top_k=TOP_K,
        )
        latency_ms = Decimal(clock_ns() - started_ns) / Decimal(1_000_000)
        if (
            retrieval_ax_observation.response.query != retrieval_case.query
            or retrieval_ax_observation.response.top_k != TOP_K
        ):
            raise ValueError("AX retrieval response does not bind the requested case")
        retrieval_observations.append(
            RetrievalObservation(
                schema_version="retrieval-observation-v1",
                case_id=retrieval_case.id,
                query=retrieval_case.query,
                retrieval_available=True,
                failure_code=None,
                candidates=[
                    _normalize_retrieval_candidate(
                        candidate,
                        case=retrieval_case,
                        source_texts=source_texts,
                        rank=rank,
                    )
                    for rank, candidate in enumerate(
                        retrieval_ax_observation.response.candidates,
                        start=1,
                    )
                ],
                operational=OperationalMeasurement(
                    latency_ms=latency_ms,
                    latency_definition=CLIENT_TOTAL_LATENCY_DEFINITION,
                    cost_usd=None,
                    cost_status="unmeasured",
                ),
            )
        )

    evidence_limit = EVIDENCE_LIMITS[role]
    grounded_observations: list[GroundedObservation] = []
    model_identities: set[tuple[str, str]] = set()
    for grounded_case in grounded_cases:
        expected_role = canonical_ax_role(grounded_case.role)
        answer_adapter = _adapter(
            base_url=base_url,
            principal=principal,
            role=expected_role,
            transport=transport,
        )
        started_ns = clock_ns()
        answer_observation = answer_adapter.answer(
            context=_context(run_id, grounded_case.case_id, "answer"),
            query=grounded_case.query,
            top_k=TOP_K,
            evidence_limit=evidence_limit,
        )
        latency_ms = Decimal(clock_ns() - started_ns) / Decimal(1_000_000)
        if answer_observation.response.query != grounded_case.query:
            raise ValueError("AX answer response does not bind the requested case")
        executed_role = answer_observation.request.roles[0]
        provider = answer_observation.response.provider_metadata.get("provider_adapter")
        model = answer_observation.response.provider_metadata.get("model")
        if not isinstance(provider, str) or not provider or not isinstance(model, str) or not model:
            raise ValueError("AX answer response omits model identity")
        answer_path = _answer_path_health(answer_observation.response.provider_metadata)
        model_identities.add((provider, model))
        citations_and_sources = [
            _normalize_grounded_citation(
                citation,
                case=grounded_case,
                source_texts=source_texts,
            )
            for citation in answer_observation.response.citations
        ]
        unique_sources = {
            (source.record_kind, source.record_id): source
            for _, source in citations_and_sources
            if source is not None
        }
        answer = answer_observation.response.structured_answer
        grounded_observations.append(
            GroundedObservation(
                case_id=grounded_case.case_id,
                executed_role=executed_role,
                available=answer_path.answer_quality_available,
                error=answer_path.failure_reason,
                answer_path=answer_path,
                answer_mode=_answer_mode(answer_observation.response.answer_mode),
                structured_answer=GroundedStructuredAnswer(
                    summary=answer.summary,
                    answer=answer.answer,
                    grounds=tuple(answer.grounds),
                    review_points=tuple(answer.review_points),
                    additional_checks=tuple(answer.additional_checks),
                    risk_warning=answer.risk_warning,
                ),
                citations=tuple(item[0] for item in citations_and_sources),
                source_texts=tuple(unique_sources.values()),
                operational=OperationalMeasurement(
                    latency_ms=latency_ms,
                    latency_definition=CLIENT_TOTAL_LATENCY_DEFINITION,
                    cost_usd=None,
                    cost_status="unmeasured",
                ),
            )
        )
    if len(model_identities) != 1:
        raise ValueError("model identity differs across answer responses")
    model_provider, model_name = model_identities.pop()

    retrieval_batch = RetrievalObservationBatch(
        schema_version="retrieval-observation-batch-v1",
        adapter_version="ax-sut-http-v1",
        observations=retrieval_observations,
    )
    grounded_batch = GroundedObservationBatch(
        schema_version="grounded-observation-batch-v1",
        adapter_version="ax-sut-http-v1",
        sut_commit_sha=sut_state.commit_sha,
        observations=tuple(grounded_observations),
    )
    prompt_path = sut_source_root / PROMPT_SOURCE
    prompt_hash = _sha256_bytes(prompt_path.read_bytes())
    provenance = ExperimentProvenance(
        evaluation_plane_sha=evaluation_state.commit_sha,
        evaluation_plane_dirty=evaluation_state.dirty_worktree,
        sut_sha=sut_state.commit_sha,
        sut_dirty=sut_state.dirty_worktree,
        dataset_id=snapshot.manifest.dataset_id,
        dataset_version=snapshot.manifest.dataset_version,
        dataset_digest=snapshot.dataset_digest,
        corpus_id=corpus_id,
        corpus_digests_by_role=corpus_digests_by_role,
        evaluator_versions=EVALUATOR_VERSIONS,
        prompt_id=PROMPT_ID,
        prompt_hash=prompt_hash,
        model_provider=model_provider,
        model_name=model_name,
        model_parameters={"reporting_status": "not_exposed_by_ax-http-v1"},
        retrieval_top_k=TOP_K,
        evidence_limit=evidence_limit,
        fixed_retrieval_config_digest=canonical_digest(
            {"adapter_version": "ax-sut-http-v1", "top_k": TOP_K}
        ),
        adapter_versions=ADAPTER_VERSIONS,
        threshold_version=THRESHOLD_VERSION,
        threshold_digest=_threshold_digest(),
        dependency_lock_digest=_sha256_bytes(dependency_lock_path.read_bytes()),
        runtime_environment_digest=_runtime_environment_digest(),
        execution_mode="live",
    )
    retrieval_reference = CaptureArtifactReference(
        file_name=f"{run_id}.retrieval-observations.json",
        content_digest=canonical_digest(retrieval_batch.model_dump(mode="json")),
        case_count=len(retrieval_batch.observations),
    )
    grounded_reference = CaptureArtifactReference(
        file_name=f"{run_id}.grounded-observations.json",
        content_digest=canonical_digest(grounded_batch.model_dump(mode="json")),
        case_count=len(grounded_batch.observations),
    )
    manifest = LiveExperimentCaptureManifest(
        schema_version="live-experiment-capture-v1",
        run_id=run_id,
        role=role,
        captured_at=captured_at,
        provenance=provenance,
        sut_state_warrant=sut_state,
        verification_case_ids=verification_case_ids,
        live_case_ids=live_case_ids,
        fixture_case_ids=fixture_case_ids,
        retrieval_observations=retrieval_reference,
        grounded_observations=grounded_reference,
        logical_digest="sha256:" + "0" * 64,
    )
    manifest = manifest.model_copy(
        update={
            "logical_digest": canonical_digest(
                manifest.model_dump(mode="json", exclude={"logical_digest"})
            )
        }
    )
    return LiveExperimentCapture(
        manifest=manifest,
        retrieval_observations=retrieval_batch,
        grounded_observations=grounded_batch,
    )


def capture_live_parsing_observations(
    *,
    run_id: str,
    captured_at: datetime,
    evaluation_state: RepositoryState,
    sut_state: SutStateWarrant,
    base_url: str,
    principal: ReviewedPrincipalBinding,
    attachment_ids_by_document_id: Mapping[str, str],
    dataset_validation: DatasetValidationReport,
    transport: httpx.BaseTransport | None = None,
) -> LiveParsingObservationCapture:
    """Capture exactly the six v3 Verification parser observations from AX.

    The attachment mapping only chooses the read-only AX endpoint.  AX's returned
    text, digest, and spans must independently reproduce the frozen document before
    any observation is emitted.  Dataset expected values are intentionally not read.
    """
    if sut_state.commit_sha != PINNED_AX_SHA:
        raise ValueError("live parsing capture SUT commit does not match the under-test AX commit")
    if sut_state.dirty_worktree:
        raise ValueError("live parsing capture requires a clean SUT checkout")
    if dataset_validation.state != "VALID" or dataset_validation.snapshot is None:
        raise ValueError("live parsing capture requires the validated frozen dataset")

    snapshot = dataset_validation.snapshot
    parsing_cases = tuple(
        sorted(
            (case for case in snapshot.parsing_dataset.cases if case.split == "verification"),
            key=lambda case: case.id,
        )
    )
    if len(parsing_cases) != LIVE_PARSING_CASE_COUNT:
        raise ValueError("live parsing capture requires exactly six Verification parsing cases")
    expected_document_ids = {case.document.id for case in parsing_cases}
    if len(expected_document_ids) != LIVE_PARSING_CASE_COUNT:
        raise ValueError("live parsing capture requires one document per Verification parsing case")
    if set(attachment_ids_by_document_id) != expected_document_ids:
        raise ValueError("attachment mapping must cover exactly the Verification parsing documents")
    if any(
        not isinstance(attachment_id, str) or not attachment_id
        for attachment_id in attachment_ids_by_document_id.values()
    ):
        raise ValueError("attachment mapping contains an invalid attachment identity")
    attachment_ids = {
        document_id: attachment_ids_by_document_id[document_id]
        for document_id in sorted(expected_document_ids)
    }
    if len(set(attachment_ids.values())) != LIVE_PARSING_CASE_COUNT:
        raise ValueError(
            "attachment mapping must bind one attachment to each Verification document"
        )

    adapter = _adapter(
        base_url=base_url,
        principal=principal,
        role=LIVE_PARSING_ROLE,
        transport=transport,
    )
    observations: list[ParsingObservation] = []
    parser_names: set[str] = set()
    parser_versions: set[str] = set()
    for case in parsing_cases:
        attachment_id = attachment_ids[case.document.id]
        parsed = adapter.parse(
            context=_context(run_id, case.id, "parse-observation"),
            attachment_id=attachment_id,
        ).response
        if parsed.attachment_id != attachment_id:
            raise ValueError("live parsing response attachment identity does not match the mapping")
        if not parsed.parse_available:
            raise ValueError(
                "live parsing response is unavailable for "
                f"{case.id}: {parsed.failure_code or 'unknown'}"
            )
        if parsed.failure_code is not None or not parsed.parser_name or not parsed.parser_version:
            raise ValueError("live parsing response has an incomplete parser identity")
        if parsed.text_truncated:
            raise ValueError("live parsing response text is truncated")

        document_text = case.document.canonical_text
        document_digest = _sha256_bytes(document_text.encode("utf-8"))
        if parsed.extracted_text != document_text:
            raise ValueError(
                "live parsing response text does not match the frozen parsing document"
            )
        if parsed.extracted_text_digest != document_digest:
            raise ValueError(
                "live parsing response digest does not match the frozen parsing document"
            )

        evidence_spans: list[EvidenceSpanExpectation] = []
        for span in parsed.evidence_spans:
            if span.source_text_digest != document_digest:
                raise ValueError(
                    "live parsing evidence span digest does not match the frozen document"
                )
            if (
                span.end_char > len(document_text)
                or document_text[span.start_char : span.end_char] != span.text
            ):
                raise ValueError("live parsing evidence span does not match the frozen document")
            evidence_spans.append(
                # The Expectation types are reused as observation carriers. Every value below comes
                # from the AX response; nothing here reads case.expected, despite the type name.
                EvidenceSpanExpectation(
                    id=span.id,
                    text=span.text,
                    start_char=span.start_char,
                    end_char=span.end_char,
                    source_text_digest=span.source_text_digest,
                )
            )
        observations.append(
            ParsingObservation(
                schema_version="parsing-observation-v1",
                case_id=case.id,
                parse_available=True,
                parser_version=parsed.parser_version,
                failure_code=None,
                evidence_spans=evidence_spans,
                headings=list(parsed.headings),
                metadata=dict(parsed.metadata),
                table=(
                    None
                    if parsed.table is None
                    else ParsingTableExpectation(
                        columns=list(parsed.table.columns),
                        rows=[list(row) for row in parsed.table.rows],
                    )
                ),
                list=(
                    None
                    if parsed.list is None
                    else ParsingListExpectation(
                        items=list(parsed.list.items),
                        ordered=parsed.list.ordered,
                    )
                ),
            )
        )
        parser_names.add(parsed.parser_name)
        parser_versions.add(parsed.parser_version)

    if len(parser_names) != 1 or len(parser_versions) != 1:
        raise ValueError("live parsing responses disagree on parser identity")
    parser_name = parser_names.pop()
    parser_version = parser_versions.pop()
    observation_batch = ParsingObservationBatch(
        schema_version="parsing-observation-batch-v1",
        adapter_version="ax-sut-http-v1",
        parser_version=parser_version,
        observations=observations,
    )
    observation_reference = CaptureArtifactReference(
        file_name=f"{run_id}.parsing-observations.json",
        content_digest=canonical_digest(observation_batch.model_dump(mode="json")),
        case_count=len(observation_batch.observations),
    )
    manifest = LiveParsingCaptureManifest(
        schema_version="live-parsing-capture-v1",
        run_id=run_id,
        captured_at=captured_at,
        evaluation_plane_commit_sha=evaluation_state.commit_sha,
        evaluation_plane_dirty=evaluation_state.dirty_worktree,
        dataset_id=snapshot.manifest.dataset_id,
        dataset_version=snapshot.manifest.dataset_version,
        dataset_digest=snapshot.dataset_digest,
        sut_state_warrant=sut_state,
        verification_case_ids=tuple(case.id for case in parsing_cases),
        document_attachment_ids=attachment_ids,
        adapter_version="ax-sut-http-v1",
        parser_name=parser_name,
        parser_version=parser_version,
        parsing_observations=observation_reference,
        logical_digest="sha256:" + "0" * 64,
    )
    manifest = manifest.model_copy(
        update={
            "logical_digest": canonical_digest(
                manifest.model_dump(mode="json", exclude={"logical_digest"})
            )
        }
    )
    return LiveParsingObservationCapture(manifest=manifest, observations=observation_batch)


def _serialized(model: BaseModel) -> str:
    return (
        json.dumps(
            model.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def write_live_experiment_capture(
    capture: LiveExperimentCapture,
    output_dir: Path,
) -> tuple[Path, Path, Path]:
    paths = (
        output_dir / f"{capture.manifest.run_id}.capture-manifest.json",
        output_dir / capture.manifest.retrieval_observations.file_name,
        output_dir / capture.manifest.grounded_observations.file_name,
    )
    if any(path.exists() for path in paths):
        raise FileExistsError("capture artifact already exists")
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = (
        _serialized(capture.manifest),
        _serialized(capture.retrieval_observations),
        _serialized(capture.grounded_observations),
    )
    linked: list[Path] = []
    try:
        with TemporaryDirectory(dir=output_dir) as temporary:
            temporary_dir = Path(temporary)
            for index, (path, payload) in enumerate(zip(paths, payloads, strict=True)):
                staged = temporary_dir / str(index)
                staged.write_text(payload, encoding="utf-8")
                os.link(staged, path)
                linked.append(path)
    except OSError:
        for path in linked:
            path.unlink(missing_ok=True)
        raise
    return paths


def write_live_parsing_observation_capture(
    capture: LiveParsingObservationCapture,
    output_dir: Path,
) -> tuple[Path, Path]:
    paths = (
        output_dir / f"{capture.manifest.run_id}.parsing-capture-manifest.json",
        output_dir / capture.manifest.parsing_observations.file_name,
    )
    if any(path.exists() for path in paths):
        raise FileExistsError("live parsing capture artifact already exists")
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = (_serialized(capture.manifest), _serialized(capture.observations))
    linked: list[Path] = []
    try:
        with TemporaryDirectory(dir=output_dir) as temporary:
            temporary_dir = Path(temporary)
            for index, (path, payload) in enumerate(zip(paths, payloads, strict=True)):
                staged = temporary_dir / str(index)
                staged.write_text(payload, encoding="utf-8")
                os.link(staged, path)
                linked.append(path)
    except OSError:
        for path in linked:
            path.unlink(missing_ok=True)
        raise
    return paths


def _load_capture_json(path: Path, *, label: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"{label} file cannot be read: {error}") from error
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} file is not valid JSON: {error}") from error


def _validate_capture_observation_reference(
    *,
    reference: CaptureArtifactReference,
    observations: RetrievalObservationBatch | GroundedObservationBatch,
    label: str,
) -> None:
    if canonical_digest(observations.model_dump(mode="json")) != reference.content_digest:
        raise ValueError(f"{label} observation content digest does not reproduce")
    if len(observations.observations) != reference.case_count:
        raise ValueError(f"{label} observation case count does not reproduce")


def _validate_capture_provenance_agreement(
    *,
    manifest: LiveExperimentCaptureManifest,
    retrieval_observations: RetrievalObservationBatch,
    grounded_observations: GroundedObservationBatch,
) -> None:
    adapter_versions = manifest.provenance.adapter_versions
    if retrieval_observations.adapter_version != adapter_versions.get("retrieval"):
        raise ValueError(
            "retrieval observation adapter version does not match capture manifest provenance"
        )
    if grounded_observations.adapter_version != adapter_versions.get("grounded"):
        raise ValueError(
            "grounded observation adapter version does not match capture manifest provenance"
        )
    if grounded_observations.sut_commit_sha != manifest.sut_state_warrant.commit_sha:
        raise ValueError(
            "grounded observation SUT commit SHA does not match capture manifest warrant"
        )


def replay_live_experiment_capture(path: Path) -> dict[str, str]:
    """Verify observation content digests, counts, case identities, adapters, and SUT SHA.

    Observation files must reproduce their declared content digests and case counts;
    their case identities must equal the live partition; their adapter versions and
    the grounded SUT commit SHA must agree with the manifest; and the manifest must
    reproduce its logical digest. This does not re-run AX or detect a consistently
    fabricated manifest and observation files.
    """
    try:
        manifest = LiveExperimentCaptureManifest.model_validate(
            _load_capture_json(path, label="capture manifest")
        )
    except ValidationError as error:
        raise ValueError(f"capture manifest does not validate: {error}") from error

    try:
        retrieval_observations = RetrievalObservationBatch.model_validate(
            _load_capture_json(
                path.parent / manifest.retrieval_observations.file_name,
                label="retrieval observation",
            )
        )
    except ValidationError as error:
        raise ValueError(f"retrieval observation file does not validate: {error}") from error

    try:
        grounded_observations = GroundedObservationBatch.model_validate(
            _load_capture_json(
                path.parent / manifest.grounded_observations.file_name,
                label="grounded observation",
            )
        )
    except ValidationError as error:
        raise ValueError(f"grounded observation file does not validate: {error}") from error

    _validate_capture_provenance_agreement(
        manifest=manifest,
        retrieval_observations=retrieval_observations,
        grounded_observations=grounded_observations,
    )
    _validate_capture_observation_reference(
        reference=manifest.retrieval_observations,
        observations=retrieval_observations,
        label="retrieval",
    )
    _validate_capture_observation_reference(
        reference=manifest.grounded_observations,
        observations=grounded_observations,
        label="grounded",
    )

    retrieval_case_ids = {
        observation.case_id for observation in retrieval_observations.observations
    }
    grounded_case_ids = {observation.case_id for observation in grounded_observations.observations}
    if (
        len(retrieval_case_ids) != LIVE_RETRIEVAL_CASE_COUNT
        or len(grounded_case_ids) != LIVE_GROUNDED_CASE_COUNT
        or retrieval_case_ids & grounded_case_ids
        or retrieval_case_ids | grounded_case_ids != set(manifest.live_case_ids)
    ):
        raise ValueError("observation case identities do not match the declared live partition")

    recomputed_logical_digest = canonical_digest(
        manifest.model_dump(mode="json", exclude={"logical_digest"})
    )
    if recomputed_logical_digest != manifest.logical_digest:
        raise ValueError("capture manifest logical digest does not reproduce")

    return {
        "logical_digest": recomputed_logical_digest,
        "retrieval_case_count": str(len(retrieval_observations.observations)),
        "grounded_case_count": str(len(grounded_observations.observations)),
    }
