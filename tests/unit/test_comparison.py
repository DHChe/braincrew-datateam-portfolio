from __future__ import annotations

import importlib.util
import os
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
LATENCY_DEFINITION = (
    "client wall-clock from adapter call start through terminal response validation, "
    "including retries; excludes corpus identity and evaluator time"
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
            "latency_definition": LATENCY_DEFINITION,
            "cost_measurement_status": "measured",
        },
        "cases": [
            {
                "case_id": f"CASE-{index:03d}",
                "metrics": {metric: metric_value for metric in PRIMARY_METRICS},
                "retrieval_metrics": {
                    "mrr_at_10": metric_value,
                    "authority_priority": metric_value,
                },
                "applicability": {
                    "recall_at_5": True,
                    "mrr_at_10": True,
                    "authority_ordering": True,
                    "forbidden_visibility": False,
                },
                "latency_ms": latency_ms,
                "cost_usd": cost_usd,
                "failures": [],
            }
            for index in range(1, 16)
        ],
    }


def _mixed_run_payload(*, role: str, evidence_limit: int) -> dict[str, Any]:
    payload = _run_payload(role=role, evidence_limit=evidence_limit)
    inapplicable = {
        "recall_at_5": False,
        "mrr_at_10": False,
        "authority_ordering": False,
        "forbidden_visibility": False,
    }
    retrieval_applicable = {
        "recall_at_5": True,
        "mrr_at_10": True,
        "authority_ordering": True,
        "forbidden_visibility": False,
    }
    parsing_cases = [
        {
            "case_id": f"P-VERIFY-{index:03d}",
            "metrics": {"evidence_span_recovery": "0.80"},
            "retrieval_metrics": {},
            "applicability": inapplicable,
            "latency_ms": "100",
            "cost_usd": "0.010",
            "failures": [],
        }
        for index in range(1, 7)
    ]
    retrieval_cases = [
        {
            "case_id": f"R-VERIFY-{index:03d}",
            "metrics": {"recall_at_5": "0.80"},
            "retrieval_metrics": {
                "mrr_at_10": "0.80",
                "authority_priority": "0.80",
            },
            "applicability": retrieval_applicable,
            "latency_ms": "100",
            "cost_usd": "0.010",
            "failures": [],
        }
        for index in range(1, 10)
    ]
    grounded_cases = []
    for index in range(1, 16):
        metrics = {"answer_mode_accuracy": "0.80"}
        if index <= 10:
            metrics.update(
                {
                    "claim_support_precision": "0.80",
                    "citation_precision": "0.80",
                }
            )
        if index <= 5:
            metrics["abstention_accuracy"] = "0.80"
        grounded_cases.append(
            {
                "case_id": f"A-VERIFY-{index:03d}",
                "metrics": metrics,
                "retrieval_metrics": {},
                "applicability": inapplicable,
                "latency_ms": "100",
                "cost_usd": "0.010",
                "failures": [],
            }
        )
    payload["cases"] = [*parsing_cases, *retrieval_cases, *grounded_cases]
    return payload


def _set_live_corpus_digests(payload: dict[str, Any]) -> None:
    payload["provenance"]["execution_mode"] = "live"
    payload["provenance"].pop("corpus_digest")
    payload["provenance"]["corpus_digests_by_role"] = {
        "Employee": "sha256:" + "7" * 64,
        "Executive": "sha256:" + "7" * 64,
        "HRPractitioner": "sha256:" + "7" * 64,
    }


def test_unmeasured_cost_is_required_but_explicitly_nullable() -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["cost_measurement_status"] = "unmeasured"
    for case in payload["cases"]:
        case["cost_usd"] = None

    summary = ExperimentRunSummary.model_validate(payload)

    assert all(case.cost_usd is None for case in summary.cases)
    del payload["cases"][0]["cost_usd"]
    with pytest.raises(ValidationError, match="cost_usd"):
        ExperimentRunSummary.model_validate(payload)


def test_run_summary_refuses_zero_cost_under_an_unmeasured_warrant() -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["cost_measurement_status"] = "unmeasured"

    with pytest.raises(ValidationError, match="unmeasured cost provenance"):
        ExperimentRunSummary.model_validate(payload)


def test_run_summary_refuses_measured_cost_warrant_without_any_measurement() -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["cost_measurement_status"] = "measured"
    for case in payload["cases"]:
        case["cost_usd"] = None

    with pytest.raises(ValidationError, match="measured cost provenance"):
        ExperimentRunSummary.model_validate(payload)


