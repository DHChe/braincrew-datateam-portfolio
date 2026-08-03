from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError

from braincrew.corpus_sealing import (
    EXPECTED_SCHEMA_DIGESTS,
    MAX_SOURCES,
    MAX_TOTAL_SOURCE_BYTES,
    canonical_json_bytes,
    sha256_digest,
)

CONTENT_SCHEMA_NAME = "ax-synthetic-seed-content-v1.schema.json"
CONTENT_SCHEMA_DIGEST_NAME = "ax-synthetic-seed-content-v1.schema.sha256"
EXPECTED_BRAINCREW_REMOTES = frozenset(
    {
        "git@github.com:DHChe/braincrew-datateam-portfolio.git",
        "https://github.com/DHChe/braincrew-datateam-portfolio.git",
        "ssh://git@github.com/DHChe/braincrew-datateam-portfolio.git",
        "git@github.com:DHChe/evidence-first-rag-evaluation.git",
        "https://github.com/DHChe/evidence-first-rag-evaluation.git",
        "ssh://git@github.com/DHChe/evidence-first-rag-evaluation.git",
    }
)
DENIED_CAPABILITY_CLASSES = (
    "ax_repository",
    "braincrew_repository",
    "credential_store",
    "database",
    "evaluation_dataset",
    "network",
    "post_seal_feedback",
    "prior_artifact",
    "private_document",
    "test_fixture",
    "undeclared_filesystem",
)
MAX_TOOL_BYTES = 64 * 1024 * 1024

Digest = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
ToolLabel = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$"),
]
Timestamp = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$"),
]


class AuthoringBoundaryError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class AuthoringToolIdentity(_StrictModel):
    name: ToolLabel
    version: ToolLabel
    executable_sha256: Digest
    invocation_sha256: Digest


class AuthoringInputDigests(_StrictModel):
    brief_sha256: Digest
    schema_sha256: Digest
    schema_digest_file_sha256: Digest
    declared_inputs_sha256: Digest


class AuthoringExitState(_StrictModel):
    status: Literal["COMPLETED", "FAILED"]
    exit_code: int = Field(ge=0, le=255)


class AuthoringOutputFileDigest(_StrictModel):
    ordinal: int = Field(ge=0, lt=MAX_SOURCES)
    path_sha256: Digest
    content_sha256: Digest
    byte_count: int = Field(ge=0)


class AuthoringOutputDigest(_StrictModel):
    file_count: int = Field(ge=0, le=MAX_SOURCES)
    total_bytes: int = Field(ge=0, le=MAX_TOTAL_SOURCE_BYTES)
    files: list[AuthoringOutputFileDigest]
    tree_sha256: Digest


class AuthoringIndependenceReceipt(_StrictModel):
    schema_version: Literal["corpus-authoring-independence-receipt-v1"]
    braincrew_commit_sha: Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
    tool: AuthoringToolIdentity
    input_digests: AuthoringInputDigests
    denied_capability_classes: list[
        Literal[
            "ax_repository",
            "braincrew_repository",
            "credential_store",
            "database",
            "evaluation_dataset",
            "network",
            "post_seal_feedback",
            "prior_artifact",
            "private_document",
            "test_fixture",
            "undeclared_filesystem",
        ]
    ]
    sandbox_backend: Literal["macos-sandbox-exec", "linux-bubblewrap"]
    staging_run_id: Annotated[str, StringConstraints(pattern=r"^authoring-[0-9a-f]{32}$")]
    started_at: Timestamp
    ended_at: Timestamp
    duration_ms: int = Field(ge=0)
    exit_state: AuthoringExitState
    output: AuthoringOutputDigest
    receipt_digest: Digest


@dataclass(frozen=True)
class AuthoringLaunchResult:
    receipt_path: Path
    receipt: AuthoringIndependenceReceipt


@dataclass(frozen=True)
class _SandboxInvocation:
    backend: Literal["macos-sandbox-exec", "linux-bubblewrap"]
    command: list[str]
    environment: dict[str, str]
    working_directory: Path


