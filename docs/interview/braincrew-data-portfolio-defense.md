# Braincrew Data Portfolio — Interview Defense Dossier

Status: Living document  
Audience: Candidate preparing for Braincrew Data Team technical and deep-dive interviews

## Purpose

This dossier turns every locked portfolio decision into interview-ready reasoning. It must evolve with the design, implementation, experiments, and final submission. A decision is not interview-ready until it records what was chosen, why, what was rejected, what could fail, and what evidence supports the claim.

Canonical sources:

- [Locked scope and design decisions](../decisions/2026-07-18-evaluation-scope-and-skill-flow-lock.md)
- [Braincrew Data role and hackathon benchmark](../research/braincrew-data-role-and-hackathon-benchmark.md)
- [Data Team growth red-team assessment](../research/braincrew-data-team-growth-red-team-2026-07-18.md)
- [Open-role and AX relevance comparison](../research/braincrew-open-roles-ax-closeness.md)

## Core interview narrative

### 30-second answer

AX_portfolio는 인사·노무 문서에 근거해 답변하는 제품이지만 아직 진화 중입니다. 저는 완성된 제품인 척 기능을 늘리는 대신, 별도의 Evaluation Plane을 만들어 파싱·검색·근거 기반 답변의 품질을 버전이 고정된 데이터셋으로 측정하고, 실패 유형과 baseline-candidate 비교, release gate를 도입했습니다. Agent trajectory로 확장 가능한 계약은 설계했지만 실제 검증하지 않은 Agent 평가는 주장하지 않습니다.

### Two-minute architecture answer

Evaluation Plane은 AX_portfolio와 별도 저장소에 있으며 HTTP SUT Adapter로 연결됩니다. Dataset Registry가 버전이 고정된 케이스를 제공하고, Experiment Runner가 정확한 SUT SHA와 데이터셋·evaluator·prompt·model 버전을 기록하며 실행합니다. Adapter는 AX 응답을 표준 observation으로 변환할 뿐 점수를 계산하지 않습니다. 결정론적 evaluator가 파싱, retrieval, grounded answer, visibility와 operational 품질을 측정하고, 결과는 append-only로 저장됩니다. 동일한 계약을 사용하는 baseline과 candidate만 비교하며, 명시적 release gate가 회귀를 차단합니다. 대시보드는 이 증거를 읽어 설명하지만 점수나 원본 결과를 수정하지 않습니다.

## Decision defense cards

### D1. Evaluate the evolving AX product instead of pretending it is complete

Decision:
: Treat AX_portfolio as the evolving SUT and evaluate only available capabilities.

Why:
: Braincrew's Data role emphasizes evaluation datasets, quality monitoring, RAG and Agent quality, and practical AI engineering. Measuring a real evolving system demonstrates those capabilities more directly than adding another shallow feature.

Rejected alternative:
: Finish every AX feature before beginning evaluation. This would consume the ten-day window and still provide weak evidence about quality.

Trade-off:
: Some product capabilities will remain `planned` or `not evaluated`, making the submission narrower but more defensible.

Evidence required before interview:
: Final SUT SHA, available endpoint inventory, evaluated-capability matrix, and explicit exclusion list.

Likely follow-up:
: "Does evaluating an unfinished product produce meaningful results?"

Answer direction:
: Yes, if the evaluated contract, SUT version, dataset version, and unavailable scope are explicit. The benchmark establishes a reproducible baseline rather than claiming product completion.

### D2. Use a separate Evaluation Plane repository with an HTTP SUT Adapter

Decision:
: `braincrew-datateam-portfolio` owns evaluation evidence; AX_portfolio remains the product SUT.

Why:
: Separate histories prevent evaluation logic from depending on AX internals and make the submission independently reviewable.

Rejected alternative:
: Import AX modules directly into the evaluator. This would create version coupling, make live-service behavior harder to reproduce, and blur product and measurement responsibilities.

Trade-off:
: Reproduction must start or reach two repositories. The mitigation is a pinned SUT SHA, documented HTTP contract, health checks, and one-command orchestration.

Failure modes:
: API drift, missing observability fields, timeouts, partial responses, and an adapter that silently invents missing values.

Evidence required before interview:
: Adapter contract tests, one live run, one deterministic fixture replay, captured version manifest, and an example of an explicit missing field.

### D3. Use bounded component responsibilities and one-way evidence flow

Decision:
: Dataset Registry → Runner → Adapter → Observation → Evaluators → Result Store → Comparison/Gate → Dashboard.

Why:
: A component should either produce observations, evaluate them, store them, or present them. Combining those roles makes results difficult to audit and easy to manipulate accidentally.

Rejected alternative:
: A notebook or dashboard that calls AX, scores responses, and renders conclusions in one place. It is fast initially but weak in reproducibility, testing, and provenance.

