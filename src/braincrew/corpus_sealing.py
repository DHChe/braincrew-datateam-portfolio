from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import date
from importlib import resources
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, JsonValue, StringConstraints, ValidationError

AX_SCHEMA_MERGE_COMMIT = "47673b83a9fb431f2bad550781db18c7bee8b67e"
EXPECTED_SCHEMA_DIGESTS = {
    "ax-synthetic-seed-content-v1.schema.json": (
        "sha256:372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb"
    ),
    "ax-synthetic-seed-pack-v1.schema.json": (
        "sha256:4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa"
    ),
}
MAX_SOURCES = 200
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_SOURCE_BYTES = 32 * 1024 * 1024
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_JSON_NESTING = 64

Digest = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
Identifier = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=160,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,159}$",
    ),
]
Identifier80 = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$",
    ),
]
VisibilityRole = Literal["Executive", "HRAdmin", "HRPractitioner", "Employee"]

_EMAIL_PATTERN = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
_NETWORK_OR_DATABASE_URL_PATTERN = re.compile(
    r"(?i)\b(?:https?://|postgres(?:ql)?://|mysql://|redis://|mongodb(?:\+srv)?://)"
)
_FORBIDDEN_FIELD_LINE_PATTERN = re.compile(
    r"(?im)^[ \t]*(?:answer[ _-]*key|benchmark|case[ _-]*to[ _-]*answer|"
    r"expected[ _-]*(?:answer|evidence)|fixture[ _-]*observation|metric|prompt|query|"
    r"score|split[ _-]*label)[ \t]*:"
)
_FORBIDDEN_KEY_PARTS = (
    "answer_key",
    "authorization",
    "benchmark",
    "case_to_answer",
    "credential",
    "database_url",
    "expected_answer",
    "expected_evidence",
    "fixture_observation",
    "metric",
    "password",
    "private_data",
    "prompt",
    "query",
    "score",
    "secret",
    "split_label",
)
_FORBIDDEN_VALUE_PARTS = (
    "-----begin private key-----",
    "private customer document",
    "real customer document",
    "unreviewed private data",
)


class CorpusPackError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class VisibilityScope(_StrictModel):
    roles: list[VisibilityRole] = Field(min_length=1, max_length=4)


class SourceDescriptor(_StrictModel):
    source_id: Identifier
    path: Annotated[str, StringConstraints(min_length=1, max_length=500)]
    source_uri: Annotated[
        str,
        StringConstraints(min_length=8, max_length=500, pattern=r"^demo://[^@?#]+$"),
    ]
    source_title: Annotated[str, StringConstraints(min_length=1, max_length=300)]
    source_type: Identifier80
    source_class: Literal["company_rule", "company_reference"]
    document_version: Identifier80
    effective_date: str | None = None
    revision_date: str | None = None
    applicability_scope: dict[str, JsonValue]
    visibility_scope: VisibilityScope
    content_sha256: Digest
    license: Literal["CC0-1.0"]
    provenance_status: Literal["reviewed"]
    synthetic: Literal[True]
    demo_company: Literal[True]
    corpus_mode: Literal["demo"]


class CorpusManifest(_StrictModel):
    schema_version: Literal["ax-synthetic-seed-content-v1"]
    corpus_id: Identifier
    corpus_version: Identifier80
    synthetic: Literal[True]
    demo_company: Literal[True]
    corpus_mode: Literal["demo"]
    license: Literal["CC0-1.0"]
    provenance_status: Literal["reviewed"]
    sources: list[SourceDescriptor] = Field(min_length=1, max_length=MAX_SOURCES)
    sealed_content_digest: Digest


class AxSchemaContract(_StrictModel):
    merge_commit: Literal["47673b83a9fb431f2bad550781db18c7bee8b67e"]
    content_schema_sha256: Literal[
        "sha256:372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb"
    ]
    pack_schema_sha256: Literal[
        "sha256:4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa"
    ]


