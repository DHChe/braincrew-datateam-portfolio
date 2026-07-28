"""Create-only live observation capture for the pinned Verification experiment."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal, cast
from uuid import UUID

import httpx
from pydantic import BaseModel, Field, field_validator, model_validator

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
    "parsing": "parsing-quality-v1",
    "retrieval": "retrieval-quality-v1",
    "grounded": "grounded-answer-v1",
    "operational": OPERATIONAL_EVALUATOR_VERSION,
}
ADAPTER_VERSIONS = {
    "parsing": "fixture-parsing-sut-v1",
    "retrieval": "ax-sut-http-v1",
    "grounded": "ax-sut-http-v1",
}


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


def load_reviewed_principal_binding(path: Path) -> ReviewedPrincipalBinding:
    # The reviewed receipt loader owns the digest, SHA, completion, subject, and
    # attachment-binding checks. This command exposes only its reviewed principal.
    from braincrew.live_preflight import _load_reviewed_handoff_binding

    binding = _load_reviewed_handoff_binding(path)
    return ReviewedPrincipalBinding(
        tenant_id=binding.tenant_id,
        user_id=binding.subject_id,
    )


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
        raise ValueError("live capture requires the pinned AX commit")
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

    corpus_identities: set[tuple[str, str]] = set()
    confirmed_roles_by_request: dict[str, tuple[str, ...]] = {}
    for corpus_role in roles:
        corpus_observation = _adapter(
            base_url=base_url,
            principal=principal,
            role=corpus_role,
            transport=transport,
        ).corpus_identity(context=_context(run_id, f"corpus-{corpus_role}", "corpus-identity"))
        confirmed_roles_by_request[corpus_role] = tuple(corpus_observation.response.principal_roles)
        corpus_identities.add(
            (
                corpus_observation.response.corpus_id,
                corpus_observation.response.corpus_digest,
            )
        )
    expected_role_evidence = {role: (role,) for role in required_roles}
    if confirmed_roles_by_request != expected_role_evidence:
        raise ValueError("AX-confirmed corpus roles do not match required dataset roles")
    if len(corpus_identities) != 1:
        raise ValueError("corpus identity differs across dataset roles")
    corpus_id, corpus_digest = corpus_identities.pop()

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
                available=True,
                error=None,
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
        corpus_digest=corpus_digest,
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