Critical invariants:
: Adapter does not score; runner does not own metrics; missing fields stay missing; published results are immutable; dashboard cannot rewrite evidence.

Evidence required before interview:
: Contract diagram, unit tests at every boundary, immutable run manifest, and a failed invalid-comparison example.

### D4. Use 100 structured cases with a 70/30 calibration-verification split

Decision:
: Build exactly 100 cases: 70 Calibration and 30 Verification.

Why 100:
: It is large enough to contain parsing, retrieval, answer, visibility, abstention, and adversarial variation while remaining feasible to author and review within ten days. It is an engineering benchmark target, not a claim of statistical population coverage.

Why 70/30:
: Evaluator and threshold development needs visible examples, while a frozen set is needed to detect whether improvements generalize beyond the cases used for tuning.

Why call it Verification rather than secret holdout:
: The repository is public and reproducible. The defensible claim is that the split and digest were frozen before final candidate tuning, not that nobody can inspect it.

Case focus allocation:
: 20 parsing, 30 retrieval, 40 grounded answer, and 10 visibility or abstention cases. The frozen Calibration/Verification allocation is 14/6, 21/9, 30/10, and 5/5 respectively. Operational metrics run across compatible live cases.

Rejected alternative:
: Use a small set of hand-picked success examples. It would encourage cherry-picking and provide little failure coverage.

Failure modes:
: ambiguous expected evidence, duplicate cases, leakage between splits, undocumented corpus changes, thresholds tuned on Verification, and reference answers that allow unsupported claims.

Evidence required before interview:
: Dataset manifest, schema validation, content digest, split assignment, distribution report, provenance report, and representative passing and failing cases.

Likely follow-ups:

- "Is 100 statistically sufficient?" — It is a scoped engineering regression suite, not a population estimate; claims remain bounded to this dataset.
- "How did you prevent leakage?" — Freeze split and digest, prohibit final tuning on Verification, and version any correction.
- "Why not use only LLM-generated labels?" — Expected evidence and safety constraints require deterministic reviewable contracts; LLM assistance cannot be the sole authority.
- "What if a metric has too few applicable Verification cases?" — The run becomes invalid under the frozen minimum-denominator contract; it does not publish a misleading average.

### D5. Reserve trajectory extension points without claiming Agent evaluation

Decision:
: Schema target types may later include trajectory observations and evaluators; the first release registers none.

Why:
: It avoids a dead-end schema while keeping submission claims honest.

Rejected alternative:
: Add a superficial Agent benchmark without a real Agent execution path and trace contract. This would optimize wording rather than evidence.

Evidence required before interview:
: Schema extension example marked `planned`, absence of registered trajectory evaluators, and submission wording that explicitly excludes Agent evaluation.

### D6. Use layered metrics and a three-gate release policy

Decision:
: Separate parsing, retrieval, grounded-answer, and operational metrics, then require hard-safety, regression, and positive-evidence gates in order.

Why:
: A single aggregate score can hide a critical leak or unsafe answer. Layered metrics locate the failure mechanism, while ordered gates prevent an average quality gain from compensating for an unacceptable safety failure.

Primary quality metrics:
: EvidenceSpan recovery rate, Recall@5, claim-support precision, citation precision, Answer Mode accuracy, and abstention accuracy.

Hard failures:
: Zero forbidden visibility exposure, role leakage, unsupported high-risk conclusion, required-abstention violation, missing required provenance, missing applicable Verification result, or invalid comparison.

Critical-failure identity:
: A versioned deterministic tuple of case, failure code, and evaluator contract. Candidate removal and new-failure detection operate on these tuples, not subjective reviewer judgment.

Regression limits:
: No primary metric worse by more than 2 percentage points; p95 latency no more than 15 percent slower; compatible-case cost no more than 20 percent higher.

Positive evidence:
: At least one primary metric improves by 3 percentage points, one critical baseline failure is removed, p95 latency falls by 15 percent, or compatible-case cost falls by 20 percent, while all preceding gates pass.

Rejected alternative:
: Optimize a weighted composite score. Weight selection would be arbitrary and could allow good latency or fluent answers to mask forbidden evidence leakage.

Trade-off:
: A zero-tolerance hard gate can block release on one case. That strictness is intentional for access leakage and high-risk unsupported conclusions, but every failure must be reproducible and reviewed for dataset validity.

Failure modes:
: tuning thresholds on Verification, comparing incompatible evaluator versions, confusing percentage with percentage points, missing operational measurements, and allowing an LLM judge to override deterministic evidence.

Evidence required before interview:
: Metric contracts, Calibration threshold manifest and digest, gate decision trace, baseline-candidate compatible manifest, and at least one intentionally failing gate fixture.

