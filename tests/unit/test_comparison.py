from __future__ import annotations

import importlib.util
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import duckdb
import pytest
from pydantic import ValidationError


def test_comparison_module_is_available() -> None:
    assert importlib.util.find_spec("braincrew.comparison") is not None


PRIMARY_METRICS = (
    "evidence_span_recovery",
    "recall_at_5",
    "claim_support_precision",
    "citation_precision",
    "answer_mode_accuracy",
    "abstention_accuracy",
)

VERSION_MISMATCHES = (
    ("sut_sha", "1" * 40, "SYS-COMPARISON-SUT_SHA-MISMATCH"),
    (
        "dataset_digest",
        "sha256:" + "1" * 64,
        "SYS-COMPARISON-DATASET_DIGEST-MISMATCH",
    ),
    (
        "evaluator_versions",
        {
            "parsing": "parsing-quality-v2",
            "retrieval": "retrieval-quality-v1",
            "grounded": "grounded-answer-v1",
        },
        "SYS-COMPARISON-EVALUATOR_VERSIONS-MISMATCH",
    ),
    ("prompt_hash", "sha256:" + "1" * 64, "SYS-COMPARISON-PROMPT_HASH-MISMATCH"),
    ("model_name", "different-model", "SYS-COMPARISON-MODEL_NAME-MISMATCH"),
    ("retrieval_top_k", 6, "SYS-COMPARISON-RETRIEVAL_TOP_K-MISMATCH"),
    (
        "adapter_versions",
        {
            "parsing": "fixture-parsing-sut-v1",
            "retrieval": "fixture-retrieval-sut-v2",
            "grounded": "fixture-grounded-sut-v1",
        },
        "SYS-COMPARISON-ADAPTER_VERSIONS-MISMATCH",
    ),
)


def _run_payload(
    *,
    role: str,
    evidence_limit: int,
    metric_value: str = "0.80",
    latency_ms: str = "100",
    cost_usd: str = "0.010",
) -> dict[str, Any]:
    return {
        "schema_version": "experiment-run-summary-v1",
        "run_id": f"{role}-run",
        "role": role,
        "split": "verification",
        "state": "COMPLETED",
        "candidate_plan_version": "candidate-plan-v1",
        "provenance": {
            "evaluation_plane_sha": "a" * 40,
            "evaluation_plane_dirty": False,
            "sut_sha": "b" * 40,
            "sut_dirty": False,
            "dataset_id": "braincrew-evaluation-dataset",
            "dataset_version": "1.0.0",
            "dataset_digest": "sha256:" + "c" * 64,
            "corpus_id": "synthetic-hr-v1",
            "corpus_digest": "sha256:" + "7" * 64,
            "evaluator_versions": {
                "parsing": "parsing-quality-v1",
                "retrieval": "retrieval-quality-v1",
                "grounded": "grounded-answer-v1",
                "operational": "operational-v1",
            },
            "prompt_id": "fixture-recorded-observations",
            "prompt_hash": "sha256:" + "d" * 64,
            "model_provider": "none",
            "model_name": "not-called",
            "model_parameters": {},
            "retrieval_top_k": 5,
            "evidence_limit": evidence_limit,
            "fixed_retrieval_config_digest": "sha256:" + "e" * 64,
            "adapter_versions": {
                "parsing": "fixture-parsing-sut-v1",
                "retrieval": "fixture-retrieval-sut-v1",
                "grounded": "fixture-grounded-sut-v1",
            },
            "threshold_version": "release-thresholds-v1",
            "threshold_digest": "sha256:" + "f" * 64,
            "dependency_lock_digest": "sha256:" + "8" * 64,
            "runtime_environment_digest": "sha256:" + "9" * 64,
            "execution_mode": "fixture",
        },
        "cases": [
            {
                "case_id": f"CASE-{index:03d}",
                "metrics": {metric: metric_value for metric in PRIMARY_METRICS},
                "retrieval_metrics": {
                    "mrr_at_10": metric_value,
                    "authority_priority": metric_value,
                },
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
                "failures": [],
            }
            for index in range(1, 16)
        ],
    }


