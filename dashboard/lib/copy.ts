/**
 * User-facing copy for the dashboard, one entry per locale.
 *
 * Only prose the dashboard itself authors belongs here. Values that come from
 * the artifact — the decision (`PASS`), metric names, gate names, digests, case
 * identifiers, dataset version and license — are rendered as exported and are
 * never translated, because the page claims they are rendered exactly as
 * exported.
 */
export type Locale = "en" | "ko";

export type DashboardCopy = {
  readonly htmlLang: string;
  readonly altLocalePath: string;
  readonly altLocaleLabel: string;
  readonly navLabel: string;
  readonly readOnlyBadge: string;
  readonly comparisonEyebrow: string;
  readonly heroTitle: string;
  readonly heroLede: string;
  readonly canonicalDecisionLabel: string;
  readonly canonicalDecisionNote: string;
  readonly publishableCases: (count: number) => string;
  readonly canonicalMetrics: (count: number) => string;
  readonly datasetPrefix: string;
  readonly fixtureEvidenceLabel: string;
  readonly liveEvidenceLabel: string;
  readonly fixtureBoundaryReason: string;
  readonly decisionRecordLink: string;
  readonly gateEyebrow: string;
  readonly gateTitle: string;
  readonly gateNote: string;
  readonly gateNoReason: string;
  readonly comparisonEyebrowLabel: string;
  readonly comparisonTitle: string;
  readonly runLegendLabel: string;
  readonly baselineLegendSuffix: string;
  readonly candidateLegendSuffix: string;
  readonly metricColumn: string;
  readonly nameColumn: string;
  readonly deltaColumn: string;
  readonly p95LatencyLabel: string;
  readonly meanCostLabel: string;
  readonly relativeSuffix: string;
  readonly drilldownEyebrow: string;
  readonly drilldownTitle: string;
  readonly drilldownNote: string;
  readonly evidenceViewsLabel: string;
  readonly metricEvidenceTab: string;
  readonly failureTaxonomyTab: string;
  readonly caseEvidenceTab: string;
  readonly emptyTaxonomy: string;
  readonly failureCodesTitle: string;
  readonly failureFamiliesTitle: string;
  readonly caseQueryLabel: string;
  readonly caseFailures: (count: number) => string;
  readonly caseDetailsSuffix: string;
  readonly logicalDigestLabel: string;
};

export const enCopy: DashboardCopy = {
  htmlLang: "en",
  altLocalePath: "/ko/",
  altLocaleLabel: "한국어",
  navLabel: "Dashboard context",
  readOnlyBadge: "READ-ONLY ARTIFACT",
  comparisonEyebrow: "Comparison",
  heroTitle: "Release evidence, without the rerun.",
  heroLede:
    "One immutable comparison, projected for review. The dashboard can reveal evidence, but it cannot execute an experiment or alter a canonical result.",
  canonicalDecisionLabel: "Canonical decision",
  canonicalDecisionNote: "Copied from the replay-validated artifact",
  publishableCases: (count) => `${count} publishable cases`,
  canonicalMetrics: (count) => `${count} canonical metrics`,
  datasetPrefix: "Dataset",
  fixtureEvidenceLabel: "Fixture evidence — not a live AX verification",
  liveEvidenceLabel: "Live verification evidence",
  fixtureBoundaryReason:
    "This PASS is a fixture-gate result, not a live release verdict: both same-commit live runs are INVALID after 13 of 15 grounded answers were discarded for citation-contract violations, leaving no answer-quality evidence.",
  decisionRecordLink: "Decision record",
  gateEyebrow: "Release gate",
  gateTitle: "Three checks. One recorded verdict.",
  gateNote: "Gate order and decisions are rendered exactly as exported.",
  gateNoReason: "No blocking reason recorded.",
  comparisonEyebrowLabel: "Baseline / candidate",
  comparisonTitle: "The measured change",
  runLegendLabel: "Run evidence limits",
  baselineLegendSuffix: "Baseline · top",
  candidateLegendSuffix: "Candidate · top",
  metricColumn: "Metric",
  nameColumn: "Name",
  deltaColumn: "Delta",
  p95LatencyLabel: "P95 latency",
  meanCostLabel: "Mean cost",
  relativeSuffix: "relative",
  drilldownEyebrow: "Drill-down",
  drilldownTitle: "Trace the decision to evidence",
  drilldownNote:
    "Synthetic, CC0-licensed identifiers only. No source document text is published.",
  evidenceViewsLabel: "Evidence views",
  metricEvidenceTab: "Metric evidence",
  failureTaxonomyTab: "Failure taxonomy",
  caseEvidenceTab: "Case evidence",
  emptyTaxonomy: "No candidate failures in this verified artifact.",
  failureCodesTitle: "Failure codes",
  failureFamiliesTitle: "Failure families",
  caseQueryLabel: "Find case evidence",
  caseFailures: (count) => `${count} failures`,
  caseDetailsSuffix: "details",
  logicalDigestLabel: "Logical digest",
};

