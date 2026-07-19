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
    RetrievalAdapterProvenance,
    RetrievalArtifactProvenance,
    RetrievalDatasetDocument,
    RetrievalEvaluatorProvenance,
    RetrievalLogicalResult,
    RetrievalObservationBatch,
    RetrievalRunArtifactDocument,
    RetrievalRunEvaluation,
    RunArtifactDocument,
    RunEnvelope,
    SutProvenance,
)
from braincrew.evaluator import evaluate_exact_answer, evaluate_retrieval_run
from braincrew.gate import decide_fixture_gate
from braincrew.grounded_contracts import (
    GroundedAdapterProvenance,
    GroundedArtifactProvenance,
    GroundedCompatibilityProvenance,
    GroundedDatasetDocument,
    GroundedLogicalResult,
    GroundedObservationBatch,
    GroundedRunArtifactDocument,
    GroundedRunEvaluation,
)
from braincrew.grounded_evaluator import (
    CLAIM_ATOMIZER_VERSION,
    CLAIM_MATCHER_SET_VERSION,
    PROPOSITION_CATALOG_VERSION,
)
from braincrew.grounded_run import execute_grounded_fixture
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
    artifact: (
        RunArtifactDocument
        | ParsingRunArtifactDocument
        | RetrievalRunArtifactDocument
        | GroundedRunArtifactDocument
    ),
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


def build_retrieval_run_artifact(
    *,
    dataset: RetrievalDatasetDocument,
    observations: RetrievalObservationBatch,
    evaluation: RetrievalRunEvaluation,
    run_id: str,
    evaluation_state: RepositoryState,
    sut_sha: str,
) -> RetrievalRunArtifactDocument:
    provenance = RetrievalArtifactProvenance(
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
        adapter=RetrievalAdapterProvenance(
            version=observations.adapter_version,
            execution_mode="fixture",
        ),
        evaluator=RetrievalEvaluatorProvenance(version=evaluation.evaluator_version),
        prompt=PromptIdentity(id="not-applicable", hash="not-applicable:deterministic-retrieval"),
        model=ModelIdentity(provider="none", name="not-called", parameters={}),
    )
    logical_result = RetrievalLogicalResult(
        dataset_snapshot=dataset,
        observation_snapshot=observations,
        evaluation=evaluation,
    )
    digest_payload = {
        "provenance": provenance.model_dump(mode="json"),
        "logical_result": logical_result.model_dump(mode="json"),
    }
    return RetrievalRunArtifactDocument(
        schema_version="retrieval-run-artifact-v1",
        run=RunEnvelope(
            run_id=run_id,
            execution_mode="fixture",
            created_at=datetime.now(UTC),
        ),
        provenance=provenance,
        logical_result=logical_result,
        logical_digest=canonical_digest(digest_payload),
    )


def write_retrieval_run_artifact(
    artifact: RetrievalRunArtifactDocument,
    output_dir: Path,
) -> Path:
    return _write_artifact_document(artifact, output_dir)


def _grounded_compatibility(
    dataset: GroundedDatasetDocument,
    evaluation: GroundedRunEvaluation,
) -> GroundedCompatibilityProvenance:
    atomizer_digest = canonical_digest(
        {
            "version": CLAIM_ATOMIZER_VERSION,
            "paths": [
                "summary",
                "answer",
                "grounds[*]",
                "review_points[*]",
                "additional_checks[*]",
                "risk_warning",
            ],
            "boundaries": ["newline", ".", "?", "!", "。", "？", "！"],
        }
    )
    normalizer_digest = canonical_digest(
        {
            "version": evaluation.normalizer_version,
            "unicode": "NFC",
            "newline": "LF",
            "trim": True,
            "collapse_inline_whitespace": True,
        }
    )
    matcher_set_digest = canonical_digest(
        [
            {
                "case_id": case.case_id,
                "propositions": [
                    {
                        "proposition_id": proposition.proposition_id,
                        "surface_matchers": [
                            matcher.model_dump(mode="json")
                            for matcher in proposition.surface_matchers
                        ],
                    }
                    for proposition in case.propositions
                ],
            }
            for case in dataset.cases
        ]
    )
    proposition_catalog_digest = canonical_digest(
        [
            {
                "case_id": case.case_id,
                "propositions": [
                    proposition.model_dump(mode="json") for proposition in case.propositions
                ],
            }
            for case in dataset.cases
        ]
    )
    case_catalog_digest = canonical_digest([case.model_dump(mode="json") for case in dataset.cases])
    return GroundedCompatibilityProvenance(
        evaluator_version=evaluation.evaluator_version,
        proposition_contract_version=evaluation.proposition_contract_version,
        traversal_contract_version=evaluation.traversal_contract_version,
        atomizer_version=CLAIM_ATOMIZER_VERSION,
        atomizer_digest=atomizer_digest,
        normalizer_version=evaluation.normalizer_version,
        normalizer_digest=normalizer_digest,
        matcher_set_version=CLAIM_MATCHER_SET_VERSION,
        matcher_set_digest=matcher_set_digest,
        proposition_catalog_version=PROPOSITION_CATALOG_VERSION,
        proposition_catalog_digest=proposition_catalog_digest,
        case_catalog_digest=case_catalog_digest,
        source_resolution_version=evaluation.source_resolution_version,
        guard_version=evaluation.guard_version,
    )