def launch_authoring_process(
    *,
    braincrew_root: Path,
    brief_relative_path: Path,
    staging_dir: Path,
    receipt_path: Path,
    tool_path: Path,
    tool_name: str,
    tool_version: str,
) -> AuthoringLaunchResult:
    source_root, commit_sha = _validate_clean_source(braincrew_root)
    brief = _resolve_committed_brief(source_root, brief_relative_path)
    schema = source_root / "schemas" / CONTENT_SCHEMA_NAME
    schema_digest_file = source_root / "schemas" / CONTENT_SCHEMA_DIGEST_NAME
    _validate_schema_pin(schema, schema_digest_file)
    staging = _validate_staging(source_root, staging_dir)
    receipt = _validate_receipt_path(source_root, staging, receipt_path)
    tool = _validate_tool(source_root, staging, tool_path)
    if receipt.exists():
        raise AuthoringBoundaryError(
            "AUTHORING_RECEIPT_EXISTS",
            "the independence receipt is create-only",
        )

    brief_bytes = brief.read_bytes()
    schema_bytes = schema.read_bytes()
    schema_digest_bytes = schema_digest_file.read_bytes()
    declared_input_payload = {
        "brief_sha256": sha256_digest(brief_bytes),
        "schema_sha256": sha256_digest(schema_bytes),
        "schema_digest_file_sha256": sha256_digest(schema_digest_bytes),
    }
    declared_input_bytes = canonical_json_bytes(declared_input_payload) + b"\n"
    input_digests = AuthoringInputDigests.model_validate(
        {
            **declared_input_payload,
            "declared_inputs_sha256": sha256_digest(declared_input_bytes),
        }
    )
    executable_digest = sha256_digest(tool.read_bytes())
    tool_identity_payload = {
        "name": tool_name,
        "version": tool_version,
        "executable_sha256": executable_digest,
    }
    try:
        tool_identity = AuthoringToolIdentity.model_validate(
            {
                **tool_identity_payload,
                "invocation_sha256": sha256_digest(canonical_json_bytes(tool_identity_payload)),
            }
        )
    except ValidationError as exc:
        raise AuthoringBoundaryError(
            "AUTHORING_TOOL_IDENTITY_INVALID",
            "tool name and version must use bounded public labels",
        ) from exc

    staging_run_id = f"authoring-{uuid.uuid4().hex}"
    started_at = datetime.now(UTC)
    monotonic_start = time.monotonic_ns()
    with TemporaryDirectory(prefix="braincrew-authoring-inputs-") as raw_inputs:
        input_directory = Path(raw_inputs).resolve()
        _write_read_only(input_directory / "authoring-brief.md", brief_bytes)
        _write_read_only(input_directory / CONTENT_SCHEMA_NAME, schema_bytes)
        _write_read_only(input_directory / CONTENT_SCHEMA_DIGEST_NAME, schema_digest_bytes)
        _write_read_only(input_directory / "input-digests.json", declared_input_bytes)
        invocation = _build_sandbox_invocation(
            input_directory=input_directory,
            staging_directory=staging,
            tool=tool,
        )
        completed = subprocess.run(
            invocation.command,
            check=False,
            cwd=invocation.working_directory,
            env=invocation.environment,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    ended_at = datetime.now(UTC)
    duration_ms = max(0, (time.monotonic_ns() - monotonic_start) // 1_000_000)
    normalized_exit_code = _normalize_exit_code(completed.returncode)
    output_digest = _digest_staging_outputs(staging)
    payload: dict[str, Any] = {
        "schema_version": "corpus-authoring-independence-receipt-v1",
        "braincrew_commit_sha": commit_sha,
        "tool": tool_identity.model_dump(mode="json"),
        "input_digests": input_digests.model_dump(mode="json"),
        "denied_capability_classes": list(DENIED_CAPABILITY_CLASSES),
        "sandbox_backend": invocation.backend,
        "staging_run_id": staging_run_id,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "ended_at": ended_at.isoformat().replace("+00:00", "Z"),
        "duration_ms": duration_ms,
        "exit_state": {
            "status": "COMPLETED" if normalized_exit_code == 0 else "FAILED",
            "exit_code": normalized_exit_code,
        },
        "output": output_digest.model_dump(mode="json"),
    }
    payload["receipt_digest"] = sha256_digest(canonical_json_bytes(payload))
    independence_receipt = AuthoringIndependenceReceipt.model_validate(payload)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    try:
        with receipt.open("xb") as receipt_file:
            receipt_file.write(
                canonical_json_bytes(independence_receipt.model_dump(mode="json")) + b"\n"
            )
    except FileExistsError as exc:
        raise AuthoringBoundaryError(
            "AUTHORING_RECEIPT_EXISTS",
            "the independence receipt is create-only",
        ) from exc
    return AuthoringLaunchResult(receipt_path=receipt, receipt=independence_receipt)


def _validate_clean_source(braincrew_root: Path) -> tuple[Path, str]:
    source_root = braincrew_root.resolve(strict=True)
    if not source_root.is_dir():
        raise AuthoringBoundaryError("BRAINCREW_SOURCE_INVALID", "source root must be a directory")
    try:
        top_level = _git_output(source_root, "rev-parse", "--show-toplevel")
        commit_sha = _git_output(source_root, "rev-parse", "HEAD")
        status = _git_output(source_root, "status", "--porcelain", "--untracked-files=all")
        origin_url = _git_output(source_root, "remote", "get-url", "origin")
    except subprocess.CalledProcessError as exc:
        raise AuthoringBoundaryError(
            "BRAINCREW_SOURCE_INVALID",
            "source root must be a Git worktree",
        ) from exc
    if Path(top_level).resolve() != source_root:
        raise AuthoringBoundaryError(
            "BRAINCREW_SOURCE_INVALID",
            "source root must be the Git worktree root",
        )
    if origin_url not in EXPECTED_BRAINCREW_REMOTES:
        raise AuthoringBoundaryError(
            "BRAINCREW_SOURCE_INVALID",
            "source root must identify the Braincrew repository",
        )
    if (
        status
        or len(commit_sha) != 40
        or any(character not in "0123456789abcdef" for character in commit_sha)
    ):
        raise AuthoringBoundaryError(
            "BRAINCREW_SOURCE_NOT_CLEAN",
            "authoring requires a clean committed Braincrew SHA",
        )
    return source_root, commit_sha


def _resolve_committed_brief(source_root: Path, relative_path: Path) -> Path:
    raw = relative_path.as_posix()
    pure_path = PurePosixPath(raw)
    if relative_path.is_absolute() or "\\" in raw or ".." in pure_path.parts:
        raise AuthoringBoundaryError(
            "AUTHORING_BRIEF_INVALID",
            "the brief must be a repository-relative POSIX path",
        )
    brief = (source_root / Path(*pure_path.parts)).resolve(strict=True)
    if not brief.is_file() or not brief.is_relative_to(source_root):
        raise AuthoringBoundaryError(
            "AUTHORING_BRIEF_INVALID",
            "the approved brief must be a regular file inside the source root",
        )
    try:
        _git_output(source_root, "ls-files", "--error-unmatch", "--", pure_path.as_posix())
    except subprocess.CalledProcessError as exc:
        raise AuthoringBoundaryError(
            "AUTHORING_BRIEF_NOT_COMMITTED",
            "the approved brief must be tracked by the clean source commit",
        ) from exc
    return brief


def _validate_schema_pin(schema: Path, digest_file: Path) -> None:
    try:
        schema_bytes = schema.read_bytes()
        declared_digest_bytes = digest_file.read_bytes()
    except OSError as exc:
        raise AuthoringBoundaryError(
            "AX_SCHEMA_DRIFT",
            "the pinned AX pack schema contract is incomplete",
        ) from exc
    expected_digest = EXPECTED_SCHEMA_DIGESTS[CONTENT_SCHEMA_NAME]
    if (
        sha256_digest(schema_bytes) != expected_digest
        or declared_digest_bytes != f"{expected_digest}\n".encode()
    ):
        raise AuthoringBoundaryError(
            "AX_SCHEMA_DRIFT",
            "the pinned AX pack schema bytes or declaration drifted",
        )


def _validate_staging(source_root: Path, staging_dir: Path) -> Path:
    if staging_dir.is_symlink():
        raise AuthoringBoundaryError(
            "AUTHORING_STAGING_NOT_ISOLATED",
            "staging must not be a symbolic link",
        )
    staging = staging_dir.resolve(strict=True)
    if not staging.is_dir() or staging.is_relative_to(source_root):
        raise AuthoringBoundaryError(
            "AUTHORING_STAGING_NOT_ISOLATED",
            "staging must be a directory outside the Braincrew source",
        )
    if any(staging.iterdir()):
        raise AuthoringBoundaryError(
            "AUTHORING_STAGING_NOT_EMPTY",
            "authoring requires an empty writable staging directory",
        )
    return staging


def _validate_receipt_path(source_root: Path, staging: Path, receipt_path: Path) -> Path:
    receipt = receipt_path.resolve()
    if receipt.is_relative_to(source_root) or receipt.is_relative_to(staging):
        raise AuthoringBoundaryError(
            "AUTHORING_RECEIPT_PATH_INVALID",
            "the independence receipt must be outside source and staging",
        )
    return receipt


def _validate_tool(source_root: Path, staging: Path, tool_path: Path) -> Path:
    tool = tool_path.resolve(strict=True)
    if (
        not tool.is_file()
        or tool.is_symlink()
        or tool.is_relative_to(source_root)
        or tool.is_relative_to(staging)
        or not os.access(tool, os.X_OK)
    ):
        raise AuthoringBoundaryError(
            "AUTHORING_TOOL_INVALID",
            "the authoring tool must be an executable regular file outside source and staging",
        )
    if tool.stat().st_size > MAX_TOOL_BYTES:
        raise AuthoringBoundaryError(
            "AUTHORING_TOOL_INVALID",
            "the authoring tool exceeds the v1 size limit",
        )
    return tool


def _write_read_only(path: Path, value: bytes) -> None:
    path.write_bytes(value)
    path.chmod(0o444)


def _build_sandbox_invocation(
    *,
    input_directory: Path,
    staging_directory: Path,
    tool: Path,
) -> _SandboxInvocation:
    safe_environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
    }
    if platform.system() == "Darwin" and Path("/usr/bin/sandbox-exec").is_file():
        safe_environment.update(
            {
                "BRAINCREW_AUTHORING_INPUT_DIR": str(input_directory),
                "BRAINCREW_AUTHORING_STAGING_DIR": str(staging_directory),
            }
        )
        profile = _macos_sandbox_profile(input_directory, staging_directory, tool)
        return _SandboxInvocation(
            backend="macos-sandbox-exec",
            command=["/usr/bin/sandbox-exec", "-p", profile, str(tool)],
            environment=safe_environment,
            working_directory=staging_directory,
        )
    bubblewrap = shutil.which("bwrap")
    if platform.system() == "Linux" and bubblewrap is not None:
        safe_environment.update(
            {
                "BRAINCREW_AUTHORING_INPUT_DIR": "/inputs",
                "BRAINCREW_AUTHORING_STAGING_DIR": "/staging",
            }
        )
        command = [
            bubblewrap,
            "--die-with-parent",
            "--new-session",
            "--unshare-all",
            "--clearenv",
            "--dev",
            "/dev",
            "--proc",
            "/proc",
        ]
        for system_root in ("/usr", "/bin", "/lib", "/lib64"):
            if Path(system_root).exists():
                command.extend(["--ro-bind", system_root, system_root])
        command.extend(
            [
                "--ro-bind",
                str(input_directory),
                "/inputs",
                "--bind",
                str(staging_directory),
                "/staging",
                "--ro-bind",
                str(tool),
                "/authoring-tool",
                "--chdir",
                "/staging",
            ]
        )
        for key, value in safe_environment.items():
            command.extend(["--setenv", key, value])
        command.append("/authoring-tool")
        return _SandboxInvocation(
            backend="linux-bubblewrap",
            command=command,
            environment={},
            working_directory=staging_directory,
        )
    raise AuthoringBoundaryError(
        "AUTHORING_SANDBOX_UNAVAILABLE",
        "a supported OS sandbox backend is required",
    )


def _macos_sandbox_profile(input_directory: Path, staging_directory: Path, tool: Path) -> str:
    readable_system_roots = (
        "/System",
        "/usr/bin",
        "/usr/lib",
        "/usr/share",
        "/bin",
        "/sbin",
        "/Library/Developer/CommandLineTools",
    )
    metadata_paths = {
        Path("/Library"),
        Path("/Library/Developer"),
        Path("/etc"),
        Path("/private/tmp"),
        Path("/tmp"),
        Path("/var"),
    }
    for allowed_path in (input_directory, staging_directory, tool):
        metadata_paths.update(allowed_path.parents)
    rules = [
        "(version 1)",
        "(deny default)",
        "(allow process*)",
        "(allow sysctl-read)",
        '(allow file-read-data (literal "/"))',
    ]
    rules.extend(
        f"(allow file-read* (subpath {_sandbox_literal(root)}))" for root in readable_system_roots
    )
    rules.extend(
        f"(allow file-read-metadata (literal {_sandbox_literal(str(path))}))"
        for path in sorted(metadata_paths, key=str)
    )
    rules.extend(
        [
            f"(allow file-read* (literal {_sandbox_literal(str(tool))}))",
            f"(allow file-read* (subpath {_sandbox_literal(str(input_directory))}))",
            f"(allow file-read* (subpath {_sandbox_literal(str(staging_directory))}))",
            f"(allow file-write* (subpath {_sandbox_literal(str(staging_directory))}))",
            '(allow file-read* (literal "/dev/null"))',
            '(allow file-read* (literal "/dev/urandom"))',
            "(deny network*)",
        ]
    )
    return "\n".join(rules) + "\n"


def _sandbox_literal(value: str) -> str:
    return json.dumps(value)


def _digest_staging_outputs(staging: Path) -> AuthoringOutputDigest:
    files: list[dict[str, Any]] = []
    total_bytes = 0
    for path in sorted(staging.rglob("*"), key=lambda item: item.relative_to(staging).as_posix()):
        if path.is_symlink():
            raise AuthoringBoundaryError(
                "AUTHORING_OUTPUT_INVALID",
                "authoring output must not contain symbolic links",
            )
        if not path.is_file():
            continue
        if len(files) >= MAX_SOURCES:
            raise AuthoringBoundaryError(
                "AUTHORING_OUTPUT_RESOURCE_LIMIT_EXCEEDED",
                "authoring output file count exceeds the v1 limit",
            )
        value = path.read_bytes()
        total_bytes += len(value)
        if total_bytes > MAX_TOTAL_SOURCE_BYTES:
            raise AuthoringBoundaryError(
                "AUTHORING_OUTPUT_RESOURCE_LIMIT_EXCEEDED",
                "authoring output bytes exceed the v1 limit",
            )
        relative_path = path.relative_to(staging).as_posix().encode()
        files.append(
            {
                "ordinal": len(files),
                "path_sha256": sha256_digest(relative_path),
                "content_sha256": sha256_digest(value),
                "byte_count": len(value),
            }
        )
    tree_payload = {"file_count": len(files), "total_bytes": total_bytes, "files": files}
    return AuthoringOutputDigest.model_validate(
        {**tree_payload, "tree_sha256": sha256_digest(canonical_json_bytes(tree_payload))}
    )


def _normalize_exit_code(return_code: int) -> int:
    if return_code < 0:
        return min(255, 128 + abs(return_code))
    return min(255, return_code)


def _git_output(repository_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
