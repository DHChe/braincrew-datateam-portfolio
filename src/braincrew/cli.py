from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from braincrew.fixture_run import execute_fixture_case, load_fixture_case
from braincrew.parsing_run import (
    execute_parsing_fixture,
    load_parsing_dataset,
    load_parsing_observations,
)
from braincrew.repository import RepositoryState, capture_evaluation_repository_state
from braincrew.result_store import (
    build_parsing_run_artifact,
    build_run_artifact,
    replay_run_artifact,
    write_parsing_run_artifact,
    write_run_artifact,
)

app = typer.Typer(no_args_is_help=True)
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
COMMIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")


def _validate_run_identity(run_id: str, sut_sha: str) -> None:
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        typer.echo(
            "Invalid run ID: use 1-64 ASCII letters, digits, dots, underscores, or hyphens",
            err=True,
        )
        raise typer.Exit(code=2)
    if COMMIT_SHA_PATTERN.fullmatch(sut_sha) is None:
        typer.echo("Invalid commit SHA: expected 40 lowercase hexadecimal characters", err=True)
        raise typer.Exit(code=2)


def _capture_repository_state() -> RepositoryState:
    try:
        return capture_evaluation_repository_state()
    except subprocess.CalledProcessError as error:
        typer.echo("Unable to capture Evaluation Plane Git provenance", err=True)
        raise typer.Exit(code=2) from error


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
    _validate_run_identity(run_id, sut_sha)
    try:
        case_document = load_fixture_case(case_path)
    except (json.JSONDecodeError, UnicodeError, ValidationError) as error:
        typer.echo(f"Invalid fixture input: {error}", err=True)
        raise typer.Exit(code=2) from error
    evaluation_state = _capture_repository_state()
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


@app.command("run-parsing")
def run_parsing_fixture(
    dataset_path: Annotated[
        Path,
        typer.Option("--dataset", exists=True, dir_okay=False, readable=True),
    ],
    observations_path: Annotated[
        Path,
        typer.Option("--observations", exists=True, dir_okay=False, readable=True),
    ],
    output_dir: Annotated[Path, typer.Option("--output-dir")],
    run_id: Annotated[str, typer.Option("--run-id")],
    sut_sha: Annotated[str, typer.Option("--sut-sha")],
) -> None:
    """Evaluate one versioned parsing dataset with fixture observations."""
    _validate_run_identity(run_id, sut_sha)
    try:
        dataset = load_parsing_dataset(dataset_path)
        observations = load_parsing_observations(observations_path)
    except (json.JSONDecodeError, UnicodeError, ValidationError) as error:
        typer.echo(f"Invalid parsing input: {error}", err=True)
        raise typer.Exit(code=2) from error
    evaluation_state = _capture_repository_state()
    artifact = build_parsing_run_artifact(
        dataset=dataset,
        observations=observations,
        evaluation=execute_parsing_fixture(dataset, observations),
        run_id=run_id,
        evaluation_state=evaluation_state,
        sut_sha=sut_sha,
    )
    try:
        artifact_path = write_parsing_run_artifact(artifact, output_dir)
    except FileExistsError as error:
        typer.echo(f"Artifact already exists: {output_dir / f'{run_id}.json'}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                "run_state": artifact.logical_result.evaluation.state,
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
