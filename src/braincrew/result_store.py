from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from braincrew.contracts import (
    AdapterProvenance,
    ArtifactProvenance,
    DatasetArtifactProvenance,
    EvaluationPlaneProvenance,
    EvaluatorProvenance,
    FixtureCaseDocument,
    LogicalResult,
    ModelIdentity,
    ParsingAdapterProvenance,
    ParsingArtifactProvenance,
    ParsingDatasetDocument,
    ParsingEvaluatorProvenance,
    ParsingLogicalResult,
    ParsingObservationBatch,
    ParsingRunArtifactDocument,
    ParsingRunEvaluation,
    PromptIdentity,
    RunArtifactDocument,
    RunEnvelope,
    SutProvenance,
)
from braincrew.evaluator import evaluate_exact_answer
from braincrew.gate import decide_fixture_gate
from braincrew.repository import RepositoryState


def canonical_digest(value: object) -> str:
    canonical = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def build_run_artifact(
    *,
    case_document: FixtureCaseDocument,
    logical_result: LogicalResult,
    run_id: str,
    evaluation_state: RepositoryState,
    sut_sha: str,
) -> RunArtifactDocument:
    dataset_content = {
        "dataset": case_document.dataset.model_dump(mode="json"),
        "case": case_document.case.model_dump(mode="json"),
        "provenance": case_document.provenance.model_dump(mode="json"),
    }
    provenance = ArtifactProvenance(
        evaluation_plane=EvaluationPlaneProvenance(
            commit_sha=evaluation_state.commit_sha,
            dirty_worktree=evaluation_state.dirty_worktree,
            executed=True,
        ),
        sut=SutProvenance(
            commit_sha=sut_sha,
            dirty_worktree=None,
            executed=False,
            claim="identity placeholder only; live AX was not called",
        ),
        dataset=DatasetArtifactProvenance(
            **case_document.dataset.model_dump(mode="python"),
            **case_document.provenance.model_dump(mode="python"),
            content_digest=canonical_digest(dataset_content),
        ),
        adapter=AdapterProvenance(version="fixture-sut-v1", execution_mode="fixture"),
        evaluator=EvaluatorProvenance(version="exact-answer-v1"),
        prompt=case_document.prompt,
        model=case_document.model,
    )
    digest_payload = {
        "provenance": provenance.model_dump(mode="json"),
        "logical_result": logical_result.model_dump(mode="json"),
    }
    return RunArtifactDocument(
        schema_version="run-artifact-v1",
        run=RunEnvelope(
            run_id=run_id,
            execution_mode="fixture",
            created_at=datetime.now(UTC),
        ),
        provenance=provenance,
        logical_result=logical_result,
        logical_digest=canonical_digest(digest_payload),
    )


def write_run_artifact(
    artifact: RunArtifactDocument,
    output_dir: Path,
) -> Path:
    return _write_artifact_document(artifact, output_dir)


def _write_artifact_document(
    artifact: RunArtifactDocument | ParsingRunArtifactDocument,
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = output_dir / f"{artifact.run.run_id}.json"
    serialized = json.dumps(
        artifact.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    with artifact_path.open("x", encoding="utf-8") as artifact_file:
        artifact_file.write(serialized + "\n")
    return artifact_path


def build_parsing_run_artifact(
    *,
    dataset: ParsingDatasetDocument,
    observations: ParsingObservationBatch,
    evaluation: ParsingRunEvaluation,
    run_id: str,
    evaluation_state: RepositoryState,
    sut_sha: str,
) -> ParsingRunArtifactDocument:
    provenance = ParsingArtifactProvenance(
        evaluation_plane=EvaluationPlaneProvenance(
            commit_sha=evaluation_state.commit_sha,
            dirty_worktree=evaluation_state.dirty_worktree,
            executed=True,
        ),
        sut=SutProvenance(
            commit_sha=sut_sha,
            dirty_worktree=None,
            executed=False,
            claim="identity placeholder only; live AX was not called",
        ),
        dataset=DatasetArtifactProvenance(
            **dataset.dataset.model_dump(mode="python"),
            **dataset.provenance.model_dump(mode="python"),
            content_digest=canonical_digest(dataset.model_dump(mode="json")),
        ),
        adapter=ParsingAdapterProvenance(
            version=observations.adapter_version,
            parser_version=observations.parser_version,
            execution_mode="fixture",
        ),
        evaluator=ParsingEvaluatorProvenance(version=evaluation.evaluator_version),
        prompt=PromptIdentity(id="not-applicable", hash="not-applicable:deterministic-parsing"),
        model=ModelIdentity(provider="none", name="not-called", parameters={}),
    )
    logical_result = ParsingLogicalResult(
        dataset_snapshot=dataset,
        observation_snapshot=observations,
        evaluation=evaluation,
    )
    digest_payload = {
        "provenance": provenance.model_dump(mode="json"),
        "logical_result": logical_result.model_dump(mode="json"),
    }
    return ParsingRunArtifactDocument(
        schema_version="parsing-run-artifact-v1",
        run=RunEnvelope(
            run_id=run_id,
            execution_mode="fixture",
            created_at=datetime.now(UTC),
        ),
        provenance=provenance,
        logical_result=logical_result,
        logical_digest=canonical_digest(digest_payload),
    )


def write_parsing_run_artifact(
    artifact: ParsingRunArtifactDocument,
    output_dir: Path,
) -> Path:
    return _write_artifact_document(artifact, output_dir)


def replay_run_artifact(path: Path) -> tuple[str, str]:
    artifact = RunArtifactDocument.model_validate_json(path.read_text(encoding="utf-8"))
    stored_result = artifact.logical_result
    evaluation = evaluate_exact_answer(stored_result.case_snapshot.case, stored_result.observation)
    recomputed_result = LogicalResult(
        case_snapshot=stored_result.case_snapshot,
        observation=stored_result.observation,
        evaluation=evaluation,
        gate=decide_fixture_gate(evaluation),
    )
    recomputed_digest = canonical_digest(
        {
            "provenance": artifact.provenance.model_dump(mode="json"),
            "logical_result": recomputed_result.model_dump(mode="json"),
        }
    )
    if stored_result != recomputed_result or artifact.logical_digest != recomputed_digest:
        raise ValueError("artifact logical content does not reproduce its stored digest")
    return recomputed_digest, recomputed_result.gate.decision