export const koCopy: DashboardCopy = {
  htmlLang: "ko",
  altLocalePath: "/",
  altLocaleLabel: "English",
  navLabel: "대시보드 정보",
  readOnlyBadge: "읽기 전용 아티팩트",
  comparisonEyebrow: "비교",
  heroTitle: "재실행 없이 확인하는 릴리스 근거.",
  heroLede:
    "변경할 수 없는 비교 결과 하나를 검토용으로 보여줍니다. 이 대시보드는 근거를 드러낼 수 있을 뿐, 실험을 실행하거나 정규 결과를 바꿀 수 없습니다.",
  canonicalDecisionLabel: "정규 판정",
  canonicalDecisionNote: "재현 검증을 마친 아티팩트에서 그대로 옮긴 값",
  publishableCases: (count) => `공개 가능 사례 ${count}건`,
  canonicalMetrics: (count) => `정규 지표 ${count}개`,
  datasetPrefix: "데이터셋",
  fixtureEvidenceLabel:
    "고정 예제(fixture) 근거 — 라이브 AX 검증 결과가 아닙니다",
  liveEvidenceLabel: "라이브 검증 근거",
  fixtureBoundaryReason:
    "이 PASS는 고정 예제 게이트의 결과이며 라이브 릴리스 판정이 아닙니다. 같은 커밋에서 실행한 두 번의 라이브 실행은 모두 INVALID였고, 근거 기반 답변 15건 중 13건이 인용 계약 위반으로 폐기되어 답변 품질을 판단할 근거가 남지 않았습니다.",
  decisionRecordLink: "결정 기록",
  gateEyebrow: "릴리스 게이트",
  gateTitle: "세 단계 점검, 하나의 기록된 판정.",
  gateNote: "게이트 순서와 판정은 내보낸 그대로 표시합니다.",
  gateNoReason: "차단 사유가 기록되지 않았습니다.",
  comparisonEyebrowLabel: "Baseline / candidate",
  comparisonTitle: "측정된 변화",
  runLegendLabel: "실행별 근거 상한",
  baselineLegendSuffix: "Baseline · 상위",
  candidateLegendSuffix: "Candidate · 상위",
  metricColumn: "지표",
  nameColumn: "이름",
  deltaColumn: "변화량",
  p95LatencyLabel: "P95 지연시간",
  meanCostLabel: "평균 비용",
  relativeSuffix: "상대 변화",
  drilldownEyebrow: "상세 보기",
  drilldownTitle: "판정을 근거까지 추적하기",
  drilldownNote:
    "합성 데이터의 CC0 라이선스 식별자만 표시하며, 원본 문서 본문은 공개하지 않습니다.",
  evidenceViewsLabel: "근거 보기 방식",
  metricEvidenceTab: "지표 근거",
  failureTaxonomyTab: "실패 분류",
  caseEvidenceTab: "사례 근거",
  emptyTaxonomy: "검증된 이 아티팩트에는 candidate 실패가 없습니다.",
  failureCodesTitle: "실패 코드",
  failureFamiliesTitle: "실패 계열",
  caseQueryLabel: "사례 근거 찾기",
  caseFailures: (count) => `실패 ${count}건`,
  caseDetailsSuffix: "상세",
  logicalDigestLabel: "논리 다이제스트",
};

/**
 * Resolved inside the client component rather than passed in as a prop: this
 * copy carries count-formatting functions, and functions cannot cross the
 * server/client boundary. Pages hand over the locale identifier instead.
 */
export function copyFor(locale: Locale): DashboardCopy {
  return locale === "ko" ? koCopy : enCopy;
}
