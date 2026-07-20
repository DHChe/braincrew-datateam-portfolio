from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from braincrew.comparison import (
    ExperimentRunSummary,
    compare_runs,
)
from braincrew.dashboard_export import export_dashboard_artifact
from braincrew.dataset_registry import validate_dataset_bundle
from braincrew.dataset_run import (
    build_dataset_run_artifact,
    execute_dataset_fixture,
    load_dataset_observations,
    write_dataset_run_artifact,
)
from braincrew.fixture_run import execute_fixture_case, load_fixture_case
from braincrew.grounded_run import (
    execute_grounded_fixture,
    load_grounded_dataset,
    load_grounded_observations,
)
from braincrew.parsing_run import (
    execute_parsing_fixture,
    load_parsing_dataset,
    load_parsing_observations,
)
from braincrew.repository import RepositoryState, capture_evaluation_repository_state
from braincrew.result_store import (
    build_grounded_run_artifact,
    build_parsing_run_artifact,
    build_retrieval_run_artifact,
    build_run_artifact,
    rebuild_duckdb_cache,
    replay_run_artifact,
    write_comparison_artifact,
    write_grounded_run_artifact,
    write_parsing_run_artifact,
    write_retrieval_run_artifact,
    write_run_artifact,
)
from braincrew.retrieval_run import (
    execute_retrieval_fixture,
    load_retrieval_dataset,
    load_retrieval_observations,
)

app = typer.Typer(no_args_is_help=True)
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
COMMIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")


def _validate_artifact_id(artifact_id: str, *, label: str) -> None:
    if RUN_ID_PATTERN.fullmatch(artifact_id) is None:
        typer.echo(
            f"Invalid {label}: use 1-64 ASCII letters, digits, dots, underscores, or hyphens",
            err=True,
        )
        raise typer.Exit(code=2)


def _validate_run_identity(run_id: str, sut_sha: str) -> None:
    _validate_artifact_id(run_id, label="run ID")
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