def test_compare_runs_passes_on_compatible_positive_quality_evidence() -> None:
    from braincrew import comparison as comparison_module

    assert hasattr(comparison_module, "ExperimentRunSummary")
    assert hasattr(comparison_module, "compare_runs")
    experiment_run_summary = comparison_module.ExperimentRunSummary
    compare_runs = comparison_module.compare_runs
    baseline = experiment_run_summary.model_validate(
        _run_payload(role="baseline", evidence_limit=3)
    )
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    for case in candidate_payload["cases"]:
        case["metrics"]["claim_support_precision"] = "0.83"
    candidate = experiment_run_summary.model_validate(candidate_payload)

    comparison = compare_runs(baseline, candidate, comparison_id="pass-comparison")

    assert comparison.decision == "PASS"
    assert [gate.decision for gate in comparison.gates] == ["PASS", "PASS", "PASS"]
    assert comparison.macro_deltas["claim_support_precision"] == Decimal("0.03")
    assert comparison.case_deltas[0].metric_deltas["claim_support_precision"] == Decimal("0.03")
    assert comparison.failure_taxonomy.new_critical == ()
    assert comparison.logical_digest.startswith("sha256:")


@pytest.mark.parametrize("non_finite", ["NaN", "Infinity", "-Infinity"])
@pytest.mark.parametrize(
    ("field_name", "metric_name"),
    [
        ("metrics", "claim_support_precision"),
        ("retrieval_metrics", "mrr_at_10"),
    ],
)
def test_run_summary_rejects_non_finite_metric_values(
    field_name: str,
    metric_name: str,
    non_finite: str,
) -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _run_payload(role="baseline", evidence_limit=3)
    payload["cases"][0][field_name][metric_name] = non_finite

    with pytest.raises(ValidationError, match="finite number"):
        ExperimentRunSummary.model_validate(payload)


def _pass_comparison(comparison_id: str = "pass-comparison") -> Any:
    from braincrew import comparison as comparison_module

    baseline = comparison_module.ExperimentRunSummary.model_validate(
        _run_payload(role="baseline", evidence_limit=3)
    )
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    for case in candidate_payload["cases"]:
        case["metrics"]["claim_support_precision"] = "0.83"
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)
    return comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id=comparison_id,
    )


def test_comparison_artifact_recursively_freezes_canonical_mappings() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    for payload in (baseline_payload, candidate_payload):
        payload["provenance"]["model_parameters"] = {
            "sampling": {"temperature": "0", "stop": ["END"]}
        }
    for case in candidate_payload["cases"]:
        case["metrics"]["claim_support_precision"] = "0.83"
    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="recursively-frozen-comparison",
    )

    with pytest.raises(TypeError, match="immutable"):
        artifact.candidate.cases[0].metrics["claim_support_precision"] = Decimal("0")
    with pytest.raises(TypeError, match="immutable"):
        artifact.candidate.provenance.model_parameters["temperature"] = Decimal("0")
    with pytest.raises(TypeError, match="immutable"):
        artifact.macro_deltas["claim_support_precision"] = Decimal("0")
    sampling = artifact.candidate.provenance.model_parameters["sampling"]
    assert isinstance(sampling, dict)
    with pytest.raises(TypeError, match="immutable"):
        sampling["temperature"] = "1"
    stop = sampling["stop"]
    assert isinstance(stop, tuple)
    with pytest.raises(AttributeError):
        cast(Any, stop).append("LATER")


def test_comparison_artifacts_replay_and_rebuild_disposable_cache(tmp_path: Path) -> None:
    from braincrew import result_store

    assert hasattr(result_store, "write_comparison_artifact")
    assert hasattr(result_store, "replay_comparison_artifact")
    assert hasattr(result_store, "rebuild_duckdb_cache")
    artifact = _pass_comparison()

    json_path, parquet_path = result_store.write_comparison_artifact(
        artifact,
        tmp_path,
    )
    replay = result_store.replay_comparison_artifact(json_path)
    cache_path = result_store.rebuild_duckdb_cache(parquet_path, tmp_path / "query.duckdb")

    assert json_path.name == "pass-comparison.json"
    assert parquet_path.name == "pass-comparison.parquet"
    assert replay == {
        "decision": "PASS",
        "logical_digest": artifact.logical_digest,
    }
    assert cache_path.is_file()
    with pytest.raises(FileExistsError):
        result_store.write_comparison_artifact(artifact, tmp_path)


def test_comparison_is_invalid_when_required_version_provenance_is_missing() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    del baseline_payload["provenance"]["evaluator_versions"]["grounded"]
    del candidate_payload["provenance"]["evaluator_versions"]["grounded"]
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="missing-provenance",
    )

    assert comparison.decision == "INVALID"
    assert "SYS-PROVENANCE-MISSING" in comparison.reasons


def test_comparison_is_invalid_without_operational_evaluator_provenance() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    del baseline_payload["provenance"]["evaluator_versions"]["operational"]
    del candidate_payload["provenance"]["evaluator_versions"]["operational"]
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="missing-operational-evaluator",
    )

    assert comparison.decision == "INVALID"
    assert "SYS-PROVENANCE-MISSING" in comparison.reasons


