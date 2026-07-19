"""Compatible experiment comparison and release-gate contracts."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from math import ceil
from typing import Literal

from pydantic import Field, TypeAdapter, field_validator, model_validator

from braincrew.contracts import StrictContract
from braincrew.digest import canonical_digest

PRIMARY_METRICS = (
    "evidence_span_recovery",
    "recall_at_5",
    "claim_support_precision",
    "citation_precision",
    "answer_mode_accuracy",
    "abstention_accuracy",
)
RETRIEVAL_CONFOUND_METRICS = ("recall_at_5", "mrr_at_10", "authority_priority")
VERIFICATION_MINIMUM_DENOMINATORS = {
    "evidence_span_recovery": 6,
    "recall_at_5": 9,
    "claim_support_precision": 10,
    "citation_precision": 10,
    "answer_mode_accuracy": 15,
    "abstention_accuracy": 5,
}
CRITICAL_FAILURE_CODES = {
    "R-FORBIDDEN-VISIBILITY",
    "A-ROLE-LEAKAGE",
    "A-UNSUPPORTED-HIGH-RISK-CONCLUSION",
    "A-FAILED-ABSTENTION",
    "SYS-PROVENANCE-MISSING",
    "SYS-COMPARISON-INVALID",
}
QUALITY_REGRESSION_LIMIT = Decimal("0.02")
QUALITY_IMPROVEMENT_MINIMUM = Decimal("0.03")
LATENCY_REGRESSION_LIMIT = Decimal("0.15")
LATENCY_IMPROVEMENT_MINIMUM = Decimal("0.15")
COST_REGRESSION_LIMIT = Decimal("0.20")
COST_IMPROVEMENT_MINIMUM = Decimal("0.20")
JSON_OBJECT_ADAPTER = TypeAdapter(dict[str, object])
SHA256_DIGEST_PATTERN = r"^sha256:[0-9a-f]{64}$"


class FailureIdentity(StrictContract):
    code: str
    severity: Literal["critical", "major", "minor", "diagnostic"]
    evaluator_version: str = Field(min_length=1)

    @field_validator("code")
    @classmethod
    def validate_failure_code(cls, code: str) -> str:
        if not code.startswith(("P-", "R-", "A-", "O-", "SYS-")):
            raise ValueError("failure code must use the frozen P/R/A/O/SYS taxonomy")
        return code

    @model_validator(mode="after")
    def validate_frozen_severity(self) -> FailureIdentity:
        if self.code in CRITICAL_FAILURE_CODES and self.severity != "critical":
            raise ValueError(f"{self.code} must retain critical severity")
        if self.code not in CRITICAL_FAILURE_CODES and self.severity == "critical":
            raise ValueError(f"{self.code} is not a frozen critical failure")
        return self


class ExperimentCaseResult(StrictContract):
    case_id: str
    metrics: dict[str, Decimal]
    retrieval_metrics: dict[str, Decimal] = Field(default_factory=dict)
    latency_ms: Decimal = Field(ge=0)
    cost_usd: Decimal = Field(ge=0)
    failures: tuple[FailureIdentity, ...]

    @model_validator(mode="after")
    def validate_metrics(self) -> ExperimentCaseResult:
        unknown = set(self.metrics) - set(PRIMARY_METRICS)
        if unknown:
            raise ValueError(f"unknown primary metrics: {sorted(unknown)}")
        if any(value < 0 or value > 1 for value in self.metrics.values()):
            raise ValueError("primary metric values must be within [0, 1]")
        unknown_retrieval = set(self.retrieval_metrics) - {
            "mrr_at_10",
            "authority_priority",
        }
        if unknown_retrieval:
            raise ValueError(f"unknown retrieval metrics: {sorted(unknown_retrieval)}")
        if any(value < 0 or value > 1 for value in self.retrieval_metrics.values()):
            raise ValueError("retrieval metric values must be within [0, 1]")
        return self


class ExperimentProvenance(StrictContract):
    evaluation_plane_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    evaluation_plane_dirty: bool
    sut_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    sut_dirty: bool
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    dataset_digest: str = Field(pattern=SHA256_DIGEST_PATTERN)
    corpus_id: str = Field(min_length=1)
    corpus_digest: str = Field(pattern=SHA256_DIGEST_PATTERN)
    evaluator_versions: dict[str, str]
    prompt_id: str = Field(min_length=1)
    prompt_hash: str = Field(pattern=SHA256_DIGEST_PATTERN)
    model_provider: str = Field(min_length=1)
    model_name: str = Field(min_length=1)
    model_parameters: dict[str, object]
    retrieval_top_k: int = Field(gt=0)
    evidence_limit: int = Field(gt=0)
    fixed_retrieval_config_digest: str = Field(pattern=SHA256_DIGEST_PATTERN)
    adapter_versions: dict[str, str]
    threshold_version: str = Field(min_length=1)
    threshold_digest: str = Field(pattern=SHA256_DIGEST_PATTERN)
    dependency_lock_digest: str = Field(pattern=SHA256_DIGEST_PATTERN)
    runtime_environment_digest: str = Field(pattern=SHA256_DIGEST_PATTERN)
    execution_mode: Literal["fixture", "live"]

    @field_validator("evaluator_versions", "adapter_versions")
    @classmethod
    def validate_version_map(cls, versions: dict[str, str]) -> dict[str, str]:
        if any(not key or not version for key, version in versions.items()):
            raise ValueError("version maps require non-empty keys and values")
        return versions


class ExperimentRunSummary(StrictContract):
    schema_version: Literal["experiment-run-summary-v1"]
    run_id: str
    role: Literal["baseline", "candidate"]
    split: Literal["verification"]
    state: Literal["COMPLETED", "FAILED", "INVALID"]
    candidate_plan_version: Literal["candidate-plan-v1"]
    provenance: ExperimentProvenance
    cases: tuple[ExperimentCaseResult, ...]

    @model_validator(mode="after")
    def validate_case_identities(self) -> ExperimentRunSummary:
        case_ids = [case.case_id for case in self.cases]
        if not case_ids:
            raise ValueError("at least one case result is required")
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("case result IDs must be unique")
        evaluator_versions = set(self.provenance.evaluator_versions.values())
        if any(
            failure.evaluator_version not in evaluator_versions
            for case in self.cases
            for failure in case.failures
        ):
            raise ValueError("failure identity must reference evaluator provenance")
        return self


class CaseDelta(StrictContract):
    case_id: str
    metric_deltas: dict[str, Decimal]
    latency_relative_delta: Decimal
    cost_relative_delta: Decimal


class OperationalDelta(StrictContract):
    baseline_p95_latency_ms: Decimal
    candidate_p95_latency_ms: Decimal
    p95_latency_relative_delta: Decimal
    baseline_mean_cost_usd: Decimal
    candidate_mean_cost_usd: Decimal
    mean_cost_relative_delta: Decimal


class FailureTaxonomyDelta(StrictContract):
    baseline_critical: tuple[str, ...]
    candidate_critical: tuple[str, ...]
    removed_critical: tuple[str, ...]
    new_critical: tuple[str, ...]
    baseline_codes: tuple[str, ...]
    candidate_codes: tuple[str, ...]
    baseline_code_counts: dict[str, int]
    candidate_code_counts: dict[str, int]
    code_count_deltas: dict[str, int]
    baseline_family_counts: dict[str, int]
    candidate_family_counts: dict[str, int]
    family_count_deltas: dict[str, int]


class GateTrace(StrictContract):
    gate: Literal["gate-1", "gate-2", "gate-3"]
    decision: Literal["PASS", "FAIL", "INVALID"]
    reasons: tuple[str, ...]


class ComparisonArtifact(StrictContract):
    schema_version: Literal["experiment-comparison-artifact-v1"]
    comparison_id: str
    baseline: ExperimentRunSummary
    candidate: ExperimentRunSummary
    compatibility_violations: tuple[str, ...]
    confound_violations: tuple[str, ...]
    case_deltas: tuple[CaseDelta, ...]
    macro_baseline: dict[str, Decimal]
    macro_candidate: dict[str, Decimal]
    macro_deltas: dict[str, Decimal]
    operational_delta: OperationalDelta | None
    failure_taxonomy: FailureTaxonomyDelta
    gates: tuple[GateTrace, ...]
    decision: Literal["PASS", "FAIL", "INVALID"]
    reasons: tuple[str, ...]
    logical_digest: str


def _failure_key(case_id: str, failure: FailureIdentity) -> str:
    return f"{case_id}|{failure.code}|{failure.evaluator_version}"


def _critical_failures(run: ExperimentRunSummary) -> set[str]:
    return {
        _failure_key(case.case_id, failure)
        for case in run.cases
        for failure in case.failures
        if failure.severity == "critical"
    }


def _compatibility_violations(
    baseline: ExperimentRunSummary,
    candidate: ExperimentRunSummary,
) -> tuple[str, ...]:
    violations: list[str] = []
    if baseline.role != "baseline" or candidate.role != "candidate":
        violations.append("SYS-COMPARISON-ROLE-INVALID")
    if baseline.state != "COMPLETED" or candidate.state != "COMPLETED":
        violations.append("SYS-COMPARISON-RUN-INCOMPLETE")
    if baseline.candidate_plan_version != candidate.candidate_plan_version:
        violations.append("SYS-COMPARISON-PLAN-VERSION-MISMATCH")
    left = baseline.provenance
    right = candidate.provenance
    comparable_fields = (
        "evaluation_plane_sha",
        "evaluation_plane_dirty",
        "sut_sha",
        "sut_dirty",
        "dataset_id",
        "dataset_version",
        "dataset_digest",
        "corpus_id",
        "corpus_digest",
        "evaluator_versions",
        "prompt_id",
        "prompt_hash",
        "model_provider",
        "model_name",
        "model_parameters",
        "retrieval_top_k",
        "fixed_retrieval_config_digest",
        "adapter_versions",
        "threshold_version",
        "threshold_digest",
        "dependency_lock_digest",
        "runtime_environment_digest",
        "execution_mode",
    )
    for field_name in comparable_fields:
        if getattr(left, field_name) != getattr(right, field_name):
            violations.append(f"SYS-COMPARISON-{field_name.upper()}-MISMATCH")
    if left.retrieval_top_k != 5 or right.retrieval_top_k != 5:
        violations.append("SYS-COMPARISON-TOP-K-CONTRACT")
    if left.evidence_limit != 3 or right.evidence_limit != 5:
        violations.append("SYS-COMPARISON-EVIDENCE-LIMIT-CONTRACT")
    if (
        left.evaluation_plane_dirty
        or right.evaluation_plane_dirty
        or left.sut_dirty
        or right.sut_dirty
    ):
        violations.append("SYS-COMPARISON-DIRTY-STATE")
    if {case.case_id for case in baseline.cases} != {case.case_id for case in candidate.cases}:
        violations.append("SYS-COMPARISON-CASE-COVERAGE-MISMATCH")
    required_evaluator_keys = {"parsing", "retrieval", "grounded", "operational"}
    required_adapter_keys = {"parsing", "retrieval", "grounded"}
    for run in (baseline, candidate):
        provenance = run.provenance
        if (
            not required_evaluator_keys.issubset(provenance.evaluator_versions)
            or not required_adapter_keys.issubset(provenance.adapter_versions)
            or not provenance.prompt_id
            or not provenance.prompt_hash
            or not provenance.model_provider
            or not provenance.model_name
            or not provenance.threshold_version
            or not provenance.threshold_digest
            or not provenance.corpus_id
            or not provenance.corpus_digest
            or not provenance.dependency_lock_digest
            or not provenance.runtime_environment_digest
        ):
            violations.append("SYS-PROVENANCE-MISSING")
    return tuple(dict.fromkeys(violations))


def _case_pairs(
    baseline: ExperimentRunSummary,
    candidate: ExperimentRunSummary,
) -> tuple[tuple[ExperimentCaseResult, ExperimentCaseResult], ...]:
    candidates = {case.case_id: case for case in candidate.cases}
    return tuple(
        (case, candidates[case.case_id])
        for case in sorted(baseline.cases, key=lambda item: item.case_id)
        if case.case_id in candidates
    )


def _relative_delta(baseline: Decimal, candidate: Decimal) -> Decimal:
    if baseline == 0:
        if candidate == 0:
            return Decimal(0)
        raise ValueError("relative delta requires a non-zero baseline")
    return (candidate - baseline) / baseline


def _macro(cases: tuple[ExperimentCaseResult, ...]) -> dict[str, Decimal]:
    aggregates: dict[str, Decimal] = {}
    for metric in PRIMARY_METRICS:
        values = [case.metrics[metric] for case in cases if metric in case.metrics]
        if values:
            aggregates[metric] = sum(values, start=Decimal(0)) / Decimal(len(values))
    return aggregates


def _p95(values: tuple[Decimal, ...]) -> Decimal:
    ordered = sorted(values)
    return ordered[ceil(Decimal("0.95") * len(ordered)) - 1]


def _confound_violations(
    pairs: tuple[tuple[ExperimentCaseResult, ExperimentCaseResult], ...],
) -> tuple[str, ...]:
    violations: list[str] = []
    for baseline_case, candidate_case in pairs:
        for metric in RETRIEVAL_CONFOUND_METRICS:
            baseline_value = (
                baseline_case.metrics.get(metric)
                if metric == "recall_at_5"
                else baseline_case.retrieval_metrics.get(metric)
            )
            candidate_value = (
                candidate_case.metrics.get(metric)
                if metric == "recall_at_5"
                else candidate_case.retrieval_metrics.get(metric)
            )
            if baseline_value is None or candidate_value is None:
                violations.append(f"SYS-CONFOUND-{metric.upper()}-MISSING:{baseline_case.case_id}")
            elif baseline_value != candidate_value:
                violations.append(f"SYS-CONFOUND-{metric.upper()}:{baseline_case.case_id}")
    return tuple(violations)


def _taxonomy(
    baseline: ExperimentRunSummary,
    candidate: ExperimentRunSummary,
) -> FailureTaxonomyDelta:
    baseline_critical = _critical_failures(baseline)
    candidate_critical = _critical_failures(candidate)
    baseline_code_counts = Counter(
        failure.code for case in baseline.cases for failure in case.failures
    )
    candidate_code_counts = Counter(
        failure.code for case in candidate.cases for failure in case.failures
    )
    baseline_family_counts = Counter(
        failure.code.split("-", maxsplit=1)[0]
        for case in baseline.cases
        for failure in case.failures
    )
    candidate_family_counts = Counter(
        failure.code.split("-", maxsplit=1)[0]
        for case in candidate.cases
        for failure in case.failures
    )
    code_count_deltas = {
        code: candidate_code_counts[code] - baseline_code_counts[code]
        for code in sorted(set(baseline_code_counts) | set(candidate_code_counts))
        if candidate_code_counts[code] != baseline_code_counts[code]
    }
    family_count_deltas = {
        family: candidate_family_counts[family] - baseline_family_counts[family]
        for family in sorted(set(baseline_family_counts) | set(candidate_family_counts))
        if candidate_family_counts[family] != baseline_family_counts[family]
    }
    return FailureTaxonomyDelta(
        baseline_critical=tuple(sorted(baseline_critical)),
        candidate_critical=tuple(sorted(candidate_critical)),
        removed_critical=tuple(sorted(baseline_critical - candidate_critical)),
        new_critical=tuple(sorted(candidate_critical - baseline_critical)),
        baseline_codes=tuple(sorted(baseline_code_counts)),
        candidate_codes=tuple(sorted(candidate_code_counts)),
        baseline_code_counts=dict(sorted(baseline_code_counts.items())),
        candidate_code_counts=dict(sorted(candidate_code_counts.items())),
        code_count_deltas=code_count_deltas,
        baseline_family_counts=dict(sorted(baseline_family_counts.items())),
        candidate_family_counts=dict(sorted(candidate_family_counts.items())),
        family_count_deltas=family_count_deltas,
    )


def _invalid_gates(reasons: tuple[str, ...]) -> tuple[GateTrace, ...]:
    return (
        GateTrace(gate="gate-1", decision="INVALID", reasons=reasons),
        GateTrace(gate="gate-2", decision="INVALID", reasons=reasons),
        GateTrace(gate="gate-3", decision="INVALID", reasons=reasons),
    )


def compare_runs(
    baseline: ExperimentRunSummary,
    candidate: ExperimentRunSummary,
    *,
    comparison_id: str,
) -> ComparisonArtifact:
    compatibility = _compatibility_violations(baseline, candidate)
    pairs = _case_pairs(baseline, candidate)
    confounds = _confound_violations(pairs)
    taxonomy = _taxonomy(baseline, candidate)
    macro_baseline = _macro(baseline.cases)
    macro_candidate = _macro(candidate.cases)
    macro_deltas = {
        metric: macro_candidate[metric] - baseline_value
        for metric, baseline_value in macro_baseline.items()
        if metric in macro_candidate
    }
    case_deltas: list[CaseDelta] = []
    operational: OperationalDelta | None = None
    delta_errors = [
        f"SYS-COMPARISON-METRIC-APPLICABILITY-MISMATCH:{left.case_id}"
        for left, right in pairs
        if set(left.metrics) != set(right.metrics)
    ]
    try:
        case_deltas = [
            CaseDelta(
                case_id=left.case_id,
                metric_deltas={
                    metric: right.metrics[metric] - value
                    for metric, value in left.metrics.items()
                    if metric in right.metrics
                },
                latency_relative_delta=_relative_delta(left.latency_ms, right.latency_ms),
                cost_relative_delta=_relative_delta(left.cost_usd, right.cost_usd),
            )
            for left, right in pairs
        ]
        baseline_p95 = _p95(tuple(case.latency_ms for case in baseline.cases))
        candidate_p95 = _p95(tuple(case.latency_ms for case in candidate.cases))
        baseline_cost = sum((case.cost_usd for case in baseline.cases), start=Decimal(0)) / Decimal(
            len(baseline.cases)
        )
        candidate_cost = sum(
            (case.cost_usd for case in candidate.cases), start=Decimal(0)
        ) / Decimal(len(candidate.cases))
        operational = OperationalDelta(
            baseline_p95_latency_ms=baseline_p95,
            candidate_p95_latency_ms=candidate_p95,
            p95_latency_relative_delta=_relative_delta(baseline_p95, candidate_p95),
            baseline_mean_cost_usd=baseline_cost,
            candidate_mean_cost_usd=candidate_cost,
            mean_cost_relative_delta=_relative_delta(baseline_cost, candidate_cost),
        )
    except ValueError:
        delta_errors.append("SYS-COMPARISON-OPERATIONAL-BASELINE-ZERO")

    missing_metrics = set(PRIMARY_METRICS) - set(macro_deltas)
    if missing_metrics:
        delta_errors.append("SYS-COMPARISON-PRIMARY-METRIC-COVERAGE")
    for metric in PRIMARY_METRICS:
        baseline_denominator = sum(metric in case.metrics for case in baseline.cases)
        candidate_denominator = sum(metric in case.metrics for case in candidate.cases)
        if baseline_denominator != candidate_denominator:
            delta_errors.append(f"SYS-COMPARISON-METRIC-DENOMINATOR-MISMATCH:{metric}")
        if (
            baseline_denominator < VERIFICATION_MINIMUM_DENOMINATORS[metric]
            or candidate_denominator < VERIFICATION_MINIMUM_DENOMINATORS[metric]
        ):
            delta_errors.append(f"SYS-COMPARISON-METRIC-DENOMINATOR-BELOW-MINIMUM:{metric}")
    invalid_reasons = tuple(dict.fromkeys([*compatibility, *confounds, *delta_errors]))
    if invalid_reasons:
        gates = _invalid_gates(invalid_reasons)
        decision: Literal["PASS", "FAIL", "INVALID"] = "INVALID"
        reasons = invalid_reasons
    else:
        gate_1_reasons = (
            ("GATE-1-CANDIDATE-CRITICAL-FAILURE",) if taxonomy.candidate_critical else ()
        )
        gate_1 = GateTrace(
            gate="gate-1",
            decision="FAIL" if gate_1_reasons else "PASS",
            reasons=gate_1_reasons,
        )
        gate_2_reasons = tuple(
            [
                *(
                    f"GATE-2-QUALITY-REGRESSION:{metric}"
                    for metric, delta in macro_deltas.items()
                    if delta < -QUALITY_REGRESSION_LIMIT
                ),
                *(
                    ["GATE-2-LATENCY-REGRESSION"]
                    if operational is not None
                    and operational.p95_latency_relative_delta > LATENCY_REGRESSION_LIMIT
                    else []
                ),
                *(
                    ["GATE-2-COST-REGRESSION"]
                    if operational is not None
                    and operational.mean_cost_relative_delta > COST_REGRESSION_LIMIT
                    else []
                ),
            ]
        )
        gate_2 = GateTrace(
            gate="gate-2",
            decision="FAIL" if gate_2_reasons else "PASS",
            reasons=gate_2_reasons,
        )
        gate_3_reasons: tuple[str, ...]
        if gate_1.decision != "PASS" or gate_2.decision != "PASS":
            gate_3_reasons = ("GATE-3-PRIOR-GATE-FAILED",)
        else:
            positive_evidence = (
                any(delta >= QUALITY_IMPROVEMENT_MINIMUM for delta in macro_deltas.values())
                or bool(taxonomy.removed_critical)
                or (
                    operational is not None
                    and operational.p95_latency_relative_delta <= -LATENCY_IMPROVEMENT_MINIMUM
                )
                or (
                    operational is not None
                    and operational.mean_cost_relative_delta <= -COST_IMPROVEMENT_MINIMUM
                )
            )
            gate_3_reasons = () if positive_evidence else ("GATE-3-NO-POSITIVE-EVIDENCE",)
        gate_3 = GateTrace(
            gate="gate-3",
            decision="FAIL" if gate_3_reasons else "PASS",
            reasons=gate_3_reasons,
        )
        gates = (gate_1, gate_2, gate_3)
        failed_reasons = tuple(reason for gate in gates for reason in gate.reasons)
        decision = "FAIL" if failed_reasons else "PASS"
        reasons = failed_reasons

    digest_payload: dict[str, object] = {
        "baseline": baseline.model_dump(mode="json", exclude={"run_id"}),
        "candidate": candidate.model_dump(mode="json", exclude={"run_id"}),
        "compatibility_violations": compatibility,
        "confound_violations": confounds,
        "case_deltas": [item.model_dump(mode="json") for item in case_deltas],
        "macro_baseline": macro_baseline,
        "macro_candidate": macro_candidate,
        "macro_deltas": macro_deltas,
        "operational_delta": (
            operational.model_dump(mode="json") if operational is not None else None
        ),
        "failure_taxonomy": taxonomy.model_dump(mode="json"),
        "gates": [gate.model_dump(mode="json") for gate in gates],
        "decision": decision,
        "reasons": reasons,
    }
    return ComparisonArtifact(
        schema_version="experiment-comparison-artifact-v1",
        comparison_id=comparison_id,
        baseline=baseline,
        candidate=candidate,
        compatibility_violations=compatibility,
        confound_violations=confounds,
        case_deltas=tuple(case_deltas),
        macro_baseline=macro_baseline,
        macro_candidate=macro_candidate,
        macro_deltas=macro_deltas,
        operational_delta=operational,
        failure_taxonomy=taxonomy,
        gates=gates,
        decision=decision,
        reasons=reasons,
        logical_digest=canonical_digest(
            JSON_OBJECT_ADAPTER.dump_python(digest_payload, mode="json")
        ),
    )
