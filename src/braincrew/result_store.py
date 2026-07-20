from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import duckdb

from braincrew.comparison import ComparisonArtifact, compare_runs
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
from braincrew.digest import canonical_digest
from braincrew.evaluator import (
    evaluate_exact_answer,
    evaluate_parsing_run,
    evaluate_retrieval_run,
)
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
        sut=_grounded_sut_provenance(sut_sha),
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
    answer_mode_contract_digest = canonical_digest(
        [
            {
                "case_id": case.case_id,
                "expected_answer_mode": case.expected_answer_mode,
                "applicable": case.applicability.answer_mode_accuracy,
            }
            for case in dataset.cases
        ]
    )
    abstention_contract_digest = canonical_digest(
        [
            {
                "case_id": case.case_id,
                "required_abstention_mode": case.required_abstention_mode,
                "forbidden_conclusive_proposition_ids": (case.forbidden_conclusive_proposition_ids),
                "applicable": case.applicability.abstention_accuracy,
            }
            for case in dataset.cases
        ]
    )
    visibility_contract_digest = canonical_digest(
        [
            {
                "case_id": case.case_id,
                "role": case.role,
                "protected_identifiers": case.protected_identifiers,
                "forbidden_role_proposition_ids": case.forbidden_role_proposition_ids,
            }
            for case in dataset.cases
        ]
    )
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
        answer_mode_contract_version=dataset.answer_mode_contract_version,
        answer_mode_contract_digest=answer_mode_contract_digest,
        abstention_contract_version=dataset.abstention_contract_version,
        abstention_contract_digest=abstention_contract_digest,
        visibility_contract_version=dataset.visibility_contract_version,
        visibility_contract_digest=visibility_contract_digest,
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
        dataset=_grounded_dataset_provenance(dataset),
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


def _grounded_dataset_provenance(
    dataset: GroundedDatasetDocument,
) -> DatasetArtifactProvenance:
    return DatasetArtifactProvenance(
        id=dataset.dataset_id,
        version=dataset.dataset_version,
        corpus_id="synthetic-hr-v1",
        source_type=dataset.provenance.source_kind,
        license=dataset.provenance.license,
        content_digest=canonical_digest(dataset.model_dump(mode="json")),
    )


def _grounded_sut_provenance(sut_sha: str) -> SutProvenance:
    return SutProvenance(
        commit_sha=sut_sha,
        dirty_worktree=None,
        executed=False,
        claim="identity placeholder only; live AX was not called",
    )