def test_comparison_is_invalid_when_retrieval_confound_changes() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    candidate_payload["cases"][0]["retrieval_metrics"]["mrr_at_10"] = "0.81"
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="confounded",
    )

    assert comparison.decision == "INVALID"
    assert comparison.confound_violations == ("SYS-CONFOUND-MRR_AT_10:CASE-001",)


def test_comparison_is_invalid_when_retrieval_confound_evidence_is_missing() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    del baseline_payload["cases"][0]["retrieval_metrics"]["authority_priority"]
    del candidate_payload["cases"][0]["retrieval_metrics"]["authority_priority"]
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="missing-confound-evidence",
    )

    assert comparison.decision == "INVALID"
    assert comparison.confound_violations == ("SYS-CONFOUND-AUTHORITY_PRIORITY-MISSING:CASE-001",)


def test_comparison_is_invalid_when_metric_denominators_differ() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    del candidate_payload["cases"][0]["metrics"]["citation_precision"]
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="denominator-drift",
    )

    assert comparison.decision == "INVALID"
    assert "SYS-COMPARISON-METRIC-DENOMINATOR-MISMATCH:citation_precision" in (comparison.reasons)


def test_comparison_is_invalid_below_verification_minimum_denominators() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    baseline_payload["cases"] = baseline_payload["cases"][:5]
    candidate_payload["cases"] = candidate_payload["cases"][:5]
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="under-covered-verification",
    )

    assert comparison.decision == "INVALID"
    assert (
        "SYS-COMPARISON-METRIC-DENOMINATOR-BELOW-MINIMUM:answer_mode_accuracy" in comparison.reasons
    )


def test_comparison_is_invalid_when_case_metric_applicability_moves() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    del baseline_payload["cases"][1]["metrics"]["citation_precision"]
    del candidate_payload["cases"][0]["metrics"]["citation_precision"]
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="applicability-drift",
    )

    assert comparison.decision == "INVALID"
    assert "SYS-COMPARISON-METRIC-APPLICABILITY-MISMATCH:CASE-001" in comparison.reasons


def test_replay_rejects_tampered_parquet_evidence(tmp_path: Path) -> None:
    from braincrew import result_store

    artifact = _pass_comparison()
    json_path, parquet_path = result_store.write_comparison_artifact(
        artifact,
        tmp_path,
    )
    tampered_path = tmp_path / "tampered.parquet"
    with duckdb.connect(":memory:") as connection:
        connection.execute(
            """
            CREATE TABLE tampered AS
            SELECT * REPLACE ('sha256:tampered' AS logical_digest)
            FROM read_parquet(?)
            """,
            [str(parquet_path)],
        )
        connection.execute(
            "COPY tampered TO ? (FORMAT PARQUET)",
            [str(tampered_path)],
        )
    tampered_path.replace(parquet_path)

    with pytest.raises(ValueError, match="Parquet"):
        result_store.replay_comparison_artifact(json_path)


def test_gate_three_cannot_pass_when_a_prior_gate_fails() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    for case in candidate_payload["cases"]:
        case["metrics"]["claim_support_precision"] = "0.83"
        case["metrics"]["citation_precision"] = "0.77"
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="ordered-gates",
    )

    assert [gate.decision for gate in comparison.gates] == ["PASS", "FAIL", "FAIL"]
    assert comparison.gates[2].reasons == ("GATE-3-PRIOR-GATE-FAILED",)


def test_parquet_preserves_repeating_operational_deltas_for_replay(tmp_path: Path) -> None:
    from braincrew import comparison as comparison_module
    from braincrew import result_store

    baseline_payload = _run_payload(
        role="baseline",
        evidence_limit=3,
        latency_ms="3",
        cost_usd="0.003",
    )
    candidate_payload = _run_payload(
        role="candidate",
        evidence_limit=5,
        latency_ms="2",
        cost_usd="0.002",
    )
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)
    artifact = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="repeating-delta",
    )
    json_path, _ = result_store.write_comparison_artifact(artifact, tmp_path)

    replay = result_store.replay_comparison_artifact(json_path)

    assert replay["logical_digest"] == artifact.logical_digest


