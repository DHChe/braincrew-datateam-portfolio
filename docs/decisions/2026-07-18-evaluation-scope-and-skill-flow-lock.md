# Braincrew Evaluation Portfolio — Scope and Skill Flow Lock

Date: 2026-07-18  
Status: LOCKED

## 1. Submission claim boundary

The portfolio evaluates only capabilities that are implemented and reproducibly verified during the ten-day build window.

- Do not add Agent evaluation merely to match job-posting terminology.
- Do not claim Agent or multi-step trajectory quality unless a real Agent execution path, trace contract, dataset, evaluator, and repeatable result all exist.
- Mark unavailable or unfinished capabilities as `planned` or `not evaluated`.
- Treat AX_portfolio as the evolving Subject Under Test (SUT), not as a finished system whose quality is assumed.
- Record the exact SUT commit SHA together with dataset, evaluator, prompt, and model versions for every published experiment.

## 2. Forward-compatible evaluation contract

The first production release validates document parsing, retrieval, grounded answering, operational measurements, experiment comparison, and release gates. Its contracts must remain extensible to later Agent trajectory evaluation without pretending that this later scope has already been built.

The evaluator and experiment schemas therefore reserve stable extension points for:

- evaluation target type, such as `parsing`, `retrieval`, `answer`, and future `trajectory`;
- ordered execution steps and tool-call observations;
- step-level inputs, outputs, evidence references, latency, token usage, and cost;
- trajectory-level expected outcomes, constraints, and failure labels;
- evaluator provenance and versioning;
- baseline-versus-candidate comparison across the same dataset revision.

These are schema and interface extension points only. The submission UI, README, resume, and demo must report only evaluators and experiments that were actually executed and verified.

## 3. Explicitly excluded claims

- No fabricated Agent benchmark.
- No LLM-judge-only proof of quality.
- No claim that the entire AX_portfolio has been evaluated.
- No claim that planned trajectory fields constitute an implemented Agent evaluator.
- No use of private customer or employee documents as portfolio evidence.

## 4. Skill and workflow ownership

### Current question-and-design loop: `brainstorming`

The current questions come from the `brainstorming` skill. Its job is to turn the chosen portfolio direction into an approved design by:

1. inspecting the project context;
2. clarifying one decision at a time;
3. comparing alternative approaches;
4. presenting and approving the design section by section;
5. writing and reviewing the final design specification;
6. handing off only to implementation planning after design approval.

Therefore, a question asking whether an evaluation scope, architecture, schema, metric, or test boundary is correct belongs to `brainstorming`, not to Ask Matt.

### Ask Matt blueprint: workflow router and execution architecture

Ask Matt previously defined the higher-level route used after the direction was selected:

```text
existing Braincrew research and AX_portfolio context
  -> setup/verify Matt Pocock workflow skills
  -> grill-with-docs for adversarial requirements interrogation
  -> optional time-boxed prototype only for a concrete runnable uncertainty
  -> handoff
  -> to-spec
  -> to-tickets with dependency edges
  -> fresh-context implementation per ticket with TDD
  -> code review per ticket
  -> full benchmark and submission verification
```

Ask Matt determines how the work moves from evidence and clarified requirements into specification, tickets, implementation, and review. It is not the source of each incremental design-approval question.

## 5. Non-negotiable wording for the final submission

Preferred claim:

> While an HR/labor AX product was evolving, I introduced measurable quality criteria, a versioned evaluation dataset, failure taxonomy, experiment comparison, and release gates for the capabilities that were actually available and tested. The evaluation contracts are designed to extend to Agent trajectories, but Agent evaluation is not claimed in this submission.

## 6. Repository and SUT boundary

The Evaluation Plane and AX_portfolio are separate repositories with separate histories and responsibilities.

