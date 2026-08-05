"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { copyFor, type DashboardCopy, type Locale } from "../lib/copy";
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
  locale,
}: Readonly<{ data: DashboardExport; locale: Locale }>) {
  const copy = copyFor(locale);
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
    <main lang={copy.htmlLang}>
      <header className="hero">
        <nav aria-label={copy.navLabel}>
          <span className="wordmark">BRAINCREW / EVALUATION PLANE</span>
          <span className="read-only">{copy.readOnlyBadge}</span>
          <Link className="locale-switch" href={copy.altLocalePath}>
            {copy.altLocaleLabel}
          </Link>
        </nav>
        <div className="hero-grid">
          <div>
            <p className="eyebrow">
              {copy.comparisonEyebrow} {data.comparison_id}
            </p>
            <h1>{copy.heroTitle}</h1>
            <p className="lede">{copy.heroLede}</p>
          </div>
          <div
            className={`decision-card decision-${data.decision.toLowerCase()}`}
          >
            <span>{copy.canonicalDecisionLabel}</span>
            <strong data-testid="canonical-decision">{data.decision}</strong>
            <small>{copy.canonicalDecisionNote}</small>
          </div>
        </div>
        <div className="artifact-strip">
          <span>{copy.publishableCases(data.totals.case_count)}</span>
          <span>{copy.canonicalMetrics(data.totals.metric_count)}</span>
          <span>
            {copy.datasetPrefix} {data.dataset.version}
          </span>
          <span>{data.dataset.license}</span>
        </div>
        <div className="evidence-mode">
          <strong>
            {data.baseline.execution_mode === "fixture"
              ? copy.fixtureEvidenceLabel
              : copy.liveEvidenceLabel}
          </strong>
          <span>Evaluation Plane {data.baseline.evaluation_plane_sha}</span>
          <span>AX SUT {data.baseline.sut_sha}</span>
          {data.baseline.execution_mode === "fixture" ? (
            <p
              className="evidence-mode-reason"
              data-testid="live-comparison-boundary"
            >
              {copy.fixtureBoundaryReason}{" "}
              <a href="https://github.com/DHChe/evidence-first-rag-evaluation/blob/develop/docs/decisions/2026-08-03-same-commit-30-case-run-and-grounded-coverage-correction.md">
                {copy.decisionRecordLink}
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
            <p className="eyebrow">{copy.gateEyebrow}</p>
            <h2 id="trace-title">{copy.gateTitle}</h2>
          </div>
          <p>{copy.gateNote}</p>
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
                    : copy.gateNoReason}
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
            <p className="eyebrow">{copy.comparisonEyebrowLabel}</p>
            <h2 id="comparison-title">{copy.comparisonTitle}</h2>
          </div>
          <div className="run-legend" aria-label={copy.runLegendLabel}>
            <span>
              <i className="baseline-dot" /> {copy.baselineLegendSuffix}{" "}
              {data.baseline.evidence_limit}
            </span>
            <span>
              <i className="candidate-dot" /> {copy.candidateLegendSuffix}{" "}
              {data.candidate.evidence_limit}
            </span>
          </div>
        </div>
        <div className="metric-table-wrap">
          <table>
            <thead>
              <tr>
                <th>{copy.metricColumn}</th>
                <th>Baseline</th>
                <th>Candidate</th>
                <th>{copy.deltaColumn}</th>
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
              <span>{copy.p95LatencyLabel}</span>
              <strong>{operationalDelta.candidate_p95_latency_ms} ms</strong>
              <small>
                {signed(operationalDelta.p95_latency_relative_delta)}{" "}
                {copy.relativeSuffix}
              </small>
            </article>
            <article>
              <span>{copy.meanCostLabel}</span>
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
            <p className="eyebrow">{copy.drilldownEyebrow}</p>
            <h2 id="evidence-title">{copy.drilldownTitle}</h2>
          </div>
          <p>{copy.drilldownNote}</p>
        </div>
        <div
          className="tabs"
          role="tablist"
          aria-label={copy.evidenceViewsLabel}
        >
          <button
            type="button"
            role="tab"
            aria-selected={detailView === "metrics"}
            onClick={() => setDetailView("metrics")}
          >
            {copy.metricEvidenceTab}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={detailView === "taxonomy"}
            onClick={() => setDetailView("taxonomy")}
          >
            {copy.failureTaxonomyTab}
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={detailView === "cases"}
            onClick={() => setDetailView("cases")}
          >
            {copy.caseEvidenceTab}
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
              <p className="empty-state">{copy.emptyTaxonomy}</p>
            ) : (
              <div className="taxonomy-grid">
                <TaxonomyTable
                  title={copy.failureCodesTitle}
                  rows={failureCodeRows}
                  copy={copy}
                />
                <TaxonomyTable
                  title={copy.failureFamiliesTitle}
                  rows={failureFamilyRows}
                  copy={copy}
                />
              </div>
            )}
          </div>
        ) : null}

        {detailView === "cases" ? (
          <div className="evidence-panel cases-panel">
            <label htmlFor="case-query">{copy.caseQueryLabel}</label>
            <input
              id="case-query"
              value={caseQuery}
              onChange={(event) => setCaseQuery(event.target.value)}
              placeholder="CASE-001"
            />
            <div className="case-list">
              {matchingCases.map((item) => (
                <details key={item.case_id}>
                  <summary
                    aria-label={`${item.case_id} ${copy.caseDetailsSuffix}`}
                  >
                    <span>{item.case_id}</span>
                    <span>
                      {copy.caseFailures(item.candidate_failures.length)}
                    </span>
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
          <span>{copy.logicalDigestLabel}</span>
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
  copy,
}: Readonly<{
  title: string;
  rows: readonly {
    name: string;
    baseline: number;
    candidate: number;
    delta: number;
  }[];
  copy: DashboardCopy;
}>) {
  return (
    <div className="taxonomy-table">
      <h3>{title}</h3>
      <table>
        <thead>
          <tr>
            <th>{copy.nameColumn}</th>
            <th>Baseline</th>
            <th>Candidate</th>
            <th>{copy.deltaColumn}</th>
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
