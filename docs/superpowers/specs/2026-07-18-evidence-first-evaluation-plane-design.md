# Evidence-First HR/Labor RAG Evaluation Plane — Design

Date: 2026-07-18  
Status: PR review corrections for claim coverage and same-SHA scheduling independently approved; pending push and user review

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

The versioned `ax-sut-http-v1` interface has `preflight`, `parse`, `retrieve`, `answer`, and permission-checked `source_text` operations. The first mapping freezes methods, paths, schema digests, and field mappings in `ax-http-v1.yaml`:

- `GET /health/ready`;
- `POST /v1/retrieval/search`;
- `POST /v1/answers/generate`;
- `GET /v1/retrieval/source-text/{record_kind}/{record_id}`;
- existing attachment upload/status APIs plus one local/test-only parsed-document observation endpoint when AX preflight proves parsed text, sections, tables/lists, and spans are otherwise unavailable.

Canonical requests carry run, case, evaluation correlation, tenant, role, corpus, query or document, `top_k`, evidence limit, and timeout fields as applicable. Canonical observations carry opaque AX identifiers, order and rank, source/chunk/span identifiers, source class, authority, visibility, snippets, allowed full text, structured answer, Answer Mode, citations, provider metadata, timings, AX correlation identifiers, and explicit availability flags.

EvidenceSpan offsets are zero-based Unicode code-point offsets over canonical source text, inclusive at `start_char` and exclusive at `end_char`, and include the source-text digest. Citation identity is `(record_kind, record_id, evidence_span_id, source_text_digest)`.

Local/test runs use AX role headers; bearer credentials remain environment-only. Only public or synthetic corpora are allowed. Preflight records capabilities and schema digests. Required missing operations or fields fail closed when they violate coverage. Authentication and contract failures are permanent; only timeout, `429`, and `5xx` are retryable.

Issue #7 implementation lock:

- `ax-sut-http-v1` is pinned to AX_portfolio commit `c318b2192006bdb36a5bd5b3a2bc403425b45701`; `ax-http-v1.yaml` is the packaged operation, request/response field-mapping, and exact Pydantic response-schema-digest contract.
- Preflight checks `/health/ready` and the live OpenAPI path inventory. It records `preflight`, `retrieve`, `answer`, and `source_text` as available only when their frozen methods and paths exist.
- The pinned AX build has no endpoint that exposes parsed text, sections, tables/lists, and EvidenceSpan offsets. `parse` is therefore unavailable with `AX_PARSE_OBSERVABILITY_UNAVAILABLE`; the Adapter performs no guessed request and the parsing benchmark remains blocked until AX adds its separately reviewed local/test-only observation boundary.
- The pinned AX build also exposes no verifiable corpus identity. Preflight records the caller-declared public or synthetic corpus with `verified_by_sut=false` and `AX_CORPUS_IDENTITY_NOT_EXPOSED`; this is evidence of a capability gap, not a successful corpus check.
- Canonical requests preserve run, case, evaluation correlation, UUID tenant, user, roles, timeout, query or record identity, `top_k`, and evidence limit. Live responses preserve AX correlations, retrieval identities, visibility decisions, structured answer fields, citations, provider metadata, source text provenance, latency, and every attempt.
- timeout, `429`, and `5xx` use at most two retries after the first attempt. Other HTTP failures and response-schema failures are permanent and are never retried. Create-only capability manifests prevent accidental local overwrite.

### Normalized Observation

Preserves the answer, retrieved evidence, citations, Answer Mode, role context, timing, token and cost information when available, errors, attempt history, and provenance required for evaluation.

### Evaluator Registry

Runs registered parsing, retrieval, grounded-answer, and operational evaluators. Deterministic evaluators are authoritative where possible. LLM-judge results are explicitly supplementary.

### Immutable Result Store

Stores manifests, observations, metrics, failure labels, and aggregate outputs as append-only artifacts. Corrections create a new run or version.

#### Issue #6 tracer-bullet artifact contract

The first executable slice freezes two Typer commands: `braincrew-eval run` executes one `fixture-case-v1` document, while `braincrew-eval replay` re-evaluates one stored `run-artifact-v1`. The module form `python -m braincrew.cli` exposes the same commands for acceptance testing.

`run-artifact-v1` separates a volatile run envelope from canonical logical content:

