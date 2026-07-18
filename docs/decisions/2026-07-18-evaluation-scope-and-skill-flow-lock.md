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

The versioned `ax-sut-http-v1` contract exposes these logical operations:

- `preflight()` verifies readiness, authentication mode, corpus identity, endpoint schemas, and available telemetry;
- `parse()` uploads or selects a synthetic/public document and returns parser, document, section, table/list, and EvidenceSpan observations;
- `retrieve()` submits a role-scoped query and returns ordered retrieval candidates and visibility decisions;
- `answer()` submits a role-scoped question and returns the Answer Mode, structured answer, citations, provider metadata, and evidence packaging;
- `source_text()` resolves an allowed source or EvidenceSpan when evaluator evidence requires full text.

The first AX mapping uses:

- `GET /health/ready` for readiness;
- `POST /v1/retrieval/search` for retrieval;
- `POST /v1/answers/generate` for answer generation;
- `GET /v1/retrieval/source-text/{record_kind}/{record_id}` for permission-checked source text;
- the existing attachment upload and status APIs plus, if preflight proves parsed artifacts are not observable, one local/test-only parsed-document observation endpoint implemented in AX through its own reviewed Track P branch.

Exact method, path, request mapping, response mapping, and expected schema digest are frozen in `ax-http-v1.yaml`. The Adapter's canonical request includes `run_id`, `case_id`, `eval_correlation_id`, role, tenant, query or document reference, corpus version, `top_k`, evidence limit, and timeout where applicable. Canonical observations preserve opaque AX identifiers, ordered rank, source and chunk identifiers, EvidenceSpan identifier, source class, authority level, visibility decision, snippets, allowed full text, answer and SUT correlation identifiers, provider metadata, latency, and explicit field-availability flags.

EvidenceSpan offsets are zero-based Unicode code-point offsets over canonical source text, with inclusive `start_char` and exclusive `end_char`, plus source-text digest. A citation refers to the canonical tuple `(record_kind, record_id, evidence_span_id, source_text_digest)`; missing members remain null and may invalidate the applicable evaluator.

Local/test authentication uses the documented AX tenant, user, and role headers. Any bearer token is supplied only through environment secrets and is never persisted. Portfolio runs are restricted to public or synthetic corpora. Adapter-generated correlation IDs and returned AX correlation IDs are both recorded.