def test_run_summary_refuses_measured_cost_with_partial_operational_coverage() -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["cost_measurement_status"] = "measured"
    for case in payload["cases"][1:]:
        case["cost_usd"] = None

    with pytest.raises(
        ValidationError,
        match="every latency-measured case",
    ):
        ExperimentRunSummary.model_validate(payload)


@pytest.mark.parametrize(
    "latency_definition",
    [None, "one attempt measured by an unrelated stopwatch"],
)
def test_run_summary_binds_latency_definition_to_measured_cases(
    latency_definition: str | None,
) -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["latency_definition"] = latency_definition

    with pytest.raises(ValidationError, match="latency"):
        ExperimentRunSummary.model_validate(payload)


def test_run_summary_refuses_a_latency_definition_without_any_measurement() -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["latency_definition"] = LATENCY_DEFINITION
    payload["provenance"]["cost_measurement_status"] = "unmeasured"
    for case in payload["cases"]:
        case["latency_ms"] = None
        case["cost_usd"] = None

    with pytest.raises(ValidationError, match="latency definition requires"):
        ExperimentRunSummary.model_validate(payload)


def test_comparison_keeps_measured_latency_when_cost_is_unmeasured() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _mixed_run_payload(role="candidate", evidence_limit=5)
    for payload in (baseline_payload, candidate_payload):
        payload["provenance"]["cost_measurement_status"] = "unmeasured"
        for case in payload["cases"]:
            case["cost_usd"] = None
        for case in payload["cases"][:6]:
            case["latency_ms"] = None
    for case in candidate_payload["cases"]:
        if "claim_support_precision" in case["metrics"]:
            case["metrics"]["claim_support_precision"] = "0.83"

    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="unmeasured-cost",
    )

    if artifact.decision != "PASS":
        pytest.fail(
            f"quality and latency comparison was blocked by unmeasured cost: {artifact.reasons}"
        )
    operational = artifact.operational_delta
    if operational is None:
        pytest.fail("measured latency must produce an operational delta")
    if operational.baseline_p95_latency_ms != Decimal("100"):
        pytest.fail(f"unexpected baseline p95: {operational.baseline_p95_latency_ms}")
    if operational.candidate_p95_latency_ms != Decimal("100"):
        pytest.fail(f"unexpected candidate p95: {operational.candidate_p95_latency_ms}")
    if operational.baseline_mean_cost_usd is not None:
        pytest.fail("excluded baseline cost must remain null")
    if operational.candidate_mean_cost_usd is not None:
        pytest.fail("excluded candidate cost must remain null")
    if operational.mean_cost_relative_delta is not None:
        pytest.fail("excluded cost must not produce a relative delta")
    if operational.cost_decision_warrant.status != "excluded":
        pytest.fail(f"cost exclusion was not explicit: {operational.cost_decision_warrant}")
    if operational.cost_decision_warrant.reason != "both runs declare cost unmeasured":
        pytest.fail(f"cost exclusion reason drifted: {operational.cost_decision_warrant}")


def test_unmeasured_cost_does_not_count_as_gate_3_positive_evidence() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _mixed_run_payload(role="candidate", evidence_limit=5)
    for payload in (baseline_payload, candidate_payload):
        payload["provenance"]["cost_measurement_status"] = "unmeasured"
        for case in payload["cases"]:
            case["cost_usd"] = None

    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="unmeasured-cost-no-positive-evidence",
    )

    if [gate.decision for gate in artifact.gates] != ["PASS", "PASS", "FAIL"]:
        pytest.fail(f"unmeasured cost affected the gate sequence: {artifact.gates}")
    if artifact.reasons != ("GATE-3-NO-POSITIVE-EVIDENCE",):
        pytest.fail(f"unmeasured cost was treated as evidence: {artifact.reasons}")


def test_measured_cost_regression_still_fails_gate_2() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _mixed_run_payload(role="candidate", evidence_limit=5)
    for case in candidate_payload["cases"]:
        case["cost_usd"] = "0.013"

    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="measured-cost-regression",
    )

    if "GATE-2-COST-REGRESSION" not in artifact.reasons:
        pytest.fail(f"measured cost regression was skipped: {artifact.reasons}")
    operational = artifact.operational_delta
    if operational is None or operational.cost_decision_warrant.status != "included":
        pytest.fail(f"measured cost was not included: {operational}")


