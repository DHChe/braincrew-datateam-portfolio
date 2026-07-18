# Evidence-First HR/Labor RAG Evaluation Plane — Design

Date: 2026-07-18  
Status: User-approved design; pending independent specification review

## 1. Objective

Build a first-production-release Evaluation Plane for Braincrew's Data Team portfolio within ten days. It evaluates the capabilities actually available in AX_portfolio, produces reproducible baseline-candidate evidence, diagnoses failure mechanisms, and enforces explicit release gates.

The portfolio must demonstrate evaluation dataset construction, RAG quality measurement, experiment comparison, quality monitoring, and product-facing AI engineering. It must not pretend that AX_portfolio is complete or claim Agent evaluation that was not implemented and verified.

## 2. Product thesis

AX_portfolio is the evolving HR/labor Subject Under Test (SUT). The Evaluation Plane is an independent measurement product.

The submission narrative is:

> While an HR/labor AX product was evolving, I introduced measurable quality criteria, a versioned evaluation dataset, failure taxonomy, experiment comparison, and release gates for the capabilities that were actually available and tested. The evaluation contracts are designed to extend to Agent trajectories, but Agent evaluation is not claimed in this submission.

## 3. Goals

- Evaluate document parsing, retrieval, grounded answering, visibility, abstention, latency, token usage, and estimated cost.
- Build exactly 100 structured and versioned evaluation cases.
- Compare compatible baseline and candidate runs against the same frozen Verification split.
- Preserve every published run's SUT, dataset, evaluator, threshold, prompt, model, and environment provenance.
- Produce an auditable release-gate decision and representative failure analysis.
- Provide a polished static dashboard, reproducible command, concise demo, resume bullets, and interview defense material.
- Preserve schema extension points for future Agent trajectory observations without registering or claiming Agent evaluation.

## 4. Non-goals

- Building another general Agent or RAG product.
- Evaluating all AX_portfolio capabilities.
- Copying or importing AX internal modules into the evaluator.
- Using private customer, employee, or company documents.
- Running a broad research-paper-scale model benchmark.
- Automatically modifying AX based on evaluation results.
- Allowing an LLM judge to determine release eligibility by itself.
- Operating a multi-user experiment service, dynamic Results API, or new PostgreSQL result database in the first release.

Unavailable product capabilities are labeled `planned` or `not evaluated`.

## 5. Repository and Git boundaries

`braincrew-datateam-portfolio` owns datasets, evaluators, experiment artifacts, comparison logic, dashboard, and submission material. AX_portfolio remains a separate repository and owns product retrieval, PostgreSQL, pgvector, answer generation, and product runtime behavior.

The repositories communicate through a documented HTTP SUT Adapter. AX may receive only narrowly scoped observability changes through its own branch and review process when required fields are unavailable.

Git branches are:

- `main`: stable recruiter-facing release;
- `develop`: verified integration baseline;
- `docs/evaluation-plane-design`: design and planning;
- short-lived `feat/*`, `fix/*`, and `chore/*` branches from the latest verified `develop`.

Features return to `develop` by reviewed pull request. A fully verified release moves from `develop` to `main` by release pull request and receives a frozen submission tag.

## 6. Architecture

```text
Dataset Registry
      ↓
Experiment Runner
      ↓
SUT Adapter ──HTTP──> AX_portfolio
      ↓
Normalized Observation
      ↓
Evaluator Registry
      ↓
Immutable Result Store
      ↓
Comparison and Release Gate
      ↓
Dashboard and Report Exporter
```

The flow is one-way and evidence-preserving. No presentation component can change observations, scores, or gate decisions.

## 7. Component responsibilities

### Dataset Registry

Owns versioned cases, corpus references, expected evidence, visibility constraints, evaluator configuration, split assignments, provenance, and content digests. It neither executes the SUT nor calculates scores.

### Experiment Runner

Owns orchestration, timeouts, retries, case attempts, execution mode, and version capture. Metric-specific score calculation is prohibited here.

### SUT Adapter

Maps standard evaluation requests to AX HTTP endpoints and normalizes responses. It does not score, invent missing values, hide contract mismatch, or import AX internals.

### Normalized Observation