- `run` contains `run_id`, `execution_mode=fixture`, and creation time;
- `provenance` records the automatically captured Evaluation Plane commit and dirty-worktree state, declared non-executed SUT identity, dataset content digest, `fixture-sut-v1`, `exact-answer-v1`, and explicit prompt/model placeholders;
- `logical_result` contains the versioned case snapshot, normalized observation, exact-answer evaluation, and gate decision;
- `logical_digest` is SHA-256 over canonical UTF-8 JSON containing `provenance` and recomputed `logical_result`, with sorted object keys and no insignificant whitespace.

The run envelope and artifact path are excluded from `logical_digest`, so the same versioned fixture inputs and contracts reproduce the same logical identity under a different `run_id`. Provenance remains inside the digest boundary so a SUT, dataset, adapter, evaluator, prompt, or model identity change cannot masquerade as the same logical result.

The Evaluation Plane commit is not accepted from a CLI argument. The command reads its own repository `HEAD` and dirty-worktree state immediately before building the artifact. The fixture-only SUT SHA remains a declared identity with `executed=false` and `dirty_worktree=null`, because this ticket does not inspect or execute an AX checkout.

The dataset content digest covers only the dataset identity, case contract, and public-or-synthetic source provenance. It excludes the fixture SUT response and prompt/model placeholders, which are execution configuration and observation inputs rather than dataset identity. The enclosing logical digest still covers those execution contracts through provenance and the normalized result.

The local JSON store uses create-only file semantics for `<run_id>.json`. A collision fails without changing existing bytes; corrections use a new run ID. Replay does not trust the stored score or gate: it recomputes them from the stored case snapshot and normalized observation, then rejects a mismatched logical payload or digest. This is application-level append-only evidence, not a claim of tamper-proof remote storage.

Pydantic validates the complete `run-artifact-v1` envelope and every nested run, provenance, observation, evaluation, and gate contract before storage and replay. A missing envelope or incompatible nested schema fails explicitly instead of replaying a partial artifact.

Because `run_id` becomes a local filename, `run-artifact-v1` accepts only 1–64 ASCII letters, digits, dots, underscores, and hyphens, beginning with a letter or digit. Evaluation Plane and SUT commit identities accept exactly 40 lowercase hexadecimal characters. Invalid identifiers fail before output creation, preventing path traversal and malformed provenance from entering the artifact store.

The fixture SUT records `executed=false` and `model.name=not-called`. It proves the CLI-to-gate and replay seams only; it does not claim a live AX call, production metric coverage, or model execution.

The executable slice preserves the architecture boundary in code: the fixture adapter creates only a normalized observation, the evaluator computes only the exact-answer score, the gate converts that score to a decision, the result store owns schema validation, digesting, append-only writes and replay, and the runner only orchestrates those components.

#### Issue #8 parsing-quality artifact contract

`parsing-dataset-v1` freezes 20 synthetic HR parsing cases at dataset `braincrew-parsing-quality@1.0.0` with exactly 14 Calibration and 6 Verification cases. The Pydantic contract rejects a different count or split, duplicate case IDs, unknown fields, malformed table rows, and EvidenceSpan text, offset, or source-digest drift. Each expected EvidenceSpan records zero-based Unicode code-point offsets with inclusive `start_char`, exclusive `end_char`, and the SHA-256 digest of canonical source text.

Dataset ground truth and fixture observations are separate versioned inputs. `parsing_observations_v1.json` is validated as `parsing-observation-batch-v1` under `fixture-parsing-sut-v1` and `fixture-parser-v1`; every available per-case observation must carry that exact parser version. Missing, duplicate, unknown, or version-drifted observations are rejected or make the run invalid rather than being silently ignored. Fixture observations prove deterministic evaluator and result-store behavior only; they do not claim live AX parsing quality.

`parsing-quality-v1` computes case-level EvidenceSpan recovery, structure preservation, metadata completeness, and applicable table/list preservation. Every score retains exact integer numerator and denominator; display decimals use half-even rounding to four places. Dataset aggregates are case-level macro means represented as reduced exact fractions, and table/list denominators include only applicable cases. The Verification EvidenceSpan denominator must be exactly 6 for this slice.

The runner emits `COMPLETED` only when all 20 expected cases are scored and the Verification EvidenceSpan denominator is 6. Any unavailable or missing parse observation, unexpected case, or denominator shortfall emits `INVALID`, preserves case diagnostics, omits the aggregate, and never emits `PASS` or a release-gate decision. This keeps parsing capability evidence distinct from a future compatible baseline-candidate release comparison.

