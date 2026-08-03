"""Integrated fixture execution for the frozen 100-case dataset."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from braincrew.comparison import ExperimentProvenance
from braincrew.contracts import (
    PARSING_EVALUATOR_V2,
    EvaluationPlaneProvenance,
    ModelIdentity,
    ParsingEvaluatorVersion,
    ParsingObservationBatch,
    ParsingRunEvaluation,
    PromptIdentity,
    RetrievalObservationBatch,
    RetrievalRunEvaluation,
    RunEnvelope,
    SutProvenance,
)
from braincrew.dataset_registry import (
    DatasetBundleSnapshot,
    DatasetValidationReport,
    Digest,
    StrictDatasetContract,
    validate_dataset_snapshot,
)
from braincrew.digest import canonical_digest
from braincrew.grounded_contracts import GroundedObservationBatch, GroundedRunEvaluation
from braincrew.grounded_run import (
    execute_grounded_fixture,
    load_grounded_observations,
)
from braincrew.operational_evaluator import OPERATIONAL_EVALUATOR_VERSION
from braincrew.parsing_run import execute_parsing_fixture, load_parsing_observations
from braincrew.repository import RepositoryState
from braincrew.retrieval_run import execute_retrieval_fixture, load_retrieval_observations


class DatasetObservationSnapshot(StrictDatasetContract):
    parsing: ParsingObservationBatch
    retrieval: RetrievalObservationBatch
    grounded: GroundedObservationBatch


class DatasetRunEvaluation(StrictDatasetContract):
    schema_version: Literal["dataset-run-evaluation-v1"]
    state: Literal["COMPLETED", "INVALID"]
    invalid_reasons: tuple[str, ...]
    total_cases: int
    scored_cases: int
    parsing: ParsingRunEvaluation | None
    retrieval: RetrievalRunEvaluation | None
    grounded: GroundedRunEvaluation | None


class DatasetRegistryArtifactProvenance(StrictDatasetContract):
    id: Literal["braincrew-evaluation-dataset"]
    version: str
    content_digest: Digest
    component_digests: dict[str, Digest]
    source_type: Literal["synthetic", "public"]
    license: str
    provenance_status: Literal["complete"]
    license_status: Literal["approved"]
    dataset_card_path: str


class DatasetAdapterProvenance(StrictDatasetContract):
    execution_mode: Literal["fixture", "live"]
    parsing_version: Literal["fixture-parsing-sut-v1", "ax-sut-http-v1"]
    retrieval_version: Literal["fixture-retrieval-sut-v1", "ax-sut-http-v1"]
    grounded_version: Literal["fixture-grounded-sut-v1", "ax-sut-http-v1"]


class DatasetEvaluatorProvenance(StrictDatasetContract):
    version: Literal["dataset-fixture-v1", "dataset-verification-v1"]
    parsing_version: ParsingEvaluatorVersion
    retrieval_version: Literal["retrieval-quality-v1"]
    grounded_version: Literal["grounded-answer-v1"]
    operational_version: Literal["operational-v1"] | None = None


class DatasetArtifactProvenance(StrictDatasetContract):
    evaluation_plane: EvaluationPlaneProvenance
    sut: SutProvenance
    dataset: DatasetRegistryArtifactProvenance
    adapter: DatasetAdapterProvenance
    evaluator: DatasetEvaluatorProvenance
    prompt: PromptIdentity
    model: ModelIdentity


class DatasetLogicalResult(StrictDatasetContract):
    dataset_snapshot: DatasetBundleSnapshot
    observation_snapshot: DatasetObservationSnapshot
    evaluation: DatasetRunEvaluation


class DatasetRunArtifactDocument(StrictDatasetContract):
    schema_version: Literal["dataset-run-artifact-v1"]
    run: RunEnvelope
    provenance: DatasetArtifactProvenance
    logical_result: DatasetLogicalResult
    logical_digest: Digest


def load_dataset_observations(
    *,
    parsing_path: Path,
    retrieval_path: Path,
    grounded_path: Path,
) -> DatasetObservationSnapshot:
    return DatasetObservationSnapshot(
        parsing=load_parsing_observations(parsing_path),
        retrieval=load_retrieval_observations(retrieval_path),
        grounded=load_grounded_observations(grounded_path),
    )


def execute_dataset_fixture(
    validation: DatasetValidationReport,
    observations: DatasetObservationSnapshot,
    *,
    parsing_evaluator_version: ParsingEvaluatorVersion = PARSING_EVALUATOR_V2,
) -> DatasetRunEvaluation:
    if validation.state != "VALID" or validation.snapshot is None:
        return DatasetRunEvaluation(
            schema_version="dataset-run-evaluation-v1",
            state="INVALID",
            invalid_reasons=tuple(item.code for item in validation.violations),
            total_cases=0,
            scored_cases=0,
            parsing=None,
            retrieval=None,
            grounded=None,
        )
    snapshot = validation.snapshot
    live_components = (
        observations.retrieval.adapter_version == "ax-sut-http-v1",
        observations.grounded.adapter_version == "ax-sut-http-v1",
    )
    if live_components[0] != live_components[1]:
        return DatasetRunEvaluation(
            schema_version="dataset-run-evaluation-v1",
            state="INVALID",
            invalid_reasons=("LIVE_COMPONENT_EXECUTION_MODE_MISMATCH",),
            total_cases=0,
            scored_cases=0,
            parsing=None,
            retrieval=None,
            grounded=None,
        )
    verification_only = all(live_components)
    parsing_observations = observations.parsing
    if verification_only:
        verification_parsing_ids = {
            case.id for case in snapshot.parsing_dataset.cases if case.split == "verification"
        }
        parsing_observations = observations.parsing.model_copy(
            update={
                "observations": [
                    observation
                    for observation in observations.parsing.observations
                    if observation.case_id in verification_parsing_ids
                ]
            }
        )
    parsing = execute_parsing_fixture(
        snapshot.parsing_dataset,
        parsing_observations,
        verification_only=verification_only,
        evaluator_version=parsing_evaluator_version,
    )
    retrieval = execute_retrieval_fixture(snapshot.retrieval_dataset, observations.retrieval)
    grounded = execute_grounded_fixture(snapshot.grounded_dataset, observations.grounded)
    total_cases = (
        sum(record.split == "Verification" for record in snapshot.case_records)
        if verification_only
        else len(snapshot.case_records)
    )
    scored_cases = (
        parsing.coverage.scored_cases
        + retrieval.coverage.scored_cases
        + sum(result.state == "COMPLETED" for result in grounded.case_evaluations)
    )
    component_states = (parsing.state, retrieval.state, grounded.state)
    state: Literal["COMPLETED", "INVALID"] = (
        "COMPLETED"
        if component_states == ("COMPLETED", "COMPLETED", "COMPLETED")
        and total_cases == (30 if verification_only else 100)
        and scored_cases == total_cases
        else "INVALID"
    )
    invalid_reasons: tuple[str, ...] = ()
    if state == "INVALID":
        invalid_reasons = tuple(
            [*(f"parsing:{reason}" for reason in parsing.invalid_reasons)]
            + [*(f"retrieval:{reason}" for reason in retrieval.invalid_reasons)]
            + (["grounded:SYS-GROUNDED-COVERAGE-INVALID"] if grounded.state == "INVALID" else [])
            + (["DATASET_CASE_COVERAGE_INVALID"] if scored_cases != total_cases else [])
        )
    return DatasetRunEvaluation(
        schema_version="dataset-run-evaluation-v1",
        state=state,
        invalid_reasons=invalid_reasons,
        total_cases=total_cases,
        scored_cases=scored_cases,
        parsing=parsing,
        retrieval=retrieval,
        grounded=grounded,
    )


def _dataset_provenance(snapshot: DatasetBundleSnapshot) -> DatasetRegistryArtifactProvenance:
    manifest = snapshot.manifest
    return DatasetRegistryArtifactProvenance(
        id=manifest.dataset_id,
        version=manifest.dataset_version,
        content_digest=snapshot.dataset_digest,
        component_digests=snapshot.component_digests,
        source_type=manifest.provenance.source_type,
        license=manifest.provenance.license,
        provenance_status=manifest.dataset_card.provenance_status,
        license_status=manifest.dataset_card.license_status,
        dataset_card_path=manifest.dataset_card.path,
    )


def _dataset_adapter(observations: DatasetObservationSnapshot) -> DatasetAdapterProvenance:
    execution_mode: Literal["fixture", "live"] = (
        "live"
        if observations.retrieval.adapter_version == "ax-sut-http-v1"
        and observations.grounded.adapter_version == "ax-sut-http-v1"
        else "fixture"
    )
    return DatasetAdapterProvenance(
        execution_mode=execution_mode,
        parsing_version=observations.parsing.adapter_version,
        retrieval_version=observations.retrieval.adapter_version,
        grounded_version=observations.grounded.adapter_version,
    )


def _dataset_evaluator(
    execution_mode: Literal["fixture", "live"],
    *,
    parsing_evaluator_version: ParsingEvaluatorVersion,
) -> DatasetEvaluatorProvenance:
    return DatasetEvaluatorProvenance(
        version=("dataset-verification-v1" if execution_mode == "live" else "dataset-fixture-v1"),
        parsing_version=parsing_evaluator_version,
        retrieval_version="retrieval-quality-v1",
        grounded_version="grounded-answer-v1",
        operational_version=(OPERATIONAL_EVALUATOR_VERSION if execution_mode == "live" else None),
    )


def _dataset_sut(
    sut_sha: str,
    *,
    execution_mode: Literal["fixture", "live"],
    dirty_worktree: bool | None = None,
) -> SutProvenance:
    if execution_mode == "live":
        if dirty_worktree is None:
            raise ValueError("live dataset execution requires the captured SUT dirtiness warrant")
        return SutProvenance(
            commit_sha=sut_sha,
            dirty_worktree=dirty_worktree,
            executed=True,
            claim="live AX called; clean state warranted by read-only checkout check",
        )
    return SutProvenance(
        commit_sha=sut_sha,
        dirty_worktree=None,
        executed=False,
        claim="identity placeholder only; live AX was not called",
    )


def _dataset_prompt() -> PromptIdentity:
    return PromptIdentity(id="fixture-recorded-observations", hash="not-applicable:fixture-batch")


def _dataset_model() -> ModelIdentity:
    return ModelIdentity(provider="none", name="not-called", parameters={})


def build_dataset_run_artifact(
    *,
    validation: DatasetValidationReport,
    observations: DatasetObservationSnapshot,
    evaluation: DatasetRunEvaluation,
    run_id: str,
    evaluation_state: RepositoryState,
    sut_sha: str,
    live_provenance: ExperimentProvenance | None = None,
) -> DatasetRunArtifactDocument:
    if validation.state != "VALID" or validation.snapshot is None:
        raise ValueError("a valid dataset snapshot is required for fixture execution")
    adapter = _dataset_adapter(observations)
    parsing_evaluator_version = (
        evaluation.parsing.evaluator_version
        if evaluation.parsing is not None
        else PARSING_EVALUATOR_V2
    )
    if adapter.execution_mode == "live":
        if live_provenance is None:
            raise ValueError("live dataset execution requires captured experiment provenance")
        if (
            live_provenance.execution_mode != "live"
            or live_provenance.sut_sha != sut_sha
            or live_provenance.evaluation_plane_sha != evaluation_state.commit_sha
            or live_provenance.evaluation_plane_dirty != evaluation_state.dirty_worktree
        ):
            raise ValueError("live dataset provenance does not match the evaluated evidence")
        if live_provenance.evaluator_versions.get("parsing") != parsing_evaluator_version:
            raise ValueError(
                "live capture parsing evaluator version does not match dataset evaluation"
            )
        sut = _dataset_sut(
            sut_sha,
            execution_mode="live",
            dirty_worktree=live_provenance.sut_dirty,
        )
        prompt = PromptIdentity(
            id=live_provenance.prompt_id,
            hash=live_provenance.prompt_hash,
        )
        model = ModelIdentity(
            provider=live_provenance.model_provider,
            name=live_provenance.model_name,
            parameters=live_provenance.model_parameters,
        )
    else:
        if live_provenance is not None:
            raise ValueError("fixture dataset execution cannot accept live provenance")
        sut = _dataset_sut(sut_sha, execution_mode="fixture")
        prompt = _dataset_prompt()
        model = _dataset_model()
    provenance = DatasetArtifactProvenance(
        evaluation_plane=EvaluationPlaneProvenance(
            commit_sha=evaluation_state.commit_sha,
            dirty_worktree=evaluation_state.dirty_worktree,
            executed=True,
        ),
        sut=sut,
        dataset=_dataset_provenance(validation.snapshot),
        adapter=adapter,
        evaluator=_dataset_evaluator(
            adapter.execution_mode,
            parsing_evaluator_version=parsing_evaluator_version,
        ),
        prompt=prompt,
        model=model,
    )
    logical_result = DatasetLogicalResult(
        dataset_snapshot=validation.snapshot,
        observation_snapshot=observations,
        evaluation=evaluation,
    )
    return DatasetRunArtifactDocument(
        schema_version="dataset-run-artifact-v1",
        run=RunEnvelope(
            run_id=run_id,
            execution_mode=adapter.execution_mode,
            created_at=datetime.now(UTC),
        ),
        provenance=provenance,
        logical_result=logical_result,
        logical_digest=canonical_digest(
            {
                "provenance": provenance.model_dump(mode="json"),
                "logical_result": logical_result.model_dump(mode="json"),
            }
        ),
    )


def write_dataset_run_artifact(
    artifact: DatasetRunArtifactDocument,
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


def replay_dataset_run_artifact(raw_artifact: object) -> dict[str, str]:
    artifact = DatasetRunArtifactDocument.model_validate(raw_artifact)
    stored = artifact.logical_result
    parsing_evaluator_version = artifact.provenance.evaluator.parsing_version
    validation = validate_dataset_snapshot(stored.dataset_snapshot)
    if validation.state != "VALID" or validation.snapshot is None:
        raise ValueError("artifact dataset snapshot does not reproduce its frozen digest")
    recomputed_evaluation = execute_dataset_fixture(
        validation,
        stored.observation_snapshot,
        parsing_evaluator_version=parsing_evaluator_version,
    )
    recomputed_logical_result = DatasetLogicalResult(
        dataset_snapshot=validation.snapshot,
        observation_snapshot=stored.observation_snapshot,
        evaluation=recomputed_evaluation,
    )
    adapter = _dataset_adapter(stored.observation_snapshot)
    if adapter.execution_mode == "live":
        recomputed_sut = _dataset_sut(
            stored.observation_snapshot.grounded.sut_commit_sha,
            execution_mode="live",
            dirty_worktree=artifact.provenance.sut.dirty_worktree,
        )
        recomputed_prompt = artifact.provenance.prompt
        recomputed_model = artifact.provenance.model
    else:
        recomputed_sut = _dataset_sut(
            stored.observation_snapshot.grounded.sut_commit_sha,
            execution_mode="fixture",
        )
        recomputed_prompt = _dataset_prompt()
        recomputed_model = _dataset_model()
    recomputed_provenance = artifact.provenance.model_copy(
        update={
            "sut": recomputed_sut,
            "dataset": _dataset_provenance(validation.snapshot),
            "adapter": adapter,
            "evaluator": _dataset_evaluator(
                adapter.execution_mode,
                parsing_evaluator_version=parsing_evaluator_version,
            ),
            "prompt": recomputed_prompt,
            "model": recomputed_model,
        }
    )
    recomputed_digest = canonical_digest(
        {
            "provenance": recomputed_provenance.model_dump(mode="json"),
            "logical_result": recomputed_logical_result.model_dump(mode="json"),
        }
    )
    if (
        stored != recomputed_logical_result
        or artifact.provenance != recomputed_provenance
        or artifact.logical_digest != recomputed_digest
    ):
        raise ValueError("artifact logical content does not reproduce its stored digest")
    return {
        "logical_digest": recomputed_digest,
        "run_state": recomputed_evaluation.state,
    }
