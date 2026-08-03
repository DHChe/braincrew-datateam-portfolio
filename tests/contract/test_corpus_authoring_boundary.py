from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from tests.authoring_boundary_fixture import (
    BRIEF_RELATIVE_PATH,
    EXPECTED_BRAINCREW_REMOTE,
    create_clean_braincrew_source,
    launch_arguments,
    run_cli,
    sandbox_backend_available,
    write_executable,
)


def successful_tool(path: Path) -> Path:
    return write_executable(
        path,
        """import os
from pathlib import Path

staging = Path(os.environ["BRAINCREW_AUTHORING_STAGING_DIR"])
(staging / "corpus-manifest.json").write_text("{}\\n", encoding="utf-8")
""",
    )


def test_launch_authoring_requires_a_clean_committed_brief(tmp_path: Path) -> None:
    source_root = create_clean_braincrew_source(tmp_path)
    (source_root / BRIEF_RELATIVE_PATH).write_text("uncommitted brief\n", encoding="utf-8")
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()

    result = run_cli(
        *launch_arguments(
            source_root=source_root,
            staging_dir=staging_dir,
            receipt_path=tmp_path / "receipt.json",
            tool_path=successful_tool(tmp_path / "tool"),
        )
    )

    assert result.returncode == 2
    assert "BRAINCREW_SOURCE_NOT_CLEAN" in result.stderr
    assert not (tmp_path / "receipt.json").exists()


def test_launch_authoring_requires_an_empty_staging_directory(tmp_path: Path) -> None:
    source_root = create_clean_braincrew_source(tmp_path)
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    (staging_dir / "existing.txt").write_text("existing\n", encoding="utf-8")

    result = run_cli(
        *launch_arguments(
            source_root=source_root,
            staging_dir=staging_dir,
            receipt_path=tmp_path / "receipt.json",
            tool_path=successful_tool(tmp_path / "tool"),
        )
    )

    assert result.returncode == 2
    assert "AUTHORING_STAGING_NOT_EMPTY" in result.stderr
    assert (staging_dir / "existing.txt").read_text(encoding="utf-8") == "existing\n"


def test_launch_authoring_rejects_a_non_braincrew_git_remote(tmp_path: Path) -> None:
    source_root = create_clean_braincrew_source(tmp_path)
    subprocess.run(
        [
            "git",
            "-C",
            source_root,
            "remote",
            "set-url",
            "origin",
            "https://github.com/DHChe/AX_portfolio.git",
        ],
        check=True,
    )
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()

    result = run_cli(
        *launch_arguments(
            source_root=source_root,
            staging_dir=staging_dir,
            receipt_path=tmp_path / "receipt.json",
            tool_path=successful_tool(tmp_path / "tool"),
        )
    )

    assert EXPECTED_BRAINCREW_REMOTE not in result.stderr
    assert result.returncode == 2
    assert "BRAINCREW_SOURCE_INVALID" in result.stderr
    assert not any(staging_dir.iterdir())


def test_launch_authoring_rejects_an_invalid_tool_identity_without_a_traceback(
    tmp_path: Path,
) -> None:
    source_root = create_clean_braincrew_source(tmp_path)
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()

    result = run_cli(
        *launch_arguments(
            source_root=source_root,
            staging_dir=staging_dir,
            receipt_path=tmp_path / "receipt.json",
            tool_path=successful_tool(tmp_path / "tool"),
            tool_name="invalid tool name",
        )
    )

    assert result.returncode == 2
    assert "AUTHORING_TOOL_IDENTITY_INVALID" in result.stderr
    assert "Traceback" not in result.stderr


@pytest.mark.skipif(not sandbox_backend_available(), reason="no supported OS sandbox backend")
def test_failed_tool_exit_is_bound_without_retaining_process_transcript(tmp_path: Path) -> None:
    source_root = create_clean_braincrew_source(tmp_path)
    staging_dir = tmp_path / "staging"
    staging_dir.mkdir()
    tool_path = write_executable(
        tmp_path / "failing-tool",
        """import os
import sys
from pathlib import Path

staging = Path(os.environ["BRAINCREW_AUTHORING_STAGING_DIR"])
(staging / "partial.txt").write_text("partial output\\n", encoding="utf-8")
print("prompt-transcript-sentinel")
print("source-text-sentinel", file=sys.stderr)
raise SystemExit(7)
""",
    )
    receipt_path = tmp_path / "receipt.json"

    result = run_cli(
        *launch_arguments(
            source_root=source_root,
            staging_dir=staging_dir,
            receipt_path=receipt_path,
            tool_path=tool_path,
        )
    )

    assert result.returncode == 7
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["exit_state"] == {"exit_code": 7, "status": "FAILED"}
    assert receipt["output"]["file_count"] == 1
    combined_retained_text = (
        result.stdout + result.stderr + receipt_path.read_text(encoding="utf-8")
    )
    assert "prompt-transcript-sentinel" not in combined_retained_text
    assert "source-text-sentinel" not in combined_retained_text


@pytest.mark.skipif(not sandbox_backend_available(), reason="no supported OS sandbox backend")
def test_independence_receipt_is_create_only(tmp_path: Path) -> None:
    source_root = create_clean_braincrew_source(tmp_path)
    receipt_path = tmp_path / "receipt.json"
    first_staging = tmp_path / "first-staging"
    first_staging.mkdir()
    first = run_cli(
        *launch_arguments(
            source_root=source_root,
            staging_dir=first_staging,
            receipt_path=receipt_path,
            tool_path=successful_tool(tmp_path / "tool"),
        )
    )
    assert first.returncode == 0, first.stderr
    original = receipt_path.read_bytes()
    second_staging = tmp_path / "second-staging"
    second_staging.mkdir()

    second = run_cli(
        *launch_arguments(
            source_root=source_root,
            staging_dir=second_staging,
            receipt_path=receipt_path,
            tool_path=tmp_path / "tool",
        )
    )

    assert second.returncode == 2
    assert "AUTHORING_RECEIPT_EXISTS" in second.stderr
    assert receipt_path.read_bytes() == original
    assert not any(second_staging.iterdir())