class SealedSourceReceipt(_StrictModel):
    source_id: Identifier
    content_sha256: Digest


class SealingReceipt(_StrictModel):
    schema_version: Literal["corpus-sealing-receipt-v1"]
    corpus_id: Identifier
    corpus_version: Identifier80
    sealed_content_digest: Digest
    source_count: int = Field(ge=1, le=MAX_SOURCES)
    total_source_bytes: int = Field(ge=1, le=MAX_TOTAL_SOURCE_BYTES)
    sources: list[SealedSourceReceipt] = Field(min_length=1, max_length=MAX_SOURCES)
    ax_schema_contract: AxSchemaContract
    receipt_digest: Digest


@dataclass(frozen=True)
class ValidatedCorpus:
    directory: Path
    manifest: CorpusManifest
    source_paths: tuple[Path, ...]
    total_source_bytes: int


@dataclass(frozen=True)
class SealingResult:
    receipt_path: Path
    receipt: SealingReceipt


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_digest(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def seal_corpus_pack(staging_dir: Path, output_root: Path) -> SealingResult:
    _verify_vendored_schemas()
    staging = staging_dir.resolve(strict=True)
    output = output_root.resolve()
    _require_isolated_staging(staging, output)
    validated = _validate_corpus_directory(staging)
    destination = output / validated.manifest.corpus_id / validated.manifest.corpus_version
    if destination.exists():
        raise CorpusPackError(
            "SEALED_CORPUS_VERSION_EXISTS",
            "the corpus version already exists and cannot be modified",
        )

    receipt = _build_receipt(validated)
    corpus_root = destination.parent
    corpus_root.mkdir(parents=True, exist_ok=True)
    try:
        with TemporaryDirectory(
            prefix=f".{validated.manifest.corpus_version}-", dir=corpus_root
        ) as raw:
            temporary = Path(raw)
            _copy_validated_bytes(validated, temporary)
            receipt_path = temporary / "sealing-receipt.json"
            receipt_path.write_bytes(canonical_json_bytes(receipt.model_dump(mode="json")) + b"\n")
            os.rename(temporary, destination)
    except FileExistsError as exc:
        raise CorpusPackError(
            "SEALED_CORPUS_VERSION_EXISTS",
            "the corpus version already exists and cannot be modified",
        ) from exc
    except OSError as exc:
        if destination.exists():
            raise CorpusPackError(
                "SEALED_CORPUS_VERSION_EXISTS",
                "the corpus version already exists and cannot be modified",
            ) from exc
        raise
    return SealingResult(receipt_path=destination / "sealing-receipt.json", receipt=receipt)


def replay_sealing_receipt(receipt_path: Path) -> dict[str, str]:
    _verify_vendored_schemas()
    raw_bytes, text = _read_utf8_bytes(receipt_path, maximum_bytes=MAX_MANIFEST_BYTES)
    try:
        payload = json.loads(text, parse_float=_reject_float)
        _validate_json_nesting(payload)
        receipt = SealingReceipt.model_validate(payload)
    except (json.JSONDecodeError, RecursionError, ValidationError, ValueError) as exc:
        raise CorpusPackError("CORPUS_RECEIPT_INVALID", "receipt is not strict JSON") from exc
    canonical_receipt = canonical_json_bytes(receipt.model_dump(mode="json")) + b"\n"
    if raw_bytes != canonical_receipt:
        raise CorpusPackError("CORPUS_RECEIPT_INVALID", "receipt bytes are not canonical")
    receipt_payload = receipt.model_dump(mode="json")
    declared_receipt_digest = receipt_payload.pop("receipt_digest")
    if sha256_digest(canonical_json_bytes(receipt_payload)) != declared_receipt_digest:
        raise CorpusPackError("CORPUS_RECEIPT_DIGEST_MISMATCH", "receipt digest does not reproduce")

    validated = _validate_corpus_directory(
        receipt_path.resolve(strict=True).parent,
        allowed_extra_files={
            "sealing-receipt.json",
            "qualification-receipt.json",
            "import-manifest.json",
        },
    )
    expected = _build_receipt(validated)
    if expected != receipt:
        raise CorpusPackError(
            "CORPUS_RECEIPT_DIGEST_MISMATCH",
            "receipt does not bind the current sealed corpus bytes",
        )
    return {
        "receipt_digest": receipt.receipt_digest,
        "sealed_content_digest": receipt.sealed_content_digest,
        "corpus_version": receipt.corpus_version,
    }


def validate_sealed_corpus(
    directory: Path,
    *,
    allowed_extra_files: set[str] | None = None,
) -> ValidatedCorpus:
    """Revalidate immutable sealed corpus bytes against the pinned AX schema."""
    _verify_vendored_schemas()
    return _validate_corpus_directory(
        directory.resolve(strict=True),
        allowed_extra_files=allowed_extra_files,
    )


def _validate_corpus_directory(
    directory: Path,
    *,
    allowed_extra_files: set[str] | None = None,
) -> ValidatedCorpus:
    raw_manifest, manifest_text = _read_utf8_bytes(
        directory / "corpus-manifest.json",
        maximum_bytes=MAX_MANIFEST_BYTES,
    )
    try:
        payload = json.loads(manifest_text, parse_float=_reject_float)
        _validate_json_nesting(payload)
    except (json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise CorpusPackError("CORPUS_PACK_SCHEMA_INVALID", "manifest is not strict JSON") from exc
    _reject_unsafe_content(payload)
    try:
        manifest = CorpusManifest.model_validate(payload)
        _validate_dates(manifest)
    except (ValidationError, ValueError) as exc:
        raise CorpusPackError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "manifest does not match the strict AX content schema",
        ) from exc
    if raw_manifest != canonical_json_bytes(manifest.model_dump(mode="json")):
        raise CorpusPackError(
            "CORPUS_PACK_CANONICAL_BYTES_INVALID",
            "manifest bytes are not canonical JSON",
        )
    manifest_payload = manifest.model_dump(mode="json")
    declared_digest = manifest_payload.pop("sealed_content_digest")
    if sha256_digest(canonical_json_bytes(manifest_payload)) != declared_digest:
        raise CorpusPackError(
            "CORPUS_PACK_DIGEST_MISMATCH",
            "sealed content digest does not reproduce",
        )

    source_ids: set[str] = set()
    relative_paths: set[str] = set()
    source_paths: list[Path] = []
    total_source_bytes = 0
    for descriptor in manifest.sources:
        if descriptor.source_id in source_ids or descriptor.path in relative_paths:
            raise CorpusPackError(
                "CORPUS_PACK_SCHEMA_INVALID",
                "source identities and paths must be unique",
            )
        if len(descriptor.visibility_scope.roles) != len(set(descriptor.visibility_scope.roles)):
            raise CorpusPackError(
                "CORPUS_PACK_SCHEMA_INVALID",
                "visibility roles must be unique",
            )
        source_ids.add(descriptor.source_id)
        relative_paths.add(descriptor.path)
        source_path = _resolve_pack_path(directory, descriptor.path)
        source_bytes, source_text = _read_utf8_bytes(
            source_path,
            maximum_bytes=MAX_SOURCE_BYTES,
        )
        total_source_bytes += len(source_bytes)
        if total_source_bytes > MAX_TOTAL_SOURCE_BYTES:
            raise CorpusPackError(
                "CORPUS_PACK_RESOURCE_LIMIT_EXCEEDED",
                "total accepted source bytes exceed the v1 limit",
            )
        if sha256_digest(source_bytes) != descriptor.content_sha256:
            raise CorpusPackError(
                "CORPUS_PACK_DIGEST_MISMATCH",
                f"source bytes do not match descriptor {descriptor.source_id}",
            )
        _reject_unsafe_content(source_text)
        source_paths.append(source_path)

    allowed_files = {"corpus-manifest.json", *relative_paths}
    allowed_files.update(allowed_extra_files or set())
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise CorpusPackError("CORPUS_PACK_PATH_INVALID", "symbolic links are forbidden")
        if path.is_file() and path.relative_to(directory).as_posix() not in allowed_files:
            raise CorpusPackError(
                "CORPUS_PACK_UNDECLARED_FILE",
                "staging contains a file not declared by the manifest",
            )
    return ValidatedCorpus(
        directory=directory,
        manifest=manifest,
        source_paths=tuple(source_paths),
        total_source_bytes=total_source_bytes,
    )


def _build_receipt(validated: ValidatedCorpus) -> SealingReceipt:
    payload: dict[str, Any] = {
        "schema_version": "corpus-sealing-receipt-v1",
        "corpus_id": validated.manifest.corpus_id,
        "corpus_version": validated.manifest.corpus_version,
        "sealed_content_digest": validated.manifest.sealed_content_digest,
        "source_count": len(validated.manifest.sources),
        "total_source_bytes": validated.total_source_bytes,
        "sources": [
            {
                "source_id": source.source_id,
                "content_sha256": source.content_sha256,
            }
            for source in validated.manifest.sources
        ],
        "ax_schema_contract": {
            "merge_commit": AX_SCHEMA_MERGE_COMMIT,
            "content_schema_sha256": EXPECTED_SCHEMA_DIGESTS[
                "ax-synthetic-seed-content-v1.schema.json"
            ],
            "pack_schema_sha256": EXPECTED_SCHEMA_DIGESTS["ax-synthetic-seed-pack-v1.schema.json"],
        },
    }
    payload["receipt_digest"] = sha256_digest(canonical_json_bytes(payload))
    return SealingReceipt.model_validate(payload)


def _copy_validated_bytes(validated: ValidatedCorpus, destination: Path) -> None:
    manifest_destination = destination / "corpus-manifest.json"
    shutil.copyfile(validated.directory / "corpus-manifest.json", manifest_destination)
    for source_path in validated.source_paths:
        relative = source_path.relative_to(validated.directory)
        destination_path = destination / relative
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, destination_path)