Likely follow-ups:

- "Why allow a 2-point regression?" — It prevents noise or minor trade-offs from blocking a candidate while bounding quality loss; critical failures remain zero-tolerance.
- "Why require positive evidence?" — Passing only by not getting worse does not justify calling a candidate an improvement.
- "Can latency gains compensate for quality loss?" — Only within the 2-point limit and never for a hard failure.
- "Why not let an LLM judge decide semantic quality?" — It can help analyze nuance, but model drift and judge bias make it unsuitable as the sole release authority.
- "How is a high-risk unsupported conclusion detected reproducibly?" — The case declares high risk and claims requiring support; the deterministic claim-support evaluator checks acceptable EvidenceSpans and emits the versioned critical identity.

### D7. Fail closed and preserve a complete run manifest

Decision:
: Runs end as `COMPLETED`, `FAILED`, or `INVALID`; only compatible completed runs may enter release comparison.

Why:
: Evaluation infrastructure can produce convincing but false conclusions when it silently drops cases, fills missing metrics, or compares different datasets and evaluator versions. Failing closed makes uncertainty visible.

Retry policy:
: Retry transient timeout, `429`, and `5xx` failures at most twice. Record every attempt. Do not retry contract, schema, validation, or provenance errors.

Manifest contract:
: Record both repository SHAs and dirty flags, dataset and corpus digests, adapter and evaluator versions, threshold manifest, prompt hash, model parameters, dependency and environment digests, execution mode, seeds, times, and case attempts.

Rejected alternative:
: Keep only aggregate scores and rerun failed cases until the dashboard is complete. This erases operational failures and makes the final result impossible to audit.

Trade-off:
: Strict compatibility rules produce more invalid comparisons and require more storage. The cost is acceptable because append-only structured results are small relative to the value of trustworthy evidence.

Failure modes:
: dirty SUT state, API drift, missing model version, fixture-live comparison, partial Verification run, silent retry bias, leaked credentials, and result mutation after publication.

Evidence required before interview:
: State-transition tests, transient and permanent failure fixtures, retry attempt log, dirty-worktree rejection, incompatible-run rejection, redaction test, and one-command manifest replay.

Likely follow-ups:

- "Why distinguish FAILED from INVALID?" — FAILED describes execution failure; INVALID says the evidence cannot support the requested comparison even if execution produced data.
- "Can a partially successful run still teach you something?" — Yes for diagnosis, but it cannot support release or submission claims.
- "How do you reproduce an external model response?" — Pin every controllable input and preserve the original observation; exact provider determinism may be impossible, so replayability and live rerun are reported separately.
- "What exactly is reproducible?" — Artifact replay, metric calculation, aggregation, and gates reproduce canonical logical digests. A live external-model rerun is a new drift measurement, not a promise of identical text.
- "Why record dirty flags?" — A commit SHA does not describe uncommitted code, so a dirty system cannot support a fully reproducible published result.

### D8. Use Python, DuckDB and Parquet with a static Next.js dashboard

Decision:
: Build the evaluation engine in Python 3.12, store canonical experiment evidence as versioned Parquet and JSON, analyze it with DuckDB, and present sanitized exports through a statically built Next.js dashboard.

Why Python:
: Evaluation, schema validation, statistical aggregation, HTTP experimentation, and AI tooling have mature Python support. It also keeps metric code close to the research workflow.

Why DuckDB and Parquet:
: The workload is append-only analytical evidence, not a multi-user transactional product. Parquet is portable and columnar; DuckDB queries it directly without operating another database server.

Why not PostgreSQL in the Evaluation Plane:
: PostgreSQL is appropriate for AX_portfolio's product data, concurrency, transactions, and pgvector retrieval. Adding it here would create service operations and mutable storage without a first-release requirement.

Why a static Next.js dashboard:
: The submission should show a frozen, reproducible experiment. Static export provides a polished interactive interface without a mutable server or database, and the data loader can later move from versioned JSON to an API.

Rejected alternatives:

- Streamlit-only application — fast to build but combines execution, analysis, and presentation too tightly for the desired evidence boundaries.
- New FastAPI and PostgreSQL result service — enables live multi-user operation but adds infrastructure not required for a ten-day recruiter-facing release.
- Store only a DuckDB database file — less portable and makes the query cache look like canonical evidence.

Trade-offs:
: The Python and TypeScript split adds two toolchains, and static results require rebuilding after each published run. In return, evaluation logic and recruiter-facing presentation remain independently testable.

Failure modes:
: treating a `.duckdb` cache as source of truth, committing unsanitized artifacts, dashboard schema drift, non-reproducible Parquet output, and accidentally adding product retrieval logic to the evaluator.