def test_measured_cost_improvement_still_counts_as_gate_3_positive_evidence() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _mixed_run_payload(role="candidate", evidence_limit=5)
    for case in candidate_payload["cases"]:
        case["cost_usd"] = "0.008"

    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="measured-cost-improvement",
    )

    if artifact.decision != "PASS":
        pytest.fail(f"measured cost improvement did not reach gate 3: {artifact.reasons}")


def test_comparison_refuses_all_null_latency_without_a_traceback() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _mixed_run_payload(role="candidate", evidence_limit=5)
    for payload in (baseline_payload, candidate_payload):
        payload["provenance"]["latency_definition"] = None
        payload["provenance"]["cost_measurement_status"] = "unmeasured"
        for case in payload["cases"]:
            case["latency_ms"] = None
            case["cost_usd"] = None

    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="unmeasured-latency",
    )

    if artifact.decision != "INVALID":
        pytest.fail(f"all-null latency was not refused: {artifact.decision}")
    if "SYS-COMPARISON-LATENCY-UNMEASURED" not in artifact.reasons:
        pytest.fail(f"all-null latency refusal missing: {artifact.reasons}")
    if artifact.operational_delta is not None:
        pytest.fail("all-null latency must not publish an operational aggregate")


def test_comparison_refuses_per_case_latency_coverage_drift() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _mixed_run_payload(role="candidate", evidence_limit=5)
    candidate_payload["cases"][0]["latency_ms"] = None
    candidate_payload["cases"][0]["cost_usd"] = None

    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="latency-coverage-drift",
    )

    expected = f"SYS-COMPARISON-LATENCY-COVERAGE-MISMATCH:{baseline_payload['cases'][0]['case_id']}"
    if expected not in artifact.reasons:
        pytest.fail(f"latency coverage drift was not refused: {artifact.reasons}")


def test_comparison_records_operational_aggregate_denominators() -> None:
    from braincrew import comparison as comparison_module

    baseline = comparison_module.ExperimentRunSummary.model_validate(
        _mixed_run_payload(role="baseline", evidence_limit=3)
    )
    candidate = comparison_module.ExperimentRunSummary.model_validate(
        _mixed_run_payload(role="candidate", evidence_limit=5)
    )

    artifact = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="operational-denominators",
    )

    operational = artifact.operational_delta
    if operational is None:
        pytest.fail("measured operational values must produce an aggregate")
    expected = len(baseline.cases)
    counts = (
        operational.baseline_latency_case_count,
        operational.candidate_latency_case_count,
        operational.baseline_cost_case_count,
        operational.candidate_cost_case_count,
    )
    if counts != (expected, expected, expected, expected):
        pytest.fail(f"operational denominators do not describe the run: {counts}")


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


def test_run_summary_requires_declared_retrieval_applicability() -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _run_payload(role="baseline", evidence_limit=3)
    del payload["cases"][0]["applicability"]

    with pytest.raises(ValidationError, match="Field required"):
        ExperimentRunSummary.model_validate(payload)


@pytest.mark.parametrize(
    ("metric_name", "applicability_field"),
    [
        ("recall_at_5", "recall_at_5"),
        ("mrr_at_10", "mrr_at_10"),
        ("authority_priority", "authority_ordering"),
    ],
)
def test_case_result_rejects_present_inapplicable_confound_metric(
    metric_name: str,
    applicability_field: str,
) -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _run_payload(role="baseline", evidence_limit=3)
    payload["cases"][0]["applicability"][applicability_field] = False

    with pytest.raises(
        ValidationError,
        match=rf"{metric_name} must be absent when declared inapplicable",
    ):
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


def test_comparison_artifact_writes_and_replays_null_cost(tmp_path: Path) -> None:
    from braincrew import comparison as comparison_module
    from braincrew import result_store

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    for payload in (baseline_payload, candidate_payload):
        payload["provenance"]["cost_measurement_status"] = "unmeasured"
        for case in payload["cases"]:
            case["cost_usd"] = None
        payload["cases"][0]["latency_ms"] = None
    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="null-cost-comparison",
    )

    json_path, parquet_path = result_store.write_comparison_artifact(artifact, tmp_path)
    replay = result_store.replay_comparison_artifact(json_path)

    assert parquet_path.is_file()
    assert replay == {
        "decision": artifact.decision,
        "logical_digest": artifact.logical_digest,
    }


