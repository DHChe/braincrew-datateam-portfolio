import { describe, expect, it } from "vitest";

import {
  loadDashboardData,
  taxonomyRows,
} from "../../dashboard/lib/dashboard-data";
import dashboardExport from "../../dashboard/data/dashboard-export-v1.json";

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
  operational_delta: null,
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
      "sha256:f8630e70892f976ee120ac497ef63ce6cc64add8aa1d71989a576891b5ae7bbe",
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