```text
braincrew-datateam-portfolio
  ├─ versioned evaluation datasets
  ├─ experiment runner and result store
  ├─ parsing, retrieval, answer, and operational evaluators
  ├─ comparison and release-gate logic
  ├─ dashboard and submission material
  └─ SUT Adapter ──HTTP──> AX_portfolio
```

- `braincrew-datateam-portfolio` owns the Evaluation Plane and submission evidence.
- `AX_portfolio` remains the evolving product and Subject Under Test.
- The live adapter calls AX through a documented HTTP contract and normalizes responses into evaluation observations.
- AX internals are not copied or imported into the Evaluation Plane.
- If required evaluation observations are unavailable, AX may receive a narrowly scoped observability endpoint through its own product branch and review process.
- Recorded fixtures may support deterministic development and replay, but they do not replace at least one reproducible live-SUT benchmark for submission claims.

## 7. Branching strategy

Use a lightweight integration-branch workflow for the ten-day delivery window:

```text
main
  └─ develop
       ├─ docs/evaluation-plane-design
       ├─ feat/evaluation-contracts
       ├─ feat/dataset-registry
       ├─ feat/ax-sut-adapter
       ├─ feat/evaluator-runner
       ├─ feat/experiment-comparison
       └─ feat/dashboard-release-gates
```

- `main` is the stable, recruiter-facing release branch. It receives release pull requests from `develop` only.
- `develop` is the integration baseline for the approved design and verified feature work.
- Design work starts on `docs/evaluation-plane-design` from `develop`; implementation does not start before the written design and implementation plan pass their gates.
- Each feature branch starts from the latest verified `develop`, owns one bounded capability, and returns through a pull request with tests and review evidence.
- Do not create all feature branches in advance. Create a branch only when its dependency is ready and its ticket is executable.
- After integration and full benchmark verification, open a release pull request from `develop` to `main` and tag the frozen submission commit.
- AX_portfolio keeps its own branch and worktree lifecycle. No branch crosses repository boundaries.

## 8. Evaluation Plane component boundaries

The Evaluation Plane uses a one-way, evidence-preserving data flow:

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

### Dataset Registry

Owns versioned evaluation cases, corpus references, expected evidence, visibility constraints, and evaluator configuration. It does not execute AX or calculate scores.

### Experiment Runner

Owns run orchestration, dependency ordering, timeouts, retries, and version capture. It must not contain metric-specific scoring logic.

### SUT Adapter

Translates standard evaluation inputs into documented AX HTTP requests and converts AX responses into normalized observations. It must not calculate quality scores or hide missing SUT fields.

### Normalized Observation

Preserves the answer, retrieved evidence, citations, answer mode, role context, timing, token and cost measurements when available, errors, and provenance needed by evaluators. Missing values remain explicitly missing rather than inferred.

### Evaluator Registry

Runs parsing, retrieval, grounded-answer, and operational evaluators through stable contracts. Deterministic evaluators are authoritative where possible. An LLM judge may provide a labeled supplementary signal but cannot independently determine a release-gate result.

### Immutable Result Store

Stores run manifests, observations, evaluator outputs, failure labels, and aggregate metrics as append-only experiment evidence. Corrections create a new run or evaluator version; published historical results are not mutated.

### Comparison and Release Gate

Compares a candidate only with a compatible baseline using the same dataset revision and metric contracts. It applies explicit thresholds and reports pass, fail, or invalid comparison with reasons.

### Dashboard and Report Exporter

Reads stored evidence and renders experiment comparisons, failure examples, and submission reports. It cannot rewrite source observations, evaluator scores, or gate decisions.

### Future trajectory extension

The contracts may later add trajectory observations and evaluators as new registered target types. The first production release registers no Agent trajectory evaluator and exposes no Agent-quality claim.

## 9. Evaluation dataset and failure taxonomy

The first production release uses exactly 100 versioned evaluation scenarios.

```text
Calibration split    70 cases
Verification split   30 cases
Total               100 cases
```