Preserves the answer, retrieved evidence, citations, Answer Mode, role context, timing, token and cost information when available, errors, attempt history, and provenance required for evaluation.

### Evaluator Registry

Runs registered parsing, retrieval, grounded-answer, and operational evaluators. Deterministic evaluators are authoritative where possible. LLM-judge results are explicitly supplementary.

### Immutable Result Store

Stores manifests, observations, metrics, failure labels, and aggregate outputs as append-only artifacts. Corrections create a new run or version.

### Comparison and Release Gate

Rejects incompatible runs, computes paired baseline-candidate deltas, applies frozen thresholds, and records a pass, fail, or invalid decision with reasons.

### Dashboard and Report Exporter

Generates sanitized versioned JSON exports and renders interactive static comparisons, gate traces, and representative failures. It cannot execute experiments or mutate evidence.

## 8. Dataset contract

The dataset contains exactly 100 cases:

```text
Calibration     70
Verification    30
Total          100
```

Primary focus allocation:

```text
Parsing                         20
Retrieval                       30
Grounded answer                 40
Visibility and abstention       10
Total                          100
```

The Verification split is reproducible and frozen, not described as a secret statistical holdout. Its assignment and content digest are frozen before final candidate tuning. Any correction requires a new dataset version and invalidates incompatible comparisons.

Each case contains a stable identifier, dataset version, split, focus and tags, role, query, document references, corpus versions, expected and alternative EvidenceSpans, forbidden evidence, visibility rules, expected Answer Mode, required and forbidden claims, evaluator applicability, difficulty, provenance, license, and review history.

## 9. Failure taxonomy

- `P-*`: parsing structure, table, list, metadata, or EvidenceSpan failure;
- `R-*`: evidence miss, authority inversion, visibility leak, or distractor capture;
- `A-*`: unsupported claim, citation mismatch, incomplete support, wrong mode, failed abstention, unsafe overclaim, or role leakage;
- `O-*`: latency, cost, timeout, or malformed-response failure;
- `SYS-*`: adapter, provenance, compatibility, or replay failure;
- `TRJ-*`: reserved and unused by the first release.

One observation may receive multiple labels. Taxonomy diagnoses mechanisms, metrics measure prevalence, and gates decide release eligibility.

## 10. Metrics

Parsing metrics:

- structure-preservation pass rate;
- EvidenceSpan recovery rate;
- metadata completeness;
- applicable table and list preservation.

Retrieval metrics:

- Recall@5;
- MRR@10;
- authority-priority hit rate;
- forbidden-visibility leakage rate.

Grounded-answer metrics:

- claim-support precision;
- citation precision and coverage;
- Answer Mode accuracy;
- abstention accuracy.

Operational metrics:

- success rate;
- p50 and p95 latency;
- input and output tokens;
- estimated cost per compatible case and run.

Primary quality metrics are EvidenceSpan recovery, Recall@5, claim-support precision, citation precision, Answer Mode accuracy, and abstention accuracy.

## 11. Release gates

Quality deltas use percentage points. Latency and cost deltas use relative percentages.

Gate 1 fails on any forbidden document exposure, role leakage, unsupported high-risk conclusion, required-abstention violation, missing required provenance, unexecuted or unscored applicable Verification case, or invalid comparison.

Gate 2 permits no primary metric regression greater than 2 percentage points, p95 latency increase greater than 15 percent, or compatible-case cost increase greater than 20 percent.

After Gates 1 and 2 pass, Gate 3 requires at least one of:

- a primary quality metric improves by at least 3 percentage points;
- a critical baseline failure is removed without another critical failure;
- all primary metrics stay within the regression limit and p95 latency falls by at least 15 percent;
- all primary metrics stay within the regression limit and compatible-case cost falls by at least 20 percent.

Non-critical absolute thresholds are calibrated once on Calibration, versioned, and frozen before final Verification. An LLM judge cannot pass, fail, or overturn a gate.

## 12. Run states and errors

```text
CREATED -> RUNNING -> COMPLETED
                   -> FAILED
                   -> INVALID
```

`FAILED` means execution could not complete. `INVALID` means produced evidence cannot support the requested comparison. Neither state may pass a gate. Partial artifacts remain available for diagnosis.