def test_comparison_artifact_pair_rolls_back_new_file_on_publish_race(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from braincrew import result_store

    artifact = _pass_comparison(comparison_id="publish-race")
    json_path = tmp_path / "publish-race.json"
    parquet_path = tmp_path / "publish-race.parquet"
    original_link = os.link

    def race_json_publish(source: str | Path, destination: str | Path) -> None:
        if Path(destination) == json_path:
            json_path.write_bytes(b"pre-existing-json")
        original_link(source, destination)

    monkeypatch.setattr(os, "link", race_json_publish)

    with pytest.raises(FileExistsError):
        result_store.write_comparison_artifact(artifact, tmp_path)

    assert json_path.read_bytes() == b"pre-existing-json"
    assert not parquet_path.exists()


def test_comparison_id_rejects_path_traversal_before_storage() -> None:
    from braincrew import comparison as comparison_module

    baseline = comparison_module.ExperimentRunSummary.model_validate(
        _run_payload(role="baseline", evidence_limit=3)
    )
    candidate = comparison_module.ExperimentRunSummary.model_validate(
        _run_payload(role="candidate", evidence_limit=5)
    )

    with pytest.raises(ValidationError, match="comparison_id"):
        comparison_module.compare_runs(
            baseline,
            candidate,
            comparison_id="../../escaped",
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("metric", "0.12345678901234567890123456789"),
        ("latency_ms", "12345678901"),
    ],
)
def test_run_summary_rejects_decimals_not_exactly_representable_in_parquet(
    field_name: str,
    value: str,
) -> None:
    from braincrew.comparison import ExperimentRunSummary

    payload = _run_payload(role="baseline", evidence_limit=3)
    if field_name == "metric":
        payload["cases"][0]["metrics"]["claim_support_precision"] = value
    else:
        payload["cases"][0][field_name] = value

    with pytest.raises(ValidationError, match=r"DECIMAL\(38, 28\)"):
        ExperimentRunSummary.model_validate(payload)


def test_relative_delta_is_quantized_to_the_published_decimal_scale() -> None:
    from braincrew import comparison as comparison_module

    delta = comparison_module._parquet_relative_delta(
        Decimal("0.164083"),
        Decimal("0.15525"),
    )

    assert delta == Decimal("-0.0538325115947416856103313567")
    assert delta.as_tuple().exponent == -28
    assert comparison_module._fits_parquet_decimal(delta)


def test_operational_aggregate_deltas_share_the_published_decimal_guard() -> None:
    from braincrew import comparison as comparison_module

    raw_latency_delta = comparison_module._relative_delta(
        Decimal("0.164083"),
        Decimal("0.165021"),
    )
    raw_cost_delta = comparison_module._relative_delta(
        Decimal("0.010001"),
        Decimal("0.010058"),
    )
    assert raw_latency_delta is not None
    assert raw_cost_delta is not None
    assert not comparison_module._fits_parquet_decimal(raw_latency_delta)
    assert not comparison_module._fits_parquet_decimal(raw_cost_delta)

    baseline_payload = _run_payload(
        role="baseline",
        evidence_limit=3,
        latency_ms="0.164083",
        cost_usd="0.010001",
    )
    candidate_payload = _run_payload(
        role="candidate",
        evidence_limit=5,
        latency_ms="0.165021",
        cost_usd="0.010058",
    )

    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="aggregate-decimal-scale",
    )

    operational = artifact.operational_delta
    if operational is None:
        pytest.fail(f"representable operational deltas were rejected: {artifact.reasons}")
    assert operational.p95_latency_relative_delta.as_tuple().exponent == -28
    assert operational.mean_cost_relative_delta is not None
    assert operational.mean_cost_relative_delta.as_tuple().exponent == -28
    assert comparison_module._fits_parquet_decimal(operational.p95_latency_relative_delta)
    assert comparison_module._fits_parquet_decimal(operational.mean_cost_relative_delta)


def test_zero_case_baseline_keeps_computable_operational_aggregate() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    baseline_payload["cases"][0]["latency_ms"] = "0"
    baseline_payload["cases"][0]["cost_usd"] = "0"
    candidate_payload["cases"][0]["latency_ms"] = "1"
    candidate_payload["cases"][0]["cost_usd"] = "0.001"
    for case in candidate_payload["cases"]:
        case["metrics"]["claim_support_precision"] = "0.83"

    comparison = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="zero-case-baseline",
    )

    assert comparison.decision == "PASS"
    assert comparison.case_deltas[0].latency_relative_delta is None
    assert comparison.case_deltas[0].cost_relative_delta is None
    assert comparison.operational_delta is not None