def test_failure_taxonomy_aggregates_codes_families_and_critical_identities() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    baseline_payload["cases"][0]["failures"] = [
        {
            "code": "O-LATENCY-REGRESSION",
            "severity": "major",
            "evaluator_version": "operational-v1",
        }
    ]
    candidate_payload["cases"][0]["failures"] = [
        {
            "code": "A-ROLE-LEAKAGE",
            "severity": "critical",
            "evaluator_version": "grounded-answer-v1",
        },
        {
            "code": "O-LATENCY-REGRESSION",
            "severity": "major",
            "evaluator_version": "operational-v1",
        },
    ]
    candidate_payload["cases"][1]["failures"] = [
        {
            "code": "O-LATENCY-REGRESSION",
            "severity": "major",
            "evaluator_version": "operational-v1",
        }
    ]
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="taxonomy",
    )

    assert comparison.decision == "FAIL"
    assert comparison.failure_taxonomy.baseline_code_counts == {
        "O-LATENCY-REGRESSION": 1,
    }
    assert comparison.failure_taxonomy.candidate_code_counts == {
        "A-ROLE-LEAKAGE": 1,
        "O-LATENCY-REGRESSION": 2,
    }
    assert comparison.failure_taxonomy.candidate_family_counts == {"A": 1, "O": 2}
    assert comparison.failure_taxonomy.code_count_deltas == {
        "A-ROLE-LEAKAGE": 1,
        "O-LATENCY-REGRESSION": 1,
    }
    assert comparison.failure_taxonomy.new_critical == (
        "CASE-001|A-ROLE-LEAKAGE|grounded-answer-v1",
    )
    assert comparison.gates[0].reasons == ("GATE-1-CANDIDATE-CRITICAL-FAILURE",)


@pytest.mark.parametrize(("field_name", "value", "reason"), VERSION_MISMATCHES)
def test_comparison_is_invalid_for_each_locked_version_dimension(
    field_name: str,
    value: object,
    reason: str,
) -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    candidate_payload["provenance"][field_name] = value
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id=f"mismatch-{field_name}",
    )

    assert comparison.decision == "INVALID"
    assert reason in comparison.reasons


def test_comparison_is_invalid_when_corpus_provenance_differs() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    for payload in (baseline_payload, candidate_payload):
        payload["provenance"].update(
            {
                "evaluation_plane_dirty": False,
                "sut_dirty": False,
                "corpus_id": "synthetic-hr-v1",
                "corpus_digest": "sha256:" + "7" * 64,
                "dependency_lock_digest": "sha256:" + "8" * 64,
                "runtime_environment_digest": "sha256:" + "9" * 64,
            }
        )
    candidate_payload["provenance"]["corpus_digest"] = "sha256:" + "0" * 64
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="corpus-drift",
    )

    assert comparison.decision == "INVALID"
    assert "SYS-COMPARISON-CORPUS_DIGEST-MISMATCH" in comparison.reasons


def test_retrieval_digest_names_only_the_fixed_configuration() -> None:
    from braincrew import comparison as comparison_module

    payload = _run_payload(role="baseline", evidence_limit=3)
    digest = payload["provenance"]["fixed_retrieval_config_digest"]

    summary = comparison_module.ExperimentRunSummary.model_validate(payload)

    assert summary.provenance.fixed_retrieval_config_digest == digest


def test_run_summary_rejects_empty_required_provenance_digest() -> None:
    from braincrew import comparison as comparison_module

    payload = _run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["fixed_retrieval_config_digest"] = ""

    with pytest.raises(ValueError, match="fixed_retrieval_config_digest"):
        comparison_module.ExperimentRunSummary.model_validate(payload)


def test_run_summary_rejects_failure_codes_outside_the_frozen_taxonomy() -> None:
    from braincrew import comparison as comparison_module

    payload = _run_payload(role="candidate", evidence_limit=5)
    payload["cases"][0]["failures"] = [
        {
            "code": "UNKNOWN",
            "severity": "critical",
            "evaluator_version": "grounded-answer-v1",
        }
    ]

    with pytest.raises(ValueError, match="failure code"):
        comparison_module.ExperimentRunSummary.model_validate(payload)


def test_run_summary_rejects_severity_drift_for_frozen_critical_codes() -> None:
    from braincrew import comparison as comparison_module

    payload = _run_payload(role="candidate", evidence_limit=5)
    payload["cases"][0]["failures"] = [
        {
            "code": "A-ROLE-LEAKAGE",
            "severity": "minor",
            "evaluator_version": "grounded-answer-v1",
        }
    ]

    with pytest.raises(ValueError, match="critical severity"):
        comparison_module.ExperimentRunSummary.model_validate(payload)


def test_run_summary_rejects_failure_evaluator_outside_provenance() -> None:
    from braincrew import comparison as comparison_module

    payload = _run_payload(role="candidate", evidence_limit=5)
    payload["cases"][0]["failures"] = [
        {
            "code": "O-LATENCY-REGRESSION",
            "severity": "major",
            "evaluator_version": "operational-v2",
        }
    ]

    with pytest.raises(ValueError, match="evaluator provenance"):
        comparison_module.ExperimentRunSummary.model_validate(payload)