def build_grounded_run_artifact(
    *,
    dataset: GroundedDatasetDocument,
    observations: GroundedObservationBatch,
    evaluation: GroundedRunEvaluation,
    run_id: str,
    evaluation_state: RepositoryState,
    sut_sha: str,
) -> GroundedRunArtifactDocument:
    provenance = GroundedArtifactProvenance(
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
            id=dataset.dataset_id,
            version=dataset.dataset_version,
            corpus_id="synthetic-hr-v1",
            source_type=dataset.provenance.source_kind,
            license=dataset.provenance.license,
            content_digest=canonical_digest(dataset.model_dump(mode="json")),
        ),
        adapter=GroundedAdapterProvenance(
            version=observations.adapter_version,
            execution_mode="fixture",
        ),
        compatibility=_grounded_compatibility(dataset, evaluation),
        prompt=PromptIdentity(id="fixture-recorded-answer", hash="not-applicable:fixture-answer"),
        model=ModelIdentity(provider="none", name="not-called", parameters={}),
    )
    logical_result = GroundedLogicalResult(
        dataset_snapshot=dataset,
        observation_snapshot=observations,
        evaluation=evaluation,
    )
    digest_payload = {
        "provenance": provenance.model_dump(mode="json"),
        "logical_result": logical_result.model_dump(mode="json"),
    }
    return GroundedRunArtifactDocument(
        schema_version="grounded-run-artifact-v1",
        run=RunEnvelope(
            run_id=run_id,
            execution_mode="fixture",
            created_at=datetime.now(UTC),
        ),
        provenance=provenance,
        logical_result=logical_result,
        logical_digest=canonical_digest(digest_payload),
    )


def write_grounded_run_artifact(
    artifact: GroundedRunArtifactDocument,
    output_dir: Path,
) -> Path:
    return _write_artifact_document(artifact, output_dir)


def replay_run_artifact(path: Path) -> dict[str, str]:
    raw_artifact: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_artifact, dict):
        raise ValueError("artifact must be a JSON object")
    schema_version = raw_artifact.get("schema_version")
    if schema_version == "grounded-run-artifact-v1":
        grounded_artifact = GroundedRunArtifactDocument.model_validate(raw_artifact)
        stored_grounded_result = grounded_artifact.logical_result
        recomputed_grounded_result = GroundedLogicalResult(
            dataset_snapshot=stored_grounded_result.dataset_snapshot,
            observation_snapshot=stored_grounded_result.observation_snapshot,
            evaluation=execute_grounded_fixture(
                stored_grounded_result.dataset_snapshot,
                stored_grounded_result.observation_snapshot,
            ),
        )
        recomputed_compatibility = _grounded_compatibility(
            recomputed_grounded_result.dataset_snapshot,
            recomputed_grounded_result.evaluation,
        )
        recomputed_grounded_digest = canonical_digest(
            {
                "provenance": grounded_artifact.provenance.model_dump(mode="json"),
                "logical_result": recomputed_grounded_result.model_dump(mode="json"),
            }
        )
        if (
            stored_grounded_result != recomputed_grounded_result
            or grounded_artifact.provenance.compatibility != recomputed_compatibility
            or grounded_artifact.logical_digest != recomputed_grounded_digest
        ):
            raise ValueError("artifact logical content does not reproduce its stored digest")
        return {
            "logical_digest": recomputed_grounded_digest,
            "run_state": recomputed_grounded_result.evaluation.state,
        }
    if schema_version == "retrieval-run-artifact-v1":
        retrieval_artifact = RetrievalRunArtifactDocument.model_validate(raw_artifact)
        stored_retrieval_result = retrieval_artifact.logical_result
        recomputed_retrieval_result = RetrievalLogicalResult(
            dataset_snapshot=stored_retrieval_result.dataset_snapshot,
            observation_snapshot=stored_retrieval_result.observation_snapshot,
            evaluation=evaluate_retrieval_run(
                stored_retrieval_result.dataset_snapshot,
                stored_retrieval_result.observation_snapshot,
            ),
        )
        recomputed_retrieval_digest = canonical_digest(
            {
                "provenance": retrieval_artifact.provenance.model_dump(mode="json"),
                "logical_result": recomputed_retrieval_result.model_dump(mode="json"),
            }
        )
        if (
            stored_retrieval_result != recomputed_retrieval_result
            or retrieval_artifact.logical_digest != recomputed_retrieval_digest
        ):
            raise ValueError("artifact logical content does not reproduce its stored digest")
        return {
            "logical_digest": recomputed_retrieval_digest,
            "run_state": recomputed_retrieval_result.evaluation.state,
        }
    if schema_version != "run-artifact-v1":
        raise ValueError(f"unsupported artifact schema: {schema_version}")
    fixture_artifact = RunArtifactDocument.model_validate(raw_artifact)
    stored_fixture_result = fixture_artifact.logical_result
    evaluation = evaluate_exact_answer(
        stored_fixture_result.case_snapshot.case,
        stored_fixture_result.observation,
    )
    recomputed_fixture_result = LogicalResult(
        case_snapshot=stored_fixture_result.case_snapshot,
        observation=stored_fixture_result.observation,
        evaluation=evaluation,
        gate=decide_fixture_gate(evaluation),
    )
    recomputed_fixture_digest = canonical_digest(
        {
            "provenance": fixture_artifact.provenance.model_dump(mode="json"),
            "logical_result": recomputed_fixture_result.model_dump(mode="json"),
        }
    )
    if (
        stored_fixture_result != recomputed_fixture_result
        or fixture_artifact.logical_digest != recomputed_fixture_digest
    ):
        raise ValueError("artifact logical content does not reproduce its stored digest")
    return {
        "logical_digest": recomputed_fixture_digest,
        "gate_decision": recomputed_fixture_result.gate.decision,
    }
