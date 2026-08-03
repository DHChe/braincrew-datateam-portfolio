"use client";

import { useMemo, useState } from "react";

import {
  operationalCostDisplay,
  taxonomyRows,
  type DashboardExport,
  type DashboardMetric,
} from "../lib/dashboard-data";

type DetailView = "metrics" | "taxonomy" | "cases";

const gateLabels = {
  "gate-1": "Compatibility",
  "gate-2": "Quality & safety",
  "gate-3": "Operational",
} as const;

function humanize(value: string) {
  return value.replaceAll("_", " ");
}

function signed(value: string) {
  const numeric = Number(value);
  return numeric > 0 ? `+${value}` : value;
}

function metricTone(metric: DashboardMetric) {
  const delta = Number(metric.delta);
  if (delta > 0) return "positive";
  if (delta < 0) return "negative";
  return "neutral";
}

export function DashboardExplorer({
  data,
}: Readonly<{ data: DashboardExport }>) {
  const [detailView, setDetailView] = useState<DetailView>("metrics");
  const [caseQuery, setCaseQuery] = useState("");
  const matchingCases = useMemo(
    () =>
      data.cases.filter(({ case_id }) =>
        case_id.toLowerCase().includes(caseQuery.toLowerCase()),
      ),
    [caseQuery, data.cases],
  );
  const failureCodeRows = taxonomyRows(
    data.failure_taxonomy.baseline_code_counts,
    data.failure_taxonomy.candidate_code_counts,
    data.failure_taxonomy.code_count_deltas,
  );
  const failureFamilyRows = taxonomyRows(
    data.failure_taxonomy.baseline_family_counts,
    data.failure_taxonomy.candidate_family_counts,
    data.failure_taxonomy.family_count_deltas,
  );
  const operationalDelta = data.operational_delta;
  const costDisplay = operationalDelta
    ? operationalCostDisplay(operationalDelta)
    : null;

  return (
    <main>
      <header className="hero">
        <nav aria-label="Dashboard context">
          <span className="wordmark">BRAINCREW / EVALUATION PLANE</span>
          <span className="read-only">READ-ONLY ARTIFACT</span>
        </nav>
        <div className="hero-grid">
          <div>
            <p className="eyebrow">Comparison {data.comparison_id}</p>
            <h1>Release evidence, without the rerun.</h1>
            <p className="lede">
              One immutable comparison, projected for review. The dashboard can
              reveal evidence, but it cannot execute an experiment or alter a
              canonical result.
            </p>
          </div>
          <div
            className={`decision-card decision-${data.decision.toLowerCase()}`}
          >
            <span>Canonical decision</span>
            <strong data-testid="canonical-decision">{data.decision}</strong>
            <small>Copied from the replay-validated artifact</small>
          </div>
        </div>
        <div className="artifact-strip">
          <span>{data.totals.case_count} publishable cases</span>
          <span>{data.totals.metric_count} canonical metrics</span>
          <span>Dataset {data.dataset.version}</span>
          <span>{data.dataset.license}</span>
        </div>
        <div className="evidence-mode">
          <strong>
            {data.baseline.execution_mode === "fixture"
              ? "Fixture evidence — not a live AX verification"
              : "Live verification evidence"}
          </strong>
          <span>Evaluation Plane {data.baseline.evaluation_plane_sha}</span>
          <span>AX SUT {data.baseline.sut_sha}</span>
          {data.baseline.execution_mode === "fixture" ? (
            <p
              className="evidence-mode-reason"
              data-testid="live-comparison-boundary"
            >
              This PASS is a fixture-gate result, not a live release verdict:
              both same-commit live runs are INVALID after 13 of 15 grounded
              answers were discarded for citation-contract violations, leaving
              no answer-quality evidence.{" "}
              <a href="https://github.com/DHChe/braincrew-datateam-portfolio/blob/develop/docs/decisions/2026-08-03-same-commit-30-case-run-and-grounded-coverage-correction.md">
                Decision record
              </a>
            </p>
          ) : null}
        </div>
      </header>

      <section
        className="content-section trace-section"
        aria-labelledby="trace-title"
      >
        <div className="section-heading">
          <div>
            <p className="eyebrow">Release gate</p>
            <h2 id="trace-title">Three checks. One recorded verdict.</h2>
          </div>
          <p>Gate order and decisions are rendered exactly as exported.</p>
        </div>
        <ol className="gate-grid">
          {data.gates.map((gate, index) => (
            <li key={gate.gate} data-testid="release-gate">
              <div className="gate-number">0{index + 1}</div>
              <div>
                <span className="gate-label">{gateLabels[gate.gate]}</span>
                <strong>{gate.decision}</strong>
                <p>
                  {gate.reasons.length
                    ? gate.reasons.join(" · ")
                    : "No blocking reason recorded."}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      <section
        className="content-section comparison-section"
        aria-labelledby="comparison-title"
      >
        <div className="section-heading">
          <div>
            <p className="eyebrow">Baseline / candidate</p>
            <h2 id="comparison-title">The measured change</h2>
          </div>
          <div className="run-legend" aria-label="Run evidence limits">
            <span>
              <i className="baseline-dot" /> Baseline · top{" "}
              {data.baseline.evidence_limit}
            </span>
            <span>
              <i className="candidate-dot" /> Candidate · top{" "}
              {data.candidate.evidence_limit}
            </span>
          </div>
        </div>
        <div className="metric-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Metric</th>
                <th>Baseline</th>
                <th>Candidate</th>
                <th>Delta</th>
              </tr>
            </thead>
            <tbody>
              {data.metrics.map((metric) => (
                <tr key={metric.name} aria-label={humanize(metric.name)}>
                  <th scope="row">{humanize(metric.name)}</th>
                  <td>{metric.baseline}</td>
                  <td>{metric.candidate}</td>
                  <td className={metricTone(metric)}>{signed(metric.delta)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {operationalDelta && costDisplay ? (
          <div className="operational-grid">
            <article>
              <span>P95 latency</span>
              <strong>{operationalDelta.candidate_p95_latency_ms} ms</strong>
              <small>
                {signed(operationalDelta.p95_latency_relative_delta)} relative
              </small>
            </article>
            <article>
              <span>Mean cost</span>
              <strong>{costDisplay.value}</strong>
              <small>{costDisplay.context}</small>
            </article>
          </div>
        ) : null}
      </section>

      <section
        className="content-section evidence-section"
        aria-labelledby="evidence-title"
      >
        <div className="section-heading">
          <div>
            <p className="eyebrow">Drill-down</p>
            <h2 id="evidence-title">Trace the decision to evidence</h2>
          </div>
          <p>
            Synthetic, CC0-licensed identifiers only. No source document text is
            published.
          </p>
        </div>
        <div className="tabs" role="tablist" aria-label="Evidence views">
          <button
            type="button"
            role="tab"
            aria-selected={detailView === "metrics"}
            onClick={() => setDetailView("metrics")}
          >
            Metric evidence
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={detailView === "taxonomy"}
            onClick={() => setDetailView("taxonomy")}
          >
            Failure taxonomy
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={detailView === "cases"}
            onClick={() => setDetailView("cases")}
          >
            Case evidence
          </button>
        </div>

        {detailView === "metrics" ? (
          <div className="evidence-panel metric-cards">
            {data.metrics.map((metric) => (
              <article key={metric.name}>
                <span>{humanize(metric.name)}</span>
                <strong className={metricTone(metric)}>
                  {signed(metric.delta)}
                </strong>
                <small>
                  {metric.baseline} → {metric.candidate}
                </small>
              </article>
            ))}
          </div>
        ) : null}

        {detailView === "taxonomy" ? (
          <div className="evidence-panel taxonomy-panel">
            {failureCodeRows.length === 0 ? (
              <p className="empty-state">
                No candidate failures in this verified artifact.
              </p>
            ) : (
              <div className="taxonomy-grid">
                <TaxonomyTable title="Failure codes" rows={failureCodeRows} />
                <TaxonomyTable
                  title="Failure families"
                  rows={failureFamilyRows}
                />
              </div>
            )}
          </div>
        ) : null}

        {detailView === "cases" ? (
          <div className="evidence-panel cases-panel">
            <label htmlFor="case-query">Find case evidence</label>
            <input
              id="case-query"
              value={caseQuery}
              onChange={(event) => setCaseQuery(event.target.value)}
              placeholder="CASE-001"
            />
            <div className="case-list">
              {matchingCases.map((item) => (
                <details key={item.case_id}>
                  <summary aria-label={`${item.case_id} details`}>
                    <span>{item.case_id}</span>
                    <span>{item.candidate_failures.length} failures</span>
                  </summary>
                  <div
                    className="case-detail"
                    data-testid={`case-detail-${item.case_id}`}
                  >
                    {item.metrics.map((metric) => (
                      <p key={metric.name}>
                        <span>{humanize(metric.name)}</span>
                        <strong>{signed(metric.delta)}</strong>
                      </p>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          </div>
        ) : null}
      </section>

      <footer>
        <div>
          <span>Logical digest</span>
          <code data-testid="logical-digest">{data.logical_digest}</code>
        </div>
        <p>
          {data.dataset.id} · {data.dataset.content_digest}
        </p>
      </footer>
    </main>
  );
}

function TaxonomyTable({
  title,
  rows,
}: Readonly<{
  title: string;
  rows: readonly {
    name: string;
    baseline: number;
    candidate: number;
    delta: number;
  }[];
}>) {
  return (
    <div className="taxonomy-table">
      <h3>{title}</h3>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Baseline</th>
            <th>Candidate</th>
            <th>Delta</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.name}>
              <th scope="row">{row.name}</th>
              <td>{row.baseline}</td>
              <td>{row.candidate}</td>
              <td>{row.delta > 0 ? `+${row.delta}` : row.delta}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