def _require_isolated_staging(staging: Path, output: Path) -> None:
    repository_root = Path(__file__).resolve().parents[2]
    if staging.is_relative_to(repository_root):
        raise CorpusPackError(
            "CORPUS_STAGING_NOT_ISOLATED",
            "staging must be outside the Braincrew repository",
        )
    if output.is_relative_to(staging) or staging.is_relative_to(output):
        raise CorpusPackError(
            "CORPUS_STAGING_NOT_ISOLATED",
            "staging and sealed output must not contain each other",
        )


def _resolve_pack_path(directory: Path, relative_path: str) -> Path:
    path = PurePosixPath(relative_path)
    if (
        "\\" in relative_path
        or "\x00" in relative_path
        or relative_path != path.as_posix()
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise CorpusPackError(
            "CORPUS_PACK_PATH_INVALID",
            "source paths must be normalized relative POSIX paths",
        )
    candidate = directory.joinpath(*path.parts)
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(directory)
    except (OSError, ValueError) as exc:
        raise CorpusPackError(
            "CORPUS_PACK_PATH_INVALID",
            "source path escapes staging or is unavailable",
        ) from exc
    if not resolved.is_file() or candidate.is_symlink():
        raise CorpusPackError("CORPUS_PACK_PATH_INVALID", "source path must name a regular file")
    return resolved


def _read_utf8_bytes(path: Path, *, maximum_bytes: int) -> tuple[bytes, str]:
    try:
        if path.stat().st_size > maximum_bytes:
            raise CorpusPackError(
                "CORPUS_PACK_RESOURCE_LIMIT_EXCEEDED",
                "pack file exceeds the v1 byte limit",
            )
        value = path.read_bytes()
    except OSError as exc:
        raise CorpusPackError(
            "CORPUS_PACK_PATH_INVALID",
            "required pack file is unavailable",
        ) from exc
    if value.startswith(b"\xef\xbb\xbf"):
        raise CorpusPackError("CORPUS_PACK_CANONICAL_BYTES_INVALID", "UTF-8 BOM is forbidden")
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CorpusPackError(
            "CORPUS_PACK_CANONICAL_BYTES_INVALID",
            "pack files must be valid UTF-8",
        ) from exc
    if "\r" in text or unicodedata.normalize("NFC", text) != text:
        raise CorpusPackError(
            "CORPUS_PACK_CANONICAL_BYTES_INVALID",
            "pack text must already be NFC with LF-only line endings",
        )
    return value, text


def _validate_dates(manifest: CorpusManifest) -> None:
    for source in manifest.sources:
        for value in (source.effective_date, source.revision_date):
            if value is not None:
                if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value) is None:
                    raise ValueError("date must use YYYY-MM-DD")
                date.fromisoformat(value)


