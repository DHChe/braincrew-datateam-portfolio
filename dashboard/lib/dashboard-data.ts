export type Decision = "PASS" | "FAIL" | "INVALID";
export type GateName = "gate-1" | "gate-2" | "gate-3";

export interface DashboardMetric {
  readonly name: string;
  readonly baseline: string;
  readonly candidate: string;
  readonly delta: string;
}

export interface DashboardFailure {
  readonly code: string;
  readonly severity: "critical" | "major" | "minor" | "diagnostic";
  readonly evaluator_version: string;
}

export interface DashboardOperationalDelta {
  readonly baseline_p95_latency_ms: string;
  readonly candidate_p95_latency_ms: string;
  readonly p95_latency_relative_delta: string;
  readonly baseline_latency_case_count: number;
  readonly candidate_latency_case_count: number;
  readonly baseline_mean_cost_usd: string | null;
  readonly candidate_mean_cost_usd: string | null;
  readonly mean_cost_relative_delta: string | null;
  readonly baseline_cost_case_count: number;
  readonly candidate_cost_case_count: number;
  readonly cost_decision_warrant: {
    readonly status: "included" | "excluded";
    readonly reason:
      | "both runs declare complete cost measurement"
      | "both runs declare cost unmeasured"
      | "cost measurement status differs or is missing";
  };
}