`parsing-run-artifact-v1` stores the complete dataset and observation snapshots, case results, coverage, exact aggregates when valid, and provenance for the automatically captured Evaluation Plane state, declared non-executed SUT SHA, dataset content digest, adapter/parser versions, evaluator version, and explicit non-applicable prompt/model identities. Its logical digest covers provenance and logical content but excludes volatile run ID, timestamp, and path. The result store uses create-only `<run_id>.json` files; a collision cannot mutate existing bytes.

The pinned AX contract remains unchanged. The Issue #7 live smoke proved `parse` unavailable with `AX_PARSE_OBSERVABILITY_UNAVAILABLE`; Issue #8 therefore supplies a fixture-complete path and a tested invalid live-capability outcome without adding or inferring an AX parsing endpoint.

#### Issue #9 retrieval-quality artifact contract

`retrieval-dataset-v1` freezes 30 synthetic HR/labor retrieval cases at dataset `braincrew-retrieval-quality@1.0.0` with exactly 21 Calibration and 9 Verification cases. Every case records role, query, corpus version, exact required evidence groups, preferred authority, forbidden identities, evaluator applicability, provenance, and review state. Retrieval identity is the exact tuple `(record_kind, record_id, evidence_span_id, source_text_digest)`; nullable members are compared as stored and fuzzy semantic matching is prohibited.

Required evidence is grouped so any exact alternative can satisfy one group. Returned array order defines one-based rank. Duplicate identities keep their first occurrence and later duplicates do not create another hit. Recall@5 is matched required groups within the first five unique identities divided by all required groups, even when a duplicate means the fifth unique identity originally appeared after rank 5. MRR@10 is the reciprocal rank of the first unique identity satisfying any required group, or `0/1` when no such identity appears. Authority priority is applicable only with reviewed resolved ground truth and scores `1/1` only when the first relevant unique result has the case's preferred authority level. Every exact score retains integer numerator and denominator, requires `numerator <= denominator`, and stores a display value that exactly matches half-even rounding to four places; aggregates are unweighted case-level macro means represented as reduced fractions. A published aggregate metric with zero applicable cases invalidates the run with an explicit denominator reason instead of dividing by zero or omitting the metric silently.

Expected source identity quality is explicit rather than silently filtered. A `missing` or `ambiguous` identity with `denominator_zero` retains its declared evidence group in Recall@5 and MRR@10 with score zero and emits `R-EXPECTED-SOURCE-IDENTITY-UNRESOLVED`. The same unresolved identity with policy `invalid` emits an `INVALID` case with no quality scores. All 9 Verification cases must carry resolved Recall@5 ground truth, so the Verification denominator cannot fall below 9 without invalidating the run.

Forbidden visibility is an exact zero-tolerance identity check over every returned unique candidate. Any forbidden tuple emits deterministic critical failure `R-FORBIDDEN-VISIBILITY`, identifies the affected case in `hard_failure_cases`, and remains visible beside aggregate diagnostics. The forbidden scan runs before invalid-return paths, so an unavailable, query-mismatched, or invalid-policy observation that still contains a returned forbidden identity remains `INVALID` while preserving its hard-failure evidence. A fully scored run remains `COMPLETED` because the canonical run-state contract reserves `FAILED` for execution that could not finish; a later release gate must fail any compatible run containing this hard failure. Missing, unavailable, query-mismatched, or unexpected observations make the run `INVALID`, suppress the aggregate, and never disappear from coverage.

`retrieval-run-artifact-v1` stores the full dataset and observation snapshots, including query, retrieved identity, rank, authority, and visibility decision; case evaluations; exact macro aggregates; and automatically captured Evaluation Plane, declared non-executed SUT, dataset content digest, `fixture-retrieval-sut-v1`, and `retrieval-quality-v1` provenance. Its logical digest covers provenance and logical content but excludes volatile run ID, timestamp, and path. The create-only result store rejects run-ID collisions without mutating existing bytes. Replay reloads the complete retrieval envelope, recomputes every case and aggregate from the stored dataset and observations, and rejects either logical-content or digest drift. `COMPLETED` and `INVALID` describe the evidence state here; `hard_failure_cases` is the separate zero-tolerance release-gate input, and none of these fields is itself a release `PASS` decision.

The pinned `ax-sut-http-v1` live smoke uses the same dataset and evaluator identities against AX commit `c318b2192006bdb36a5bd5b3a2bc403425b45701`. The final synthetic request completed successfully but returned zero candidates; the durable evidence therefore records an empty retrieved-identity/rank/authority list and zero Recall@5, MRR@10, and authority scores without claiming positive live retrieval quality. AX still does not verify the declared corpus identity, so this one-case smoke cannot replace the future complete live benchmark.

