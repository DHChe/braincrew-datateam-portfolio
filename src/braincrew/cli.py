from __future__ import annotations

import json
import re
import subprocess
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal

import typer
from pydantic import ValidationError

from braincrew.ax_http_adapter import AxHttpFailure
from braincrew.comparison import (
    ExperimentRunSummary,
    compare_runs,
)
from braincrew.contracts import PARSING_EVALUATOR_V2
from braincrew.corpus_authoring import AuthoringBoundaryError, launch_authoring_process
from braincrew.corpus_qualification import (
    CorpusQualificationError,
    qualify_corpus_pack,
    replay_qualification_receipt,
)
from braincrew.corpus_sealing import (
    CorpusPackError,
    replay_sealing_receipt,
    seal_corpus_pack,
)
from braincrew.dashboard_export import export_dashboard_artifact
from braincrew.dataset_registry import validate_dataset_bundle
from braincrew.dataset_run import (
    DatasetRunArtifactDocument,
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
from braincrew.live_experiment import (
    LiveExperimentCaptureManifest,
    SutStateSubject,
    SutStateWarrant,
    capture_live_experiment,
    load_reviewed_principal_binding,
    write_live_experiment_capture,
)
from braincrew.live_preflight import (
    PINNED_AX_SHA,
    capture_reviewed_live_verification_preflight,
    replay_live_preflight_artifact,
    write_live_preflight_artifact,
)
from braincrew.parsing_run import (
    execute_parsing_fixture,
    load_parsing_dataset,
    load_parsing_observations,
)
from braincrew.repository import RepositoryState, capture_repository_state
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
from braincrew.run_summary import (
    build_experiment_run_summary,
    write_experiment_run_summary,
)

app = typer.Typer(no_args_is_help=True)
RUN_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
COMMIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}\Z")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FROZEN_DATASET_MANIFEST = PROJECT_ROOT / "datasets" / "dataset_manifest_v3.json"
NOT_READY_EXIT_CODE = 3


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
        return capture_repository_state()
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
        evaluation=execute_parsing_fixture(
            dataset,
            observations,
            evaluator_version=PARSING_EVALUATOR_V2,
        ),
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
    capture_manifest_path: Annotated[
        Path | None,
        typer.Option("--capture-manifest", exists=True, dir_okay=False, readable=True),
    ] = None,
) -> None:
    """Evaluate either the full fixture dataset or one captured Verification partition."""
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
    live_provenance = None
    if capture_manifest_path is not None:
        try:
            capture_manifest = LiveExperimentCaptureManifest.model_validate_json(
                capture_manifest_path.read_text(encoding="utf-8")
            )
        except (UnicodeError, ValidationError) as error:
            typer.echo(f"Invalid capture manifest: {error}", err=True)
            raise typer.Exit(code=2) from error
        if capture_manifest.run_id != run_id or capture_manifest.provenance.sut_sha != sut_sha:
            typer.echo(
                "Invalid capture manifest: run ID and SUT SHA must match the dataset run",
                err=True,
            )
            raise typer.Exit(code=2)
        live_provenance = capture_manifest.provenance
    evaluation_state = _capture_repository_state()
    evaluation = execute_dataset_fixture(
        validation,
        observations,
        parsing_evaluator_version=PARSING_EVALUATOR_V2,
    )
    try:
        artifact = build_dataset_run_artifact(
            validation=validation,
            observations=observations,
            evaluation=evaluation,
            run_id=run_id,
            evaluation_state=evaluation_state,
            sut_sha=sut_sha,
            live_provenance=live_provenance,
        )
        artifact_path = write_dataset_run_artifact(artifact, output_dir)
    except ValueError as error:
        typer.echo(f"Invalid dataset run provenance: {error}", err=True)
        raise typer.Exit(code=2) from error
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