- The Calibration split may be used to develop evaluators and tune explicit thresholds.
- The Verification split is frozen before final candidate tuning and is used for the submission comparison.
- Because the repository is public, this is a reproducible verification split rather than a claim of a secret statistical holdout.
- The split assignment, dataset manifest, and content digest are recorded. Changing a frozen case requires a new dataset version and invalidates comparisons made against the old version.

The 100 cases have one primary focus each:

```text
Parsing-focused                  20
Retrieval-focused                30
Grounded-answer-focused          40
Visibility-and-abstention-focused 10
Total                           100
```

Operational measurements run across compatible live-SUT cases rather than forming a separate synthetic case category.

Each case contains structured ground truth rather than only a free-form reference answer:

- stable case identifier, dataset version, and split;
- primary evaluation stage and secondary tags;
- user role, input query, and input-document references;
- corpus and document versions;
- expected EvidenceSpans and acceptable alternative evidence;
- forbidden evidence and visibility constraints;
- expected Answer Mode;
- required, optional, and forbidden claims;
- evaluator configuration and applicability conditions;
- difficulty and adversarial tags;
- public or synthetic provenance and license metadata;
- creation, review, and correction history.

Failure labels use stable families:

- `P-*`: parsing structure loss, table or list loss, missing metadata, or unrecoverable EvidenceSpan;
- `R-*`: relevant-evidence miss, authority-order inversion, forbidden-visibility retrieval, or distractor capture;
- `A-*`: unsupported claim, citation mismatch, incomplete support, wrong Answer Mode, failed abstention, unsafe overclaim, or role leakage;
- `O-*`: latency or cost regression, timeout, or malformed response;
- `SYS-*`: adapter-contract failure, missing version provenance, invalid comparison, or non-deterministic replay;
- `TRJ-*`: reserved for future trajectory evaluation and unused by the first production release.

One observation may receive multiple failure labels. Labels identify failure mechanisms; aggregate metrics determine scale, and release gates determine ship eligibility.

## 10. Metrics and release gates

Metrics are grouped by evaluation layer.

### Parsing metrics

- structure-preservation pass rate;
- EvidenceSpan recovery rate;
- metadata completeness rate;
- table and list preservation pass rate where applicable.

### Retrieval metrics

- Recall@5;
- MRR@10;
- authority-priority hit rate;
- forbidden-visibility leakage rate.

### Grounded-answer metrics

- claim-support precision;
- citation precision;
- citation coverage;
- Answer Mode accuracy;
- abstention accuracy.

### Operational metrics

- run success rate;
- p50 and p95 latency;
- input and output token usage;
- estimated cost per compatible case and per run.

The primary quality metrics used for regression and improvement decisions are:

- EvidenceSpan recovery rate;
- Recall@5;
- claim-support precision;
- citation precision;
- Answer Mode accuracy;
- abstention accuracy.

All percentage changes in quality gates are percentage-point changes. Latency and cost limits are relative percentage changes.

### Gate 1: non-negotiable hard failures

The candidate fails if the Verification split contains any of the following:

- forbidden document exposure;
- role-information leakage;
- unsupported high-risk conclusion;
- a forced answer on a case explicitly requiring abstention;
- missing dataset, SUT, adapter, evaluator, prompt, or model provenance required by the run contract;
- an unexecuted or unscored applicable Verification case;
- an invalid baseline-candidate comparison.

### Gate 2: regression limits

- No primary quality metric may regress by more than 2 percentage points.
- Candidate p95 latency may not increase by more than 15 percent.
- Candidate estimated cost per compatible case may not increase by more than 20 percent.
- A run that lacks comparable latency or cost evidence reports the metric as unavailable; it cannot claim operational improvement.

### Gate 3: positive candidate evidence

After Gates 1 and 2 pass, the candidate must satisfy at least one of:

- improve at least one primary quality metric by 3 or more percentage points;
- eliminate at least one critical baseline failure without introducing another critical failure;
- preserve all primary quality metrics within the 2-point regression limit while reducing p95 latency by at least 15 percent;
- preserve all primary quality metrics within the 2-point regression limit while reducing estimated cost per compatible case by at least 20 percent.

Non-critical absolute thresholds are calibrated once on the 70-case Calibration split, written to a versioned threshold manifest, and frozen before any final Verification candidate run. Threshold or metric-contract changes require a new evaluator or gate version and invalidate direct comparison with earlier incompatible runs.

An LLM judge may be reported as supplementary qualitative evidence. It cannot independently pass, fail, or overturn any release gate.

## 11. Run state, error handling, and reproducibility

Every experiment run follows this state model:

```text
CREATED -> RUNNING -> COMPLETED
                   -> FAILED
                   -> INVALID
```

- `COMPLETED` means every applicable case was attempted and produced an evaluation result under the run contract.
- `FAILED` means execution could not finish because of a runtime or infrastructure failure.
- `INVALID` means the run completed partially or fully but lacks the provenance, compatibility, or contract validity required for comparison.
- Individual case failures and partial observations remain stored for diagnosis, but a `FAILED` or `INVALID` run cannot pass a release gate.

### Retry contract

- Retry only transient HTTP timeouts, `429`, and `5xx` responses.
- Allow at most two retries after the initial attempt.
- Record every attempt, delay, response status, and elapsed time.
- Do not retry `4xx` contract errors, schema mismatch, validation failure, or missing required provenance.
- Preserve the initial failure even when a later attempt succeeds.
- Never replace missing metrics or fields with zero, success, or inferred values.

### Run manifest

Every run records:

- Evaluation Plane commit SHA and dirty-worktree flag;
- AX SUT commit SHA and dirty-worktree flag;
- dataset, split, and corpus identifiers and content digests;
- SUT Adapter, evaluator, and threshold-manifest versions and configuration digests;
- prompt hash;
- model, provider, and generation parameters;
- dependency-lock and execution-environment digests;
- `live` or `fixture` execution mode;
- run start and end times, deterministic seeds where applicable, and every case attempt;
- non-secret endpoint and environment identity required to understand the run.

Secrets, credentials, personal information, and private document content are redacted or excluded from the manifest and stored results.

### Comparison and publication invariants

- Published submission results require clean committed states for both repositories.
- Baseline and candidate must use compatible dataset, corpus, evaluator, threshold, and execution-mode contracts.
- A fixture run is never directly compared with a live run.
- Submission quality claims require at least one complete live-SUT Verification run.
- Results and manifests are append-only. Corrections create a new run and, where applicable, a new version.
- A partial run may support diagnosis but never release evidence.
- Missing compatibility or provenance fails closed as `INVALID`; the dashboard must display unavailable data rather than fabricate a comparison.
- The repository provides one documented command that can reproduce a run from its manifest, subject to external model availability and credentials.

## 12. First-production-release technology stack

The Evaluation Plane uses a Python evaluation core, DuckDB over Parquet and JSON evidence, and a statically exported Next.js dashboard.

### Evaluation core

- Python 3.12;
- `uv` for Python dependency and lockfile management;
- Pydantic v2 for dataset, adapter, observation, metric, manifest, and gate contracts;
- Typer for the command-line interface;
- `httpx` for the live AX SUT Adapter;
- DuckDB for analytical queries over experiment artifacts;
- Parquet for tabular observations, metrics, and failure labels;
- JSON for manifests, gate decisions, and dashboard export contracts;
- pytest for unit, contract, integration, and replay tests;
- Hypothesis only where property-based testing materially strengthens stable contracts;
- Ruff and mypy for static quality checks.

### Evidence storage contract

- Versioned JSON and Parquet artifacts are the canonical experiment evidence.
- DuckDB is a query and transformation engine, not the authoritative source of truth.
- Any local `.duckdb` file must be reproducible from canonical artifacts and may be treated as disposable cache.
- PostgreSQL and pgvector remain AX_portfolio product responsibilities. The Evaluation Plane does not duplicate product retrieval or introduce a service database in the first release.

