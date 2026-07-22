from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BRIEF_RELATIVE_PATH = Path("docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md")
PACK_SCHEMA_RELATIVE_PATH = Path("schemas/ax-synthetic-seed-pack-v1.schema.json")
PACK_DIGEST_RELATIVE_PATH = Path("schemas/ax-synthetic-seed-pack-v1.schema.sha256")
EXPECTED_BRAINCREW_REMOTE = "https://github.com/DHChe/braincrew-datateam-portfolio.git"


def run_cli(
    *arguments: str,
    environment: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    process_environment = os.environ.copy()
    process_environment.update(environment or {})
    return subprocess.run(
        [sys.executable, "-m", "braincrew.cli", *arguments],
        check=False,
        capture_output=True,
        text=True,
        cwd=REPOSITORY_ROOT,
        env=process_environment,
    )


def create_clean_braincrew_source(tmp_path: Path) -> Path:
    source_root = tmp_path / "braincrew-source"
    brief_path = source_root / BRIEF_RELATIVE_PATH
    brief_path.parent.mkdir(parents=True)
    brief_path.write_text(
        "Approved synthetic demo corpus authoring brief.\n"
        "Use only CC0-1.0 synthetic material and declared AX roles.\n",
        encoding="utf-8",
    )
    schema_dir = source_root / "schemas"
    schema_dir.mkdir()
    shutil.copyfile(
        REPOSITORY_ROOT / PACK_SCHEMA_RELATIVE_PATH, schema_dir / PACK_SCHEMA_RELATIVE_PATH.name
    )
    shutil.copyfile(
        REPOSITORY_ROOT / PACK_DIGEST_RELATIVE_PATH, schema_dir / PACK_DIGEST_RELATIVE_PATH.name
    )

    protected_files = {
        "datasets/evaluation.json": (
            "query-sentinel answer-sentinel expected-evidence-sentinel score-sentinel\n"
        ),
        "tests/fixtures/case.json": "fixture-sentinel Verification\n",
        "artifacts/prior-run.json": "prior-artifact-sentinel\n",
        ".env": "OPENAI_API_KEY=credential-sentinel\n",
        "private/employee.txt": "private-document-sentinel\n",
        "post-seal/validator-result.json": "post-seal-failure-sentinel\n",
    }
    for relative_path, value in protected_files.items():
        path = source_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    subprocess.run(["git", "init", "-q", source_root], check=True)
    subprocess.run(
        ["git", "-C", source_root, "config", "user.email", "authoring-boundary@example.invalid"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", source_root, "config", "user.name", "Authoring Boundary Test"],
        check=True,
    )
    subprocess.run(["git", "-C", source_root, "add", "."], check=True)
    subprocess.run(
        ["git", "-C", source_root, "commit", "-q", "-m", "fixture"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", source_root, "remote", "add", "origin", EXPECTED_BRAINCREW_REMOTE],
        check=True,
    )
    return source_root


def write_executable(path: Path, body: str) -> Path:
    path.write_text("#!/usr/bin/python3\n" + body, encoding="utf-8")
    path.chmod(0o755)
    return path


def launch_arguments(
    *,
    source_root: Path,
    staging_dir: Path,
    receipt_path: Path,
    tool_path: Path,
    tool_name: str = "boundary-probe",
    tool_version: str = "1.0.0",
) -> tuple[str, ...]:
    return (
        "launch-authoring",
        "--braincrew-root",
        str(source_root),
        "--brief",
        BRIEF_RELATIVE_PATH.as_posix(),
        "--staging-dir",
        str(staging_dir),
        "--receipt",
        str(receipt_path),
        "--tool-path",
        str(tool_path),
        "--tool-name",
        tool_name,
        "--tool-version",
        tool_version,
    )


def sandbox_backend_available() -> bool:
    if platform.system() == "Darwin":
        return Path("/usr/bin/sandbox-exec").is_file()
    if platform.system() == "Linux":
        return shutil.which("bwrap") is not None
    return False
