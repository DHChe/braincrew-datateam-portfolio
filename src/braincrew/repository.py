from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepositoryState:
    commit_sha: str
    dirty_worktree: bool


def capture_evaluation_repository_state() -> RepositoryState:
    repository_root = Path(__file__).resolve().parents[2]
    return capture_repository_state(repository_root)


def capture_repository_state(repository_root: Path | None = None) -> RepositoryState:
    if repository_root is None:
        repository_root = Path(__file__).resolve().parents[2]
    commit_sha = _git_output(repository_root, "rev-parse", "HEAD")
    dirty_worktree = bool(_git_output(repository_root, "status", "--porcelain"))
    return RepositoryState(commit_sha=commit_sha, dirty_worktree=dirty_worktree)


def _git_output(repository_root: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repository_root), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