export interface DashboardExport {
  readonly schema_version: "dashboard-export-v1";
  readonly source_schema_version: "experiment-comparison-artifact-v1";
  readonly comparison_id: string;
  readonly decision: Decision;
  readonly logical_digest: string;
  readonly dataset: {
    readonly id: string;
    readonly version: string;
    readonly content_digest: string;
    readonly source_type: "synthetic";
    readonly license: "CC0-1.0";
  };
  readonly baseline: {
    readonly role: "baseline";
    readonly evidence_limit: number;
    readonly execution_mode: "fixture" | "live";
    readonly evaluation_plane_sha: string;
    readonly sut_sha: string;
  };
  readonly candidate: {
    readonly role: "candidate";
    readonly evidence_limit: number;
    readonly execution_mode: "fixture" | "live";
    readonly evaluation_plane_sha: string;
    readonly sut_sha: string;
  };
  readonly totals: {
    readonly case_count: number;
    readonly metric_count: number;
    readonly gate_count: 3;
  };
  readonly metrics: readonly DashboardMetric[];
  readonly operational_delta: DashboardOperationalDelta | null;
  readonly failure_taxonomy: {
    readonly baseline_critical: readonly string[];
    readonly candidate_critical: readonly string[];
    readonly removed_critical: readonly string[];
    readonly new_critical: readonly string[];
    readonly baseline_codes: readonly string[];
    readonly candidate_codes: readonly string[];
    readonly baseline_code_counts: Readonly<Record<string, number>>;
    readonly candidate_code_counts: Readonly<Record<string, number>>;
    readonly code_count_deltas: Readonly<Record<string, number>>;
    readonly baseline_family_counts: Readonly<Record<string, number>>;
    readonly candidate_family_counts: Readonly<Record<string, number>>;
    readonly family_count_deltas: Readonly<Record<string, number>>;
  };
  readonly gates: readonly [
    {
      readonly gate: "gate-1";
      readonly decision: Decision;
      readonly reasons: readonly string[];
    },
    {
      readonly gate: "gate-2";
      readonly decision: Decision;
      readonly reasons: readonly string[];
    },
    {
      readonly gate: "gate-3";
      readonly decision: Decision;
      readonly reasons: readonly string[];
    },
  ];
  readonly reasons: readonly string[];
  readonly cases: readonly {
    readonly case_id: string;
    readonly metrics: readonly DashboardMetric[];
    readonly latency_relative_delta: string | null;
    readonly cost_relative_delta: string | null;
    readonly candidate_failures: readonly DashboardFailure[];
  }[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isDashboardRun(value: unknown, role: "baseline" | "candidate") {
  return (
    isRecord(value) &&
    value.role === role &&
    Number.isInteger(value.evidence_limit) &&
    Number(value.evidence_limit) > 0 &&
    new Set(["fixture", "live"]).has(String(value.execution_mode)) &&
    typeof value.evaluation_plane_sha === "string" &&
    /^[0-9a-f]{40}$/.test(value.evaluation_plane_sha) &&
    typeof value.sut_sha === "string" &&
    /^[0-9a-f]{40}$/.test(value.sut_sha)
  );
}

function isOperationalDelta(
  value: unknown,
): value is DashboardOperationalDelta {
  if (!isRecord(value) || !isRecord(value.cost_decision_warrant)) {
    return false;
  }
  const nullableCostFields = [
    value.baseline_mean_cost_usd,
    value.candidate_mean_cost_usd,
    value.mean_cost_relative_delta,
  ];
  const costsArePresent = nullableCostFields.every(
    (field) => typeof field === "string",
  );
  const costsAreAbsent = nullableCostFields.every((field) => field === null);
  const warrant = value.cost_decision_warrant;
  const warrantMatchesCosts =
    (warrant.status === "included" &&
      warrant.reason === "both runs declare complete cost measurement" &&
      costsArePresent) ||
    (warrant.status === "excluded" &&
      new Set([
        "both runs declare cost unmeasured",
        "cost measurement status differs or is missing",
      ]).has(String(warrant.reason)) &&
      costsAreAbsent);

  return (
    typeof value.baseline_p95_latency_ms === "string" &&
    typeof value.candidate_p95_latency_ms === "string" &&
    typeof value.p95_latency_relative_delta === "string" &&
    Number.isInteger(value.baseline_latency_case_count) &&
    Number(value.baseline_latency_case_count) > 0 &&
    Number.isInteger(value.candidate_latency_case_count) &&
    Number(value.candidate_latency_case_count) > 0 &&
    Number.isInteger(value.baseline_cost_case_count) &&
    Number(value.baseline_cost_case_count) >= 0 &&
    Number.isInteger(value.candidate_cost_case_count) &&
    Number(value.candidate_cost_case_count) >= 0 &&
    warrantMatchesCosts
  );
}

function assertDashboardEnvelope(
  value: unknown,
): asserts value is DashboardExport {
  if (!isRecord(value)) {
    throw new TypeError("dashboard export must be an object");
  }
  if (
    value.schema_version !== "dashboard-export-v1" ||
    value.source_schema_version !== "experiment-comparison-artifact-v1"
  ) {
    throw new TypeError("dashboard export schema is not supported");
  }
  if (!new Set(["PASS", "FAIL", "INVALID"]).has(String(value.decision))) {
    throw new TypeError("dashboard decision is invalid");
  }
  if (
    typeof value.logical_digest !== "string" ||
    !/^sha256:[0-9a-f]{64}$/.test(value.logical_digest)
  ) {
    throw new TypeError("dashboard logical digest is invalid");
  }
  if (!isRecord(value.totals) || value.totals.gate_count !== 3) {
    throw new TypeError(
      "dashboard totals must declare the canonical three gates",
    );
  }
  if (
    !isDashboardRun(value.baseline, "baseline") ||
    !isDashboardRun(value.candidate, "candidate")
  ) {
    throw new TypeError("dashboard run provenance is invalid");
  }
  if (!Array.isArray(value.gates) || value.gates.length !== 3) {
    throw new TypeError(
      "dashboard export must contain the canonical three-gate trace",
    );
  }
  const gateOrder = ["gate-1", "gate-2", "gate-3"];
  if (
    value.gates.some(
      (gate, index) => !isRecord(gate) || gate.gate !== gateOrder[index],
    )
  ) {
    throw new TypeError("dashboard gate trace order is invalid");
  }
  if (!Array.isArray(value.metrics) || !Array.isArray(value.cases)) {
    throw new TypeError("dashboard metric and case evidence must be arrays");
  }
  if (
    value.operational_delta !== null &&
    !isOperationalDelta(value.operational_delta)
  ) {
    throw new TypeError("dashboard operational delta is invalid");
  }
}

function deepFreeze<T>(value: T): T {
  if (typeof value !== "object" || value === null || Object.isFrozen(value)) {
    return value;
  }
  for (const child of Object.values(value as Record<string, unknown>)) {
    deepFreeze(child);
  }
  return Object.freeze(value);
}

export function loadDashboardData(value: unknown): DashboardExport {
  assertDashboardEnvelope(value);
  return deepFreeze(value);
}

export function operationalCostDisplay(
  operational: DashboardOperationalDelta,
): Readonly<{ value: string; context: string }> {
  if (
    operational.candidate_mean_cost_usd === null ||
    operational.mean_cost_relative_delta === null
  ) {
    return {
      value: "Not measured",
      context: operational.cost_decision_warrant.reason,
    };
  }
  const relativeDelta =
    Number(operational.mean_cost_relative_delta) > 0
      ? `+${operational.mean_cost_relative_delta}`
      : operational.mean_cost_relative_delta;
  return {
    value: `$${operational.candidate_mean_cost_usd}`,
    context: `${relativeDelta} relative`,
  };
}

export function taxonomyRows(
  baseline: Readonly<Record<string, number>>,
  candidate: Readonly<Record<string, number>>,
  deltas: Readonly<Record<string, number>>,
) {
  return [
    ...new Set([
      ...Object.keys(baseline),
      ...Object.keys(candidate),
      ...Object.keys(deltas),
    ]),
  ]
    .sort()
    .map((name) => ({
      name,
      baseline: baseline[name] ?? 0,
      candidate: candidate[name] ?? 0,
      delta: deltas[name] ?? 0,
    }));
}

export const dashboardData = loadDashboardData(dashboardExport);
import dashboardExport from "../data/dashboard-export-v1.json";
