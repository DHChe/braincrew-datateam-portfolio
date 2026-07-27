from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from types import MappingProxyType
from typing import Literal
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, model_validator

from braincrew.ax_http_adapter import (
    AxCanonicalRequest,
    AxHttpAdapter,
    AxHttpAdapterConfig,
    AxHttpFailure,
    AxRequestContext,
    CorpusIdentityObservation,
    CorpusIdentityResponse,
    HttpAttempt,
    OperationName,
    ParseObservation,
)
from braincrew.contracts import ParsingCase
from braincrew.dataset_registry import DatasetValidationReport
from braincrew.digest import canonical_digest

SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"
COMMIT_SHA_PATTERN = r"^[0-9a-f]{40}$"
SAFE_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$"
SAFE_DETAIL_PATTERN = r"^[A-Za-z0-9_.:-]{1,160}$"
PINNED_AX_SHA = "2bcaee3495fd7b3f624398819575cd86a5a15c47"
REVIEWED_HANDOFF_RECEIPT_SHA256 = "8d59a7907894532d702d0b7c658b8b28bc8370670b69f04884c42d8d1843c767"
PARSING_AUTHORIZATION_ROLE = "HRPractitioner"
EXPECTED_PARSER_IDENTITY = ("utf8-text", "stdlib-1")
PRINCIPAL_PARSE_TIMEOUT_SECONDS = 10.0
PRINCIPAL_ATTACHMENT_CAPTURE_CONTRACT: Literal["principal-attachment-preflight-v1"] = (
    "principal-attachment-preflight-v1"
)
FROZEN_DATASET_ID: Literal["braincrew-evaluation-dataset"] = "braincrew-evaluation-dataset"
FROZEN_DATASET_VERSION: Literal["2.0.0"] = "2.0.0"
FROZEN_DATASET_DIGEST = "sha256:ef6b0a1f50fcd2ecb8b5d7addc7bc5daaa54537899a1ac6faba7c784eee6e98a"
FROZEN_COMPONENT_DIGESTS: Mapping[str, str] = MappingProxyType(
    {
        "parsing": "sha256:a4ce3d2381853288e92cc2fd21df5cfcd9629db39ea134d8314594e146b48127",
        "retrieval": "sha256:5364cb7d7919304f5ebe78e4b7bd9bf2ed073c5e9f1e84c36f48697c2759fca8",
        "grounded": "sha256:f3a6f6848cccb4c5bddea8f5f9df9151b08b61b8537054c46afb7855957d3fbe",
    }
)
REVIEWED_PARSING_SOURCE_EVIDENCE: Mapping[str, tuple[str, str]] = MappingProxyType(
    {
        "synthetic-rule-015": (
            "sha256:6e418e4be8e4de344d6b3e0162d00177668483c21e864b477fae6b1b044bf7a2",
            "근속 연수 | 휴가 일수\n1년 | 15일\n3년 | 16일",
        ),
        "synthetic-rule-016": (
            "sha256:620ad58790745f5d1852c3e97a36ce40ca74d8b6dd6e010469ea44b2ec4b3a75",
            "퇴직 절차\n1. 퇴직 의사 제출\n2. 인수인계\n3. 자산 반납",
        ),
        "synthetic-rule-017": (
            "sha256:3982c372a75d30b3b1699a58a9d567ad0072fb088f3a10ab929dcbb6096319c6",
            "문서명: 육아휴직 안내\n담당: 피플팀\n육아휴직은 최대 1년이다.",
        ),
        "synthetic-rule-018": (
            "sha256:9070d1c9cab7d54d7836d1ef28369f2ab9a4968a23208e10a9e66585ecca8d1f",
            "제5조 초과근무\n평일 한도는 2시간이다. 주간 한도는 12시간이다.",
        ),
        "synthetic-rule-019": (
            "sha256:0937ba63f9fde634c13bea38c3974e0226b083fb299bfdd5a111789c190d0042",
            "제1절 신고\n괴롭힘 신고는 익명으로 가능하다.\n"
            "제2절 보호\n신고자에게 불이익을 주어서는 안 된다.",
        ),
        "synthetic-rule-020": (
            "sha256:333a023c2e477249aa2b16718826c897f4efed6c4358bd86fe4f6d9cc386a23d",
            "교육 과정 | 시간\n윤리 | 2시간\n안전 | 3시간\n이수 방법\n- 온라인\n- 집합",
        ),
    }
)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _ReceiptModel(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class _ReceiptRepository(_ReceiptModel):
    commit_sha: str


class _ReceiptTarget(_ReceiptModel):
    subject_id: str


class _ReceiptAttachment(_ReceiptModel):
    case_id: str
    attachment_id: str


class _ReviewedHandoffReceipt(_ReceiptModel):
    repository: _ReceiptRepository
    target: _ReceiptTarget
    state: str
    completion_confirmed: bool
    attachments: tuple[_ReceiptAttachment, ...]


@dataclass(frozen=True)
class _ReviewedHandoffBinding:
    subject_id: str
    attachment_mapping: Mapping[str, str]


class LivePreflightBlocker(StrictModel):
    code: str = Field(pattern=SAFE_DETAIL_PATTERN)
    operation: OperationName | None = None
    case_id: str | None = Field(default=None, pattern=SAFE_ID_PATTERN)
    request: AxCanonicalRequest | None = None
    detail: str | None = Field(default=None, pattern=SAFE_DETAIL_PATTERN)
    attempts: tuple[HttpAttempt, ...] = ()


class CorpusIdentityEvidence(StrictModel):
    context: AxRequestContext
    request: AxCanonicalRequest
    response: CorpusIdentityResponse
    response_digest: str = Field(pattern=SHA256_PATTERN)
    attempts: tuple[HttpAttempt, ...]


class SanitizedParseEvidenceSpan(StrictModel):
    id: str
    text_digest: str = Field(pattern=SHA256_PATTERN)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    source_text_digest: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def require_valid_range(self) -> SanitizedParseEvidenceSpan:
        if self.end_char <= self.start_char:
            raise ValueError("parse evidence span end must be greater than start")
        return self


class SanitizedTableShape(StrictModel):
    column_count: int = Field(ge=1)
    row_count: int = Field(ge=1)


class SanitizedListShape(StrictModel):
    item_count: int = Field(ge=1)
    ordered: bool


class SanitizedParseResponse(StrictModel):
    schema_version: Literal["ax-parse-observation-v1"]
    attachment_id: str
    lifecycle_state: str
    parse_state: str
    materialization_state: str
    parse_available: bool
    parser_name: str | None
    parser_version: str | None
    failure_code: str | None
    extracted_text_digest: str | None = Field(default=None, pattern=SHA256_PATTERN)
    text_truncated: bool
    evidence_spans: tuple[SanitizedParseEvidenceSpan, ...]
    headings_count: int = Field(ge=0)
    metadata_keys: tuple[str, ...]
    table_shape: SanitizedTableShape | None
    list_shape: SanitizedListShape | None
    unavailable_fields: tuple[str, ...]


class ParseObservationEvidence(StrictModel):
    context: AxRequestContext
    request: AxCanonicalRequest
    response: SanitizedParseResponse
    response_digest: str = Field(pattern=SHA256_PATTERN)
    attempts: tuple[HttpAttempt, ...]


class DatasetComponentDigests(StrictModel):
    parsing: str = Field(pattern=SHA256_PATTERN)
    retrieval: str = Field(pattern=SHA256_PATTERN)
    grounded: str = Field(pattern=SHA256_PATTERN)


class DatasetIdentityEvidence(StrictModel):
    id: Literal["braincrew-evaluation-dataset"]
    version: Literal["2.0.0"]
    content_digest: str = Field(pattern=SHA256_PATTERN)
    component_digests: DatasetComponentDigests

    @model_validator(mode="after")
    def require_frozen_dataset_digests(self) -> DatasetIdentityEvidence:
        if (
            self.content_digest != FROZEN_DATASET_DIGEST
            or self.component_digests.model_dump() != dict(FROZEN_COMPONENT_DIGESTS)
        ):
            raise ValueError("dataset identity must match the frozen dataset digests")
        return self


class LivePreflightArtifact(StrictModel):
    schema_version: Literal[
        "live-preflight-evidence-v1",
        "principal-attachment-preflight-evidence-v1",
    ]
    capture_state: Literal["captured"]
    capture_contract: Literal["principal-attachment-preflight-v1"] | None = None
    run_id: str = Field(pattern=SAFE_ID_PATTERN)
    captured_at: datetime
    evaluation_plane_sha: str = Field(pattern=COMMIT_SHA_PATTERN)
    sut_commit_sha: str = Field(pattern=COMMIT_SHA_PATTERN)
    dataset_identity: DatasetIdentityEvidence | None = None
    corpus_observations: tuple[CorpusIdentityEvidence, ...]
    parse_observations: tuple[ParseObservationEvidence, ...]
    blockers: tuple[LivePreflightBlocker, ...]
    logical_digest: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def require_aware_capture_time(self, info: ValidationInfo) -> LivePreflightArtifact:
        if self.captured_at.tzinfo is None or self.captured_at.utcoffset() is None:
            raise ValueError("captured_at must include a timezone")
        if self.sut_commit_sha != PINNED_AX_SHA:
            raise ValueError("live preflight artifact must use the pinned AX commit")
        observations: tuple[CorpusIdentityEvidence | ParseObservationEvidence, ...] = (
            *self.corpus_observations,
            *self.parse_observations,
        )
        for observation in observations:
            if (
                observation.context.run_id != self.run_id
                or observation.request.run_id != self.run_id
            ):
                raise ValueError("observation run_id must match artifact run_id")
            if (
                observation.context.case_id != observation.request.case_id
                or observation.context.eval_correlation_id
                != observation.request.eval_correlation_id
            ):
                raise ValueError("observation context must match canonical request identity")
        for observation in self.corpus_observations:
            expected = canonical_digest(observation.response.model_dump(mode="json"))
            if observation.response_digest != expected:
                raise ValueError("corpus response digest does not match sanitized response")
        for observation in self.parse_observations:
            expected = canonical_digest(observation.response.model_dump(mode="json"))
            if observation.response_digest != expected:
                raise ValueError("parse response digest does not match sanitized response")
        if self.schema_version == "principal-attachment-preflight-evidence-v1":
            if self.capture_contract != PRINCIPAL_ATTACHMENT_CAPTURE_CONTRACT:
                raise ValueError("principal attachment schema requires its capture contract")
            if self.dataset_identity is None:
                raise ValueError("principal attachment capture requires frozen dataset identity")
            _validate_principal_attachment_capture(
                self,
                reviewed_binding=_reviewed_binding_from_context(info),
            )
        else:
            if self.capture_contract is not None:
                raise ValueError("generic live preflight schema cannot declare a capture contract")
            if any(blocker.request is not None for blocker in self.blockers):
                raise ValueError("generic live preflight blocker cannot retain a request")
        if _contains_private_path(self.model_dump(mode="json")):
            raise ValueError("live preflight artifact cannot retain a private path")
        return self


def build_live_preflight_artifact(
    *,
    run_id: str,
    captured_at: datetime,
    evaluation_plane_sha: str,
    sut_commit_sha: str,
    corpus_observations: tuple[CorpusIdentityObservation, ...],
    parse_observations: tuple[ParseObservation, ...],
    blockers: tuple[LivePreflightBlocker, ...],
    dataset_identity: DatasetIdentityEvidence | None = None,
    capture_contract: Literal["principal-attachment-preflight-v1"] | None = None,
    _reviewed_handoff_binding: _ReviewedHandoffBinding | None = None,
) -> LivePreflightArtifact:
    # Pydantic __init__ cannot carry validation context; model_validate keeps the
    # independently reviewed receipt binding attached to principal validation.
    artifact = LivePreflightArtifact.model_validate(
        {
            "schema_version": (
                "principal-attachment-preflight-evidence-v1"
                if capture_contract is not None
                else "live-preflight-evidence-v1"
            ),
            "capture_state": "captured",
            "capture_contract": capture_contract,
            "run_id": run_id,
            "captured_at": captured_at,
            "evaluation_plane_sha": evaluation_plane_sha,
            "sut_commit_sha": sut_commit_sha,
            "dataset_identity": dataset_identity,
            "corpus_observations": tuple(_sanitize_corpus(item) for item in corpus_observations),
            "parse_observations": tuple(_sanitize_parse(item) for item in parse_observations),
            "blockers": tuple(_sanitize_blocker(item) for item in blockers),
            "logical_digest": "sha256:" + "0" * 64,
        },
        context={"reviewed_handoff_binding": _reviewed_handoff_binding},
    )
    return artifact.model_copy(
        update={"logical_digest": canonical_digest(_logical_payload(artifact))}
    )


def capture_principal_attachment_preflight(
    *,
    run_id: str,
    captured_at: datetime,
    evaluation_plane_sha: str,
    sut_commit_sha: str,
    base_url: str,
    tenant_id: str,
    user_id: str,
    attachment_mapping: Mapping[str, str],
    dataset_validation: DatasetValidationReport,
    handoff_receipt_path: Path,
    transport: httpx.BaseTransport | None = None,
) -> LivePreflightArtifact:
    reviewed_binding = _load_reviewed_handoff_binding(handoff_receipt_path)
    accepted_dataset_identity: DatasetIdentityEvidence | None = None

    def blocked(
        blocker: LivePreflightBlocker,
        parse_observations: tuple[ParseObservation, ...] = (),
    ) -> LivePreflightArtifact:
        return _blocked_capture(
            run_id=run_id,
            captured_at=captured_at,
            evaluation_plane_sha=evaluation_plane_sha,
            sut_commit_sha=sut_commit_sha,
            blocker=blocker,
            parse_observations=parse_observations,
            dataset_identity=accepted_dataset_identity,
            capture_contract=(
                PRINCIPAL_ATTACHMENT_CAPTURE_CONTRACT
                if accepted_dataset_identity is not None
                else None
            ),
            reviewed_handoff_binding=reviewed_binding,
        )

    if not _is_canonical_uuid(tenant_id) or not _is_canonical_uuid(user_id):
        return blocked(
            LivePreflightBlocker(
                code="EVALUATION_PRINCIPAL_ID_INVALID",
                detail="tenant_or_user_uuid_invalid",
            )
        )
    if user_id != reviewed_binding.subject_id:
        return blocked(
            LivePreflightBlocker(
                code="EVALUATION_PRINCIPAL_SUBJECT_INVALID",
                detail="subject_is_not_reviewed_owner",
            )
        )
    accepted_dataset_identity = _frozen_dataset_identity(dataset_validation)
    if accepted_dataset_identity is None:
        return blocked(
            LivePreflightBlocker(
                code="PARSE_ATTACHMENT_MAPPING_INVALID",
                detail="dataset_identity_mismatch",
            )
        )
    verification_cases = _verification_cases(dataset_validation)
    if not _approved_mapping(
        attachment_mapping,
        verification_cases,
        reviewed_binding.attachment_mapping,
    ):
        return blocked(
            LivePreflightBlocker(
                code="PARSE_ATTACHMENT_MAPPING_INVALID",
                detail="mapping_missing_malformed_or_unreviewed",
            )
        )
    adapter = AxHttpAdapter(
        AxHttpAdapterConfig(
            base_url=base_url,
            sut_commit_sha=sut_commit_sha,
            tenant_id=tenant_id,
            user_id=user_id,
            roles=(PARSING_AUTHORIZATION_ROLE,),
            timeout_seconds=PRINCIPAL_PARSE_TIMEOUT_SECONDS,
        ),
        transport=transport,
    )
    observations: list[ParseObservation] = []
    for document_id in sorted(verification_cases):
        attachment_id = attachment_mapping[document_id]
        try:
            observation = adapter.parse(
                context=AxRequestContext(
                    run_id=run_id,
                    case_id=document_id,
                    eval_correlation_id=f"{run_id}-{document_id}-parse",
                ),
                attachment_id=attachment_id,
            )
        except AxHttpFailure as error:
            code, detail = _classify_parse_failure(error)
            return blocked(
                _parse_blocker(
                    code=code,
                    document_id=document_id,
                    request=error.request,
                    detail=detail,
                    attempts=error.attempts,
                ),
                tuple(observations),
            )
        response = observation.response
        if response.attachment_id != attachment_id:
            return blocked(
                _parse_blocker(
                    code="PARSE_ATTACHMENT_MAPPING_INVALID",
                    document_id=document_id,
                    request=observation.request,
                    detail="attachment_identity_mismatch",
                    attempts=tuple(observation.attempts),
                ),
                tuple(observations),
            )
        evidence_failure = _parse_evidence_failure(
            response=observation,
            case=verification_cases[document_id],
        )
        if evidence_failure is not None:
            code, detail = evidence_failure
            return blocked(
                _parse_blocker(
                    code=code,
                    document_id=document_id,
                    request=observation.request,
                    detail=detail,
                    attempts=tuple(observation.attempts),
                ),
                tuple(observations),
            )
        observations.append(observation)
    return build_live_preflight_artifact(
        run_id=run_id,
        captured_at=captured_at,
        evaluation_plane_sha=evaluation_plane_sha,
        sut_commit_sha=sut_commit_sha,
        corpus_observations=(),
        parse_observations=tuple(observations),
        blockers=(),
        dataset_identity=accepted_dataset_identity,
        capture_contract=PRINCIPAL_ATTACHMENT_CAPTURE_CONTRACT,
        _reviewed_handoff_binding=reviewed_binding,
    )


def write_live_preflight_artifact(
    artifact: LivePreflightArtifact,
    path: Path,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        artifact.model_dump(mode="json", exclude_unset=True),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    with path.open("x", encoding="utf-8") as artifact_file:
        artifact_file.write(serialized + "\n")
    return path


def replay_live_preflight_artifact(
    path: Path,
    *,
    handoff_receipt_path: Path | None = None,
) -> dict[str, str | int]:
    raw_artifact = path.read_text(encoding="utf-8")
    payload = json.loads(raw_artifact)
    reviewed_binding: _ReviewedHandoffBinding | None = None
    if (
        isinstance(payload, dict)
        and payload.get("schema_version") == "principal-attachment-preflight-evidence-v1"
    ):
        if handoff_receipt_path is None:
            raise ValueError("principal attachment replay requires the reviewed handoff receipt")
        reviewed_binding = _load_reviewed_handoff_binding(handoff_receipt_path)
    artifact = LivePreflightArtifact.model_validate(
        payload,
        context={"reviewed_handoff_binding": reviewed_binding},
    )
    recomputed_digest = canonical_digest(_logical_payload(artifact))
    if artifact.logical_digest != recomputed_digest:
        raise ValueError("artifact logical content does not reproduce its stored digest")
    return {
        "schema_version": artifact.schema_version,
        "logical_digest": recomputed_digest,
        "capture_state": artifact.capture_state,
        "corpus_observation_count": len(artifact.corpus_observations),
        "parse_observation_count": len(artifact.parse_observations),
        "blocker_count": len(artifact.blockers),
    }


def _sanitize_corpus(observation: CorpusIdentityObservation) -> CorpusIdentityEvidence:
    response_payload = observation.response.model_dump(mode="json")
    return CorpusIdentityEvidence(
        context=observation.context,
        request=observation.request,
        response=observation.response,
        response_digest=canonical_digest(response_payload),
        attempts=_sanitize_attempts(observation.attempts),
    )


def _sanitize_parse(observation: ParseObservation) -> ParseObservationEvidence:
    response = observation.response
    sanitized = SanitizedParseResponse(
        schema_version=response.schema_version,
        attachment_id=response.attachment_id,
        lifecycle_state=response.lifecycle_state,
        parse_state=response.parse_state,
        materialization_state=response.materialization_state,
        parse_available=response.parse_available,
        parser_name=response.parser_name,
        parser_version=response.parser_version,
        failure_code=response.failure_code,
        extracted_text_digest=response.extracted_text_digest,
        text_truncated=response.text_truncated,
        evidence_spans=tuple(
            SanitizedParseEvidenceSpan(
                id=span.id,
                text_digest=_text_digest(span.text),
                start_char=span.start_char,
                end_char=span.end_char,
                source_text_digest=span.source_text_digest,
            )
            for span in response.evidence_spans
        ),
        headings_count=len(response.headings),
        metadata_keys=tuple(sorted(response.metadata)),
        table_shape=(
            None
            if response.table is None
            else SanitizedTableShape(
                column_count=len(response.table.columns),
                row_count=len(response.table.rows),
            )
        ),
        list_shape=(
            None
            if response.list is None
            else SanitizedListShape(
                item_count=len(response.list.items),
                ordered=response.list.ordered,
            )
        ),
        unavailable_fields=tuple(response.unavailable_fields),
    )
    return ParseObservationEvidence(
        context=observation.context,
        request=observation.request,
        response=sanitized,
        response_digest=canonical_digest(sanitized.model_dump(mode="json")),
        attempts=_sanitize_attempts(observation.attempts),
    )


def _sanitize_blocker(blocker: LivePreflightBlocker) -> LivePreflightBlocker:
    return blocker.model_copy(update={"attempts": _sanitize_attempts(blocker.attempts)})


def _sanitize_attempts(attempts: Iterable[HttpAttempt]) -> tuple[HttpAttempt, ...]:
    return tuple(
        attempt.model_copy(
            update={
                "response_correlation_id": (
                    None
                    if attempt.response_correlation_id is None
                    else _text_digest(attempt.response_correlation_id)
                )
            }
        )
        for attempt in attempts
    )


def _blocked_capture(
    *,
    run_id: str,
    captured_at: datetime,
    evaluation_plane_sha: str,
    sut_commit_sha: str,
    blocker: LivePreflightBlocker,
    parse_observations: tuple[ParseObservation, ...] = (),
    dataset_identity: DatasetIdentityEvidence | None = None,
    capture_contract: Literal["principal-attachment-preflight-v1"] | None = None,
    reviewed_handoff_binding: _ReviewedHandoffBinding | None = None,
) -> LivePreflightArtifact:
    return build_live_preflight_artifact(
        run_id=run_id,
        captured_at=captured_at,
        evaluation_plane_sha=evaluation_plane_sha,
        sut_commit_sha=sut_commit_sha,
        corpus_observations=(),
        parse_observations=parse_observations,
        blockers=(blocker,),
        dataset_identity=dataset_identity,
        capture_contract=capture_contract,
        _reviewed_handoff_binding=reviewed_handoff_binding,
    )


def _parse_blocker(
    *,
    code: str,
    document_id: str,
    request: AxCanonicalRequest,
    detail: str,
    attempts: tuple[HttpAttempt, ...] = (),
) -> LivePreflightBlocker:
    return LivePreflightBlocker(
        code=code,
        operation="parse",
        case_id=document_id,
        request=request,
        detail=detail,
        attempts=attempts,
    )


def _classify_parse_failure(error: AxHttpFailure) -> tuple[str, str]:
    if error.failure_code == "AX_REQUEST_FAILURE":
        return "LIVE_PARSE_OBSERVATION_UNREACHABLE", "parse_endpoint_unreachable"
    if error.detail == "evaluation_principal_id_invalid":
        return "EVALUATION_PRINCIPAL_ID_INVALID", "principal_rejected_by_ax"
    if error.detail == "evaluation_principal_subject_invalid":
        return "EVALUATION_PRINCIPAL_SUBJECT_INVALID", "subject_unknown_or_inactive"
    if error.detail == "not_found":
        return "PARSE_ATTACHMENT_MAPPING_INVALID", "attachment_not_found"
    return "LIVE_PARSE_OBSERVATION_FAILED", error.failure_code


def _load_reviewed_handoff_binding(path: Path) -> _ReviewedHandoffBinding:
    try:
        receipt_bytes = path.read_bytes()
    except OSError as error:
        raise ValueError("reviewed handoff receipt is unreadable") from error

    actual_digest = hashlib.sha256(receipt_bytes).hexdigest()
    if actual_digest != REVIEWED_HANDOFF_RECEIPT_SHA256:
        raise ValueError("reviewed handoff receipt digest does not match the pinned digest")

    try:
        receipt = _ReviewedHandoffReceipt.model_validate_json(receipt_bytes)
    except ValueError as error:
        raise ValueError("reviewed handoff receipt is invalid") from error

    if receipt.state != "COMPLETED" or receipt.completion_confirmed is not True:
        raise ValueError("reviewed handoff receipt is not completed")
    if receipt.repository.commit_sha != PINNED_AX_SHA:
        raise ValueError("reviewed handoff receipt was produced from an unreviewed AX commit")
    if len(receipt.attachments) != 6:
        raise ValueError("reviewed handoff receipt must contain exactly six attachments")

    attachment_mapping = {
        attachment.case_id: attachment.attachment_id for attachment in receipt.attachments
    }
    if set(attachment_mapping) != set(REVIEWED_PARSING_SOURCE_EVIDENCE):
        raise ValueError("reviewed handoff receipt reviewed case mapping is incomplete")
    if len(attachment_mapping) != len(receipt.attachments) or not all(
        _is_canonical_uuid(attachment_id) for attachment_id in attachment_mapping.values()
    ):
        raise ValueError("reviewed handoff receipt attachment mapping is invalid")
    if not _is_canonical_uuid(receipt.target.subject_id):
        raise ValueError("reviewed handoff receipt subject is invalid")

    return _ReviewedHandoffBinding(
        subject_id=receipt.target.subject_id,
        attachment_mapping=MappingProxyType(attachment_mapping),
    )


def _reviewed_binding_from_context(info: ValidationInfo) -> _ReviewedHandoffBinding:
    context = info.context
    binding = context.get("reviewed_handoff_binding") if isinstance(context, Mapping) else None
    if not isinstance(binding, _ReviewedHandoffBinding):
        raise ValueError("principal attachment capture requires reviewed handoff binding")
    return binding


def _validate_principal_attachment_capture(
    artifact: LivePreflightArtifact,
    *,
    reviewed_binding: _ReviewedHandoffBinding,
) -> None:
    if artifact.corpus_observations:
        raise ValueError("principal attachment capture cannot contain corpus observations")

    expected_probes = tuple(sorted(reviewed_binding.attachment_mapping.items()))
    if len(artifact.parse_observations) > len(expected_probes):
        raise ValueError("principal attachment capture has too many parse observations")

    tenant_ids: set[str] = set()
    for observation, (document_id, attachment_id) in zip(
        artifact.parse_observations,
        expected_probes,
        strict=False,
    ):
        request = observation.request
        _validate_principal_parse_request(
            request,
            artifact_run_id=artifact.run_id,
            document_id=document_id,
            attachment_id=attachment_id,
            subject_id=reviewed_binding.subject_id,
        )
        if observation.response.attachment_id != attachment_id:
            raise ValueError("principal attachment capture must use the reviewed probe mapping")
        tenant_ids.add(request.tenant_id)

        source_digest, source_text = REVIEWED_PARSING_SOURCE_EVIDENCE[document_id]
        response = observation.response
        if (
            not response.parse_available
            or response.failure_code is not None
            or (response.parser_name, response.parser_version) != EXPECTED_PARSER_IDENTITY
            or response.extracted_text_digest != source_digest
        ):
            raise ValueError("principal attachment capture has invalid strict parse evidence")
        if any(
            re.fullmatch(SAFE_ID_PATTERN, span.id) is None
            or span.source_text_digest != source_digest
            or span.end_char > len(source_text)
            or span.text_digest != _text_digest(source_text[span.start_char : span.end_char])
            for span in response.evidence_spans
        ):
            raise ValueError("principal attachment capture has invalid span evidence")
        _validate_principal_parse_attempts(
            observation.attempts,
            attachment_id=attachment_id,
            require_success=True,
        )

    if not artifact.blockers:
        if len(artifact.parse_observations) != len(expected_probes):
            raise ValueError("unblocked principal attachment capture requires all six probes")
        if len(tenant_ids) != 1:
            raise ValueError("principal attachment capture must use one tenant identity")
        return

    if len(artifact.blockers) != 1:
        raise ValueError("principal attachment capture requires exactly one terminal blocker")
    if len(artifact.parse_observations) == len(expected_probes):
        raise ValueError("complete principal attachment capture cannot contain a blocker")

    blocker = artifact.blockers[0]
    if blocker.operation is None:
        if (
            artifact.parse_observations
            or blocker.case_id is not None
            or blocker.code != "PARSE_ATTACHMENT_MAPPING_INVALID"
            or blocker.request is not None
            or blocker.detail != "mapping_missing_malformed_or_unreviewed"
            or blocker.attempts
        ):
            raise ValueError("pre-probe principal attachment blocker is inconsistent")
        return

    expected_case_id = expected_probes[len(artifact.parse_observations)][0]
    if blocker.operation != "parse" or blocker.case_id != expected_case_id:
        raise ValueError("partial principal attachment capture requires its next probe blocker")
    expected_attachment_id = expected_probes[len(artifact.parse_observations)][1]
    if blocker.request is None:
        raise ValueError("principal attachment operation blocker requires its canonical request")
    _validate_principal_parse_request(
        blocker.request,
        artifact_run_id=artifact.run_id,
        document_id=expected_case_id,
        attachment_id=expected_attachment_id,
        subject_id=reviewed_binding.subject_id,
    )
    tenant_ids.add(blocker.request.tenant_id)
    if len(tenant_ids) != 1:
        raise ValueError("principal attachment capture must use one tenant identity")
    _validate_principal_parse_attempts(
        blocker.attempts,
        attachment_id=expected_attachment_id,
        require_success=False,
    )
    if blocker.detail is None:
        raise ValueError("principal attachment blocker requires a typed detail")
    blocker_identity = (blocker.code, blocker.detail)
    allowed_terminal_outcomes = {
        ("EVALUATION_PRINCIPAL_ID_INVALID", "principal_rejected_by_ax"): {"permanent_http"},
        ("EVALUATION_PRINCIPAL_SUBJECT_INVALID", "subject_unknown_or_inactive"): {"permanent_http"},
        ("PARSE_ATTACHMENT_MAPPING_INVALID", "attachment_not_found"): {"permanent_http"},
        ("PARSE_ATTACHMENT_MAPPING_INVALID", "attachment_identity_mismatch"): {"success"},
        ("LIVE_PARSE_OBSERVATION_UNAVAILABLE", "parse_unavailable"): {"success"},
        ("LIVE_PARSE_OBSERVATION_UNREACHABLE", "parse_endpoint_unreachable"): {"request_error"},
        ("LIVE_PARSE_OBSERVATION_FAILED", "AX_TRANSIENT_RETRIES_EXHAUSTED"): {
            "timeout",
            "retryable_http",
        },
        ("LIVE_PARSE_OBSERVATION_FAILED", "AX_PERMANENT_HTTP_FAILURE"): {"permanent_http"},
        ("LIVE_PARSE_OBSERVATION_FAILED", "AX_RESPONSE_SCHEMA_MISMATCH"): {"schema_error"},
        ("LIVE_PARSE_OBSERVATION_FAILED", "parse_failure_code_present"): {"success"},
        ("LIVE_PARSE_OBSERVATION_FAILED", "parser_identity_missing"): {"success"},
        ("LIVE_PARSE_OBSERVATION_FAILED", "parser_identity_mismatch"): {"success"},
        ("LIVE_PARSE_OBSERVATION_FAILED", "source_text_digest_mismatch"): {"success"},
        ("LIVE_PARSE_OBSERVATION_FAILED", "evidence_span_invalid"): {"success"},
    }
    terminal_attempt = blocker.attempts[-1]
    if terminal_attempt.outcome not in allowed_terminal_outcomes.get(
        blocker_identity,
        set(),
    ):
        raise ValueError("principal attachment blocker contradicts its terminal attempt")
    expected_status = {
        ("EVALUATION_PRINCIPAL_ID_INVALID", "principal_rejected_by_ax"): 400,
        ("EVALUATION_PRINCIPAL_SUBJECT_INVALID", "subject_unknown_or_inactive"): 401,
        ("PARSE_ATTACHMENT_MAPPING_INVALID", "attachment_not_found"): 404,
    }.get(blocker_identity)
    if expected_status is not None and terminal_attempt.status_code != expected_status:
        raise ValueError("principal attachment blocker contradicts its terminal attempt")


def _validate_principal_parse_request(
    request: AxCanonicalRequest,
    *,
    artifact_run_id: str,
    document_id: str,
    attachment_id: str,
    subject_id: str,
) -> None:
    if (
        request.operation != "parse"
        or request.run_id != artifact_run_id
        or request.case_id != document_id
        or request.eval_correlation_id != f"{artifact_run_id}-{document_id}-parse"
        or request.attachment_id != attachment_id
    ):
        raise ValueError("principal attachment capture must use the reviewed probe mapping")
    if request.user_id != subject_id or request.roles != (PARSING_AUTHORIZATION_ROLE,):
        raise ValueError("principal attachment capture must use the reviewed owner role")
    if not _is_canonical_uuid(request.tenant_id):
        raise ValueError("principal attachment capture must use a canonical tenant UUID")
    if request.timeout_seconds != PRINCIPAL_PARSE_TIMEOUT_SECONDS:
        raise ValueError("principal attachment capture must use the frozen parse timeout")
    if any(
        value is not None
        for value in (
            request.corpus_id,
            request.corpus_version,
            request.query,
            request.record_kind,
            request.record_id,
            request.top_k,
            request.evidence_limit,
        )
    ):
        raise ValueError("principal attachment parse request cannot contain unrelated payload")


def _validate_principal_parse_attempts(
    attempts: tuple[HttpAttempt, ...],
    *,
    attachment_id: str,
    require_success: bool,
) -> None:
    if not attempts or len(attempts) > 3:
        raise ValueError("principal attachment operation requires bounded attempt evidence")

    expected_path = f"/v1/evaluation/attachments/{attachment_id}/parse-observation"
    for attempt_number, attempt in enumerate(attempts, start=1):
        if (
            attempt.operation != "parse"
            or attempt.attempt_number != attempt_number
            or attempt.method != "GET"
            or attempt.path != expected_path
        ):
            raise ValueError("principal attachment attempt identity is inconsistent")
        if (
            attempt.response_correlation_id is not None
            and re.fullmatch(
                SHA256_PATTERN,
                attempt.response_correlation_id,
            )
            is None
        ):
            raise ValueError("principal attachment attempt correlation must be digest-only")
        if (
            attempt.outcome in {"timeout", "request_error"}
            and attempt.response_correlation_id is not None
        ):
            raise ValueError(
                "principal attachment attempt without a response cannot declare "
                "a response correlation"
            )
        if attempt.outcome == "success" and not (
            attempt.status_code is not None and 200 <= attempt.status_code < 300
        ):
            raise ValueError("successful principal attachment attempt requires a success status")
        if attempt.outcome in {"timeout", "request_error"} and attempt.status_code is not None:
            raise ValueError("failed principal attachment request cannot declare a status")
        if attempt.outcome == "retryable_http" and not (
            attempt.status_code == 429
            or (attempt.status_code is not None and attempt.status_code >= 500)
        ):
            raise ValueError("retryable principal attachment attempt has invalid status")
        if attempt.outcome == "permanent_http" and (
            attempt.status_code is None
            or 200 <= attempt.status_code < 300
            or attempt.status_code == 429
            or attempt.status_code >= 500
        ):
            raise ValueError("permanent principal attachment attempt has invalid status")
        if attempt.outcome == "schema_error" and not (
            attempt.status_code is not None and 200 <= attempt.status_code < 300
        ):
            raise ValueError("schema-error principal attachment attempt needs a success status")
        if attempt_number < len(attempts) and attempt.outcome not in {
            "timeout",
            "retryable_http",
        }:
            raise ValueError("only retryable attempts may precede the terminal attempt")

    if require_success and attempts[-1].outcome != "success":
        raise ValueError("principal attachment observation requires a successful final attempt")
    if attempts[-1].outcome in {"timeout", "retryable_http"} and len(attempts) != 3:
        raise ValueError("terminal retryable failure requires three exhausted attempts")


def _verification_cases(
    validation: DatasetValidationReport,
) -> dict[str, ParsingCase]:
    snapshot = validation.snapshot
    if validation.state != "VALID" or snapshot is None:
        return {}
    if snapshot.manifest.dataset_version != "2.0.0":
        return {}
    return {
        case.document.id: case
        for case in snapshot.parsing_dataset.cases
        if case.split == "verification"
    }


def _frozen_dataset_identity(
    validation: DatasetValidationReport,
) -> DatasetIdentityEvidence | None:
    snapshot = validation.snapshot
    if validation.state != "VALID" or snapshot is None:
        return None
    manifest = snapshot.manifest
    manifest_component_digests = {
        "parsing": manifest.components.parsing.content_digest,
        "retrieval": manifest.components.retrieval.content_digest,
        "grounded": manifest.components.grounded.content_digest,
    }
    if not (
        manifest.dataset_id == FROZEN_DATASET_ID
        and manifest.dataset_version == FROZEN_DATASET_VERSION
        and manifest.content_digest == FROZEN_DATASET_DIGEST
        and snapshot.dataset_digest == FROZEN_DATASET_DIGEST
        and validation.computed_dataset_digest == FROZEN_DATASET_DIGEST
        and snapshot.component_digests == FROZEN_COMPONENT_DIGESTS
        and validation.computed_component_digests == FROZEN_COMPONENT_DIGESTS
        and manifest_component_digests == FROZEN_COMPONENT_DIGESTS
    ):
        return None
    return DatasetIdentityEvidence(
        id=FROZEN_DATASET_ID,
        version=FROZEN_DATASET_VERSION,
        content_digest=FROZEN_DATASET_DIGEST,
        component_digests=DatasetComponentDigests(
            parsing=FROZEN_COMPONENT_DIGESTS["parsing"],
            retrieval=FROZEN_COMPONENT_DIGESTS["retrieval"],
            grounded=FROZEN_COMPONENT_DIGESTS["grounded"],
        ),
    )


def _approved_mapping(
    mapping: Mapping[str, str],
    verification_cases: Mapping[str, ParsingCase],
    reviewed_mapping: Mapping[str, str],
) -> bool:
    if set(verification_cases) != set(reviewed_mapping):
        return False
    if dict(mapping) != dict(reviewed_mapping):
        return False
    return all(_is_canonical_uuid(value) for value in mapping.values())


def _parse_evidence_failure(
    *,
    response: ParseObservation,
    case: ParsingCase,
) -> tuple[str, str] | None:
    parsed = response.response
    if not parsed.parse_available:
        return "LIVE_PARSE_OBSERVATION_UNAVAILABLE", "parse_unavailable"
    if parsed.failure_code is not None:
        return "LIVE_PARSE_OBSERVATION_FAILED", "parse_failure_code_present"
    if not parsed.parser_name or not parsed.parser_version:
        return "LIVE_PARSE_OBSERVATION_FAILED", "parser_identity_missing"
    if (parsed.parser_name, parsed.parser_version) != EXPECTED_PARSER_IDENTITY:
        return "LIVE_PARSE_OBSERVATION_FAILED", "parser_identity_mismatch"
    expected_source_digest = _text_digest(case.document.canonical_text)
    if (
        parsed.extracted_text is None
        or parsed.extracted_text_digest != expected_source_digest
        or _text_digest(parsed.extracted_text) != expected_source_digest
    ):
        return "LIVE_PARSE_OBSERVATION_FAILED", "source_text_digest_mismatch"
    if any(
        re.fullmatch(SAFE_ID_PATTERN, span.id) is None
        or span.source_text_digest != expected_source_digest
        or span.end_char > len(parsed.extracted_text)
        or parsed.extracted_text[span.start_char : span.end_char] != span.text
        for span in parsed.evidence_spans
    ):
        return "LIVE_PARSE_OBSERVATION_FAILED", "evidence_span_invalid"
    return None


def _logical_payload(artifact: LivePreflightArtifact) -> dict[str, object]:
    return artifact.model_dump(
        mode="json",
        exclude={"logical_digest"},
        exclude_unset=True,
    )


def _text_digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def _is_canonical_uuid(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(UUID(value)) == value
    except ValueError:
        return False


def _contains_private_path(value: object, *, field_name: str | None = None) -> bool:
    if isinstance(value, str):
        if field_name == "path":
            return False
        return value.startswith(("/", "~/", "\\\\")) or (
            len(value) >= 3 and value[1] == ":" and value[2] in {"/", "\\"}
        )
    if isinstance(value, dict):
        return any(_contains_private_path(item, field_name=str(key)) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_private_path(item) for item in value)
    return False