Preflight stores a capability manifest. If a required operation, identifier, span field, citation field, visibility decision, or provenance field is unavailable, applicable cases are not silently skipped: the run becomes `INVALID` when the minimum coverage contract cannot be met. `401`, `403`, contract `4xx`, schema mismatch, and missing required fields are permanent contract failures; timeout, `429`, and `5xx` follow the bounded retry contract.

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
Primary focus                 Calibration  Verification  Total
Parsing                                14             6     20
Retrieval                              21             9     30
Grounded answer                        30            10     40
Visibility and abstention               5             5     10
Total                                  70            30    100
```

- The Calibration split may be used to develop evaluators and tune explicit thresholds.
- The Verification split is frozen before final candidate tuning and is used for the submission comparison.
- Because the repository is public, this is a reproducible verification split rather than a claim of a secret statistical holdout.
- The split assignment, dataset manifest, and content digest are recorded. Changing a frozen case requires a new dataset version and invalidates comparisons made against the old version.

The Verification split must provide these minimum applicable denominators:

- EvidenceSpan recovery rate: 6;
- Recall@5: 9;
- claim-support precision and citation precision: 10 each;
- Answer Mode accuracy: 15 across grounded-answer and visibility/abstention cases;
- abstention accuracy: 5.

Each metric reports its actual denominator. If applicability, missing telemetry, or execution failure reduces a primary metric below its minimum denominator, the run is `INVALID`; no aggregate score or gate decision is emitted for that comparison.

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
- versioned proposition catalog, required claim paths, high-risk conclusion paths, and forbidden propositions;
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

`failure-taxonomy-v1.yaml` assigns every failure code one severity: `critical`, `major`, `minor`, or `diagnostic`. Only deterministic evaluator outputs may create gate-authoritative critical failures. The first critical predicates are:

- `R-FORBIDDEN-VISIBILITY`: a returned retrieval or citation identifier matches the case's forbidden source, document, chunk, or EvidenceSpan set;
- `A-ROLE-LEAKAGE`: the normalized answer contains a case-declared protected identifier or forbidden claim for the executing role;
- `A-UNSUPPORTED-HIGH-RISK-CONCLUSION`: a high-risk case contains a forbidden, unsupported, contradicted, ambiguous, or unmapped conclusion under the versioned claim-proposition contract;
- `A-FAILED-ABSTENTION`: the case requires `insufficient_evidence` or `out_of_scope`, but the returned Answer Mode differs or the answer contains a case-declared forbidden conclusive claim;
- `SYS-PROVENANCE-MISSING`: a required manifest, contract, or evidence provenance field is missing;
- `SYS-COMPARISON-INVALID`: dataset, corpus, evaluator, threshold, execution-mode, or coverage compatibility fails.

A failure identity is `(case_id, failure_code, evaluator_contract_version)`. A critical baseline failure is eliminated only when the same case remains applicable and that identity is absent from the candidate. A candidate introduces another critical failure when it contains any critical identity absent from the compatible baseline. LLM-judge outputs cannot create, clear, or change the severity of these identities.

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

### `metric-contract-v2`

All gate-authoritative primary metrics use case-level macro aggregation. Each applicable case produces a score in `[0, 1]`; the dataset score is the arithmetic mean of case scores, with every applicable case weighted equally. Micro-pooling across claims, spans, or citations is prohibited.

Gold evidence is stored as requirement groups. Each group contains one or more exact acceptable alternatives. Matching uses canonical identity, not fuzzy semantic overlap:

- parsing spans match `(document_id, source_text_digest, start_char, end_char)`;
- retrieval and citation evidence match `(record_kind, record_id, evidence_span_id, source_text_digest)`, with explicitly nullable tuple members compared as stored;
- an expected group is satisfied when any one declared alternative matches.

Primary formulas are:

- EvidenceSpan recovery case score = matched required span groups / required span groups;
- Recall@5 case score = required evidence groups represented at least once in the first five unique returned evidence identities / required evidence groups;
- claim-support precision case score = supported generated claim atoms / all generated claim atoms, including unsupported, contradicted, ambiguous, and unmapped atoms in the denominator;
- citation precision case score = unique returned citations belonging to a matched proposition's `supports` evidence groups for one of their declared existing claim paths / all unique returned citations;
- Answer Mode accuracy case score = `1` when the normalized returned enum exactly equals the case's expected enum, otherwise `0`;
- abstention accuracy case score = `1` only when the required abstention mode matches and no case-declared forbidden conclusive claim is present, otherwise `0`.

#### `claim-proposition-v1`

Claim support is a closed-world, deterministic contract over the frozen evaluation dataset. It does not claim to understand arbitrary natural language. Each grounded-answer case declares a versioned proposition catalog with:

- `proposition_id`: stable meaning identity;
- `subject`, `predicate`, and optional `object` concept identifiers;
- `polarity`: `affirmed` or `denied`;
- `modality`: `must`, `may`, `must_not`, `unknown`, or `review_required`;
- `risk_level` and `conclusive`: whether the assertion can trigger a high-risk gate;
- case-level `high_risk_conclusion_paths`: exact structured-answer paths where unrecognized language must fail closed;
- normalized literal or regular-expression surface matchers with their own digest;
- `supports`: acceptable evidence groups whose text supports this exact proposition;
- `contradicts`: evidence groups whose text supports the opposite proposition;
- exact allowed and forbidden Answer Modes when applicable.

The evaluator creates a stable atom identity `(claim_path, atom_index, normalized_text_digest)`. List elements are already separate paths. Scalar `summary` and `answer` values are split on normalized newlines and the terminal punctuation characters `.`, `?`, `!`, `。`, `？`, and `！`; empty segments are removed. Support-required paths are `summary`, `answer`, and every `grounds[i]`; a case may additionally mark exact `review_points[i]`, `additional_checks[i]`, or `risk_warning` paths.

`claim-normalizer-v1` applies Unicode NFC normalization, converts CRLF to LF, trims leading and trailing whitespace, collapses internal whitespace, and normalizes only declared punctuation variants. It performs no stemming, stop-word deletion, embedding similarity, or negation/modality removal. Matchers use anchored whole-atom literal equality or anchored bounded regular expressions. The atomizer, normalizer, matcher-set version, proposition catalog digest, and case catalog digest are comparison compatibility fields.

The deterministic support predicate is true only when all of the following hold:

1. the atom maps to exactly one proposition;
2. a returned citation declares the atom's exact claim path;
3. the citation identity belongs to the proposition's `supports` evidence groups;
4. the same citation does not belong to the proposition's `contradicts` groups;
5. the proposition's polarity, modality, and allowed Answer Mode match the case contract;
6. no forbidden proposition is present in the same atom.

An atom mapping to no proposition is `A-UNMAPPED-CLAIM`; mapping to multiple propositions is `A-AMBIGUOUS-CLAIM`; citing no supporting evidence is `A-UNSUPPORTED-CLAIM`; and citing contradictory evidence is `A-CONTRADICTED-CLAIM`. All four remain in the metric denominator with score `0`; none may be dropped as inapplicable. An empty support-required path is also an unsupported atom when the case requires content there.

For a high-risk case, a matched conclusive proposition that is forbidden, unsupported, or contradicted emits `A-UNSUPPORTED-HIGH-RISK-CONCLUSION`. Any ambiguous or unmapped atom occurring in a declared `high_risk_conclusion_paths` location emits the same critical identity. Both conditions fail Gate 1. This path policy makes the decision deterministic even when unknown text cannot be labeled conclusive by a proposition matcher, and prevents novel high-risk wording from receiving a passing score. Supplementary LLM-judge output may help a human review unmatched language, but it cannot change the deterministic score or gate.

Citation coverage, a secondary metric, is support-required claim paths with at least one linked citation / all support-required claim paths regardless of semantic support. It is intentionally separate from claim-support precision.

For grounded-answer cases, zero returned citations produce citation precision `0`. A primary metric with zero applicable cases is unavailable and makes the run `INVALID`. Any applicable case that cannot be scored because required observation fields are missing makes the run `INVALID`; it is never removed from the denominator.

Returned rank is array order. Duplicate evidence or citation identities keep their first occurrence and later duplicates are ignored. MRR@10 uses the reciprocal rank of the first unique result satisfying any required evidence group, or `0` if none appears in the first ten.

Calculations retain exact integer counts and rational division through gate comparison. Gate deltas use unrounded values. Stored display values round half-even to four decimal places, and displayed percentages round half-even to two decimal places.

Each primary metric has at least one hand-calculated golden fixture containing its case numerator, denominator, case score, macro aggregate, and expected gate delta. Claim-support fixtures must include at least one supported atom, one contradiction using a correct document identity, one negation or modality reversal, one unmapped atom, one ambiguous atom, and one high-risk fail-closed result.

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
- SUT Adapter, evaluator, atomizer, claim normalizer, matcher set, proposition catalog, and threshold-manifest versions and configuration digests;
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
- The repository provides one documented command that performs deterministic artifact replay or a separately labeled best-effort live rerun from a manifest, subject to external model availability and credentials.

“Reproduction” has two explicit modes:

- deterministic artifact replay reloads stored normalized observations, recalculates evaluators, aggregates, and gates, and must reproduce the same canonical logical-content digests;
- best-effort live rerun sends the same versioned inputs and configuration to the pinned SUT and external provider, creates a new immutable run, and is not expected to reproduce identical generated text.

Clean-container equality applies to deterministic artifact replay. Live reruns report metric and gate deltas, provider availability, and observed drift; they never overwrite the original run. Published wording says “reproducible evaluation artifacts and calculations” rather than promising byte-identical external-model responses.

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
Day 1  Final design, reviewed specification and plan; pin AX baseline SHA; run capability preflight; freeze candidate-plan-v1
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

`candidate-plan-v1` is an immediately executable answer-context-depth comparison over the existing AX HTTP contract. Both runs retrieve with `top_k=5`; baseline passes `evidence_limit=3` and candidate passes the product default `evidence_limit=5`. SUT SHA, corpus, model, prompt, role, evaluator, thresholds, and retrieval measurement depth remain fixed. It is described as a configuration experiment, not a product-code improvement. Retrieval metrics are expected to remain identical and are retained as a confound check. A later product-fix candidate may be added as a separate versioned experiment but cannot silently replace this frozen pair.

Day 1 preflight must prove `/health/ready`, retrieval, answer, role visibility, synthetic corpus identity, and parsed-artifact observability. If parsed artifacts require the allowed local/test-only endpoint, that endpoint is the only AX evaluation-unblocking priority on Days 1–2. Failure to make it observable by the end of Day 2 is a go/no-go failure for the locked parsing acceptance criteria; dashboard ornamentation and supplementary LLM-judge work are cut before any evidence, coverage, or live-Verification requirement.

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