def test_unrepresentable_relative_deltas_fail_closed_but_remain_replayable(
    tmp_path: Path,
) -> None:
    from braincrew import comparison as comparison_module
    from braincrew import result_store

    baseline_payload = _run_payload(
        role="baseline",
        evidence_limit=3,
        latency_ms="0.0000000000000000000000000001",
        cost_usd="0.01",
    )
    candidate_payload = _run_payload(
        role="candidate",
        evidence_limit=5,
        latency_ms="9999999999",
        cost_usd="0.01",
    )
    artifact = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="relative-delta-overflow",
    )

    assert artifact.decision == "INVALID"
    assert "SYS-COMPARISON-DECIMAL-RANGE" in artifact.reasons
    assert artifact.case_deltas[0].latency_relative_delta is None
    assert artifact.case_deltas[0].cost_relative_delta == Decimal(0)
    json_path, _ = result_store.write_comparison_artifact(artifact, tmp_path)
    assert result_store.replay_comparison_artifact(json_path) == {
        "decision": "INVALID",
        "logical_digest": artifact.logical_digest,
    }


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

    expected = ("SYS-CONFOUND-MRR_AT_10:CASE-001",)
    if comparison.decision != "INVALID" or comparison.confound_violations != expected:
        pytest.fail(
            "differing applicable retrieval values must remain a confound: "
            f"decision={comparison.decision}, confounds={comparison.confound_violations}"
        )


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

    expected = ("SYS-CONFOUND-AUTHORITY_PRIORITY-MISSING:CASE-001",)
    if comparison.decision != "INVALID" or comparison.confound_violations != expected:
        pytest.fail(
            "missing applicable retrieval evidence must remain a confound: "
            f"decision={comparison.decision}, confounds={comparison.confound_violations}"
        )


def test_realistic_mixed_verification_cases_ignore_inapplicable_retrieval_confounds() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _mixed_run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _mixed_run_payload(role="candidate", evidence_limit=5)
    for case in candidate_payload["cases"]:
        if "claim_support_precision" in case["metrics"]:
            case["metrics"]["claim_support_precision"] = "0.83"

    comparison = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="mixed-verification",
    )

    if comparison.confound_violations:
        pytest.fail(
            "declared-inapplicable parsing and grounded cases must not be confound candidates: "
            f"{comparison.confound_violations}"
        )
    if comparison.decision != "PASS":
        pytest.fail(f"the realistic mixed comparison must reach PASS, got {comparison.decision}")


def test_comparison_is_invalid_when_declared_retrieval_applicability_differs() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    candidate_payload["cases"][0]["applicability"]["mrr_at_10"] = False
    del candidate_payload["cases"][0]["retrieval_metrics"]["mrr_at_10"]

    comparison = comparison_module.compare_runs(
        comparison_module.ExperimentRunSummary.model_validate(baseline_payload),
        comparison_module.ExperimentRunSummary.model_validate(candidate_payload),
        comparison_id="applicability-mismatch",
    )

    expected = "SYS-COMPARISON-METRIC-APPLICABILITY-MISMATCH:CASE-001"
    if expected not in comparison.reasons:
        pytest.fail(f"declared applicability drift must fail closed with {expected}")


def test_authority_priority_confound_maps_to_authority_ordering_applicability() -> None:
    from braincrew import comparison as comparison_module

    expected = {
        "recall_at_5": "recall_at_5",
        "mrr_at_10": "mrr_at_10",
        "authority_priority": "authority_ordering",
    }
    if comparison_module.RETRIEVAL_CONFOUND_APPLICABILITY_FIELDS != expected:
        pytest.fail(
            "authority_priority must remain explicitly mapped to authority_ordering applicability"
        )


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


def test_comparison_is_invalid_when_fixture_corpus_provenance_differs() -> None:
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


def test_comparison_refuses_one_roles_corpus_digest_change_between_runs() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    _set_live_corpus_digests(baseline_payload)
    _set_live_corpus_digests(candidate_payload)
    candidate_payload["provenance"]["corpus_digests_by_role"]["Employee"] = "sha256:" + "0" * 64
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="role-corpus-digest-drift",
    )

    reason = "SYS-COMPARISON-CORPUS_DIGESTS_BY_ROLE-MISMATCH"
    assert comparison.decision == "INVALID"
    assert reason in comparison.compatibility_violations
    assert reason in comparison.reasons
    assert all(gate.decision == "INVALID" for gate in comparison.gates)