@app.command("run-retrieval")
def run_retrieval_fixture(
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
    """Evaluate one versioned retrieval dataset with fixture observations."""
    _validate_run_identity(run_id, sut_sha)
    try:
        dataset = load_retrieval_dataset(dataset_path)
        observations = load_retrieval_observations(observations_path)
    except (json.JSONDecodeError, UnicodeError, ValidationError) as error:
        typer.echo(f"Invalid retrieval input: {error}", err=True)
        raise typer.Exit(code=2) from error
    evaluation_state = _capture_repository_state()
    artifact = build_retrieval_run_artifact(
        dataset=dataset,
        observations=observations,
        evaluation=execute_retrieval_fixture(dataset, observations),
        run_id=run_id,
        evaluation_state=evaluation_state,
        sut_sha=sut_sha,
    )
    try:
        artifact_path = write_retrieval_run_artifact(artifact, output_dir)
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


@app.command("run-grounded")
def run_grounded_fixture(
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
    """Evaluate the bounded grounded-answer fixture dataset."""
    _validate_run_identity(run_id, sut_sha)
    try:
        dataset = load_grounded_dataset(dataset_path)
        observations = load_grounded_observations(observations_path)
    except (json.JSONDecodeError, UnicodeError, ValidationError) as error:
        typer.echo(f"Invalid grounded input: {error}", err=True)
        raise typer.Exit(code=2) from error
    if sut_sha != observations.sut_commit_sha:
        typer.echo(
            "Invalid grounded input: --sut-sha does not match observation SUT SHA",
            err=True,
        )
        raise typer.Exit(code=2)
    evaluation_state = _capture_repository_state()
    artifact = build_grounded_run_artifact(
        dataset=dataset,
        observations=observations,
        evaluation=execute_grounded_fixture(dataset, observations),
        run_id=run_id,
        evaluation_state=evaluation_state,
        sut_sha=sut_sha,
    )
    try:
        artifact_path = write_grounded_run_artifact(artifact, output_dir)
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


@app.command("run-dataset")
def run_dataset_fixture(
    manifest_path: Annotated[
        Path,
        typer.Option("--manifest", exists=True, dir_okay=False, readable=True),
    ],
    parsing_observations_path: Annotated[
        Path,
        typer.Option("--parsing-observations", exists=True, dir_okay=False, readable=True),
    ],
    retrieval_observations_path: Annotated[
        Path,
        typer.Option("--retrieval-observations", exists=True, dir_okay=False, readable=True),
    ],
    grounded_observations_path: Annotated[
        Path,
        typer.Option("--grounded-observations", exists=True, dir_okay=False, readable=True),
    ],
    output_dir: Annotated[Path, typer.Option("--output-dir")],
    run_id: Annotated[str, typer.Option("--run-id")],
    sut_sha: Annotated[str, typer.Option("--sut-sha")],
) -> None:
    """Evaluate the frozen integrated 100-case fixture dataset."""
    _validate_run_identity(run_id, sut_sha)
    validation = validate_dataset_bundle(manifest_path)
    if validation.state != "VALID":
        codes = ",".join(item.code for item in validation.violations)
        typer.echo(f"Invalid dataset: {codes}", err=True)
        raise typer.Exit(code=2)
    try:
        observations = load_dataset_observations(
            parsing_path=parsing_observations_path,
            retrieval_path=retrieval_observations_path,
            grounded_path=grounded_observations_path,
        )
    except (json.JSONDecodeError, UnicodeError, ValidationError) as error:
        typer.echo(f"Invalid dataset observations: {error}", err=True)
        raise typer.Exit(code=2) from error
    if sut_sha != observations.grounded.sut_commit_sha:
        typer.echo(
            "Invalid dataset observations: --sut-sha does not match grounded observation SUT SHA",
            err=True,
        )
        raise typer.Exit(code=2)
    evaluation_state = _capture_repository_state()
    evaluation = execute_dataset_fixture(validation, observations)
    artifact = build_dataset_run_artifact(
        validation=validation,
        observations=observations,
        evaluation=evaluation,
        run_id=run_id,
        evaluation_state=evaluation_state,
        sut_sha=sut_sha,
    )
    try:
        artifact_path = write_dataset_run_artifact(artifact, output_dir)
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


@app.command("compare")
def compare_experiment_runs(
    baseline_path: Annotated[
        Path,
        typer.Option("--baseline", exists=True, dir_okay=False, readable=True),
    ],
    candidate_path: Annotated[
        Path,
        typer.Option("--candidate", exists=True, dir_okay=False, readable=True),
    ],
    output_dir: Annotated[Path, typer.Option("--output-dir")],
    comparison_id: Annotated[str, typer.Option("--comparison-id")],
) -> None:
    """Compare compatible baseline and candidate summaries through three release gates."""
    _validate_artifact_id(comparison_id, label="comparison ID")
    try:
        baseline = ExperimentRunSummary.model_validate_json(
            baseline_path.read_text(encoding="utf-8")
        )
        candidate = ExperimentRunSummary.model_validate_json(
            candidate_path.read_text(encoding="utf-8")
        )
    except (UnicodeError, ValidationError) as error:
        typer.echo(f"Invalid comparison run summary: {error}", err=True)
        raise typer.Exit(code=2) from error
    artifact = compare_runs(
        baseline,
        candidate,
        comparison_id=comparison_id,
    )
    try:
        json_path, parquet_path = write_comparison_artifact(artifact, output_dir)
    except FileExistsError as error:
        typer.echo(f"Comparison artifact already exists: {comparison_id}", err=True)
        raise typer.Exit(code=2) from error
    cache_path = rebuild_duckdb_cache(parquet_path, output_dir / f"{comparison_id}.duckdb")
    typer.echo(
        json.dumps(
            {
                "comparison_id": comparison_id,
                "decision": artifact.decision,
                "logical_digest": artifact.logical_digest,
                "json_artifact_path": str(json_path),
                "parquet_artifact_path": str(parquet_path),
                "duckdb_cache_path": str(cache_path),
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
    """Recompute a stored fixture artifact's logical result and digest."""
    try:
        replay_summary = replay_run_artifact(artifact_path)
    except ValueError as error:
        typer.echo(f"Invalid artifact: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "artifact_path": str(artifact_path),
                **replay_summary,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@app.command("export-dashboard")
def export_dashboard(
    comparison_path: Annotated[
        Path,
        typer.Option("--comparison", exists=True, dir_okay=False, readable=True),
    ],
    dataset_manifest_path: Annotated[
        Path,
        typer.Option("--dataset-manifest", exists=True, dir_okay=False, readable=True),
    ],
    output_path: Annotated[Path, typer.Option("--output")],
) -> None:
    """Project replay-validated comparison evidence into publishable dashboard JSON."""
    try:
        document = export_dashboard_artifact(
            comparison_path,
            output_path,
            dataset_manifest_path=dataset_manifest_path,
        )
    except (FileExistsError, UnicodeError, ValueError) as error:
        typer.echo(f"Invalid dashboard export: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "comparison_id": document.comparison_id,
                "decision": document.decision,
                "logical_digest": document.logical_digest,
                "output_path": str(output_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    app()