### Recruiter-facing dashboard

- Next.js with TypeScript;
- static export with no required server runtime;
- reads only validated, sanitized JSON exports generated from canonical experiment artifacts;
- supports client-side comparison, filtering, sorting, charts, gate traces, and representative failure drill-down;
- cannot start experiments, change scores, or mutate evidence;
- changing experiment results requires generating a new export and rebuilding the site.

### Reproduction and continuous integration

- Docker defines the reproducible evaluation environment;
- a Make target exposes the one-command manifest reproduction workflow;
- GitHub Actions runs Python lint, type checking, unit and contract tests, fixture benchmark, and dashboard lint, type checking, and static build;
- live AX and external-model Verification remains an explicit credentialed run whose resulting manifest and sanitized artifacts are published after validation.

A dynamic Results API, PostgreSQL result store, multi-user execution service, and UI-triggered experiment control are future operational extensions, not first-release scope.

## 13. Testing, ten-day delivery, and submission package

### Verification layers

The first production release must produce evidence at these layers:

1. schema tests for every versioned input and artifact contract;
2. metric golden tests using hand-calculated expected values;
3. property tests for invariants that benefit from generated cases;
4. SUT Adapter contract tests against controlled HTTP responses;
5. result-store, run-state, compatibility, immutability, retry, and redaction tests;
6. fixture-mode end-to-end benchmark tests;
7. live AX smoke tests and a complete live Verification benchmark;
8. dashboard lint, type checking, static build, export-contract, and browser smoke tests;
9. clean Docker manifest reproduction.

Required adversarial evidence includes:

- a hand-calculated metric matching the implementation;
- timeout, `429`, and `5xx` retries stopping after the configured two retries;
- schema mismatch becoming `INVALID` without retry;
- append-only artifacts rejecting or exposing attempted mutation;
- incompatible baseline-candidate comparison rejection;
- fixture-live comparison rejection;
- forbidden document exposure causing a hard-gate failure;
- sanitized dashboard export excluding secrets and private fields;
- a clean-container reproduction from one documented command;
- a complete 30-case live-SUT Verification result.

### Ten-day sequence

```text
Day 1  Final design, reviewed specification and plan; pin AX baseline SHA
Day 2  Contracts, manifest, artifact store and 20 parsing-focused cases
Day 3  SUT Adapter, retrieval evaluator and 20 additional cases
Day 4  Answer, citation and abstention evaluators and 20 additional cases
Day 5  Failure taxonomy, release gates and 20 additional cases
Day 6  Complete and review 100 cases; freeze 70/30 split and content digest
Day 7  Execute live baseline; analyze representative failures; prepare candidate
Day 8  Pin candidate SUT SHA; execute compatible live Verification A/B run
Day 9  Static dashboard, README, reproduction and interview dossier completion
Day 10 Independent QA, demo video, resume bullets and release pull request
```

The Evaluation Plane receives 9 to 10 hours per day. Existing AX work receives at most 2 to 3 hours per day and only for already-started work or evaluation-unblocking changes. If AX work blocks the portfolio for more than one day, defer that product work until after submission.

### Submission package

- public GitHub repository with an architecture diagram and evidence-first README;
- public or synthetic 100-case dataset card and provenance report;
- compatible baseline-candidate experiment report;
- failure taxonomy and representative failure analysis;
- release-gate decision trace;
- statically deployed interactive dashboard;
- one-command reproduction guide and clean-environment evidence;
- two-to-three-minute demo video;
- resume-ready impact bullets;
- explicit `planned` and `not evaluated` capability matrix;
- maintained interview defense dossier.

No deliverable may claim a capability, metric improvement, live result, or Agent evaluation that lacks the corresponding versioned evidence.