Evidence required before interview:
: Python and dashboard lockfiles, artifact schemas, DuckDB rebuild test, static dashboard build, sanitized export contract test, Docker reproduction, and CI evidence.

Likely follow-ups:

- "Why not use your familiar PostgreSQL stack?" — Tool choice follows workload: AX needs transactional product storage; the Evaluation Plane needs portable append-only analytical evidence.
- "Does static mean non-interactive?" — No. Filtering and charts run client-side; static means data is frozen at build time and no server is required.
- "When would you migrate to PostgreSQL?" — When multiple users or workers need concurrent writes, live run control, authentication, or continuously updated operational monitoring.

### D9. Use layered verification and an evidence-driven ten-day sequence

Decision:
: Deliver schemas, metric goldens, properties, adapter contracts, state and storage tests, fixture E2E, live Verification, dashboard checks, and clean-container reproduction in dependency order.

Why:
: Passing unit tests alone cannot prove that the published experiment came from a compatible live SUT, that the metrics are mathematically correct, or that the dashboard preserved the evidence. Each layer validates a different claim.

Schedule rationale:
: Contracts and dataset cases begin before UI work. A baseline is run before candidate improvement. The dashboard is built from validated artifacts only after the evidence pipeline exists. Submission QA and storytelling occupy dedicated final days instead of being treated as leftover work.

Frozen first comparison:
: The existing AX API supports an immediate `top_k=3` baseline and `top_k=5` candidate while holding SUT SHA and other contracts constant. This guarantees an honest configuration experiment even if no product-code fix is ready; a failed candidate remains valid evidence.

Rejected alternative:
: Build the dashboard first and backfill evaluation data later. It would optimize visible progress while leaving the core evidence and failure analysis at highest schedule risk.

Trade-off:
: Authoring and reviewing 100 structured cases consumes substantial time. The fixed daily case allocation and narrow AX-product allowance protect that critical path.

Failure modes:
: late dataset completion, a baseline run after candidate tuning, no live Verification, irreproducible external-model behavior, dashboard-only success examples, and sacrificing final QA to feature work.

Evidence required before interview:
: Test matrix with current status, CI runs, golden metric fixtures, live run manifests, clean Docker reproduction log, dashboard build and browser evidence, demo recording, and final claim-to-evidence matrix.

Likely follow-ups:

- "Why spend so much time on the dataset?" — Evaluator sophistication cannot compensate for ambiguous or cherry-picked ground truth; the dataset is the quality contract.
- "What would you cut first if behind?" — Dashboard ornamentation and supplementary LLM-judge analysis, not provenance, live Verification, critical gates, or failure analysis.
- "Why is the dashboard late in the schedule?" — It must render validated evidence rather than drive the design of the evaluation system.
- "How do you know the project is complete?" — Every submission claim maps to versioned evidence, the full Verification run is valid, reproduction passes cleanly, and the release gates produce an auditable decision.
- "Why choose top-k as the first candidate?" — It is already executable through the current API, isolates one retrieval-depth variable, and can reveal whether added evidence justifies latency and cost. It is not misrepresented as a code improvement.

## Failure taxonomy defense

- `P-*` answers where document understanding failed.
- `R-*` answers where evidence selection failed.
- `A-*` answers where reasoning, grounding, answer mode, or abstention failed.
- `O-*` answers where operational quality regressed.
- `SYS-*` answers where the evaluation itself is invalid or unreproducible.
- `TRJ-*` is reserved and unused in the first release.

Multiple labels may attach to one observation because one user-visible failure can have more than one mechanism. Metrics summarize prevalence; taxonomy supports diagnosis; release gates enforce decisions. These are deliberately separate concepts.

## Evidence ledger to complete during implementation

- [ ] Final repository and SUT commit SHAs
- [ ] Dataset manifest, schema version, split digest, and provenance report
- [ ] SUT Adapter request and normalized-observation contracts
- [ ] Contract, unit, integration, and live-SUT test outputs
- [ ] Baseline and candidate run manifests
- [ ] Metric definitions and release-gate thresholds
- [ ] Representative failure analyses with before-and-after evidence
- [ ] Latency, token, and cost comparison
- [ ] Reproduction command and clean-machine result
- [ ] Dashboard screenshots and two-to-three-minute demo script
- [ ] Explicit `planned` and `not evaluated` capability matrix

## Update protocol for every future locked decision

Add or revise a decision card with:

1. the exact decision and invariant;
2. why it serves the Braincrew role and portfolio thesis;
3. alternatives rejected and why;
4. trade-offs and known failure modes;
5. validation evidence produced or still required;
6. likely interviewer objections and concise answer direction;
7. links to implementation, tests, experiment results, and submission claims when they exist.