@pytest.mark.parametrize("coverage_change", ["missing", "extra"])
def test_comparison_refuses_role_scoped_corpus_coverage_change_between_runs(
    coverage_change: str,
) -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    _set_live_corpus_digests(baseline_payload)
    _set_live_corpus_digests(candidate_payload)
    candidate_digests = candidate_payload["provenance"]["corpus_digests_by_role"]
    if coverage_change == "missing":
        candidate_digests.pop("Employee")
    else:
        candidate_digests["HRAdmin"] = "sha256:" + "7" * 64
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id=f"role-corpus-coverage-{coverage_change}",
    )

    reason = "SYS-COMPARISON-CORPUS_DIGESTS_BY_ROLE-MISMATCH"
    assert comparison.decision == "INVALID"
    assert reason in comparison.compatibility_violations


def test_comparison_refuses_corpus_id_change_between_runs() -> None:
    from braincrew import comparison as comparison_module

    baseline_payload = _run_payload(role="baseline", evidence_limit=3)
    candidate_payload = _run_payload(role="candidate", evidence_limit=5)
    _set_live_corpus_digests(baseline_payload)
    _set_live_corpus_digests(candidate_payload)
    candidate_payload["provenance"]["corpus_id"] = "different-live-corpus-v1"
    baseline = comparison_module.ExperimentRunSummary.model_validate(baseline_payload)
    candidate = comparison_module.ExperimentRunSummary.model_validate(candidate_payload)

    comparison = comparison_module.compare_runs(
        baseline,
        candidate,
        comparison_id="corpus-id-drift",
    )

    reason = "SYS-COMPARISON-CORPUS_ID-MISMATCH"
    assert comparison.decision == "INVALID"
    assert reason in comparison.compatibility_violations
    assert reason in comparison.reasons


def test_fixture_corpus_digest_is_explicitly_not_role_scoped() -> None:
    from braincrew import comparison as comparison_module

    summary = comparison_module.ExperimentRunSummary.model_validate(
        _run_payload(role="baseline", evidence_limit=3)
    )

    assert summary.provenance.execution_mode == "fixture"
    assert summary.provenance.corpus_digest == "sha256:" + "7" * 64
    assert summary.provenance.corpus_digests_by_role is None


def test_corpus_digests_by_role_refuses_an_empty_map() -> None:
    from braincrew import comparison as comparison_module

    payload = _run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["execution_mode"] = "live"
    payload["provenance"].pop("corpus_digest")
    payload["provenance"]["corpus_digests_by_role"] = {}

    with pytest.raises(
        ValidationError,
        match="per-role corpus digests require non-empty role keys",
    ):
        comparison_module.ExperimentRunSummary.model_validate(payload)


def test_corpus_digests_by_role_refuses_an_empty_role_key() -> None:
    from braincrew import comparison as comparison_module

    payload = _run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["execution_mode"] = "live"
    payload["provenance"].pop("corpus_digest")
    payload["provenance"]["corpus_digests_by_role"] = {
        "": "sha256:" + "7" * 64,
    }

    with pytest.raises(
        ValidationError,
        match="per-role corpus digests require non-empty role keys",
    ):
        comparison_module.ExperimentRunSummary.model_validate(payload)


def test_live_provenance_refuses_an_unscoped_fixture_digest() -> None:
    from braincrew import comparison as comparison_module

    payload = _run_payload(role="baseline", evidence_limit=3)
    payload["provenance"]["execution_mode"] = "live"

    with pytest.raises(
        ValidationError,
        match="live provenance requires corpus_digests_by_role",
    ):
        comparison_module.ExperimentRunSummary.model_validate(payload)


def test_fixture_provenance_refuses_role_scoped_corpus_digests() -> None:
    from braincrew import comparison as comparison_module

    payload = _run_payload(role="baseline", evidence_limit=3)
    payload["provenance"].pop("corpus_digest")
    payload["provenance"]["corpus_digests_by_role"] = {
        "Employee": "sha256:" + "7" * 64,
    }

    with pytest.raises(
        ValidationError,
        match="fixture provenance requires one unscoped corpus_digest",
    ):
        comparison_module.ExperimentRunSummary.model_validate(payload)


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
