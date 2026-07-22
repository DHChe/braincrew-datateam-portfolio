from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from braincrew.ax_http_adapter import (
    AxCanonicalRequest,
    AxRequestContext,
    CorpusIdentityObservation,
    CorpusIdentityResponse,
    HttpAttempt,
    OperationName,
    ParseObservation,
)
from braincrew.digest import canonical_digest

SHA256_PATTERN = r"^sha256:[0-9a-f]{64}$"
COMMIT_SHA_PATTERN = r"^[0-9a-f]{40}$"
SAFE_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$"
SAFE_DETAIL_PATTERN = r"^[A-Za-z0-9_.:-]{1,160}$"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class LivePreflightBlocker(StrictModel):
    code: str = Field(pattern=SAFE_DETAIL_PATTERN)
    operation: OperationName | None = None
    case_id: str | None = Field(default=None, pattern=SAFE_ID_PATTERN)
    detail: str | None = Field(default=None, pattern=SAFE_DETAIL_PATTERN)


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


class LivePreflightArtifact(StrictModel):
    schema_version: Literal["live-preflight-evidence-v1"]
    capture_state: Literal["captured"]
    run_id: str = Field(pattern=SAFE_ID_PATTERN)
    captured_at: datetime
    evaluation_plane_sha: str = Field(pattern=COMMIT_SHA_PATTERN)
    sut_commit_sha: str = Field(pattern=COMMIT_SHA_PATTERN)
    corpus_observations: tuple[CorpusIdentityEvidence, ...]
    parse_observations: tuple[ParseObservationEvidence, ...]
    blockers: tuple[LivePreflightBlocker, ...]
    logical_digest: str = Field(pattern=SHA256_PATTERN)

    @model_validator(mode="after")
    def require_aware_capture_time(self) -> LivePreflightArtifact:
        if self.captured_at.tzinfo is None or self.captured_at.utcoffset() is None:
            raise ValueError("captured_at must include a timezone")
        if self.sut_commit_sha != "72805930d9addd8ea41743d1922acf8de621c3f8":
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
) -> LivePreflightArtifact:
    artifact = LivePreflightArtifact(
        schema_version="live-preflight-evidence-v1",
        capture_state="captured",
        run_id=run_id,
        captured_at=captured_at,
        evaluation_plane_sha=evaluation_plane_sha,
        sut_commit_sha=sut_commit_sha,
        corpus_observations=tuple(_sanitize_corpus(item) for item in corpus_observations),
        parse_observations=tuple(_sanitize_parse(item) for item in parse_observations),
        blockers=blockers,
        logical_digest="sha256:" + "0" * 64,
    )
    return artifact.model_copy(
        update={"logical_digest": canonical_digest(_logical_payload(artifact))}
    )


def write_live_preflight_artifact(
    artifact: LivePreflightArtifact,
    path: Path,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(
        artifact.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    with path.open("x", encoding="utf-8") as artifact_file:
        artifact_file.write(serialized + "\n")
    return path


def replay_live_preflight_artifact(path: Path) -> dict[str, str | int]:
    artifact = LivePreflightArtifact.model_validate_json(path.read_text(encoding="utf-8"))
    recomputed_digest = canonical_digest(_logical_payload(artifact))
    if artifact.logical_digest != recomputed_digest:
        raise ValueError("artifact logical content does not reproduce its stored digest")
    return {
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
        attempts=tuple(observation.attempts),
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
        attempts=tuple(observation.attempts),
    )


def _logical_payload(artifact: LivePreflightArtifact) -> dict[str, object]:
    return artifact.model_dump(mode="json", exclude={"logical_digest"})


def _text_digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


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