def _validate_json_nesting(value: object) -> None:
    pending: list[tuple[object, int]] = [(value, 0)]
    while pending:
        current, depth = pending.pop()
        if depth > MAX_JSON_NESTING:
            raise CorpusPackError(
                "CORPUS_PACK_RESOURCE_LIMIT_EXCEEDED",
                "JSON nesting exceeds the v1 resource envelope",
            )
        if isinstance(current, dict):
            pending.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, list):
            pending.extend((child, depth + 1) for child in current)


def _reject_unsafe_content(value: object) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = key.casefold().replace("-", "_")
            if any(part in normalized_key for part in _FORBIDDEN_KEY_PARTS):
                raise CorpusPackError(
                    "CORPUS_PACK_UNSAFE_CONTENT",
                    "pack contains a forbidden field",
                )
            _reject_unsafe_content(child)
        return
    if isinstance(value, list):
        for child in value:
            _reject_unsafe_content(child)
        return
    if isinstance(value, float):
        raise CorpusPackError(
            "CORPUS_PACK_SCHEMA_INVALID",
            "floating-point numbers are forbidden",
        )
    if not isinstance(value, str):
        return
    lowered = value.casefold()
    if (
        _EMAIL_PATTERN.search(value)
        or _NETWORK_OR_DATABASE_URL_PATTERN.search(value)
        or _FORBIDDEN_FIELD_LINE_PATTERN.search(value)
        or any(part in lowered for part in _FORBIDDEN_VALUE_PARTS)
    ):
        raise CorpusPackError(
            "CORPUS_PACK_UNSAFE_CONTENT",
            "pack contains a forbidden value class",
        )


def _verify_vendored_schemas() -> None:
    schema_dir = _schema_directory()
    for schema_name, expected_digest in EXPECTED_SCHEMA_DIGESTS.items():
        schema_path = schema_dir / schema_name
        digest_path = schema_path.with_suffix(".sha256")
        try:
            schema_bytes = schema_path.read_bytes()
            declared_digest = digest_path.read_text(encoding="ascii")
        except OSError as exc:
            raise CorpusPackError("AX_SCHEMA_DRIFT", "vendored AX schema is unavailable") from exc
        if (
            sha256_digest(schema_bytes) != expected_digest
            or declared_digest != f"{expected_digest}\n"
        ):
            raise CorpusPackError(
                "AX_SCHEMA_DRIFT",
                "vendored AX schema bytes or digest differ from the pinned merge contract",
            )


def _schema_directory() -> Path:
    repository_schema_dir = Path(__file__).resolve().parents[2] / "schemas"
    if repository_schema_dir.is_dir():
        return repository_schema_dir
    package_schema_dir = resources.files("braincrew").joinpath("schemas")
    return Path(str(package_schema_dir))


def _reject_float(_: str) -> None:
    raise ValueError("floating-point JSON values are forbidden")
