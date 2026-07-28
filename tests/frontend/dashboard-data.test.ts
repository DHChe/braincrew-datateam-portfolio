import { describe, expect, it } from "vitest";

import {
  loadDashboardData,
  operationalCostDisplay,
  taxonomyRows,
} from "../../dashboard/lib/dashboard-data";
import dashboardExport from "../../dashboard/data/dashboard-export-v1.json";

const unmeasuredOperationalDelta = {
  baseline_p95_latency_ms: "100",
  candidate_p95_latency_ms: "100",
  p95_latency_relative_delta: "0",
  baseline_latency_case_count: 9,
  candidate_latency_case_count: 9,
  baseline_mean_cost_usd: null,
  candidate_mean_cost_usd: null,
  mean_cost_relative_delta: null,
  baseline_cost_case_count: 0,
  candidate_cost_case_count: 0,
  cost_decision_warrant: {
    status: "excluded",
    reason: "both runs declare cost unmeasured",
  },
} as const;

const goldenExport = {
  schema_version: "dashboard-export-v1",
  source_schema_version: "experiment-comparison-artifact-v1",
  comparison_id: "dashboard-golden",
  decision: "PASS",
  logical_digest: `sha256:${"a".repeat(64)}`,
  dataset: {
    id: "braincrew-evaluation-dataset",
    version: "1.0.0",
    content_digest: `sha256:${"b".repeat(64)}`,
    source_type: "synthetic",
    license: "CC0-1.0",
  },
  baseline: {
    role: "baseline",
    evidence_limit: 3,
    execution_mode: "fixture",
    evaluation_plane_sha: "a".repeat(40),
    sut_sha: "b".repeat(40),
  },
  candidate: {
    role: "candidate",
    evidence_limit: 5,
    execution_mode: "fixture",
    evaluation_plane_sha: "a".repeat(40),
    sut_sha: "b".repeat(40),
  },
  totals: { case_count: 15, metric_count: 6, gate_count: 3 },
  metrics: [
    {
      name: "claim_support_precision",
      baseline: "0.80",
      candidate: "0.83",
      delta: "0.03",
    },
  ],
  operational_delta: unmeasuredOperationalDelta,
  failure_taxonomy: {
    baseline_critical: [],
    candidate_critical: [],
    removed_critical: [],
    new_critical: [],
    baseline_codes: [],
    candidate_codes: [],
    baseline_code_counts: {},
    candidate_code_counts: {},
    code_count_deltas: {},
    baseline_family_counts: {},
    candidate_family_counts: {},
    family_count_deltas: {},
  },
  gates: [
    { gate: "gate-1", decision: "PASS", reasons: [] },
    { gate: "gate-2", decision: "PASS", reasons: [] },
    { gate: "gate-3", decision: "PASS", reasons: [] },
  ],
  reasons: [],
  cases: [
    {
      case_id: "CASE-001",
      metrics: [
        {
          name: "claim_support_precision",
          baseline: "0.80",
          candidate: "0.83",
          delta: "0.03",
        },
      ],
      latency_relative_delta: "0",
      cost_relative_delta: "0",
      candidate_failures: [],
    },
  ],
} as const;

describe("loadDashboardData", () => {
  it("preserves and freezes canonical totals, digest, and gate decisions", () => {
    const dashboard = loadDashboardData(goldenExport);

    expect(dashboard.decision).toBe(goldenExport.decision);
    expect(dashboard.logical_digest).toBe(goldenExport.logical_digest);
    expect(dashboard.totals).toEqual(goldenExport.totals);
    expect(dashboard.gates).toEqual(goldenExport.gates);
    expect(Object.isFrozen(dashboard)).toBe(true);
    expect(Object.isFrozen(dashboard.metrics)).toBe(true);
    expect(Object.isFrozen(dashboard.gates[0])).toBe(true);
    expect(Object.isFrozen(dashboard.cases[0].metrics)).toBe(true);
  });

  it("loads the checked-in golden export without changing canonical outcomes", () => {
    const dashboard = loadDashboardData(dashboardExport);

    expect(dashboard.logical_digest).toBe(
      "sha256:d426e04c0c2b960d8c8c17efc216688891b2078faaaa51ff226c137c2f8694ae",
    );
    expect(dashboard.decision).toBe("PASS");
    expect(dashboard.totals).toEqual({
      case_count: 15,
      gate_count: 3,
      metric_count: 6,
    });
    expect(dashboard.gates.map(({ decision }) => decision)).toEqual([
      "PASS",
      "PASS",
      "PASS",
    ]);
    const operational = dashboard.operational_delta;
    expect(operational).not.toBeNull();
    if (operational === null) {
      throw new Error(
        "checked-in dashboard export omitted operational evidence",
      );
    }
    expect(operationalCostDisplay(operational)).toEqual({
      value: "Not measured",
      context: "both runs declare cost unmeasured",
    });
  });

  it("keeps excluded cost absent and explains the recorded exclusion", () => {
    const dashboard = loadDashboardData(goldenExport);

    expect(dashboard.operational_delta).not.toBeNull();
    expect(operationalCostDisplay(unmeasuredOperationalDelta)).toEqual({
      value: "Not measured",
      context: "both runs declare cost unmeasured",
    });
  });

  it("accepts and renders a measured cost when one is actually reported", () => {
    const operational_delta = {
      ...unmeasuredOperationalDelta,
      baseline_mean_cost_usd: "0.010",
      candidate_mean_cost_usd: "0.010",
      mean_cost_relative_delta: "0",
      baseline_cost_case_count: 9,
      candidate_cost_case_count: 9,
      cost_decision_warrant: {
        status: "included",
        reason: "both runs declare complete cost measurement",
      },
    } as const;

    const dashboard = loadDashboardData({ ...goldenExport, operational_delta });

    expect(dashboard.operational_delta).not.toBeNull();
    expect(operationalCostDisplay(operational_delta)).toEqual({
      value: "$0.010",
      context: "0 relative",
    });
    expect(
      operationalCostDisplay({
        ...operational_delta,
        mean_cost_relative_delta: "0.04",
      }),
    ).toEqual({ value: "$0.010", context: "+0.04 relative" });
  });

  it("rejects an operational payload that contradicts its cost warrant", () => {
    const operational_delta = {
      ...unmeasuredOperationalDelta,
      cost_decision_warrant: {
        status: "included",
        reason: "both runs declare complete cost measurement",
      },
    } as const;

    expect(() =>
      loadDashboardData({ ...goldenExport, operational_delta }),
    ).toThrow("dashboard operational delta is invalid");
  });

  it("rejects a display payload that omits canonical execution provenance", () => {
    const baseline = Object.fromEntries(
      Object.entries(goldenExport.baseline).filter(
        ([key]) => key !== "execution_mode",
      ),
    );

    expect(() => loadDashboardData({ ...goldenExport, baseline })).toThrow(
      "dashboard run provenance is invalid",
    );
  });
});

describe("taxonomyRows", () => {
  it("projects canonical code counts and deltas without reclassifying failures", () => {
    expect(
      taxonomyRows(
        { "R-MISSED-EVIDENCE": 2 },
        { "R-MISSED-EVIDENCE": 1, "A-UNSUPPORTED-CLAIM": 1 },
        { "R-MISSED-EVIDENCE": -1, "A-UNSUPPORTED-CLAIM": 1 },
      ),
    ).toEqual([
      { name: "A-UNSUPPORTED-CLAIM", baseline: 0, candidate: 1, delta: 1 },
      { name: "R-MISSED-EVIDENCE", baseline: 2, candidate: 1, delta: -1 },
    ]);
  });
});