### Comparison and Release Gate

Rejects incompatible runs, computes paired baseline-candidate deltas, applies frozen thresholds, and records a pass, fail, or invalid decision with reasons.

### Dashboard and Report Exporter

Generates sanitized versioned JSON exports and renders interactive static comparisons, gate traces, and representative failures. It cannot execute experiments or mutate evidence.

## 8. Dataset contract

The dataset contains exactly 100 cases:

```text
Primary focus                 Calibration  Verification  Total
Parsing                                14             6     20
Retrieval                              21             9     30
Grounded answer                        30            10     40
Visibility and abstention               5             5     10
Total                                  70            30    100
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

Minimum applicable Verification denominators are 6 for EvidenceSpan recovery, 9 for Recall@5, 10 each for claim-support and citation precision, 15 for Answer Mode accuracy, and 5 for abstention accuracy. Actual denominators are reported. Falling below any primary minimum makes the run `INVALID`.

Each case contains a stable identifier, dataset version, split, focus and tags, role, query, document references, corpus versions, expected and alternative EvidenceSpans, forbidden evidence, visibility rules, expected Answer Mode, a versioned proposition catalog, required-output paths, forbidden propositions, evaluator applicability, difficulty, provenance, license, and review history. Cases cannot narrow the evaluator-derived coverage of generated answer paths.

### Issue #12 integrated dataset-freeze implementation lock

Issue #12 freezes `braincrew-evaluation-dataset@1.0.0` in `datasets/dataset_manifest_v1.json` and publishes its status in `datasets/DATASET_CARD.md`. The manifest composes, rather than copies, the existing versioned parsing, retrieval, and grounded datasets. Validation normalizes them into exactly 100 globally unique cases with the locked 20/30/40/10 primary-focus allocation, 70/30 Calibration/Verification split, risk classification, provenance and `CC0-1.0` license status. The frozen integrated scoring-content digest is `sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b`; it covers the normalized manifest contract and every scoring-relevant field in all three component datasets. Any scoring-relevant edit requires updated component and integrated digests and therefore a new compatible dataset version before comparison.

Validation is fail closed. Missing components or dataset card, component paths outside the dataset bundle, duplicate or unstable identities, duplicate scoring content, wrong component schema declarations, count or split drift, absent or unreviewed provenance, component/case source-type disagreement with the integrated provenance declaration, unapproved component- or case-level license, invalid risk policy, focus-specific applicability drift, insufficient Verification applicability, Calibration/Verification scoring-content overlap, banned free-text answer keys, expected grounded-answer literals embedded in queries, and digest mismatch produce `INVALID` rather than a partial aggregate. Retrieval cases must apply Recall@5 and MRR@10; all 40 grounded-answer cases must apply claim support, citation precision, citation coverage, and Answer Mode; all 10 visibility/abstention cases must apply Answer Mode and abstention. Case-level provenance status is derived from the validated review state rather than asserted as a constant. These semantic invariants are shared by bundle load and snapshot replay, including path, source-type, and dataset-level license checks. Minimum Verification denominators remain EvidenceSpan recovery 6, Recall@5 9, claim support 10, citation precision 10, Answer Mode 15, and abstention 5.

`braincrew-eval run-dataset` combines the frozen parsing, retrieval, and grounded fixture observations into one immutable `dataset-run-artifact-v1`. It retains case-level and aggregate component results, the normalized dataset snapshot, exact Evaluation Plane and declared SUT provenance, and a logical digest that excludes run-envelope identity so independent executions can be compared. Replay recomputes dataset validation and every component evaluation before accepting the stored logical digest. The existing 20-, 30-, and 50-case commands and replay contracts remain independently executable; Issue #12 also repairs the previously unsupported `parsing-run-artifact-v1` replay path.

The rejected alternatives were concatenating all cases into a fourth authoritative copy, hashing only case IDs or top-level metadata, silently dropping invalid cases or reducing denominators, and treating the public Verification split as secret. They were rejected because they invite source drift, allow scoring changes to escape invalidation, or turn missing evidence into better-looking scores. The accepted trade-off is that even a legitimate scoring correction invalidates the frozen digest and needs explicit versioning. Failure modes include content-equivalent cases with different IDs, answer text embedded in dataset keys, schema declarations that disagree with component contracts, missing license evidence, and replay artifacts rehashed after snapshot tampering. This ticket remains fixture-authoritative and does not implement Issue #13 comparison or release gates, live baseline/candidate runs, dashboard work, LLM-as-judge scoring, AX product changes, or Agent trajectory evaluation.

## 9. Failure taxonomy

- `P-*`: parsing structure, table, list, metadata, or EvidenceSpan failure;
- `R-*`: evidence miss, authority inversion, visibility leak, or distractor capture;
- `A-*`: unsupported claim, citation mismatch, incomplete support, wrong mode, failed abstention, unsafe overclaim, or role leakage;
- `O-*`: latency, cost, timeout, or malformed-response failure;
- `SYS-*`: adapter, provenance, compatibility, or replay failure;
- `TRJ-*`: reserved and unused by the first release.

One observation may receive multiple labels. Taxonomy diagnoses mechanisms, metrics measure prevalence, and gates decide release eligibility.

The versioned taxonomy assigns `critical`, `major`, `minor`, or `diagnostic` severity. Gate-authoritative critical identities are deterministic `(case_id, failure_code, evaluator_contract_version)` tuples:

- forbidden returned source/chunk/span identity: `R-FORBIDDEN-VISIBILITY`;
- case-declared protected identifier or forbidden role claim in the answer: `A-ROLE-LEAKAGE`;
- unsupported conclusive claim on a high-risk case: `A-UNSUPPORTED-HIGH-RISK-CONCLUSION`;
- wrong mode or forbidden conclusive claim on a required-abstention case: `A-FAILED-ABSTENTION`;
- required provenance missing: `SYS-PROVENANCE-MISSING`;
- incompatible or under-covered comparison: `SYS-COMPARISON-INVALID`.

A baseline critical identity is removed only if its case remains applicable and the identity is absent in the candidate. Any candidate critical identity absent from baseline is new. LLM-judge output cannot create, clear, or reclassify critical identity.

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

### Metric contract v2

Every primary metric is a case score in `[0, 1]`; dataset results are unweighted macro means over applicable cases. Micro-pooling is prohibited. Gold evidence uses requirement groups with exact acceptable alternatives. Parsing spans match document ID, source digest, and inclusive/exclusive code-point offsets. Retrieval and citations match record kind, record ID, span ID, and source digest. Any declared alternative satisfies its group.

- EvidenceSpan recovery = matched required span groups / required span groups.
- Recall@5 = required evidence groups appearing in the first five unique returned evidence identities / required evidence groups.
- Claim-support precision = supported generated claim atoms / all generated claim atoms. Unsupported, contradicted, ambiguous, and unmapped atoms remain in the denominator with score zero.
- Citation precision = unique citations belonging to a matched proposition's supporting evidence groups for one of their declared existing claim paths / all unique citations.
- Answer Mode accuracy is exact normalized-enum equality.
- Abstention accuracy requires the expected abstention mode and absence of case-declared forbidden conclusive claims.

#### Claim-proposition contract v1

The first release uses a closed-world deterministic proposition catalog for the frozen dataset rather than claiming unrestricted natural-language understanding. Each case declares stable proposition IDs, subject/predicate/object concepts, affirmed or denied polarity, modality, risk and conclusion flags, versioned literal or regular-expression surface matchers, supporting and contradicting evidence groups, and allowed or forbidden Answer Modes.

`claim-traversal-v1` automatically enumerates every non-empty generated value in `summary`, `answer`, `grounds[*]`, `review_points[*]`, `additional_checks[*]`, and `risk_warning` for every grounded-answer case, not only high-risk cases. It splits every value on normalized newlines and `.`, `?`, `!`, `。`, `？`, or `！`, and gives each atom the stable identity `(claim_path, atom_index, normalized_text_digest)`. A case cannot opt out a returned path. Case-declared required-output paths add a zero-score placeholder when expected content is absent or empty; they never narrow generated-content scoring.

Normalization uses Unicode NFC, CRLF-to-LF conversion, edge trimming, internal whitespace collapse, and declared punctuation variants only; it never removes negation or modality and uses no stemming or embedding similarity. Matchers are anchored whole-atom literals or bounded regular expressions.

An atom is supported only when it maps to exactly one proposition, at least one citation linked to its exact parent path belongs to the proposition's supporting evidence, no citation linked to that path belongs to contradicting evidence, polarity and modality match, the Answer Mode is allowed, and no forbidden proposition occurs in the atom. Therefore one supporting citation cannot cancel out a second contradictory citation. Atomizer, normalizer, matcher-set, and proposition-catalog versions and digests are required comparison compatibility fields.

Unmapped, ambiguous, unsupported, and contradicted atoms receive score zero and remain in the denominator. An absent or empty required-output path adds one unsupported placeholder atom. `high-risk-guard-v1` consumes the same `claim-traversal-v1` atoms and adds fail-closed behavior rather than broader coverage. For high-risk cases, a matched conclusive proposition that is forbidden, unsupported, or contradicted fails closed as `A-UNSUPPORTED-HIGH-RISK-CONCLUSION`, and every ambiguous or unmapped atom produces the same critical failure. An LLM judge may explain unmatched language but cannot alter the score or gate.

Example: if rule 15 says that an employee cannot be dismissed immediately, the proposition “immediate dismissal is prohibited” lists rule 15 under `supports`, while “immediate dismissal is allowed” lists the same evidence under `contradicts` and is forbidden. An answer saying “dismiss immediately” with a citation to rule 15 therefore scores zero and triggers the high-risk gate even though it cited the correct document identity.

Secondary citation coverage measures whether every generated path from `claim-traversal-v1` has a linked citation, with every absent or empty required-output path retained in the denominator. It is explicitly not semantic groundedness. Grounded cases with no citations score citation precision `0`. Zero applicable cases or missing required observation fields makes the run `INVALID`.

Array order defines rank; duplicate identities keep the first occurrence. MRR@10 is reciprocal rank of the first unique relevant result or zero. Gates use unrounded exact counts and rational divisions. Stored decimals use half-even four-place display rounding and percentages use half-even two-place display rounding. Each primary metric requires a hand-calculated golden containing case and macro calculations plus expected gate delta. Claim-support goldens include a correct support, a correct-document contradiction, mixed supporting and contradicting citations, a negation or modality reversal, an unmapped atom, an ambiguous atom, a non-high-risk unsupported claim in `additional_checks[*]`, a rejected attempt to narrow traversal, and a high-risk fail-closed case.

#### Issue #10 grounded-answer implementation lock

Issue #10 introduces the bounded dataset `braincrew-grounded-answer-initial@1.0.0` with ten synthetic Verification cases. This is the minimum executable claim-support and citation-precision denominator, not the complete 40-case grounded-answer dataset and not the Issue #11 Answer Mode or abstention suite.

The executable contract versions are `claim-proposition-v1`, `claim-traversal-v1`, `claim-atomizer-v1`, `claim-normalizer-v1`, `claim-matcher-set-v1`, `claim-proposition-catalog-v1`, `source-text-resolution-v1`, `high-risk-guard-v1`, and evaluator `grounded-answer-v1`. `claim-traversal-v1` owns coverage: cases may declare concrete required-output paths but cannot provide a traversal allowlist. Every non-empty `summary`, `answer`, `grounds[*]`, `review_points[*]`, `additional_checks[*]`, and `risk_warning` value is atomized. Required but absent concrete paths contribute one `missing_required` placeholder.

Atom identity is `(claim_path, atom_index, normalized_text_digest)`. Normalization applies Unicode NFC, CRLF/CR-to-LF conversion, edge trimming, and inline-whitespace collapse before splitting on normalized newlines and sentence terminators. It does not remove negation or modality. Literal matchers use whole-atom equality; regular expressions must be explicitly bounded.

Each proposition freezes subject, predicate, optional object, polarity, canonical modality (`must`, `may`, `must_not`, `unknown`, or `review_required`), risk, conclusion and forbidden flags, allowed and forbidden Answer Modes, digest-identified surface matchers, and supporting and contradicting evidence groups. A citation is eligible only when its `(record_kind, record_id, evidence_span_id, source_text_digest)` identity matches and `source-text-resolution-v1` verifies the permission-checked text returned through `AxHttpAdapter.source_text()` against the evidence matcher. Fixture observations store that normalized Adapter result; they do not replace the live Adapter seam or claim a live answer-quality run. Document identity alone is not semantic support.

An atom is supported only when it maps to exactly one non-forbidden proposition, the observed Answer Mode is allowed and not forbidden, its exact parent path has resolved supporting evidence, and that path has no resolved contradicting evidence. Mixed support and contradiction therefore scores zero. Unsupported, contradicted, unmapped, ambiguous, and missing-required atoms remain in claim-support precision's denominator and use the locked identities `A-UNSUPPORTED-CLAIM`, `A-CONTRADICTED-CLAIM`, `A-UNMAPPED-CLAIM`, and `A-AMBIGUOUS-CLAIM` where applicable. Citation precision deduplicates citation identities and represents zero returned citations as exact zero `0/1`; citation coverage measures only cited generated paths while retaining missing required paths in the denominator. A citation naming an absent placeholder path cannot enter the coverage numerator. Zero applicable metric cases makes the run `INVALID`.

The hand-calculated ten-case fixture goldens are claim-support precision `1/4`, citation precision `9/20`, and citation coverage `13/20`. Tests freeze every case numerator and denominator, the three macro aggregates, and a `0.00` percentage-point compatibility-replay gate delta. Cases cover correct support, mixed citations, a forbidden `may` conclusion, unmapped and ambiguous atoms, unsupported non-high-risk `additional_checks[*]`, a missing required path, disallowed modality/Answer Mode use, unresolved source support, and a cited `grounds[0]` claim. `GA-003` and `GA-008` preserve `A-UNSUPPORTED-HIGH-RISK-CONCLUSION` hard-failure evidence. A fully evaluated fixture run remains `COMPLETED`; hard-failure evidence is consumed by a later release gate and is not mislabeled as an infrastructure execution failure.

The CLI command `braincrew-eval run-grounded` writes create-only `grounded-run-artifact-v1`. It fails closed when the CLI-declared SUT SHA differs from the observation batch SUT SHA. The artifact records the exact Evaluation Plane state, declared non-executed AX SUT SHA, dataset digest and version, fixture adapter version, prompt/model non-execution identities, and the atomizer, normalizer, matcher-set, proposition-catalog, case-catalog, traversal, source-resolution, guard, and evaluator compatibility versions or digests. Replay revalidates the complete artifact, recomputes every case and macro metric from stored dataset and observation snapshots, and rejects metric or digest tampering.

Rejected alternatives were document-identity-only grounding, author-selected traversal allowlists, dropping unmatched atoms, and using an LLM judge to repair deterministic failures. They were rejected because each can inflate groundedness or hide unsafe uncertainty. The accepted trade-off is bounded closed-world language coverage: unseen valid paraphrases score unmapped until a reviewed matcher and new dataset version are added.

Issue #10 validation is fixture-authoritative only. It does not claim the full grounded-answer benchmark, live AX answer quality, LLM-as-judge quality, AX product changes, or Agent trajectory evaluation.

#### Issue #11 answer-mode, abstention, and visibility implementation lock

Issue #11 replaces the bounded initial slice with `braincrew-answer-quality@1.0.0`: exactly 40 grounded-answer cases split 30 Calibration / 10 Verification and 10 visibility/abstention cases split 5 Calibration / 5 Verification. All 50 cases apply Answer Mode accuracy; the frozen Verification denominator is therefore 15. All ten visibility/abstention cases apply abstention accuracy; its frozen Verification denominator is 5. Missing or unavailable observations, runtime split drift, or lower applicable Verification coverage makes the run `INVALID` and suppresses aggregates.

Answer Mode scoring uses `answer-mode-v1` exact enum equality across `direct_grounded`, `conditional_grounded`, `insufficient_evidence`, `out_of_scope`, and `review_required`. `abstention-v1` scores one only when the returned mode equals the case's required `insufficient_evidence` or `out_of_scope` mode and no generated atom matches a case-declared forbidden conclusive proposition. The forbidden scan fails closed when an atom is ambiguous but any candidate proposition is forbidden. A wrong required mode or forbidden conclusion emits the zero-tolerance `A-FAILED-ABSTENTION` hard failure. `answer-visibility-v1` scans each full normalized generated field before sentence punctuation is atomized, so a protected literal such as an email address cannot be split out of detection; case-declared forbidden-role propositions use the evaluator atoms. Either condition emits `A-ROLE-LEAKAGE` regardless of citation, Answer Mode, availability, or other metric quality.

Every fixture observation records `executed_role`. A mismatch with the case role produces `SYS-GROUNDED-ROLE-MISMATCH` and `INVALID`; an answer produced under one role cannot be graded as evidence for another. An unavailable observation still makes the run `INVALID`, but any role-leakage evidence present in its returned fields remains in the case and run hard-failure records instead of being erased by the invalid-return path. Unsupported confident high-risk conclusions continue to emit `A-UNSUPPORTED-HIGH-RISK-CONCLUSION`, so Issue #11 extends rather than weakens the Issue #10 evidence guard. A fully scored run containing deterministic safety failures remains `COMPLETED` with immutable `hard_failure_codes`, atom identities, and case identities for the later release gate.

The hand-calculated 50-case macro goldens are claim-support precision `13/16`, citation precision `69/80`, citation coverage `73/80`, Answer Mode accuracy `49/50`, and abstention accuracy `4/5`. Case-level exact fractions are frozen; `GA-003`, `GA-008`, `VA-003`, `VA-005`, `VA-008`, and `VA-009` preserve the intended unsupported-confidence, failed-abstention, protected-identifier, forbidden-conclusion, and forbidden-role hard-failure evidence.

`grounded-run-artifact-v1` remains create-only and stores all 50 case evaluations plus macro aggregates. Its compatibility manifest adds the version and snapshot-derived digest of `answer-mode-v1`, `abstention-v1`, and `answer-visibility-v1` alongside the dataset, evaluator, Adapter, SUT, claim, traversal, normalizer, matcher, source-resolution, and guard identities. Replay recomputes evaluation, dataset provenance, SUT identity, and every compatibility digest from the immutable dataset and observation snapshots, rejecting a tampered dataset, SUT, or contract identity even when the attacker rehashes the top-level logical digest.

Rejected alternatives were text-only abstention heuristics, trusting the declared case role without observation-side execution role, silently reducing denominators, and letting correct grounding or mode scores offset leakage. They were rejected because they make safety evidence ambiguous or allow missing execution to improve results. The accepted trade-off is a reviewed closed-world catalog: an unseen sensitive paraphrase requires a new protected literal or proposition and a new compatible dataset version. This ticket remains fixture-authoritative and does not introduce the Issue #12 full 100-case freeze, live baseline/candidate comparison, release thresholds, dashboard work, LLM-as-judge scoring, AX product changes, or Agent trajectory evaluation.

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
- adapter, evaluator, atomizer, claim normalizer, matcher set, proposition catalog, and threshold versions and configuration digests;
- prompt hash, provider, model, and generation parameters;
- dependency-lock and runtime-environment digests;
- live or fixture mode;
- times, seeds where applicable, and all attempts.

Published results require clean committed states. Fixture and live runs are never compared. Submission claims require at least one complete live-SUT Verification run. Results are append-only, secrets are redacted, and missing compatibility fails closed.

Deterministic artifact replay recalculates evaluators, aggregates, and gates from stored normalized observations and must reproduce canonical logical-content digests in a clean container. A best-effort live rerun sends the same pinned inputs and configuration, creates a new run, and may differ because of external-model stochasticity or availability. It reports drift and never overwrites the original. Publication claims reproducible artifacts and calculations, not byte-identical external responses.

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

Required layers are schema tests, hand-calculated metric goldens, claim atomization and proposition-matcher tests, relevant property tests, Adapter HTTP contracts, state and storage invariants, fixture-mode E2E, live AX smoke and Verification, dashboard export and browser checks, and clean Docker reproduction.

Adversarial tests must prove that a correct document with the opposite proposition fails support, negation and modality reversals fail, unknown high-risk wording fails closed, retry limits hold, non-retryable errors invalidate, results remain immutable, incompatible and fixture-live comparisons are rejected, hard-gate safety failures block release, exports are redacted, and all 30 live Verification cases execute.

## 16. Ten-day execution sequence

```text
Day 1  Design, reviewed spec and plan; pin baseline SUT SHA; preflight capabilities; freeze candidate-plan-v1
Day 2  Contracts, manifests, artifact store and 20 parsing cases
Day 3  Adapter, retrieval evaluator and 20 cases
Day 4  Answer evaluators and 20 cases
Day 5  Taxonomy, gates and 20 cases
Day 6  Finish 100 cases; review and freeze 70/30 digest
Day 7  Live baseline and failure analysis; candidate-configuration preparation
Day 8  Reuse the pinned baseline SUT SHA, freeze candidate configuration, and run compatible live Verification A/B
Day 9  Dashboard, README, reproduction and interview dossier
Day 10 Independent QA, demo, resume bullets and release PR
```

The guaranteed first experiment is `candidate-plan-v1`: both runs use `top_k=5`; baseline uses `evidence_limit=3` and candidate uses `evidence_limit=5` through the existing answer endpoint. SUT SHA, corpus, model, prompt, roles, evaluators, thresholds, and retrieval depth stay fixed. This is labeled an answer-context-depth configuration experiment. Retrieval metrics must remain identical as a confound check. A product-code candidate may be evaluated separately but cannot replace the frozen pair without a new candidate-plan version.

Day 1 preflight verifies health, retrieval, answer, role visibility, synthetic corpus identity, and parsed-artifact observability. If parsing needs the permitted local/test-only observation endpoint, it is the sole AX unblocking priority through Day 2. Missing that checkpoint is a no-go for the locked parsing acceptance criteria; dashboard ornamentation and supplementary judge analysis are cut before any evidence requirement.

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
