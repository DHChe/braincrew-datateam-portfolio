from __future__ import annotations

import builtins
import hashlib
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Literal
from urllib.parse import quote

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

OperationName = Literal[
    "preflight",
    "corpus_identity",
    "parse",
    "retrieve",
    "answer",
    "source_text",
]
HttpMethod = Literal["GET", "POST"]
CommitSha = str


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ContractOperation(StrictModel):
    method: HttpMethod | None
    path: str | None
    request_mapping: dict[str, str]
    response_mapping: dict[str, str]
    expected_schema_digest: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    unavailable_reason: str | None = None


class AxHttpContract(StrictModel):
    schema_version: Literal["ax-http-contract-v1"]
    adapter_version: Literal["ax-sut-http-v1"]
    sut_repository: str
    sut_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    discovery_path: str
    operations: dict[OperationName, ContractOperation]


class AxHttpAdapterConfig(StrictModel):
    base_url: str
    sut_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    tenant_id: str = Field(
        pattern=r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    )
    user_id: str
    roles: tuple[str, ...]
    bearer_token: str | None = Field(default=None, repr=False, exclude=True)
    timeout_seconds: float = Field(default=10.0, gt=0)

    @model_validator(mode="after")
    def require_roles(self) -> AxHttpAdapterConfig:
        if not self.roles:
            raise ValueError("at least one AX role is required")
        return self


class AxRequestContext(StrictModel):
    run_id: str
    case_id: str
    eval_correlation_id: str


class AxCanonicalRequest(StrictModel):
    operation: OperationName
    run_id: str
    case_id: str
    eval_correlation_id: str
    tenant_id: str
    user_id: str
    roles: tuple[str, ...]
    timeout_seconds: float
    corpus_id: str | None = None
    corpus_version: str | None = None
    query: str | None = None
    attachment_id: str | None = None
    record_kind: str | None = None
    record_id: str | None = None
    top_k: int | None = None
    evidence_limit: int | None = None


class HttpAttempt(StrictModel):
    operation: OperationName
    attempt_number: int = Field(ge=1)
    method: HttpMethod
    path: str
    outcome: Literal["success", "timeout", "retryable_http", "permanent_http", "schema_error"]
    status_code: int | None
    elapsed_ms: float = Field(ge=0)
    response_correlation_id: str | None = None


class CorpusCapability(StrictModel):
    id: str
    version: str
    verified_by_sut: bool
    reason: str | None = None


class OperationCapability(StrictModel):
    available: bool
    method: HttpMethod | None
    path: str | None
    schema_digest: str | None
    reason: str | None = None


class CapabilityManifest(StrictModel):
    schema_version: Literal["ax-capability-manifest-v1"]
    adapter_version: Literal["ax-sut-http-v1"]
    sut_repository: str
    sut_commit_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    request: AxCanonicalRequest
    readiness_status: str
    dependencies: dict[str, str]
    corpus: CorpusCapability
    operations: dict[OperationName, OperationCapability]
    attempts: list[HttpAttempt]


class AxHttpFailure(RuntimeError):
    def __init__(
        self,
        *,
        operation: OperationName,
        failure_code: str,
        request: AxCanonicalRequest,
        attempts: list[HttpAttempt],
        detail: str | None = None,
    ) -> None:
        message = f"{operation}: {failure_code}"
        if detail is not None:
            message = f"{message}: {detail}"
        super().__init__(message)
        self.operation = operation
        self.failure_code = failure_code
        self.request = request
        self.attempts = tuple(attempts)
        self.detail = detail


class AxTransientFailure(AxHttpFailure):
    pass


class ReadinessResponse(StrictModel):
    status: str
    service: str
    dependencies: dict[str, str]


