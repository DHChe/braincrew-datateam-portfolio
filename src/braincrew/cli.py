from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from braincrew.fixture_run import execute_fixture_case, load_fixture_case
from braincrew.repository import capture_evaluation_repository_state
from braincrew.result_store import build_run_artifact, replay_run_artifact, write_run_artifact

app = typer.Typer(no_args_is_help=True)
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
COMMIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")


@app.callback()
def main() -> None:
    """Run and replay versioned evaluation artifacts."""


@app.command("run")
def run_fixture(
    case_path: Annotated[
        Path,
        typer.Option("--case", exists=True, dir_okay=False, readable=True),
    ],
    output_dir: Annotated[Path, typer.Option("--output-dir")],
    run_id: Annotated[str, typer.Option("--run-id")],
    sut_sha: Annotated[str, typer.Option("--sut-sha")],
) -> None:
    """Run one versioned fixture case and persist its gate artifact."""
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        typer.echo(
            "Invalid run ID: use 1-64 ASCII letters, digits, dots, underscores, or hyphens",
            err=True,
        )
        raise typer.Exit(code=2)
    if COMMIT_SHA_PATTERN.fullmatch(sut_sha) is None:
        typer.echo("Invalid commit SHA: expected 40 lowercase hexadecimal characters", err=True)
        raise typer.Exit(code=2)
    try:
        case_document = load_fixture_case(case_path)
    except (json.JSONDecodeError, UnicodeError, ValidationError) as error:
        typer.echo(f"Invalid fixture input: {error}", err=True)
        raise typer.Exit(code=2) from error
    try:
        evaluation_state = capture_evaluation_repository_state()
    except subprocess.CalledProcessError as error:
        typer.echo("Unable to capture Evaluation Plane Git provenance", err=True)
        raise typer.Exit(code=2) from error
    artifact = build_run_artifact(
        case_document=case_document,
        logical_result=execute_fixture_case(case_document),
        run_id=run_id,
        evaluation_state=evaluation_state,
        sut_sha=sut_sha,
    )
    try:
        artifact_path = write_run_artifact(artifact, output_dir)
    except FileExistsError as error:
        typer.echo(f"Artifact already exists: {output_dir / f'{run_id}.json'}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "gate_decision": artifact.logical_result.gate.decision,
                "logical_digest": artifact.logical_digest,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@app.command("replay")
def replay_fixture(
    artifact_path: Annotated[
        Path,
        typer.Option("--artifact", exists=True, dir_okay=False, readable=True),
    ],
) -> None:
    """Recompute a stored fixture artifact's logical result and gate."""
    try:
        logical_digest, gate_decision = replay_run_artifact(artifact_path)
    except ValueError as error:
        typer.echo(f"Invalid artifact: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "gate_decision": gate_decision,
                "logical_digest": logical_digest,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    app()