Only timeout, `429`, and `5xx` responses are retried, at most twice after the initial attempt. Every attempt is recorded. Contract, schema, validation, provenance, and non-transient `4xx` errors are not retried. Missing data is never converted to zero or success.

## 13. Reproducibility manifest

Every run records:

- Evaluation Plane and AX commit SHAs and dirty flags;
- dataset, split, and corpus identifiers and digests;
- adapter, evaluator, and threshold versions and configuration digests;
- prompt hash, provider, model, and generation parameters;
- dependency-lock and runtime-environment digests;
- live or fixture mode;
- times, seeds where applicable, and all attempts.

Published results require clean committed states. Fixture and live runs are never compared. Submission claims require at least one complete live-SUT Verification run. Results are append-only, secrets are redacted, and missing compatibility fails closed.

## 14. Technology stack

Evaluation core:

- Python 3.12, `uv`, Pydantic v2, Typer, and `httpx`;
- DuckDB querying canonical Parquet and JSON artifacts;
- pytest, selective Hypothesis, Ruff, and mypy.

Dashboard:

- Next.js and TypeScript;
- static export reading validated sanitized JSON;
- client-side comparison and drill-down;
- no runtime result mutation or experiment control.

Reproduction and CI:

- Docker environment;
- Make-based one-command replay;
- GitHub Actions for Python and dashboard quality gates, fixture benchmark, and static build;
- explicit credentialed live Verification outside routine CI.

PostgreSQL and pgvector remain in AX_portfolio. A local DuckDB database is disposable query cache; canonical evidence is versioned Parquet and JSON.

## 15. Testing strategy

Required layers are schema tests, hand-calculated metric goldens, relevant property tests, Adapter HTTP contracts, state and storage invariants, fixture-mode E2E, live AX smoke and Verification, dashboard export and browser checks, and clean Docker reproduction.

Adversarial tests must prove retry limits, non-retryable invalidation, immutable results, comparison incompatibility rejection, fixture-live rejection, hard-gate safety failure, redaction, and complete 30-case live Verification.

## 16. Ten-day execution sequence

```text
Day 1  Design, reviewed spec and plan; pin baseline SUT SHA
Day 2  Contracts, manifests, artifact store and 20 parsing cases
Day 3  Adapter, retrieval evaluator and 20 cases
Day 4  Answer evaluators and 20 cases
Day 5  Taxonomy, gates and 20 cases
Day 6  Finish 100 cases; review and freeze 70/30 digest
Day 7  Live baseline and failure analysis; candidate preparation
Day 8  Pin candidate SHA and run compatible live Verification A/B
Day 9  Dashboard, README, reproduction and interview dossier
Day 10 Independent QA, demo, resume bullets and release PR
```

Evaluation work receives 9 to 10 hours per day. AX work is limited to 2 to 3 hours and must already be in progress or unblock evaluation. Product work blocking the portfolio for more than one day is deferred.

## 17. Submission artifacts

- public repository and architecture diagram;
- 100-case dataset card and provenance report;
- baseline-candidate experiment report;
- failure taxonomy and representative failure analysis;
- release-gate trace;
- statically deployed interactive dashboard;
- one-command reproduction and clean-environment evidence;
- two-to-three-minute demo;
- resume impact bullets;
- `planned/not evaluated` matrix;
- interview defense dossier.

## 18. Acceptance criteria

The first production release is acceptable only when:

- all 100 cases validate and the frozen 70/30 digest is recorded;
- metric goldens and boundary tests pass;
- at least one baseline and candidate pair is compatible and auditable;
- a complete live-SUT Verification run exists;
- release-gate output is reproducible and includes reasons;
- canonical artifacts reconstruct analytical outputs;
- dashboard static build and sanitized export checks pass;
- clean Docker reproduction succeeds or an external-provider limitation is explicitly evidenced;
- every submission claim links to versioned evidence;
- Agent evaluation remains explicitly unimplemented and unclaimed.

## 19. Interview readiness

Every locked decision must be mirrored in the interview defense dossier with rationale, rejected alternatives, trade-offs, failure modes, validation evidence, and likely follow-up questions. Implementation and experiment evidence replaces checklist placeholders as it becomes available.