@app.command("build-run-summary")
def build_run_summary(
    capture_manifest_path: Annotated[
        Path,
        typer.Option("--capture-manifest", exists=True, dir_okay=False, readable=True),
    ],
    run_artifact_path: Annotated[
        Path,
        typer.Option("--run-artifact", exists=True, dir_okay=False, readable=True),
    ],
    output_path: Annotated[Path, typer.Option("--output")],
) -> None:
    """Derive one create-only comparison input from captured run evidence."""
    try:
        manifest = LiveExperimentCaptureManifest.model_validate_json(
            capture_manifest_path.read_text(encoding="utf-8")
        )
        artifact = DatasetRunArtifactDocument.model_validate_json(
            run_artifact_path.read_text(encoding="utf-8")
        )
        summary = build_experiment_run_summary(manifest, artifact)
        written_path = write_experiment_run_summary(summary, output_path)
    except (UnicodeError, ValidationError, ValueError) as error:
        typer.echo(f"Invalid run summary evidence: {error}", err=True)
        raise typer.Exit(code=2) from error
    except FileExistsError as error:
        typer.echo(f"Run summary already exists: {output_path}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "run_id": summary.run_id,
                "case_count": len(summary.cases),
                "output_path": str(written_path),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@app.command("seal-corpus")
def seal_corpus(
    staging_dir: Annotated[
        Path,
        typer.Option("--staging-dir", exists=True, file_okay=False, readable=True),
    ],
    output_root: Annotated[Path, typer.Option("--output-root")],
    provenance_sidecar: Annotated[
        Path | None,
        typer.Option("--provenance-sidecar", exists=True, dir_okay=False, readable=True),
    ] = None,
) -> None:
    """Validate and create one immutable synthetic corpus version with provenance evidence."""
    try:
        result = seal_corpus_pack(staging_dir, output_root, provenance_sidecar)
    except CorpusPackError as error:
        typer.echo(f"Invalid corpus pack: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "receipt_path": str(result.receipt_path),
                "receipt_digest": result.receipt.receipt_digest,
                "sealed_content_digest": result.receipt.sealed_content_digest,
                "provenance_digest": result.receipt.provenance_digest,
                "corpus_id": result.receipt.corpus_id,
                "corpus_version": result.receipt.corpus_version,
                "source_count": result.receipt.source_count,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@app.command("launch-authoring")
def launch_authoring(
    braincrew_root: Annotated[
        Path,
        typer.Option("--braincrew-root", exists=True, file_okay=False, readable=True),
    ],
    brief: Annotated[Path, typer.Option("--brief")],
    staging_dir: Annotated[
        Path,
        typer.Option("--staging-dir", exists=True, file_okay=False, writable=True),
    ],
    receipt: Annotated[Path, typer.Option("--receipt")],
    tool_path: Annotated[
        Path,
        typer.Option("--tool-path", exists=True, dir_okay=False, readable=True),
    ],
    tool_name: Annotated[str, typer.Option("--tool-name")],
    tool_version: Annotated[str, typer.Option("--tool-version")],
) -> None:
    """Run one evaluation-blind authoring process inside an OS capability sandbox."""
    try:
        result = launch_authoring_process(
            braincrew_root=braincrew_root,
            brief_relative_path=brief,
            staging_dir=staging_dir,
            receipt_path=receipt,
            tool_path=tool_path,
            tool_name=tool_name,
            tool_version=tool_version,
        )
    except AuthoringBoundaryError as error:
        typer.echo(f"Authoring boundary rejected: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "braincrew_commit_sha": result.receipt.braincrew_commit_sha,
                "exit_code": result.receipt.exit_state.exit_code,
                "receipt_digest": result.receipt.receipt_digest,
                "staging_run_id": result.receipt.staging_run_id,
                "status": result.receipt.exit_state.status,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if result.receipt.exit_state.exit_code != 0:
        raise typer.Exit(code=result.receipt.exit_state.exit_code)


@app.command("qualify-corpus")
def qualify_corpus(
    sealed_dir: Annotated[
        Path,
        typer.Option("--sealed-dir", exists=True, file_okay=False, readable=True),
    ],
    dataset_manifest_path: Annotated[
        Path,
        typer.Option(
            "--dataset-manifest",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    tenant_slug: Annotated[str, typer.Option("--tenant-slug")],
    demo_company_id: Annotated[str, typer.Option("--demo-company-id")],
) -> None:
    """Read-only qualify one sealed corpus against the exact successor dataset identity."""
    try:
        result = qualify_corpus_pack(
            sealed_dir=sealed_dir,
            dataset_manifest_path=dataset_manifest_path,
            tenant_slug=tenant_slug,
            demo_company_id=demo_company_id,
        )
    except (CorpusQualificationError, OSError) as error:
        typer.echo(f"Corpus qualification rejected: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "receipt_path": result.receipt_path.name,
                "import_manifest_path": result.import_manifest_path.name,
                "receipt_digest": result.receipt.receipt_digest,
                "qualification_receipt_digest": result.qualification_receipt_digest,
                "import_digest": result.import_manifest.import_digest,
                "sealed_content_digest": result.receipt.corpus.sealed_content_digest,
                "dataset_content_digest": result.receipt.dataset.content_digest,
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
    handoff_receipt_path: Annotated[
        Path | None,
        typer.Option(
            "--handoff-receipt",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
) -> None:
    """Recompute a stored fixture artifact's logical result and digest."""
    replay_summary: Mapping[str, object]
    try:
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("schema_version") in {
            "corpus-sealing-receipt-v1",
            "corpus-sealing-receipt-v2",
        }:
            replay_summary = replay_sealing_receipt(artifact_path)
        elif isinstance(payload, dict) and payload.get("schema_version") in {
            "corpus-qualification-receipt-v1",
            "corpus-qualification-receipt-v2",
        }:
            replay_summary = replay_qualification_receipt(artifact_path)
        elif isinstance(payload, dict) and payload.get("schema_version") in {
            "live-preflight-evidence-v1",
            "principal-attachment-preflight-evidence-v1",
            "live-verification-preflight-artifact-v2",
        }:
            replay_summary = replay_live_preflight_artifact(
                artifact_path,
                handoff_receipt_path=handoff_receipt_path,
            )
        else:
            replay_summary = replay_run_artifact(artifact_path)
    except (UnicodeError, ValueError) as error:
        typer.echo(f"Invalid artifact: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {
                "artifact_path": artifact_path.name,
                **replay_summary,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


@app.command("capture-live-verification")
def capture_live_verification(
    output_path: Annotated[Path, typer.Option("--output", dir_okay=False)],
    run_id: Annotated[str, typer.Option("--run-id")],
    base_url: Annotated[str, typer.Option("--base-url")],
    handoff_receipt_path: Annotated[
        Path,
        typer.Option(
            "--handoff-receipt",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
) -> None:
    """Capture the reviewed v2 live preflight artifact create-only.

    Exit 0: READY; replay and record the evidence. Exit 3: NOT_READY artifact
    created; stop, replay, and inspect its typed blocker. Exit 2: no artifact
    created; stop and investigate the capture failure before retrying.
    """
    _validate_artifact_id(run_id, label="run ID")
    if output_path.exists():
        typer.echo(f"Artifact already exists: {output_path.name}", err=True)
        raise typer.Exit(code=2)

    dataset_validation = validate_dataset_bundle(FROZEN_DATASET_MANIFEST)
    if dataset_validation.state != "VALID":
        codes = ",".join(item.code for item in dataset_validation.violations)
        typer.echo(f"Invalid frozen dataset: {codes}", err=True)
        raise typer.Exit(code=2)

    evaluation_state = _capture_repository_state()
    if evaluation_state.dirty_worktree:
        typer.echo("Capture requires a clean committed Evaluation Plane checkout", err=True)
        raise typer.Exit(code=2)
    try:
        artifact = capture_reviewed_live_verification_preflight(
            run_id=run_id,
            captured_at=datetime.now(UTC),
            evaluation_plane_sha=evaluation_state.commit_sha,
            sut_commit_sha=PINNED_AX_SHA,
            base_url=base_url,
            dataset_validation=dataset_validation,
            handoff_receipt_path=handoff_receipt_path,
        )
        artifact_path = write_live_preflight_artifact(artifact, output_path)
    except FileExistsError as error:
        typer.echo(f"Artifact already exists: {output_path.name}", err=True)
        raise typer.Exit(code=2) from error
    except ValueError as error:
        typer.echo(f"Live verification capture rejected: {error}", err=True)
        raise typer.Exit(code=2) from error
    except OSError as error:
        typer.echo("Unable to write live verification artifact", err=True)
        raise typer.Exit(code=2) from error

    typer.echo(
        json.dumps(
            {
                "artifact_path": artifact_path.name,
                "blocker_count": len(artifact.blockers),
                "capture_state": artifact.capture_state,
                "logical_digest": artifact.logical_digest,
                "readiness": artifact.readiness,
                "schema_version": artifact.schema_version,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    if artifact.readiness == "NOT_READY":
        raise typer.Exit(code=NOT_READY_EXIT_CODE)


@app.command("capture-live-experiment")
def capture_live_experiment_command(
    output_dir: Annotated[Path, typer.Option("--output-dir")],
    run_id: Annotated[str, typer.Option("--run-id")],
    role: Annotated[Literal["baseline", "candidate"], typer.Option("--role")],
    base_url: Annotated[str, typer.Option("--base-url")],
    handoff_receipt_path: Annotated[
        Path,
        typer.Option(
            "--handoff-receipt",
            exists=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    sut_checkout: Annotated[
        Path,
        typer.Option(
            "--sut-checkout",
            exists=True,
            file_okay=False,
            readable=True,
        ),
    ],
) -> None:
    """Capture the pinned 30-case live experiment observations create-only."""
    _validate_artifact_id(run_id, label="run ID")
    dataset_validation = validate_dataset_bundle(FROZEN_DATASET_MANIFEST)
    if dataset_validation.state != "VALID":
        codes = ",".join(item.code for item in dataset_validation.violations)
        typer.echo(f"Invalid frozen dataset: {codes}", err=True)
        raise typer.Exit(code=2)
    try:
        evaluation_state = _capture_repository_state()
        sut_state = capture_repository_state(sut_checkout)
        checked_at = datetime.now(UTC)
        principal = load_reviewed_principal_binding(handoff_receipt_path)
        capture = capture_live_experiment(
            run_id=run_id,
            role=role,
            captured_at=checked_at,
            evaluation_state=evaluation_state,
            sut_state=SutStateWarrant(
                schema_version="sut-state-warrant-v1",
                method="read-only-git-check",
                subject=SutStateSubject(
                    repository="AX_portfolio",
                    checkout_path=sut_checkout.name,
                    checked_at=checked_at,
                ),
                commit_sha=sut_state.commit_sha,
                dirty_worktree=sut_state.dirty_worktree,
            ),
            sut_source_root=sut_checkout,
            base_url=base_url,
            principal=principal,
            dataset_validation=dataset_validation,
            dependency_lock_path=PROJECT_ROOT / "uv.lock",
        )
        artifact_paths = write_live_experiment_capture(capture, output_dir)
    except subprocess.CalledProcessError as error:
        typer.echo("Unable to capture SUT Git provenance", err=True)
        raise typer.Exit(code=2) from error
    except AxHttpFailure as error:
        typer.echo(f"Live experiment capture failed: {error.failure_code}", err=True)
        raise typer.Exit(code=2) from error
    except (OSError, ValueError, ValidationError) as error:
        typer.echo(f"Live experiment capture rejected: {error}", err=True)
        raise typer.Exit(code=2) from error
    typer.echo(
        json.dumps(
            {"artifact_paths": [path.name for path in artifact_paths]},
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