def _comparison_parquet_rows(artifact: ComparisonArtifact) -> list[tuple[object, ...]]:
    baseline_cases = {case.case_id: case for case in artifact.baseline.cases}
    candidate_cases = {case.case_id: case for case in artifact.candidate.cases}
    rows: list[tuple[object, ...]] = []
    for case_delta in artifact.case_deltas:
        baseline = baseline_cases[case_delta.case_id]
        candidate = candidate_cases[case_delta.case_id]
        for metric in sorted(case_delta.metric_deltas):
            rows.append(
                (
                    artifact.logical_digest,
                    artifact.decision,
                    case_delta.case_id,
                    metric,
                    baseline.metrics[metric],
                    candidate.metrics[metric],
                    case_delta.metric_deltas[metric],
                    baseline.latency_ms,
                    candidate.latency_ms,
                    case_delta.latency_relative_delta,
                    baseline.cost_usd,
                    candidate.cost_usd,
                    case_delta.cost_relative_delta,
                    json.dumps(
                        [failure.model_dump(mode="json") for failure in candidate.failures],
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
            )
    return rows


def _write_comparison_parquet(artifact: ComparisonArtifact, path: Path) -> None:
    connection = duckdb.connect(":memory:")
    try:
        connection.execute(
            """
            CREATE TABLE comparison_cases (
                logical_digest VARCHAR NOT NULL,
                decision VARCHAR NOT NULL,
                case_id VARCHAR NOT NULL,
                metric_name VARCHAR NOT NULL,
                baseline_value DECIMAL(38, 28) NOT NULL,
                candidate_value DECIMAL(38, 28) NOT NULL,
                delta DECIMAL(38, 28) NOT NULL,
                baseline_latency_ms DECIMAL(38, 28) NOT NULL,
                candidate_latency_ms DECIMAL(38, 28) NOT NULL,
                latency_relative_delta DECIMAL(38, 28),
                baseline_cost_usd DECIMAL(38, 28) NOT NULL,
                candidate_cost_usd DECIMAL(38, 28) NOT NULL,
                cost_relative_delta DECIMAL(38, 28),
                candidate_failures_json VARCHAR NOT NULL
            )
            """
        )
        connection.executemany(
            "INSERT INTO comparison_cases VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            _comparison_parquet_rows(artifact),
        )
        connection.execute(
            "COPY comparison_cases TO ? (FORMAT PARQUET, COMPRESSION ZSTD)",
            [str(path)],
        )
    finally:
        connection.close()


def write_comparison_artifact(
    artifact: ComparisonArtifact,
    output_dir: Path,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{artifact.comparison_id}.json"
    parquet_path = output_dir / f"{artifact.comparison_id}.parquet"
    if json_path.exists() or parquet_path.exists():
        raise FileExistsError(f"comparison artifact already exists: {artifact.comparison_id}")
    serialized = json.dumps(
        artifact.model_dump(mode="json"),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    with TemporaryDirectory(prefix=".comparison-", dir=output_dir) as temporary_dir:
        temporary_root = Path(temporary_dir)
        temporary_json = temporary_root / json_path.name
        temporary_parquet = temporary_root / parquet_path.name
        _write_comparison_parquet(artifact, temporary_parquet)
        temporary_json.write_text(serialized + "\n", encoding="utf-8")
        published: list[Path] = []
        try:
            for temporary_path, final_path in (
                (temporary_parquet, parquet_path),
                (temporary_json, json_path),
            ):
                os.link(temporary_path, final_path)
                published.append(final_path)
        except OSError:
            for published_path in published:
                published_path.unlink()
            raise
    return json_path, parquet_path


def replay_comparison_artifact(path: Path) -> dict[str, str]:
    raw_artifact: object = json.loads(path.read_text(encoding="utf-8"))
    stored = ComparisonArtifact.model_validate(raw_artifact)
    recomputed = compare_runs(
        stored.baseline,
        stored.candidate,
        comparison_id=stored.comparison_id,
    )
    if stored != recomputed:
        raise ValueError("comparison artifact does not reproduce its decision and digest")
    parquet_path = path.with_suffix(".parquet")
    if not parquet_path.is_file():
        raise ValueError("comparison Parquet artifact is missing")
    connection = duckdb.connect(":memory:")
    try:
        parquet_rows = connection.execute(
            """
            SELECT
                logical_digest,
                decision,
                case_id,
                metric_name,
                baseline_value,
                candidate_value,
                delta,
                baseline_latency_ms,
                candidate_latency_ms,
                latency_relative_delta,
                baseline_cost_usd,
                candidate_cost_usd,
                cost_relative_delta,
                candidate_failures_json
            FROM read_parquet(?)
            ORDER BY case_id, metric_name
            """,
            [str(parquet_path)],
        ).fetchall()
    finally:
        connection.close()
    if parquet_rows != _comparison_parquet_rows(recomputed):
        raise ValueError("comparison Parquet evidence does not reproduce canonical rows")
    return {
        "decision": recomputed.decision,
        "logical_digest": recomputed.logical_digest,
    }


def rebuild_duckdb_cache(parquet_path: Path, cache_path: Path) -> Path:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect(str(cache_path))
    try:
        connection.execute(
            "CREATE OR REPLACE TABLE comparison_cases AS SELECT * FROM read_parquet(?)",
            [str(parquet_path)],
        )
    finally:
        connection.close()
    return cache_path


def replay_run_artifact(path: Path) -> dict[str, str]:
    raw_artifact: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw_artifact, dict):
        raise ValueError("artifact must be a JSON object")
    schema_version = raw_artifact.get("schema_version")
    if schema_version == "live-verification-preflight-artifact-v2":
        from braincrew.live_verification import replay_live_preflight_artifact

        return replay_live_preflight_artifact(raw_artifact)
    if schema_version == "experiment-comparison-artifact-v1":
        return replay_comparison_artifact(path)
    if schema_version == "dataset-run-artifact-v1":
        from braincrew.dataset_run import replay_dataset_run_artifact

        return replay_dataset_run_artifact(raw_artifact)
    if schema_version == "parsing-run-artifact-v1":
        parsing_artifact = ParsingRunArtifactDocument.model_validate(raw_artifact)
        stored_parsing_result = parsing_artifact.logical_result
        recomputed_parsing_result = ParsingLogicalResult(
            dataset_snapshot=stored_parsing_result.dataset_snapshot,
            observation_snapshot=stored_parsing_result.observation_snapshot,
            evaluation=evaluate_parsing_run(
                stored_parsing_result.dataset_snapshot,
                stored_parsing_result.observation_snapshot,
            ),
        )
        recomputed_parsing_digest = canonical_digest(
            {
                "provenance": parsing_artifact.provenance.model_dump(mode="json"),
                "logical_result": recomputed_parsing_result.model_dump(mode="json"),
            }
        )
        if (
            stored_parsing_result != recomputed_parsing_result
            or parsing_artifact.logical_digest != recomputed_parsing_digest
        ):
            raise ValueError("artifact logical content does not reproduce its stored digest")
        return {
            "logical_digest": recomputed_parsing_digest,
            "run_state": recomputed_parsing_result.evaluation.state,
        }
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
        recomputed_dataset_provenance = _grounded_dataset_provenance(
            recomputed_grounded_result.dataset_snapshot
        )
        recomputed_sut_provenance = _grounded_sut_provenance(
            recomputed_grounded_result.observation_snapshot.sut_commit_sha
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
            or grounded_artifact.provenance.dataset != recomputed_dataset_provenance
            or grounded_artifact.provenance.sut != recomputed_sut_provenance
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