class OpenApiDocument(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    openapi: str
    info: dict[str, object]
    paths: dict[str, dict[str, object]]


class CorpusIdentityResponse(StrictModel):
    schema_version: Literal["ax-corpus-identity-v1"]
    corpus_id: str
    corpus_version: Literal["retrieval-inventory-v1"]
    corpus_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    principal_roles: list[str]
    inventory_count: int = Field(ge=0)
    counts: dict[str, dict[str, int]]
    contributing_versions: list[str]
    generated_at: datetime


class CorpusIdentityObservation(StrictModel):
    context: AxRequestContext
    request: AxCanonicalRequest
    response: CorpusIdentityResponse
    attempts: list[HttpAttempt]


class ParseEvidenceSpan(StrictModel):
    id: str
    text: str = Field(min_length=1)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    source_text_digest: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")


class ParseTableObservation(StrictModel):
    columns: list[str] = Field(min_length=1)
    rows: list[list[str]] = Field(min_length=1)

    @model_validator(mode="after")
    def require_rectangular_rows(self) -> ParseTableObservation:
        if any(len(row) != len(self.columns) for row in self.rows):
            raise ValueError("table rows must match the declared column count")
        return self


class ParseListObservation(StrictModel):
    items: list[str] = Field(min_length=1)
    ordered: bool


class ParseObservationResponse(StrictModel):
    schema_version: Literal["ax-parse-observation-v1"]
    attachment_id: str
    lifecycle_state: str
    parse_state: str
    materialization_state: str
    parse_available: bool
    parser_name: str | None
    parser_version: str | None
    failure_code: str | None
    extracted_text: str | None
    extracted_text_digest: str | None = Field(
        default=None,
        pattern=r"^sha256:[0-9a-f]{64}$",
    )
    text_truncated: bool
    evidence_spans: list[ParseEvidenceSpan]
    headings: list[str]
    metadata: dict[str, str]
    table: ParseTableObservation | None
    list: ParseListObservation | None
    unavailable_fields: builtins.list[str]


class ParseObservation(StrictModel):
    context: AxRequestContext
    request: AxCanonicalRequest
    response: ParseObservationResponse
    attempts: list[HttpAttempt]


class RetrievalCandidate(StrictModel):
    vector_record_id: str
    record_kind: str
    record_id: str
    snippet: str
    source_id: str | None
    chunk_id: str | None
    evidence_span_id: str | None
    source_class: str | None
    authority_level: int | None
    provenance: dict[str, object]
    metadata: dict[str, object]
    retrieval_score: float
    retrieval_score_kind: str
    visibility_decision: dict[str, object]
    synthetic: bool
    demo_company: bool
    corpus_mode: str


class RetrievalResponse(StrictModel):
    query: str
    top_k: int
    max_top_k: int
    answer_mode: str
    candidates: list[RetrievalCandidate]
    matched_evidence: list[RetrievalCandidate]
    risk_tags: list[str]
    visibility_decisions: list[dict[str, object]]
    correlation_id: str
    audit_recorded: bool
    precedent_capability_enabled: bool
    provider_free: bool
    notices: list[str]
    currentness_checks: list[str]
    natural_language_answer_generated: bool


class RetrievalObservation(StrictModel):
    context: AxRequestContext
    request: AxCanonicalRequest
    query: str
    top_k: int
    response: RetrievalResponse
    attempts: list[HttpAttempt]


class AnswerCitation(BaseModel):
    model_config = ConfigDict(extra="allow", frozen=True)

    record_kind: str
    record_id: str
    snippet: str
    source_id: str | None = None
    chunk_id: str | None = None
    evidence_span_id: str | None = None
    source_class: str | None = None
    authority_level: int | None = None
    synthetic: bool
    demo_company: bool
    corpus_mode: str
    claim_paths: list[str]


class StructuredAnswer(StrictModel):
    summary: str
    answer: str
    grounds: list[str]
    review_points: list[str]
    additional_checks: list[str]
    risk_warning: str
    citations: list[AnswerCitation]


class AnswerResponse(StrictModel):
    query: str
    answer_mode: str
    structured_answer: StructuredAnswer
    citations: list[AnswerCitation]
    reference_context: list[dict[str, object]] | None = None
    retrieval_correlation_id: str
    answer_correlation_id: str
    audit_recorded: bool
    natural_language_answer_generated: bool
    provider_metadata: dict[str, object]
    evidence_packaging: dict[str, object]
    debug: dict[str, object] | None = None


class AnswerObservation(StrictModel):
    context: AxRequestContext
    request: AxCanonicalRequest
    query: str
    top_k: int
    evidence_limit: int
    response: AnswerResponse
    attempts: list[HttpAttempt]


class SourceTextResponse(StrictModel):
    record_kind: str
    record_id: str
    text: str
    provenance: dict[str, object]
    correlation_id: str


class SourceTextObservation(StrictModel):
    context: AxRequestContext
    request: AxCanonicalRequest
    response: SourceTextResponse
    attempts: list[HttpAttempt]


def load_ax_http_contract() -> AxHttpContract:
    contract_path = Path(__file__).with_name("ax-http-v1.yaml")
    contract = AxHttpContract.model_validate_json(contract_path.read_text(encoding="utf-8"))
    response_models: dict[OperationName, type[BaseModel] | None] = {
        "preflight": ReadinessResponse,
        "corpus_identity": CorpusIdentityResponse,
        "parse": ParseObservationResponse,
        "retrieve": RetrievalResponse,
        "answer": AnswerResponse,
        "source_text": SourceTextResponse,
    }
    for name, response_model in response_models.items():
        expected = contract.operations[name].expected_schema_digest
        actual = None if response_model is None else _model_schema_digest(response_model)
        if expected != actual:
            raise ValueError(f"{name} response schema digest does not match ax-http-v1 contract")
    return contract


def _model_schema_digest(response_model: type[BaseModel]) -> str:
    canonical = json.dumps(
        response_model.model_json_schema(),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def _safe_response_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        return f"HTTP_{response.status_code}"
    if isinstance(payload, dict):
        detail: object = payload.get("detail")
        if (
            isinstance(detail, str)
            and len(detail) <= 160
            and re.fullmatch(r"[A-Za-z0-9_.:-]+", detail) is not None
        ):
            return detail
    return f"HTTP_{response.status_code}"


def write_capability_manifest(manifest: CapabilityManifest, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        manifest.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    with path.open("x", encoding="utf-8") as manifest_file:
        manifest_file.write(serialized + "\n")
    return path


class AxHttpAdapter:
    def __init__(
        self,
        config: AxHttpAdapterConfig,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._config = config
        self._contract = load_ax_http_contract()
        if config.sut_commit_sha != self._contract.sut_commit_sha:
            raise ValueError("configured AX SHA does not match ax-http-v1 contract")
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=config.timeout_seconds,
            transport=transport,
            headers=self._headers(),
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "x-ax-tenant-id": self._config.tenant_id,
            "x-ax-user-id": self._config.user_id,
            "x-ax-roles": ",".join(self._config.roles),
        }
        if self._config.bearer_token is not None:
            headers["Authorization"] = f"Bearer {self._config.bearer_token}"
        return headers

    def preflight(
        self,
        *,
        context: AxRequestContext,
        corpus_id: str,
        corpus_version: str,
    ) -> CapabilityManifest:
        request = self._canonical_request(
            operation="preflight",
            context=context,
            corpus_id=corpus_id,
            corpus_version=corpus_version,
        )
        readiness, readiness_attempts = self._request_json(
            operation="preflight",
            method="GET",
            path=self._contract.operations["preflight"].path or "/health/ready",
            response_model=ReadinessResponse,
            request=request,
        )
        openapi, openapi_attempts = self._request_json(
            operation="preflight",
            method="GET",
            path=self._contract.discovery_path,
            response_model=OpenApiDocument,
            request=request,
        )
        operations: dict[OperationName, OperationCapability] = {}
        for name, operation in self._contract.operations.items():
            if name == "preflight":
                available = True
            elif operation.method is None or operation.path is None:
                available = False
            else:
                available = operation.method.lower() in openapi.paths.get(operation.path, {})
            operations[name] = OperationCapability(
                available=available,
                method=operation.method,
                path=operation.path,
                schema_digest=operation.expected_schema_digest,
                reason=None
                if available
                else operation.unavailable_reason or "AX_ENDPOINT_UNAVAILABLE",
            )
        return CapabilityManifest(
            schema_version="ax-capability-manifest-v1",
            adapter_version=self._contract.adapter_version,
            sut_repository=self._contract.sut_repository,
            sut_commit_sha=self._config.sut_commit_sha,
            request=request,
            readiness_status=readiness.status,
            dependencies=readiness.dependencies,
            corpus=CorpusCapability(
                id=corpus_id,
                version=corpus_version,
                verified_by_sut=False,
                reason="AX_CORPUS_IDENTITY_NOT_PROBED",
            ),
            operations=operations,
            attempts=[*readiness_attempts, *openapi_attempts],
        )

    def retrieve(
        self,
        *,
        context: AxRequestContext,
        query: str,
        top_k: int,
    ) -> RetrievalObservation:
        operation = self._contract.operations["retrieve"]
        if operation.path is None:
            raise ValueError("retrieve operation has no configured AX path")
        request = self._canonical_request(
            operation="retrieve",
            context=context,
            query=query,
            top_k=top_k,
        )
        response, attempts = self._request_json(
            operation="retrieve",
            method="POST",
            path=operation.path,
            response_model=RetrievalResponse,
            request=request,
            json_body={"query": query, "top_k": top_k},
        )
        return RetrievalObservation(
            context=context,
            request=request,
            query=query,
            top_k=top_k,
            response=response,
            attempts=attempts,
        )

    def corpus_identity(
        self,
        *,
        context: AxRequestContext,
    ) -> CorpusIdentityObservation:
        operation = self._contract.operations["corpus_identity"]
        if operation.path is None:
            raise ValueError("corpus_identity operation has no configured AX path")
        request = self._canonical_request(
            operation="corpus_identity",
            context=context,
        )
        response, attempts = self._request_json(
            operation="corpus_identity",
            method="GET",
            path=operation.path,
            response_model=CorpusIdentityResponse,
            request=request,
        )
        return CorpusIdentityObservation(
            context=context,
            request=request,
            response=response,
            attempts=attempts,
        )

    def parse(
        self,
        *,
        context: AxRequestContext,
        attachment_id: str,
    ) -> ParseObservation:
        operation = self._contract.operations["parse"]
        if operation.path is None:
            raise ValueError("parse operation has no configured AX path")
        path = operation.path.format(attachment_id=quote(attachment_id, safe=""))
        request = self._canonical_request(
            operation="parse",
            context=context,
            attachment_id=attachment_id,
        )
        response, attempts = self._request_json(
            operation="parse",
            method="GET",
            path=path,
            response_model=ParseObservationResponse,
            request=request,
        )
        return ParseObservation(
            context=context,
            request=request,
            response=response,
            attempts=attempts,
        )

    def answer(
        self,
        *,
        context: AxRequestContext,
        query: str,
        top_k: int,
        evidence_limit: int,
    ) -> AnswerObservation:
        operation = self._contract.operations["answer"]
        if operation.path is None:
            raise ValueError("answer operation has no configured AX path")
        request = self._canonical_request(
            operation="answer",
            context=context,
            query=query,
            top_k=top_k,
            evidence_limit=evidence_limit,
        )
        response, attempts = self._request_json(
            operation="answer",
            method="POST",
            path=operation.path,
            response_model=AnswerResponse,
            request=request,
            json_body={"query": query, "top_k": top_k, "evidence_limit": evidence_limit},
        )
        return AnswerObservation(
            context=context,
            request=request,
            query=query,
            top_k=top_k,
            evidence_limit=evidence_limit,
            response=response,
            attempts=attempts,
        )

    def source_text(
        self,
        *,
        context: AxRequestContext,
        record_kind: str,
        record_id: str,
    ) -> SourceTextObservation:
        operation = self._contract.operations["source_text"]
        if operation.path is None:
            raise ValueError("source_text operation has no configured AX path")
        path = operation.path.format(
            record_kind=quote(record_kind, safe=""),
            record_id=quote(record_id, safe=""),
        )
        request = self._canonical_request(
            operation="source_text",
            context=context,
            record_kind=record_kind,
            record_id=record_id,
        )
        response, attempts = self._request_json(
            operation="source_text",
            method="GET",
            path=path,
            response_model=SourceTextResponse,
            request=request,
        )
        return SourceTextObservation(
            context=context,
            request=request,
            response=response,
            attempts=attempts,
        )

    def _canonical_request(
        self,
        *,
        operation: OperationName,
        context: AxRequestContext,
        corpus_id: str | None = None,
        corpus_version: str | None = None,
        query: str | None = None,
        attachment_id: str | None = None,
        record_kind: str | None = None,
        record_id: str | None = None,
        top_k: int | None = None,
        evidence_limit: int | None = None,
    ) -> AxCanonicalRequest:
        return AxCanonicalRequest(
            operation=operation,
            run_id=context.run_id,
            case_id=context.case_id,
            eval_correlation_id=context.eval_correlation_id,
            tenant_id=self._config.tenant_id,
            user_id=self._config.user_id,
            roles=self._config.roles,
            timeout_seconds=self._config.timeout_seconds,
            corpus_id=corpus_id,
            corpus_version=corpus_version,
            query=query,
            attachment_id=attachment_id,
            record_kind=record_kind,
            record_id=record_id,
            top_k=top_k,
            evidence_limit=evidence_limit,
        )

    def _request_json[ResponseModel: BaseModel](
        self,
        *,
        operation: OperationName,
        method: HttpMethod,
        path: str,
        response_model: type[ResponseModel],
        request: AxCanonicalRequest,
        json_body: dict[str, object] | None = None,
    ) -> tuple[ResponseModel, list[HttpAttempt]]:
        attempts: list[HttpAttempt] = []
        request_headers = {
            "x-eval-run-id": request.run_id,
            "x-eval-case-id": request.case_id,
            "x-eval-correlation-id": request.eval_correlation_id,
        }
        for attempt_number in range(1, 4):
            started = time.perf_counter()
            try:
                if method == "GET":
                    response = self._client.get(
                        path,
                        headers=request_headers,
                    )
                else:
                    response = self._client.post(
                        path,
                        json=json_body,
                        headers=request_headers,
                    )
            except httpx.TimeoutException:
                attempts.append(
                    HttpAttempt(
                        operation=operation,
                        attempt_number=attempt_number,
                        method=method,
                        path=path,
                        outcome="timeout",
                        status_code=None,
                        elapsed_ms=(time.perf_counter() - started) * 1000,
                    )
                )
                if attempt_number < 3:
                    continue
                raise AxTransientFailure(
                    operation=operation,
                    failure_code="AX_TRANSIENT_RETRIES_EXHAUSTED",
                    request=request,
                    attempts=attempts,
                ) from None
            elapsed_ms = (time.perf_counter() - started) * 1000
            if response.status_code == 429 or response.status_code >= 500:
                attempts.append(
                    HttpAttempt(
                        operation=operation,
                        attempt_number=attempt_number,
                        method=method,
                        path=path,
                        outcome="retryable_http",
                        status_code=response.status_code,
                        elapsed_ms=elapsed_ms,
                        response_correlation_id=response.headers.get("x-correlation-id"),
                    )
                )
                if attempt_number < 3:
                    continue
                raise AxTransientFailure(
                    operation=operation,
                    failure_code="AX_TRANSIENT_RETRIES_EXHAUSTED",
                    request=request,
                    attempts=attempts,
                )
            if not response.is_success:
                attempts.append(
                    HttpAttempt(
                        operation=operation,
                        attempt_number=attempt_number,
                        method=method,
                        path=path,
                        outcome="permanent_http",
                        status_code=response.status_code,
                        elapsed_ms=elapsed_ms,
                        response_correlation_id=response.headers.get("x-correlation-id"),
                    )
                )
                raise AxHttpFailure(
                    operation=operation,
                    failure_code="AX_PERMANENT_HTTP_FAILURE",
                    request=request,
                    attempts=attempts,
                    detail=_safe_response_detail(response),
                )
            try:
                parsed = response_model.model_validate(response.json())
            except (json.JSONDecodeError, ValidationError) as error:
                attempts.append(
                    HttpAttempt(
                        operation=operation,
                        attempt_number=attempt_number,
                        method=method,
                        path=path,
                        outcome="schema_error",
                        status_code=response.status_code,
                        elapsed_ms=elapsed_ms,
                        response_correlation_id=response.headers.get("x-correlation-id"),
                    )
                )
                raise AxHttpFailure(
                    operation=operation,
                    failure_code="AX_RESPONSE_SCHEMA_MISMATCH",
                    request=request,
                    attempts=attempts,
                ) from error
            attempts.append(
                HttpAttempt(
                    operation=operation,
                    attempt_number=attempt_number,
                    method=method,
                    path=path,
                    outcome="success",
                    status_code=response.status_code,
                    elapsed_ms=elapsed_ms,
                    response_correlation_id=response.headers.get("x-correlation-id"),
                )
            )
            return parsed, attempts
        raise AssertionError("unreachable retry loop")
