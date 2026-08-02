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
: Dataset manifest, schema validation, content digest, split assignment, distribution report, provenance report, dataset card, deterministic full fixture create/replay, and representative passing and failing cases.

Issue #12 implementation decision:
: `datasets/dataset_manifest_v1.json` now composes the existing parsing, retrieval, and grounded sources as `braincrew-evaluation-dataset@1.0.0`; it does not create a second copy of their case content. `datasets/DATASET_CARD.md` records the approved synthetic `CC0-1.0` provenance/license boundary, risk policy, applicability minimums, leakage controls, exclusions, and frozen integrated digest `sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b`.

Why the digest covers normalized scoring content:
: Identity-only or file-byte-only hashes would either miss evaluator-relevant edits or change for irrelevant formatting. The accepted digest covers the normalized manifest contract plus every validated component field used to define scoring, provenance, risk, applicability, and split identity. A legitimate scoring correction is intentionally incompatible until the dataset version and digests are updated.

Execution and replay evidence:
: `braincrew-eval run-dataset` executes all 100 fixture observations into an immutable `dataset-run-artifact-v1` with component case results and aggregates. Independent run IDs produce the same logical digest because run-envelope identity is excluded. Replay revalidates the frozen snapshot and recomputes parsing, retrieval, and grounded evaluations. The earlier parsing artifact replay gap was reproduced as an unsupported-schema failure and repaired without changing the 20-, 30-, or 50-case contracts.

Invalid-state boundary:
: Missing or duplicate cases, unstable identities, count/split drift, schema mismatch, a component path outside the dataset bundle, missing or unreviewed provenance, source-type disagreement between the manifest and any component/case, unapproved component- or case-level license, invalid risk policy, focus-specific metric applicability drift, inadequate Verification denominators, cross-split scoring-content duplication, an expected grounded-answer literal embedded in a query, banned answer keys, or digest mismatch returns `INVALID`; it never publishes a partial aggregate. Retrieval, grounded-answer, and visibility/abstention cases each preserve their required metric family rather than merely enabling any one metric. Case-level provenance status is derived from the source review state, and bundle load and replay share the same semantic checks. A successful fixture run demonstrates evaluator and artifact determinism only, not live AX quality.

Likely follow-ups:

- "Is 100 statistically sufficient?" — It is a scoped engineering regression suite, not a population estimate; claims remain bounded to this dataset.
- "How did you prevent leakage?" — Freeze split and digest, prohibit final tuning on Verification, and version any correction.
- "Why is the Verification split not secret?" — The repository is public; the defensible control is a frozen pre-tuning assignment and digest, not secrecy.
- "Why not merge the three JSON files into one?" — Composition preserves one authoritative source per existing contract and lets the registry detect drift without introducing a fourth case copy.
- "What does a matching replay prove?" — It proves the stored snapshot reproduces the same deterministic evaluator result and logical digest; it does not prove live model quality.
- "Why not use only LLM-generated labels?" — Expected evidence and safety constraints require deterministic reviewable contracts; LLM assistance cannot be the sole authority.
- "What if a metric has too few applicable Verification cases?" — The run becomes invalid under the frozen minimum-denominator contract; it does not publish a misleading average.
- "Could a case count toward 100 without testing its declared focus?" — No. Retrieval requires Recall@5 and MRR@10, grounded-answer requires its claim/citation/mode metrics, and visibility/abstention requires mode and abstention, in addition to the aggregate Verification minimums.
- "How do you stop the prompt from containing the answer?" — Grounded queries are checked against their literal proposition matchers, and any exact normalized answer literal makes the dataset invalid.

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

Semantic-support boundary:
: Claim-support is not inferred merely from a linked document. `claim-traversal-v1` inspects every generated value in summary, answer, grounds, review points, additional checks, and risk warning for every grounded-answer case, regardless of risk level. Each frozen case defines a closed-world proposition catalog with polarity, modality, supporting and contradicting evidence, and deterministic Korean surface matchers. A generated claim atom passes only when its meaning, citation, evidence stance, and Answer Mode agree. Any contradictory citation linked to the same path makes the atom fail even when another citation supports it.

Issue #10 implementation decision:
: The first executable grounded-answer slice uses ten synthetic Verification cases at `braincrew-grounded-answer-initial@1.0.0`, with canonical `claim-proposition-v1` modalities, `claim-traversal-v1`, permission-checked source-text resolution through the AX SUT Adapter seam, three exact macro metrics, and fail-closed high-risk evidence. Ten cases satisfy the initial claim-support and citation-precision denominator but are explicitly not the complete 40-case answer benchmark.

Why this design:
: Citation identity proves where the answer pointed, not whether the source actually supports the sentence. The evaluator therefore resolves the pinned source text and checks its stance. Traversal belongs to the evaluator, so a case author cannot omit a difficult returned field. Unmapped and ambiguous language stays in the denominator, making evaluator uncertainty visible instead of improving the score by omission.

Rejected alternative:
: Document-level citation matching, case-authored path allowlists, dropping unmatched atoms, and LLM-judge overrides were rejected. A correct document can contradict the generated claim, path allowlists can cherry-pick coverage, dropping atoms hides uncertainty, and a judge override would make deterministic release evidence irreproducible.

Trade-off:
: Closed-world proposition catalogs are auditable but do not claim unrestricted Korean natural-language understanding. A legitimate unseen paraphrase scores unmapped until a reviewed matcher and dataset version explicitly cover it.

Failure modes and response:
: Mixed supporting and contradicting citations on one claim path score the atom zero. Missing required output creates a zero-score placeholder that remains in the coverage denominator but cannot gain numerator credit from a dangling citation. Unsupported, contradicted, unmapped, and ambiguous atoms preserve the exact release identities `A-UNSUPPORTED-CLAIM`, `A-CONTRADICTED-CLAIM`, `A-UNMAPPED-CLAIM`, and `A-AMBIGUOUS-CLAIM`; high-risk variants also preserve `A-UNSUPPORTED-HIGH-RISK-CONCLUSION`. A zero-applicability metric or missing Verification observation makes the run `INVALID` rather than silently shrinking coverage.

Validation evidence:
: The ten fixture cases freeze every case numerator and denominator and produce hand-calculated macro goldens of claim-support precision `1/4`, citation precision `9/20`, and citation coverage `13/20`, with a `0.00` percentage-point compatibility-replay delta. Controlled HTTP evidence proves that cited source text is fetched through `AxHttpAdapter.source_text()`. `grounded-run-artifact-v1` rejects a CLI/observation SUT SHA mismatch and records dataset, evaluator, adapter, SUT, atomizer, proposition, traversal, normalizer, matcher-set, case-catalog, source-resolution, and guard identities or digests; replay recomputes the stored snapshots and rejects tampering. This proves deterministic fixture evaluation and the Adapter seam, not live AX answer quality.

Likely follow-ups:

- "Why not use an LLM judge for paraphrases?" — A judge can later explain unmatched language, but it cannot change the authoritative score or clear a critical identity because that would weaken reproducibility.
- "Why does a correct citation still fail?" — Citation identity and evidence stance are different. If the source says dismissal is prohibited while the answer says it is allowed, the identity is correct but the proposition is contradicted.
- "Why only ten cases?" — Ten is the locked initial Verification denominator for these two primary metrics. The remaining grounded-answer and Issue #11 mode/abstention cases are separately scoped and cannot be claimed early.
- "Why can a completed run contain a hard failure?" — `COMPLETED` means execution and scoring succeeded. The preserved hard-failure identity is later consumed by the release gate; calling it an execution failure would mix quality evidence with infrastructure state.
- "Why store both versions and digests?" — A version names the contract family; the digest proves the exact atomizer, normalizer, matcher set, proposition catalog, and case catalog configuration used. A changed catalog cannot masquerade as a comparable run under the same label.

Issue #11 implementation decision:
: Freeze `braincrew-answer-quality@1.0.0` as 40 grounded-answer cases with a 30/10 Calibration/Verification split plus 10 visibility/abstention cases with a 5/5 split. Apply exact Answer Mode accuracy to all 50 cases, apply abstention accuracy to the 10 visibility/abstention cases, and preserve zero-tolerance hard failures separately from run completion.

Why this design:
: Answer safety has three independent questions: did AX choose the required mode, did an abstention still make a forbidden conclusion, and did the generated answer expose role-protected content? Separate deterministic contracts prevent one correct answer dimension from hiding another unsafe dimension. Recording the observation's executed role prevents an answer produced under a privileged role from being scored against a lower-privilege case.

Rejected alternatives:
: Keyword-only refusal detection, using only the case's declared role, shrinking denominators when telemetry is missing, combining leakage with a weighted quality score, and allowing an LLM judge to clear deterministic failures. Each alternative can make an unsafe or unexecuted case appear better than the evidence supports.

Trade-offs and failure modes:
: The visibility contract is intentionally closed-world. A sensitive paraphrase that is absent from reviewed protected literals and proposition matchers can be missed until the dataset is versioned. Full normalized fields are scanned before punctuation atomization, so dots inside a protected email address do not hide it; an unavailable observation still makes the run `INVALID` but cannot erase detected leakage. Forbidden-conclusion detection also fails closed when a generated atom matches multiple propositions and any match is forbidden. To keep this limitation auditable, artifacts record `answer-mode-v1`, `abstention-v1`, and `answer-visibility-v1` plus snapshot-derived digests. Missing, unavailable, role-mismatched, split-drifted, or under-applicable evidence makes the run `INVALID`; wrong required mode and forbidden conclusive output emit `A-FAILED-ABSTENTION`; protected identifiers or forbidden-role propositions emit `A-ROLE-LEAKAGE`. Unsupported confident high-risk output retains `A-UNSUPPORTED-HIGH-RISK-CONCLUSION` from the grounded contract.

Validation evidence:
: The fixture executes all 50 cases through the installed CLI and create-only result store. Hand calculations freeze claim support `13/16`, citation precision `69/80`, citation coverage `73/80`, Answer Mode accuracy `49/50`, and abstention accuracy `4/5`, with every case fraction stored immutably. Verification applicability is exactly 15 for Answer Mode and 5 for abstention. `GA-003`, `GA-008`, `VA-003`, `VA-005`, `VA-008`, and `VA-009` retain the intended hard-failure identities. Replay recomputes snapshot-derived evaluation, compatibility, dataset provenance, and SUT identity and rejects rehashed Answer Mode, dataset-digest, or SUT-identity tampering. This is reproducible fixture evidence, not a live AX answer-quality claim or a release decision.

Likely follow-ups:

- "Can a correct refusal still fail?" — Yes. If it repeats a forbidden conclusive claim or exposes a protected identifier, abstention or role leakage fails even when the enum is correct.
- "Why is Answer Mode `49/50` but abstention `4/5`?" — One case returns the wrong enum. A different case returns the correct abstention enum but still states a forbidden conclusion, so abstention captures a failure that enum equality alone cannot see.
- "Why can a `COMPLETED` run contain six hard-failure cases?" — Completion describes successful execution and scoring. The immutable hard-failure identities are evidence for the later release gate, which Issue #11 intentionally does not implement.
- "How do you know the role was really the tested role?" — Every normalized fixture observation stores `executed_role`; mismatch with the case role invalidates the run before scoring.
- "Does this prove AX is safe in production?" — No. It proves deterministic fixture behavior and replay integrity for the frozen contracts. A compatible live Verification run and release gate remain later work.

Concrete example:
: If a rule says immediate dismissal is prohibited, an answer saying “dismiss immediately” fails even when it cites that exact rule. The evidence identity is correct, but its stance contradicts the generated proposition.

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
: tuning thresholds on Verification, comparing incompatible evaluator versions, confusing percentage with percentage points, missing operational measurements, treating document linkage as semantic support, and allowing an LLM judge to override deterministic evidence.

Evidence required before interview:
: Metric contracts, Calibration threshold manifest and digest, gate decision trace, baseline-candidate compatible manifest, and at least one intentionally failing gate fixture.

Likely follow-ups:

- "Why allow a 2-point regression?" — It prevents noise or minor trade-offs from blocking a candidate while bounding quality loss; critical failures remain zero-tolerance.
- "Why require positive evidence?" — Passing only by not getting worse does not justify calling a candidate an improvement.
- "Can latency gains compensate for quality loss?" — Only within the 2-point limit and never for a hard failure.
- "Why not let an LLM judge decide semantic quality?" — It can help analyze nuance, but model drift and judge bias make it unsuitable as the sole release authority.
- "Is a correct citation enough to call a claim grounded?" — No. Citation coverage checks linkage only. Claim-support additionally requires a deterministic proposition match, correct polarity and modality, supporting rather than contradicting evidence, and an allowed Answer Mode.
- "Can a non-high-risk claim in review points or additional checks escape the metric?" — No. The same immutable traversal covers every generated structured-answer field at every risk level; high-risk mode changes the gate consequence, not metric coverage.
- "How is a high-risk unsupported conclusion detected reproducibly?" — The case declares high risk and a versioned proposition catalog. The evaluator automatically inspects every generated structured-answer path, so a dataset author cannot omit a path. Unsupported or contradicted matched conclusions and every ambiguous or unmapped high-risk atom fail closed and emit the deterministic critical identity.
- "Does this understand every possible Korean sentence?" — No. It is a closed-world regression contract for the frozen dataset. Unknown wording receives no credit and high-risk unknown conclusions fail closed; an LLM judge may assist review but never changes the gate.

Issue #13 implementation decision:
: Compare only strict `experiment-run-summary-v1` inputs and publish one replayable `experiment-comparison-artifact-v1` with ordered Gate 1/2/3 traces, case and macro deltas, operational deltas, and deterministic failure-taxonomy evidence.

Compatibility and confound boundary:
: Both inputs are explicit Verification summaries. Evaluation Plane and SUT SHAs plus clean dirty flags, dataset and corpus IDs/versions/digests, parsing/retrieval/grounded/operational evaluator versions, prompt ID/hash, model provider/name/parameters, retrieval `top_k` and `fixed_retrieval_config_digest`, Adapter versions, threshold version/digest, dependency-lock and runtime-environment digests, execution mode, case identities, per-case applicability, and metric denominators must match. Denominators must also meet the frozen 6/9/10/10/15/5 Verification minima. `candidate-plan-v1` permits only `evidence_limit=3` to `5`; Recall@5, MRR@10, and authority-priority must be present and identical or the comparison is `INVALID`.

Storage and replay:
: The Immutable Result Store, not the gate logic, writes create-only JSON and Parquet canonical evidence. Source metric, latency, and cost values must fit Parquet `DECIMAL(38, 28)` exactly; an out-of-range derived case-relative value makes the comparison `INVALID` and is stored as null rather than rounded. A zero case baseline makes only that case-relative delta unavailable while p95 and mean aggregates remain independently computable. JSON and Parquet are completed under a temporary directory, then published with create-only links; a reported second-link failure removes only the first newly published file and preserves competing bytes. `comparison_id` is path-safe in the model as well as the CLI. DuckDB is rebuilt from Parquet and can be deleted without losing evidence. Before the logical digest is exposed, accepted input and derived mappings are recursively frozen so a caller cannot mutate a returned metric, model parameter, delta, or taxonomy count while retaining stale gates and digest. Non-finite decimal inputs fail Pydantic validation before arithmetic. Replay recomputes compatibility, confounds, aggregation, taxonomy, gates, decision, logical digest, and every Parquet row.

Rejected alternatives:
: Use a weighted composite score, store only DuckDB, compare only top-level aggregates, or let Gate 3 pass after Gate 1 or 2 fails. These would let favorable metrics mask safety evidence, make applicability drift invisible, or turn a cache into mutable authority.

Trade-offs and failure modes:
: Strict compatibility and exact decimal constraints create more `INVALID` results, and JSON/Parquet duplicate some logical content. That cost is intentional. Create-only pair publication handles reported failures and races but is not a crash-atomic filesystem transaction. The local store is auditable but not remote object lock; a forged upstream summary can still lie about execution, so live publication later requires a pinned producer path and clean committed provenance.

Validation evidence:
: Fifteen-case installed-CLI Verification fixtures meet every locked denominator and produce PASS for a 3-point claim-support improvement, FAIL for a 16-percent p95 latency regression, and INVALID for model-version drift. Focused RED/GREEN tests cover missing and malformed provenance, operational evaluator provenance, each locked version dimension, missing and changed retrieval confounds, applicability and denominator drift, minimum coverage, frozen critical severity, failure-to-evaluator provenance, baseline/candidate taxonomy deltas, ordered gates, recursive mapping immutability, safe comparison IDs, zero-case aggregate preservation, exact Decimal range and scale, derived overflow invalidation, failure-safe pair publication, append-only collision, Parquet tampering, exact repeating-decimal replay, deterministic decision digests, and disposable DuckDB rebuild. Review verification also confirms `NaN` and positive or negative infinity already produce a controlled `ValidationError` under the locked Pydantic version.

Likely follow-ups:

- "Why is DuckDB disposable?" — The portable JSON and Parquet files are the evidence. DuckDB is only a local acceleration structure reconstructed from Parquet.
- "Why does the logical digest ignore comparison and run IDs?" — Those are volatile envelope identities. The digest includes every provenance, input, metric, failure, and gate field that can change the logical conclusion.
- "Can a caller mutate the in-memory artifact after the digest is computed?" — No. Frozen Pydantic models alone are shallow, so the comparison contract additionally freezes every nested mapping and nested list-like value before returning the artifact.
- "Does one free or instant case invalidate the operational aggregate?" — No. Its per-case relative delta is unavailable when the baseline is zero, but p95 latency and mean cost are computed independently from the full compatible pair. Only an aggregate zero baseline prevents aggregate-relative comparison.
- "Can canonical Parquet silently round a valid Decimal?" — No. Source values must fit `DECIMAL(38, 28)` exactly, and an unrepresentable derived case delta fails closed instead of being coerced.
- "Are JSON and Parquet transactionally atomic?" — They are staged together and application failures roll back the first newly published link, but a local filesystem process crash between links is still a documented failure mode rather than a transactional guarantee.
- "Does PASS prove the AX candidate is better?" — No. These fixtures prove the deterministic comparison engine. A compatible complete live Verification pair is still required for a live quality claim.
- "Why invalidate retrieval movement?" — The frozen candidate changes evidence packaging only. Retrieval movement would introduce an uncontrolled variable and prevent attributing the outcome to `evidence_limit`.

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

Issue #6 implementation decision:
: `run-artifact-v1` stores a volatile run envelope separately from provenance and the logical result. Its SHA-256 logical digest covers provenance, case snapshot, normalized observation, recomputed exact-answer evaluation, and gate decision, but excludes `run_id`, creation time, and file path.

Why:
: Independent reruns need the same logical identity even though operational run metadata changes. Keeping provenance inside the digest prevents a different dataset, SUT identity, adapter, evaluator, prompt, or model placeholder from being mistaken for the same evidence.

Provenance capture:
: The CLI captures the Evaluation Plane repository `HEAD` and dirty-worktree state itself instead of trusting caller input. The fixture SUT remains an explicitly declared, non-executed identity with unknown dirty state. Dataset content identity hashes the dataset, case, and source provenance only; fixture responses and prompt/model placeholders remain separate execution provenance.

Rejected alternatives:
: Digest the entire JSON artifact, which would make every new run differ because of run ID and time; or digest only the score and gate, which would allow incompatible provenance to collide logically.

Trade-offs and failure modes:
: Create-only local files prevent accidental overwrite but are not cryptographic remote retention. A user with filesystem write access can still mutate bytes; replay detects logical tampering but this ticket does not provide object-lock storage. A crashed write can also leave an unusable file that must be replaced by a new run ID. Because the run ID becomes a filename, unrestricted input would permit path traversal; the CLI therefore restricts it to a short ASCII identifier and validates the declared SUT commit SHA before creating output. A wheel detached from its Git checkout cannot capture truthful Evaluation Plane provenance and must fail rather than accept a caller-supplied substitute.

Validation evidence:
: The Issue #6 acceptance test executes the CLI twice with different run IDs and checks equal logical digests, verifies the automatically captured Evaluation Plane SHA and dirty state, replays the stored artifact and checks the same digest and gate, rejects an existing run ID without changing bytes, rejects tampered, incomplete, non-UTF-8, or invalid input without a partial result, blocks output-directory traversal, keeps dataset identity stable across fixture execution changes, and rejects malformed SUT identities. Ruff, mypy, and pytest remain required before review.

Likely follow-ups:

- "Why is the SUT SHA present when AX was not called?" — It is a declared identity placeholder with `executed=false`; `fixture-sut-v1` proves orchestration only and cannot support a live-quality claim.
- "Is the result truly immutable?" — It is append-only at the application boundary and replay-verifiable. Strong retention guarantees such as object lock are a later operational concern and are not claimed here.
- "Why include provenance in the digest?" — A score under a different evaluator or dataset is different evidence even when the displayed number is equal.

Issue #7 implementation decision:
: Freeze `ax-sut-http-v1` against AX commit `c318b2192006bdb36a5bd5b3a2bc403425b45701`, validate its live path inventory before a run, preserve every HTTP attempt, and fail closed on unavailable parsing or corpus identity.

Why:
: A nominal endpoint list is not enough to support an evaluation claim. The Adapter must prove which operations and fields the pinned SUT actually exposes, retain request and response provenance, and make missing observation surfaces visible before scoring begins.

Rejected alternatives:
: Import AX models directly, infer missing parse output from attachment status, or mark the caller's corpus label as SUT-verified. Each would make the Evaluation Plane claim evidence that AX did not return.

Trade-offs and failure modes:
: The first live preflight intentionally leaves `parse` unavailable and corpus identity unverified, so the locked parsing benchmark cannot run yet. UUID tenant validation rejects bad local configuration before HTTP. Only timeout, `429`, and `5xx` retry, and every attempt remains visible; authentication, contract `4xx`, and schema mismatch fail permanently. A path being present proves interface availability, not retrieval quality or data coverage.

Validation evidence:
: Fifteen controlled HTTP tests cover preflight, frozen request/response mappings and schema digests, retrieve, answer, source text, explicit parse unavailability, timeout recovery, `429` recovery, exhausted `5xx`, permanent `401`, malformed response, UUID tenant validation, bearer-credential exclusion, and create-only manifest persistence. Review-driven tests also prove that success and failure evidence preserve run, case, query or document identity. A live synthetic smoke against the pinned AX SHA returned ready health, confirmed the four supported operations, recorded the two capability gaps, completed retrieval with zero candidates, and returned an evidence-insufficient answer without generated text or citations.

Likely follow-ups:

- "Why is parsing still blocked?" — AX does not expose parsed text, structure, tables/lists, and EvidenceSpan offsets through a reviewed HTTP boundary. Attachment processing status is not equivalent evidence.
- "Does an available retrieval endpoint prove search quality?" — No. It proves only that the contract can be called and normalized. The live smoke returned zero candidates and supports no quality claim.
- "Why preserve failed attempts?" — Retry hides operational instability unless every timeout and transient response remains in the evidence. The final success alone would bias reliability reporting.
- "Why is corpus identity unverified?" — The current AX response surface has no authoritative corpus identifier or digest. The Adapter records the declared synthetic corpus but refuses to relabel it as SUT-verified.

Issue #8 implementation decision:
: Freeze `braincrew-parsing-quality@1.0.0` as 20 synthetic parsing cases with a 14/6 Calibration/Verification split, keep dataset ground truth separate from `fixture-parsing-sut-v1` observations, and evaluate EvidenceSpan, structure, metadata, table, and list preservation with deterministic `parsing-quality-v1` exact counts.

Why:
: Separating expected evidence from observed parser output prevents fixture changes from silently changing dataset identity. Exact numerators, denominators, and case-level macro aggregation make every published decimal traceable to reviewable case evidence. A frozen six-case Verification denominator demonstrates coverage without claiming that 20 cases estimate population quality.

Rejected alternatives:
: Generate fixture observations from the expected dataset during the run, which would let the evaluator grade its own answer key; treat missing parse telemetry as score zero, which would conflate product quality with unobservable evidence; or return `PASS` for a fixture-complete run, which would misrepresent a deterministic pipeline check as a release decision.

Trade-offs and failure modes:
: The explicit dataset and fixture files duplicate some text and span identities, but that duplication is intentional independent evidence. Unicode offsets, source digests, parser versions, case IDs, split counts, and table/list applicability can drift; strict Pydantic contracts reject drift before scoring. A missing or unavailable Verification parse reduces the EvidenceSpan denominator below six, makes the run `INVALID`, and suppresses the aggregate while retaining case diagnostics.

Validation evidence:
: Contract tests validate all 20 unique cases, the 14/6 split, every EvidenceSpan Unicode slice and SHA-256 source digest, strict extra-field rejection, parser-version consistency, and exact fixture coverage. Hand-calculated goldens prove EvidenceSpan `1/2`, metadata `1/2`, structure `1/1`, and applicable table/list outcomes. The CLI executes all 20 fixture cases into a create-only `parsing-run-artifact-v1`, records exact dataset/evaluator/adapter/SUT identities, and persists an unavailable parse as `INVALID` with no aggregate or `PASS` claim.

Likely follow-ups:

- "Does a perfect fixture aggregate prove AX parsing quality?" — No. It proves the versioned evaluator, observation, aggregation, provenance, and storage contracts. The live AX contract currently exposes no parse observation and remains explicitly invalid for this benchmark.
- "Why not score missing parse output as zero?" — Zero means an observed parser failed to recover evidence. `INVALID` means the evidence required to make that quality judgment was not observable; combining them would hide an integration boundary failure inside a quality average.
- "Why store exact fractions as well as decimals?" — Gate comparison must use unrounded values. The four-place decimal is presentation; the numerator and denominator are the authoritative, reproducible calculation.
- "Why no PASS decision?" — This ticket evaluates one fixture run, not a compatible baseline-candidate release comparison. `COMPLETED` means evidence is complete; a future release gate decides pass or fail under its own versioned contract.

Issue #9 implementation decision:
: Freeze `braincrew-retrieval-quality@1.0.0` as 30 synthetic retrieval cases with a 21/9 Calibration/Verification split, score exact identity groups with deterministic `retrieval-quality-v1`, and persist the complete query, candidate identity, rank, authority, visibility, version, and failure evidence in `retrieval-run-artifact-v1`.

Why:
: Search quality claims are not auditable when a dashboard shows only aggregate decimals. Exact source tuples and case-level ranks let an interviewer trace Recall@5, MRR@10, authority ordering, and forbidden visibility back to the returned evidence. Keeping fixture observations separate from dataset ground truth also prevents the evaluator from grading an answer key it generated itself.

Rejected alternatives:
: Use fuzzy text or embedding similarity to decide relevant identity, drop cases whose expected source is missing or ambiguous, treat a returned forbidden item as acceptable when AX marks it denied, or collapse safety and quality into one weighted retrieval score. These options would make denominator changes invisible, weaken the role boundary, or allow good relevance to mask critical leakage.

Trade-offs and failure modes:
: Exact tuple matching is intentionally strict and can expose annotation debt. A reviewed unresolved identity therefore has only two legal paths: remain in the denominator as zero with `R-EXPECTED-SOURCE-IDENTITY-UNRESOLVED`, or make the case `INVALID`; it is never silently skipped. All nine Verification cases require resolved Recall@5 ground truth. Recall@5 counts the first five unique identities after duplicate removal, while MRR@10 preserves the first matching identity's original rank. Authority priority scores the first relevant unique result against the reviewed preferred authority. Any forbidden identity in returned candidates emits `R-FORBIDDEN-VISIBILITY` and a `hard_failure_cases` entry even if the candidate carries a deny-like visibility reason or the observation is otherwise `INVALID`; the fully scored run remains `COMPLETED`, while any later release gate must fail it. Missing, unavailable, query-mismatched, unexpected, or zero-applicability aggregate evidence invalidates the run and suppresses aggregates without erasing separately observed forbidden-source evidence.

Validation evidence:
: Contract tests freeze all 30 unique cases, the 21/9 split, strict schemas, reviewed applicability, exact fixture coverage, one-based array rank, and unresolved-identity policy. Hand-calculated goldens prove duplicate suppression, the fifth unique identity at original rank 6 still entering Recall@5, Recall@5 `2/2`, MRR@10 `1/2`, authority inversion `0/1`, denominator-zero unresolved identity, and explicit invalidation. Negative tests reject impossible or display-mismatched exact fractions, make a zero-applicability aggregate `INVALID`, prove forbidden identity produces a critical `hard_failure_cases` entry in both a fully scored `COMPLETED` run and an otherwise unavailable `INVALID` observation, and prove missing Verification evidence reduces the Recall@5 denominator below nine and produces `INVALID`. The CLI stores all 30 cases through the create-only result store with exact dataset/evaluator/adapter/SUT provenance; replay recomputes the retrieval evaluation and digest and rejects tampered case scores. A live synthetic request against pinned AX commit `c318b2192006bdb36a5bd5b3a2bc403425b45701` completed after the temporary demo tenant and official seed were installed, returned zero candidates, and therefore recorded empty identity/rank/authority evidence plus zero retrieval scores without a quality claim.

Likely follow-ups:

- "Why does an unresolved expected identity sometimes score zero instead of always invalidating?" — `denominator_zero` is an explicit conservative annotation policy for reviewed Calibration cases: the unresolved group remains visible and cannot improve the metric. `invalid` is available when scoring would be misleading. Verification forbids unresolved Recall@5 ground truth entirely.
- "What exactly counts as a duplicate?" — The tuple `(record_kind, record_id, evidence_span_id, source_text_digest)`. The first array occurrence keeps its original rank; later identical tuples are ignored for Recall@5 and MRR@10.
- "Why can rank 6 count toward Recall@5?" — Recall@5 is explicitly defined over five unique identities. If rank 2 duplicates rank 1, the fifth unique result can first appear at raw rank 6; MRR still uses that result's original rank 6.
- "Why is a forbidden-source run still COMPLETED?" — Run state describes whether execution finished and the evidence is comparable. Zero-tolerance safety is carried separately by `hard_failure_cases`; the release gate must fail that run even though its evaluation completed. `FAILED` remains reserved for runtime or infrastructure failure.
- "Did the live smoke prove the fixture's 30-case quality?" — No. It proved pinned HTTP execution and evaluator wiring for one synthetic query. AX returned no candidates and did not verify the declared corpus identity, so the result is explicit negative diagnostic evidence, not a benchmark pass.

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

Issue #14 implementation decision:
: Export only a replay-validated `experiment-comparison-artifact-v1` JSON/Parquet pair into a strict `dashboard-export-v1`, then render that frozen projection with Next.js static export. The exporter copies canonical scores, deltas, failure counts, logical digest, ordered gate trace, and decision; neither Python projection code nor React recalculates Issue #13 semantics.

Frontend toolchain decision:
: Use root-managed `npm@11.12.1` with committed `package-lock.json` lockfile v3, Node.js `>=20.19.0`, Next.js `16.2.10`, React `19.2.7`, TypeScript `5.9.3`, ESLint `9.39.5`, Vitest `4.1.10`, and Playwright `1.61.1` with package-pinned Chromium. The lockfile pins patched transitive PostCSS `8.5.10`; clean install and audit report no known vulnerability. The full contract is `npm ci`, `npm run format:check`, `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`, and `npm run test:e2e`.

Why this toolchain:
: The repository had no frontend manifest, lockfile, workspace, or existing package-manager convention. npm ships with Node and `npm ci` fails when the manifest and lock disagree, so it adds no global bootstrap dependency. Vitest is sufficient for the readonly export/view-model contracts, while Playwright checks the actual `dashboard/out` files in Chromium rather than a mutable development server.

Rejected alternatives:
: pnpm, Yarn, and Bun add a second package-manager bootstrap without repository evidence that their workspace or speed advantages are needed. ESLint 10 was rejected after its plugin peer ranges conflicted with `eslint-config-next@16.2.10`; the latest compatible ESLint 9 line avoids overriding the linter ecosystem. Jest duplicates the TypeScript contract-test role with more configuration. Cypress adds another browser-test ecosystem when Playwright already pins browser compatibility. A dynamic Next.js server, API route, PostgreSQL connection, or DuckDB-in-browser query was rejected because it would turn frozen presentation into a mutable runtime.

Trade-offs and failure modes:
: The lockfile is large, Python and TypeScript remain separate toolchains, and the first browser smoke downloads Chromium. The critical risks are schema drift, accidentally publishing credentials or private strings, recalculating canonical values in React, and testing a dev server instead of the static export. Replay-before-export, strict publishability validation, readonly TypeScript contracts, golden total/decision equality, `output: "export"`, and a Playwright smoke against `dashboard/out` are the required controls.

Likely follow-ups:

- "Can the dashboard change a release decision?" — No. It receives the canonical decision and ordered gate reasons as data and has no evaluator or gate implementation.
- "What case evidence is safe to publish?" — Stable public case labels, canonical metric/delta values, operational deltas, and deterministic failure identities. Raw source text, prompts, headers, credentials, private document content, and database rows are excluded.
- "Why install a browser during the smoke command?" — Playwright versions require matching browser binaries. The package-local pretest step makes a clean `npm ci` checkout self-contained without assuming a global Chrome installation.
- "Does this dashboard prove live AX quality?" — No. The Issue #14 golden is fixture-authoritative presentation evidence. A separately pinned live Verification comparison is still required before a live product-quality claim.
- "How does the screen prevent that confusion?" — The export copies `execution_mode`, Evaluation Plane SHA, and SUT SHA from the immutable run summaries, and the golden screen labels itself “Fixture evidence — not a live AX verification.” React does not infer or upgrade that status.

### D8.1 Seal independent corpus bytes before evaluation comparison

Decision:
: Vendor the AX `ax-synthetic-seed-content-v1` and `ax-synthetic-seed-pack-v1` schema files from
  merge `47673b83a9fb431f2bad550781db18c7bee8b67e` by exact bytes and fixed digest, then accept only
  strict isolated staging input into a create-only corpus version.

Why:
: Independent evaluation fails if expected answers can shape the evidence world or if corpus
  bytes can be repaired after inspection. Byte-exact schema pinning, ordered source digests, and
  replay make the boundary reviewable without importing AX code or reading the evaluation dataset.

Rejected alternatives:
: Normalizing CRLF or Unicode, generating corrected digests, overwriting a sealed version, reading
  dataset v2 during sealing, and placing raw text or local paths in the receipt. Each alternative
  either changes authored evidence, leaks evaluation context, weakens immutability, or makes the
  retained evidence unsafe.

Trade-offs and failure modes:
: Strict rejection makes authoring mistakes require a new corrected staging attempt and later a
  new corpus version. The filesystem is not claimed as cryptographic write-once storage; the
  enforceable guarantees are application create-only publication plus digest replay. Drifted AX
  schemas, path escapes, undeclared files, noncanonical bytes, stale per-source hashes, receipt
  edits, and post-seal source mutations all fail closed.

Validation evidence:
: Contract and CLI tests reproduce the two AX schema byte counts and SHA-256 values, observe the
  missing schema/CLI RED before implementation, cover recursive unsafe fields and canonical byte
  rejection, prove ordered digest changes, preserve exact source bytes, refuse existing versions,
  sanitize receipts, and reject replay after a one-byte source mutation. A review-driven test also
  caught and repaired backslash path acceptance. The final full repository gate passes 232 tests;
  installed CLI seal/replay, sanitized receipt scanning, and wheel schema inclusion also pass.

Likely follow-ups:

- "Does sealing prove dataset v2 coverage?" — No. Issue #31 never reads the dataset. Post-seal
  qualification belongs to Issue #33 and may only compare the unchanged sealed digest read-only.
- "Why vendor both schemas when sealing uses the content manifest?" — The repository boundary
  must pin the complete reviewed AX v1 file contract before later qualification creates an import
  manifest; Issue #31 validates drift but does not create that later envelope.
- "Can someone still chmod and edit the files?" — The local filesystem is not object lock. Such an
  edit is detected by replay and cannot be accepted as the same sealed identity; stronger retention
  is a later operational concern and is not claimed here.

### D8.2 Enforce authoring independence with OS capabilities

Decision:
: Run the corpus-authoring tool through `braincrew-eval launch-authoring` with a clean committed
  Braincrew source, exactly four read-only declared inputs, one empty writable staging directory,
  a cleared environment, and a deny-by-default operating-system sandbox. Retain only a create-only
  `corpus-authoring-independence-receipt-v1` with bounded identities and digests.

Why:
: Prompt instructions cannot prove that an author never opened the evaluation dataset or reused a
  prior result. Filesystem and network denial makes the independence claim executable, while the
  receipt lets a reviewer bind the attempt to the clean source, tool, inputs, timing, exit state,
  and produced bytes without retaining sensitive content.

Rejected alternatives:
: A prompt-only warning, a normal subprocess with a reduced environment, mounting the Braincrew
  repository read-only, passing qualification failures back for repair, and storing stdout/stderr or
  raw paths in the receipt. Each leaves an evaluation-feedback path, an undeclared input path, or an
  unsafe retained transcript.

Trade-offs and failure modes:
: macOS uses the built-in `sandbox-exec`; Linux requires an already-installed Bubblewrap backend.
  Unsupported environments fail closed, so portability is narrower than an unrestricted CLI. The
  launcher proves capability denial and byte identity, not that the future brief is substantively
  good or that authored content qualifies against dataset v2. Sandbox-profile overbreadth,
  inherited secrets, raw output retention, or a validator feedback mount would weaken the claim and
  must remain regression-tested. Runtime libraries remain a narrowly declared execution substrate,
  not authoring inputs; unsupported tool runtimes fail rather than widening the profile.

Validation evidence:
: Five contract/acceptance tests first failed on the missing `launch-authoring` command. Review then
  reproduced four further boundary defects: a non-Braincrew Git remote could be mislabeled, file
  metadata was too broad, an invalid tool label leaked a traceback, and `/Library` data access
  exposed the system keychain. The repaired seven-test suite passes. The macOS acceptance process
  sees only the brief, AX pack schema, schema digest declaration, input digest inventory, runtime
  substrate, and staging; Braincrew/AX repositories, dataset, fixture, prior artifact, database,
  credentials, private document, generic undeclared path, system keychain, and post-seal result are
  denied at both data and metadata probes, as is a live localhost network connection. Failure exit
  state is retained while process stdout/stderr is discarded and raw/private material is absent
  from the receipt. The final repository gate reports `239 passed`; the authoring and reused sealing
  boundary subset reports `32 passed`; frozen sync, Ruff format/lint, mypy, installed CLI help, and
  Git whitespace validation also pass.

Likely follow-ups:

- "Does this prove the corpus is independent?" — It proves the declared process lacked the tested
  repository, evaluation, filesystem, credential, database, and network capabilities. Brief review
  and operator discipline remain separate evidence.
- "Why not let qualification repair the pack?" — A repair informed by expected results would turn
  the benchmark into its own evidence author. Qualification may emit only success or typed blockers.
- "Does Issue #32 write the brief or corpus?" — No. Brief approval is Issue #35, actual restricted
  authoring/sealing is Issue #36, and read-only dataset qualification starts later.
- "What happens without a supported sandbox?" — `AUTHORING_SANDBOX_UNAVAILABLE`; there is no
  unrestricted fallback.

### D8.3 Qualify only immutable corpus bytes against the exact dataset identity

Decision:
: Run `braincrew-eval qualify-corpus` only after Issue #31 sealing. Reproduce schema, manifest,
  per-source, sealed-content, sealing-receipt, and exact dataset-v2 identities before checking the
  100-case source, digest, role, provenance, and distractor contracts. Publish sanitized receipt and
  import bytes only on complete success.

Why:
: A matching corpus label does not prove that the bytes cover the benchmark or respect role
  visibility. The validator must connect two independently frozen identities without giving the
  authoring process access to expected evidence or permission to repair a mismatch.

Rejected alternatives:
: Trusting source IDs without content hashes, checking only sources cited by successful answers,
  allowing qualification to edit either input, creating an import manifest before complete
  validation, and passing raw source/query/answer material into the receipt. Each alternative can
  hide content drift, leakage, missing distractors, or a benchmark-authored corpus.

Trade-offs and failure modes:
: The exact v2 digest means any scoring-relevant dataset change requires a new qualification
  version. The reviewed AX schema does not accept `@` in `seed_version`, so the import envelope uses
  `braincrew-evaluation-dataset-2.0.0`; exact ID `braincrew-evaluation-dataset`, semantic version
  `2.0.0`, integrated/component digests, and 100-case count remain explicit in the qualification
  receipt. Missing resources in an installed wheel, stale dataset-card metadata, output-pair I/O
  failure, source tampering, or visibility drift must all fail closed.

Validation evidence:
: Thirteen tests first failed because dataset v2 and `qualify-corpus` did not exist. Minimal GREEN
  covered all approved blockers, wrong dataset identity, sanitized success, create-only behavior,
  replay, and tamper rejection. Review-driven RED/GREEN added a dedicated v2 card, the exact wheel
  replay bundle, and rollback-safe two-file publication. All 15 focused qualification tests and all
  254 repository tests pass; Ruff format/lint, strict mypy, wheel inspection, and Git whitespace
  validation also pass.

Likely follow-ups:

- "Did Issue #33 qualify a real authored corpus?" — No. It implements and verifies the read-only
  mechanism. Brief approval is #35, authoring/sealing is #36, and the actual qualification is #37.
- "Why is the import seed string not written with `@`?" — The exact AX schema forbids that
  character. The schema-safe string is only an envelope identifier; the receipt holds the exact
  dataset ID, version, and digests.
- "Can qualification repair a missing source?" — No. It returns
  `CORPUS_REQUIRED_SOURCE_MISSING` and emits neither qualification nor import output.

### D8.4 Extract live transport evidence before adding evaluation policy

Decision:
: Add Braincrew Issue #42 from merged `develop` as the minimum substrate between AX's reviewed
  evaluation router and Issue #34. Pin AX
  `72805930d9addd8ea41743d1922acf8de621c3f8`, freeze strict corpus-identity and parse-observation
  HTTP contracts, and retain their sanitized evidence in create-only
  `live-preflight-evidence-v1`. Leave principal, attachment, role, blocker, and READY policy to
  Issues #34 and #38.

Why:
: The requested Issue #34 policy could not be tested independently because merged `develop` had
  only the old Adapter where parse was unavailable and corpus identity was caller-declared. The
  missing seam existed inside draft PR #29 together with unrelated Issue #15 prompt/model and live
  experiment scope. A small prerequisite makes the dependency explicit without copying those
  commits or weakening the branch boundary.

Rejected alternatives:
: Cherry-picking PR #29's four Issue #15 commits, re-creating the entire live runner inside #34,
  or treating transport success as a preflight or parsing-quality result. Each would mix
  infrastructure, policy, and experiment execution, making the ticket review and resulting claim
  ambiguous.

Trade-offs and failure modes:
: #42 deliberately cannot report `READY`; its only state is `captured`. The Adapter response may
  contain raw text in memory because that is the strict AX wire contract, but the retained artifact
  replaces extracted and span text with digests and stores only structure counts. A changed AX
  schema, unencoded attachment identity, leaked raw field, stale digest, overwrite attempt, or
  tampered artifact fails closed. Timeout, `429`, and `5xx` retain bounded retries; other HTTP
  failures stop after one attempt with only a short token-like detail.

Validation evidence:
: A clean baseline passed frozen sync, Ruff, strict mypy, and all 254 pre-change tests before the
  first RED. New contract and acceptance tests first failed because the pinned SHA, strict response
  models, and `braincrew.live_preflight` module did not exist. The focused GREEN covers both strict
  transports, schema drift, path encoding, retry and permanent-error behavior, raw-text-free
  create-only capture, installed CLI replay, digest tampering, and raw-field injection. Review
  tests additionally reproduced nested-digest rehash bypass, private-path retention, stale
  capability evidence, ambiguous attachment naming, mixed run identity, and the old grounded
  Adapter pin before repair. Final evidence is 26 focused tests including that grounded regression
  and 264 full repository tests, with Ruff, strict mypy, and Git whitespace validation passing.

Likely follow-ups:

- "Did #42 validate the six real attachments?" — No. It proves only that strict transport evidence
  can be collected and retained safely. #34 owns the actual six-document mapping, owner subject,
  exact `HRPractitioner` role, digests, spans, and blocker classification.
- "Why keep AX raw text in the in-memory response at all?" — Strict response validation must match
  what AX actually publishes. The retention boundary sanitizes before writing, so wire fidelity
  and safe evidence storage remain separate responsibilities.
- "Does a replayable captured artifact prove parsing quality?" — No. It proves schema, request,
  response-summary, attempt, and digest integrity only. Evaluators and Issue #38's READY decision
  remain downstream.

### D8.5 Separate principal, mapping, and live-operation failures

Decision:
: Implement Issue #34 on merged Issue #42 only. Reject noncanonical tenant/user UUIDs before HTTP,
  require active owner `22222222-2222-2222-2222-222222222222`, apply exactly
  `HRPractitioner`, freeze the six reviewed parsing attachment UUIDs, and bind the collector to the
  exact dataset-v2 integrated and component digests. Retain accepted dataset identity and probe
  evidence only through the create-only `principal-attachment-preflight-evidence-v1` artifact,
  layered on the generic Issue #42 replay boundary.

Why:
: The earlier placeholder user could reach AX as a malformed subject and make an authorization
  problem look like service failure. A document label could also point to a nonexistent or wrong
  attachment. Separating configuration, subject, mapping, and operation failures makes the
  evidence actionable without weakening fail-closed behavior.

Rejected alternatives:
: Normalize malformed IDs, retry unknown subjects, accept a partial or caller-invented mapping,
  infer authorization from persona text, or turn six HTTP 200 responses into a parsing-quality
  pass. Each hides a different failure cause or claims more than the probe measured.

Trade-offs and failure modes:
: The reviewed owner and attachment UUIDs are environment-specific contract data, so a legitimate
  corpus re-import requires an explicit reviewed mapping update rather than automatic repair.
  A dataset substitution is rejected before HTTP. After the frozen identity is accepted, complete,
  partial, and blocked captures use `principal-attachment-preflight-evidence-v1`, whose required
  contract and dataset identity make rehashed removal invalid while that schema remains unchanged.
  Generic Issue #42 `live-preflight-evidence-v1` artifacts retain full backward compatibility, and
  an Issue #34 consumer must require the newer schema. The logical digest proves replay consistency,
  not who created the artifact. Within the newer schema replay revalidates the exact ordered six
  case/attachment pairs, reviewed owner, and sole role. A missing probe cannot be hidden by
  recomputing the logical digest: a complete artifact needs all six, while a partial artifact needs
  the terminal blocker for its next probe. An available response with
  zero spans is retained as measurable poor parsing quality; an available response with a failure
  code is rejected as inconsistent evidence. Server-controlled correlation headers are retained
  only as digests, and legacy v1 artifacts keep their omitted-field digest semantics.
  Missing/nonexistent/mismatched attachment identity becomes `PARSE_ATTACHMENT_MAPPING_INVALID`;
  malformed principals become `EVALUATION_PRINCIPAL_ID_INVALID`; unknown/inactive subjects become
  `EVALUATION_PRINCIPAL_SUBJECT_INVALID`; inaccessible or unstable live operations retain the
  existing `LIVE_PARSE_OBSERVATION_*` family, with exhausted attempts retained on the blocker. If
  retries recover to an HTTP success whose evidence is then rejected, that blocker still retains
  the complete retry-plus-success attempt sequence. A non-timeout connection failure is
  non-retryable but retains a `request_error` attempt with method, path, ordinal, and timing on
  `LIVE_PARSE_OBSERVATION_UNREACHABLE`. Every operation blocker also retains its canonical request,
  so a failure on the first probe still proves the tenant, owner, role, and attachment. Replay
  requires the fixed parse-only request shape and rejects query/corpus/retrieval fields, impossible
  correlations on attempts without a response, mismatched code/detail/outcome/status taxonomy, and
  server-controlled span IDs outside the bounded safe grammar.

Validation evidence:
: A clean baseline passed frozen sync, Ruff, strict mypy, and all 264 pre-change tests before the
  first RED. Fifteen new acceptance/contract tests then failed on the absent policy. Minimal GREEN
  covers pre-HTTP rejection, owner/role projection, exact mapping, typed AX errors, digest/span
  checks including exact `utf8-text`/`stdlib-1` parser identity, retry retention, six sanitized
  probes, create-only publication, and replay. Review first reproduced acceptance of a non-matching
  parser. PR #44 review remediation then reproduced empty-span overblocking, failure-code
  inconsistency, retry-evidence loss, dataset digest substitution/removal, legacy replay drift, and
  hostile correlation retention before repair. A later Codex re-review reproduced attempt loss
  after recovery to invalid evidence and dataset-identity removal from a blocked partial capture.
  Independent re-review then reproduced simultaneous contract-and-identity removal before semantic
  downgrade protection was added, then reproduced overbroad classification of generic
  reviewed-attachment evidence and unrelated legacy `LIVE_PARSE_*` blockers. Fingerprint inference
  was removed in favor of a separate required-field Issue #34 schema. The latest Codex review then
  reproduced acceptance of a rehashed five-probe artifact and a missing connection-attempt receipt;
  both became RED before the six-probe/terminal-blocker validator and `request_error` receipt
  reached GREEN. Independent review then reproduced rejection of the existing unavailable blocker,
  rehashed strict-response drift, and attempt removal from a blocked receipt before repair. The five
  focused preflight/adapter files report 50 passes. A final adversarial pass bound span digests to
  the frozen substrings, one tenant to all retained observations, and blocker codes to terminal
  attempt outcomes, then rejected shortening a terminal retryable failure below its three-attempt
  exhaustion history. A fourth Codex review then produced six RED failures covering five gaps:
  first-probe principal evidence, blocker taxonomy binding, parse-only requests, response-less
  correlation, and safe span IDs. Independent review then caught a generic-v1 span compatibility
  regression and raw query retention through generic blocker requests. Both were RED before the
  safe-ID check was confined to Issue #34 and generic blocker requests were rejected. The focused
  five-file suite reports 54 passes after repair, and all 293 repository tests pass. No real
  preflight or READY artifact was produced.

Likely follow-ups:

- "Why is an HTTP 200 not enough?" — It proves transport and schema only. Source digest and span
  integrity must also match for spans that exist, while zero spans, headings, metadata, tables, and
  lists remain later quality data. `parse_available=true` also cannot carry a failure code.
- "Why hard-code the six UUIDs?" — They are reviewed attachment identities for the pinned local
  corpus. Accepting arbitrary caller input would make the evidence non-reproducible.
- "How does replay prove which dataset drove the probe?" — The collector validates the exact ID,
  version, integrated digest, and three component digests before HTTP, stores that frozen identity,
  and rejects identity removal or substitution even when the top-level digest is recomputed.
- "Can AX smuggle secrets into retained retry metadata?" — Response correlation headers are
  server-controlled, so the retention boundary stores only their SHA-256 digests while preserving
  attempt number, outcome, status, timing, method, and path.
- "Did Issue #34 make the system READY?" — No. It implements and tests the policy collector. Issue
  #38 alone may perform the actual renewed preflight and publish READY.

### D8.5a Split missing AX principal state from missing parse-source state

Decision:
: Preserve AX `validated_evaluation_principal` and split the follow-up into two dependent AX
  contracts. AX-A provisions one deterministic active local/test subject in the imported target
  tenant. AX-B then uses that subject to create one conversation and re-provision the six reviewed
  `.txt` sources through upload, scan, parse, approval, and materialization before it emits the new
  attachment mapping. Braincrew Issue #38 consumes the two sanitized receipts, repins the reviewed
  identities, runs the strict probes, and remains the only owner of a new `READY` artifact.

Why:
: Read-only evidence changed the earlier assumption. The target corpus tenant
  `ae09ec7f-a7bc-5bf8-a645-8b3f1e623850` has no user, and the inspected database has no
  `ThreadAttachment` or `AttachmentExtraction` row in any tenant. A principal-only repair would
  therefore change the first failure from tenant/subject 401 to attachment 404 without producing
  one parse observation. Keeping repair inside AX preserves the SUT/Evaluation Plane boundary:
  the product creates its own user and attachment state, while Braincrew verifies only versioned
  receipts and HTTP facts.

Identity and dataset lock:
: The new subject is
  `26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe`, the literal result of
  `uuid5(NAMESPACE_URL,
  "ax-evaluation-principal:braincrew-demo-tenant:braincrew-live-evaluation-v1")`.
  AX-A creates exactly that one active target-tenant `User` in local/test and no persisted role or
  membership state. Requests still carry one exact role through `x-ax-roles`, and AX derives
  permissions from its existing static mapping: `HRPractitioner` owns, uploads, and reads the
  parse sources; `HRAdmin` approves them; the three evaluation roles are probed separately for
  corpus identity. The imported corpus contribution is `braincrew-evaluation-dataset-3.0.0`,
  while the six parse cases retain the historical v2 component contract inside integrated dataset
  bundle `braincrew-evaluation-dataset@3.0.0`.

Rejected alternatives:
: Relaxing the joined active-user validation was rejected because it weakens tenant isolation.
  Reusing or moving user `22222222-2222-2222-2222-222222222222` was rejected because the user is
  bound to another tenant. A principal-only issue was rejected because no attachment exists. One
  combined AX issue was rejected because user provisioning and blob/job/provider lifecycle have
  different permissions, tests, and recovery points. Moving upload or direct database repair into
  Braincrew #38 was rejected because a verifier must not manufacture its own SUT evidence.
  Caller-forced historical attachment UUIDs and extraction-only success were rejected because they
  bypass lifecycle ownership and cannot produce the stored non-empty spans required by the strict
  response.

Trade-offs and failure modes:
: AX-A deliberately provisions only one synthetic local/test `User`. Singleton-role probes stay
  reviewable because each request records one exact `x-ax-roles` value and AX applies the existing
  static permission mapping; no persisted membership is required. This is not a production
  identity pattern. AX-B locks approval to `company_reference`, `hr_only`, and policy version 1 to
  reduce grounding authority and exposure, but materialization still adds six source documents,
  chunks, and spans plus twelve vectors. The imported seed-table counts therefore move from
  `14/77/77/154` to `20/83/83/166`, and the HRPractitioner corpus identity gains six
  `tenant-upload-v1:<approval_id>` contributors. Counts and digests must be captured after AX-B,
  not copied from the import receipt.

: AX-A cannot make a database commit and filesystem receipt one atomic operation. It reserves the
  create-only path before mutation, validates the exact user before and after the commit attempt,
  and writes success evidence only after the post-commit read. A pre-commit failure rolls back and
  removes the reservation. A lost commit response or failed post-commit confirmation returns
  `EVALUATION_PRINCIPAL_COMMIT_INDETERMINATE` and retains the empty reserved path; a receipt write
  failure returns `EVALUATION_PRINCIPAL_RECEIPT_UNAVAILABLE` and also retains that path. The
  reservation blocks an unreviewed retry without pretending the database rolled back. Adding an
  `AuditEvent` was rejected because the locked AX-A acceptance contract permits exactly one new
  `User` and no other database row.

: The normal tenant-upload lifecycle stores `synthetic=false`, `demo_company=false`, and
  `corpus_mode=tenant` even though the external six-file bundle has reviewed synthetic
  provenance. The handoff must retain both facts as a representational limitation and must not
  relabel the materialized rows as seed-generated synthetic data. Any UUID, `x-ax-roles` request
  value, seed-run, source byte, parser, digest, approval, provider, row-count, tenant, owner, HTTP
  schema, or receipt mismatch stops the operation. The lifecycle crosses database, blob, worker,
  provider, and HTTP boundaries, so partial failure never authorizes automatic retry, cleanup,
  deletion, snapshot restore, or re-import.

Operational safety:
: The Issue #37 database snapshot predates the successful import and is not an acceptable recovery
  point for later writes. A fresh post-import/pre-A restricted database dump with digest and
  restore-list readability must precede AX-A apply. After AX-A, a second database dump and a
  digest-bound blob inventory plus restricted checkpoint must precede AX-B. These checkpoints do
  not authorize restore. Recovery is a separately reviewed proposal naming exact state. The
  previously exposed `OPENAI_API_KEY` response is recorded as resolved by user-confirmed rotation;
  neither this decision nor later verification may inspect or retain the replacement secret.

Validation evidence:
: Repository inspection confirms the current joined principal query, target-bound user model,
  normal upload role matrix, scan/parse job, approval permission, materializer, and strict
  parse-observation data flow. In particular, the strict response reads evidence spans from
  materialized `TenantSourceDocument`, `SeedSourceChunk`, and `SeedEvidenceSpan` rows; it cannot
  obtain them from `AttachmentExtraction` alone. Braincrew code inspection confirms that the
  current AX SHA, owner UUID, six attachment IDs, and v2 dataset identity are hard-coded and
  replay-validated. SELECT-only evidence supplies the zero-user and zero-attachment state. AX PR
  #46 at reviewed head `6499e1b42730f72bf03db769a3f95cb186f1fb07` passed all five required
  checks with zero unresolved review threads and squash-merged into `develop` as
  `fe16c0cedc1e64856d9e107e111665d0ba2e444d`; Issue #44 closed. Review-driven tests cover
  destination reservation, exact receipt replay including JSON types, concurrent exact insertion,
  pre- and post-commit confirmation, lost commit responses, and repository-anchored Git evidence;
  `63` targeted tests and the full backend suite (`1553 passed, 75 skipped`) passed locally. The
  repository-wide Ruff format baseline still reports `62` unrelated pre-existing files, while all
  changed files and full Ruff lint pass. No live database mutation, HTTP call, AX-B implementation,
  parse response, role-visible corpus identity, snapshot recovery, or Braincrew `READY` was
  produced.

Likely follow-ups:

- "Why not fix the 401 by removing the tenant join?" — The 401 proves the isolation check works.
  The missing target-tenant state must be provisioned; authentication must not be weakened to fit
  stale test data.
- "Why does AX-B need materialization if parsing already succeeded?" — Extraction proves parser
  output, but the strict observation obtains non-empty stored EvidenceSpans from materialized
  source/chunk/span rows. Extraction alone cannot satisfy that evidence contract.
- "What if the database commits but the receipt cannot be finalized?" — AX-A retains the
  create-only reserved path and returns a typed failure. It does not claim rollback or authorize a
  retry; an operator must inspect the exact stored state and propose recovery separately.
- "Why not add an audit row with the new user?" — Auditability matters, but Issue #44 deliberately
  locks AX-A to one `User` and no other database row. Changing that invariant requires a new
  reviewed contract rather than silently widening this provisioning transaction.
- "Does adding parse sources change the corpus being evaluated?" — Yes, for roles that can see
  `hr_only` tenant uploads. That is why all three corpus identities are re-measured after AX-B and
  why the handoff freezes the actual counts, digests, and contributing versions rather than
  reusing pre-B values.
- "Why keep v2 language at all after loading v3?" — The integrated successor bundle and imported
  corpus are v3, but the component files preserve version 2.0.0 semantics and the six parsing
  Verification cases remain that historical component. The decision states both identities
  instead of collapsing them.
- "Can the old artifacts still replay?" — Yes. Replay uses immutable artifact bytes and does not
  query current AX rows. Only the new live-preflight contract repins the principal, tenant, AX SHA,
  and generated attachment IDs.
- "Did key rotation or a snapshot prove the system is safe and ready?" — No. Rotation resolves one
  credential-response action, and snapshots are recovery evidence. `READY` still requires merged
  AX code, separately authorized operations, six strict responses, three post-B corpus identities,
  sanitized receipt replay, and Braincrew #38 verification.

### D8.5b Amend our own ticket instead of weakening the platform's bounded-resource control

Decision:
: AX-B uploads the six reviewed `.txt` sources as **two bounded requests of five and one** into
  **one** target-owned conversation, through the existing
  `POST /v1/conversations/{thread_id}/attachments` route. The superseded instruction — six files in
  one multipart request — was not executable, because AX enforces `MAX_FILES_PER_OPERATION = 5` per
  upload request. We amended the Braincrew-authored ticket and left the AX control untouched. This
  needs zero AX source change. The canonical record is
  `docs/decisions/2026-07-25-ax-b-bounded-upload-request-split.md`.

Why:
: Pre-implementation review compared the ticket against the merged AX-A baseline
  `fe16c0cedc1e64856d9e107e111665d0ba2e444d` and found that our own specification asserted an
  ingestion shape the product does not permit. `MAX_FILES_PER_OPERATION = 5`
  (`backend/src/ax_engine/attachments/intake.py:12`) is validated per call
  (`intake.py:54`) at the single unconditional call site in `stage_files`
  (`backend/src/ax_engine/attachments/service.py:64`), and
  `backend/tests/unit/test_attachment_intake.py:25` pins exactly the six-file rejection. Critically,
  the cap is **per request**, and `stage_files` (`service.py:51-90`) imposes no per-thread total, so
  `5 + 1` into one thread satisfies the platform contract as written. The Evaluation Plane exists to
  measure the product, not to reshape the product's controls so that the measurement is more
  convenient to collect.

Rejected alternatives:
: Raising `MAX_FILES_PER_OPERATION` was rejected because the constant governs every tenant HTTP
  caller of a multipart endpoint, not only our local/test operator command; it would weaken a
  deliberate bounded-resource control for all tenants and require deleting or rewriting an existing
  test that exists to pin that boundary. An operator-only `max_files=` override on `stage_files` was
  rejected because it adds a permanent bypass surface to a security-relevant validator while
  still requiring the same ticket amendment — the locked mutation boundary is the HTTP route, not
  the service method, so the override buys wording rather than capability. Reclassifying the cap as
  an AX bug to be fixed was rejected because nothing in AX presents it as defective; calling a
  working control a defect so our ticket can stand unchanged inverts the SUT/Evaluation Plane
  relationship.

Trade-offs and failure modes:
: The split introduces a durable partial-batch state, and this is the real cost. The commit boundary
  is per request (`backend/src/ax_engine/api/routes/attachments.py:191`), and each staged attachment
  is flushed and immediately enqueued as a scan/parse job
  (`backend/src/ax_engine/attachments/service.py:105-115`). If the five-file request commits and the
  one-file request fails, five attachments and five running jobs are already durable, and no
  cross-request transaction exists or may be manufactured. The required behavior is to fail with
  `PARSE_SOURCE_UPLOAD_FAILED`, retain the partial state as evidence, and perform no delete, purge,
  cancel, rollback, retry, or partial-success receipt.

: The subtle hazard is that a naive retry would appear to succeed. `stage_files` de-duplicates by
  content hash within the thread (`service.py:68-76`): an attachment with the same
  `(tenant_id, thread_id, content_hash)` that is not deleted is returned as-is and no new row is
  created. A retried upload therefore returns HTTP 201 with the existing IDs while creating nothing.
  The platform will not signal this, so the rerun must be refused up front by
  `PARSE_SOURCE_PREEXISTING_STATE`, and the count-delta assertion must be computed against a
  pre-run baseline rather than inferred from HTTP responses.

: The preserved invariant is unchanged: one target-owned thread and six AX-generated attachment IDs,
  with caller-forced IDs still forbidden. Only the "one multipart request" wording is superseded.
  The request split is an ingestion detail and is deliberately not visible in the case-to-attachment
  mapping, which stays ordered by reviewed bundle order.

Validation evidence:
: Read-only inspection of AX `origin/develop` at `fe16c0cedc1e64856d9e107e111665d0ba2e444d`
  established the per-request cap, the absence of a per-thread cap, the per-request commit boundary,
  the per-attachment job enqueue, and the content-hash de-duplication branch, at the exact file and
  line references above. The finding was independently re-verified before escalation, and the
  resolution is the user-authorized option. No AX source was modified, no AX test was executed, and
  no live upload, attachment, extraction, approval, materialization, parse observation, or corpus
  identity was created or observed for this decision. AX-B implementation was in progress and
  unreviewed when this card was written; nothing here claims AX-B completion, live readiness, parse
  quality, or Braincrew `READY`.

Likely follow-ups:

- "Why not just raise the limit? It is one constant." — Because the constant is not scoped to our
  operation. It bounds every tenant's multipart upload on a public route, and an existing test pins
  the six-file rejection deliberately. We would be widening a resource control for all callers to
  save ourselves one HTTP request, and we would be doing it inside a ticket whose own boundary says
  existing services are the only mutation surface. The cheaper change was to our own sentence.
- "Is this not just working around a product limitation?" — It is conforming to one. The limit is a
  policy, not an obstacle; five per request with no per-thread total is a coherent design, and
  `5 + 1` uses it as intended. A workaround would be the override argument we rejected.
- "Who found it, and why did it not surface earlier?" — Pre-implementation review, comparing the
  ticket to the merged AX-A baseline before the implementer reached the upload step. It did not
  surface during scope-lock authoring because that phase was documentation-only against a
  pre-AX-A investigation baseline and never executed or code-checked the upload path. That is the
  process lesson: a lock authored without reading the call site can specify an unexecutable shape.
- "Does the split change what you are measuring?" — No. The same six byte-exact sources land in the
  same thread with the same approval, provider lineage, and count deltas. The ingestion request
  boundary does not appear in the attachment mapping, the parse observations, or the corpus
  identities.
- "What breaks if the second request fails?" — Five committed attachments and five running scan
  jobs, with no cross-request rollback. We stop, keep the evidence, and refuse the rerun by
  pre-existing-state check. We specifically do not clean up, because deletion is out of scope and
  because the partial state is the evidence an operator needs.
- "Why is a retry dangerous rather than merely useless?" — Content-hash de-duplication makes it
  return 201 with the existing IDs and create nothing, so a retry can look like success while
  producing no new rows. That is why the guard is a pre-flight state check rather than an error
  observed after the fact.
- "You changed a document that was pinned as immutable — how is that safe?" — The pinned commit
  `fc1302d54ab3f3735800d31a321b6f70e947572e` is untouched, and the original sentences remain verbatim
  at HEAD. The supersession is a separate dated decision record plus explicit forward pointers, so a
  reader arriving from either the pin or HEAD reaches the same current answer and can see exactly
  what changed and why.

### D8.6 Approve exact evaluation-blind authoring guidance before corpus bytes exist

Decision:
: Freeze `docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md` before Issue #36. Bind
  its exact 10,680 bytes to
  `sha256:121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3`, an adjacent digest
  declaration, and a separate independent leakage-review record. Keep authoring blocked until a
  clean committed Braincrew SHA reproduces that digest and the provenance-evidence plus
  source-order prerequisites are resolved.

Why:
: A filesystem sandbox proves which inputs an authoring process can read, but it does not prove
  that the allowed brief is generic, accurate, or free of hidden benchmark hints. Reviewing and
  digest-locking the brief before any corpus byte exists closes that semantic gap and prevents a
  later wording edit from inheriting an earlier approval.

  PR #45 review also proved that isolation alone cannot make an impossible contract satisfiable.
  A blind author cannot reproduce source identities and digests hidden inside an already-frozen
  evaluation dataset, and a literal `provenance_status=reviewed` cannot prove who reviewed which
  bytes. Issue #46 therefore selects source-first evaluation freeze, plus durable review evidence,
  before authoring.

Issue #46 source-order decision:
: Selected source-order contract: **source-first evaluation freeze**.

  Rejected alternative: pre-existing, evaluation-independent exact source bytes or generator.

  Reason: no independently versioned, provenance-bearing artifact predates the evaluation-specific freeze.

  Failure mode: frozen evaluation identifiers, digests, or qualification feedback reach authoring.

  `braincrew-evaluation-dataset@2.0.0` remains immutable and is not a target for authoring or qualification in this lane.

  A successor dataset version greater than `2.0.0` is required after the new corpus version is sealed.

  The successor qualification receipt must bind that successor dataset version and digest to the unchanged sealed corpus digest.

  Qualification remains read-only and cannot return feedback, identifiers, or digests to authoring.

  PR #49 has merged and verified Issue #47, and Issue #47 is closed. Case freezing and
  qualification remain later tickets. The data-creation policy below authorizes only the new
  restricted Issue #36 session and its source-first lifecycle.

Issue #36 data-creation approval:
: Data-creation proposal gate: **APPROVED_FOR_NEW_SESSION**.

  Approval baseline: `5cec187af3e2d5b95b35f6e6f81fee55a73d5409`.

  The execution SHA must be the clean `origin/develop` commit containing this approval record, be
  descended from the baseline, and reproduce approved brief digest
  `sha256:121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3`.

  Authoring owner: `codex-issue-36-authoring-agent`.

  Manual provenance reviewer: `DHChe-corpus-provenance-reviewer`. This is the human approval
  authority and must differ from the authoring owner.

  External lifecycle root: `/Users/astralpig/braincrew-issue-36-authoring`.

  Exact lifecycle targets are
  `/Users/astralpig/braincrew-issue-36-authoring/authorization/data-creation-authorization.json`,
  `/Users/astralpig/braincrew-issue-36-authoring/tool/author-corpus`, empty
  `/Users/astralpig/braincrew-issue-36-authoring/staging`, absent
  `/Users/astralpig/braincrew-issue-36-authoring/receipts/authoring-independence-receipt.json`, absent
  `/Users/astralpig/braincrew-issue-36-authoring/review/provenance-review.json`, and absent
  `/Users/astralpig/braincrew-issue-36-authoring/sealed`. The staging target must be empty; all
  other create-only targets must be absent. All targets must be outside the repository and must not
  be symbolic links.

  Create-only authorization record:
  `/Users/astralpig/braincrew-issue-36-authoring/authorization/data-creation-authorization.json`
  uses schema `corpus-data-creation-authorization-v1`. It binds approval authority `DHChe`, the
  exact execution SHA, authoring-tool SHA-256, four exact input digests, all lifecycle target paths,
  authoring owner, manual reviewer, and its own canonical digest. The authorization record is
  create-only and must exist before authoring. Launch must reject any authorization-record
  mismatch.

  Allowed authoring inputs are exactly
  `docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md` at
  `sha256:121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3`,
  `schemas/ax-synthetic-seed-content-v1.schema.json` at
  `sha256:372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb`,
  `schemas/ax-synthetic-seed-content-v1.schema.sha256` at
  `sha256:c9dae9c47ce20f2e4b5c954dbd467e051ebf33081e13a033cc23f9b418897dff`, and
  sandbox-mounted `input-digests.json` at
  `sha256:e707333d28fb9452b2823d1b6c125a1b6dcc3a0d5b118069e8bf7b502854061e`.
  These are the authoring brief, content schema, schema digest declaration, and canonical
  input-digest inventory. Repository contents, pack schema, datasets, fixtures, prior artifacts,
  credentials, network, database, AX, and qualification feedback are denied.

  No source byte may be created before the clean execution SHA and external authoring tool SHA-256
  are recorded and revalidated. The user delegated those dynamic pin decisions to the new-session
  agent under this policy; their values must be durable before the authoring process starts.

  Author, then review, then seal, then replay. Both the independence receipt and provenance sidecar
  are create-only. Sealing may start only after the manual reviewer approves every exact source
  digest, and qualification remains out of scope.

  No automatic retry, in-place repair, overwrite, alternate input, feedback-driven second pass, or
  cleanup after a failed run is authorized. Dirty or wrong source SHA, any digest drift, denied
  capability success, non-empty staging, existing target, unsupported sandbox, nonzero authoring
  exit, empty or invalid output, manual rejection, sidecar mismatch, sealing failure, or replay
  failure stops the lifecycle.

  RED contract tests must first prove the entry pins, restricted inputs, create-only targets,
  distinct owner/reviewer authority, lifecycle order, and stop conditions before any source-byte
  authoring attempt.

Rejected alternatives:
: Prompt-only confidentiality instructions, guessed lowercase role aliases, public-source
  ingestion or adaptation under a pack-wide synthetic label, approval without an exact byte
  digest, opening evaluation design or result material during authoring, and feeding qualification
  mismatches back into authoring. Those paths make
  independence unverifiable, can produce AX-invalid visibility/provenance metadata, or allow a
  changed brief to masquerade as reviewed.

Trade-offs and failure modes:
: Exact-byte approval makes even a harmless wording change require a fresh evaluation-blind
  authoring and review cycle. The brief must also track external AX contracts without importing
  AX code. Staged authoring is pinned to
  `schemas/ax-synthetic-seed-content-v1.schema.json` at
  `sha256:372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb`; the later
  `schemas/ax-synthetic-seed-pack-v1.schema.json` at
  `sha256:4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa` governs only the
  post-qualification import manifest. Issue #47 repairs and tests the production boundary: the
  restricted sandbox mounts the content schema and its pinned digest, never the pack schema. To
  keep the role pin narrow, the brief records AX merge
  `47673b83a9fb431f2bad550781db18c7bee8b67e`, content version
  `ax-synthetic-seed-content-v1`, canonical `pack_contract.py` digest
  `09fe230ca2e976bec156d72987b5cf1f39419c34829e323222d11bef35e1fc2a`, and exact roles
  `Executive`, `HRAdmin`, `HRPractitioner`, and `Employee`. Post-review drift, incorrect aliases,
  non-CC0 licensing, BOM/Unicode/line-ending drift, and unsafe paths all fail closed.

  The strict staged pack cannot contain an undeclared receipt. Issue #47 therefore requires an
  external, read-only, create-only provenance sidecar that binds the sealed digest, per-source
  identities and digests, synthetic origin, author, CC0 assignment, reviewer/date/timezone,
  decision, and its own digest; reviewer identity must differ from the authoring owner.
  `corpus-sealing-receipt-v2` binds the validated sidecar digest. The external sealing input must
  be read-only; replay validates canonical bytes and digest independent of normalized filesystem
  write bits and fails on missing, pending, mismatched, or tampered evidence. Historical v1 receipt
  replay remains supported, while new seals require v2.

Validation evidence:
: The first TDD run failed twice because the brief was absent. Review-driven cycles then failed
  four tests for the unpinned role authority and missing reviewed-to-committed byte binding, two
  tests for overbroad licensing and incomplete byte/path rules, and two tests for missing digest
  and review artifacts. Standards later caught stale gate-state wording inside the brief; a fresh
  evaluation-blind repair invalidated the first approval, and two exact-byte tests failed against
  the stale artifacts before reapproval and relocking. Spec review then caught a remaining
  contradiction that excluded the brief's own digest lock; another fresh evaluation-blind RED/GREEN
  repair and exact-byte reapproval restored ten passes. Final Spec review then found that external
  CC0 adaptation contradicted the synthetic-only pack contract; another fresh blind RED/GREEN cycle
  required every source to be newly authored, `CC0-1.0`, and reviewed, prohibited public-source
  ingestion/adaptation, and rebound the ten-pass suite. PR #45 review then produced targeted RED
  failures for the wrong authoring schema and stale exact-byte artifacts. A new evaluation-blind
  author amended only the brief contract, a separate blind reviewer approved it with zero material
  findings, and the focused suite passed with the content/import schema split, provenance sidecar
  blocker, source-order blocker, and exact digest above.
  A fresh independent `code-reviewer` inspected only sanitized, allowlisted policy inputs; all
  tests, prior digests, prior review evidence, and downstream documents were denied. The reviewer
  found zero material issues and independently reproduced the exact digest above. The fixed repair
  commit's post-commit byte equality is **PASS**. Issue #46 is closed after PR #48. PR #49 merged
  Issue #47 into `develop` as `4d80b9b8950f4d7356a9aa9806f492ae79126dab`; its Python and frontend
  checks succeeded, and Issue #47 is closed. The separate data-creation proposal gate is now
  `APPROVED_FOR_NEW_SESSION`; Issue #36 remains blocked only until this approval record is merged
  and the new session passes the dynamic execution-SHA and authoring-tool-digest entry checks.

  PR #49 review then found three contract gaps before merge: self-review was accepted, replay
  depended on preserved read-only filesystem bits, and the canonical design still described the
  older v1/pack-schema boundary. Each received a focused RED/GREEN repair: reviewer identity must
  differ from authoring owner, sealing enforces read-only only on the external input while replay
  uses canonical bytes and digest independent of normalized filesystem write bits, and the
  canonical design now records the v2/content-schema contract. PR #49 subsequently received
  successful Python and frontend checks and merged into `develop`; that merge is the verification
  evidence for the closed Issue #47 dependency.

Issue #36 execution checkpoint:
: The restricted lifecycle ran from clean Braincrew SHA
  `8e669db46b698b8791739feee910ba1b561a0936` only after a 320-test baseline and the
  content-addressed entry checks passed. Create-only authorization digest
  `sha256:9eabf4fff6de5bf54065c8d4bd657eda4ebeb06c630ad45f53fe41c36457a1a7`
  bound the reviewed authoring-tool digest, four approved input digests, exact lifecycle paths,
  and the distinct author/reviewer authorities. One sandboxed authoring run produced 14 exact
  source digests and independence receipt
  `sha256:28a22cb6f1c0d35ced80d43dc727699cecae388a8012f6a292d618719371cf7f`.
  `DHChe-corpus-provenance-reviewer` manually approved every source digest, newly authored
  synthetic origin, `codex-issue-36-authoring-agent` ownership, and `CC0-1.0` assignment on
  `2026-07-23` in `Asia/Seoul`. Seal and replay each succeeded once. The immutable corpus digest is
  `sha256:5f0c254b3dc64b23470029b1004106dc078a9602062da8fa8041623bf91fb7e4`,
  provenance digest is
  `sha256:eb43fc824cd54bf10e8805b5fdeb1915bcaac368cb458ce8981a481cd7d4fce1`,
  and receipt digest is
  `sha256:bc508b6001facbef67bacd7e0c1d4d5123f04bc1e33d2849b5e7d455183df62b`.
  Retained evidence contains identities and digests, not source text. Qualification, successor
  dataset freeze, AX/DB/service calls, preflight, experiments, repair, and retry remain absent.

Likely follow-ups:

- "Did the reviewer see the benchmark cases?" — No. The authoring and leakage-review contexts
  excluded datasets, fixtures, queries, expected answers/evidence, scores, splits, prior results,
  PR #29, and its branch.
- "Why are the AX roles capitalized?" — They are exact case-sensitive values from the external
  seed-pack `VisibilityRole` validator, not UI labels or guessed aliases.
- "Did APPROVE immediately start Issue #36?" — No. The brief approval alone did not authorize
  authoring. The later data-creation gate had to merge, and the fresh session then pinned the exact
  clean execution SHA, external tool digest, lifecycle paths, and RED contracts before creating
  source bytes. Only after those checks passed did the one-run Author → manual Review → Seal →
  Replay lifecycle execute.
- "Did Issue #35 create a corpus or manifest?" — No. It created only the generic brief, its
  digest declaration, contract tests, and leakage-review evidence.

### D8.7 Gate the successor dataset freeze on a separate human reviewer

Decision:
: Publish `braincrew-evaluation-dataset@3.0.0` first as a candidate, not an automatic freeze. Bind its integrated
  digest `sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d`, its three
  component digests, and the sealed `braincrew-independent-hr-corpus@1.0.0` predecessor digests to
  `docs/reviews/2026-07-23-issue-53-successor-dataset-review.md`, and keep the card and checklist
  at `PENDING_MANUAL_APPROVAL` until the `DHChe-successor-dataset-reviewer` authority records an
  approve or reject decision on those exact bytes. On 2026-07-23 that authority confirmed all eight
  checks and recorded `Decision: APPROVED`, so the exact candidate is now `FROZEN`.

Why:
: Contract tests can prove that the successor is internally consistent — 100 unique cases, the
  20/30/40/10 allocation, the 70/30 split, unchanged evaluator semantics, closed source digests,
  and rejection of case, source, visibility, split, predecessor, and version-only tampering. They
  cannot prove that the rebound evidence actually answers each query, that role visibility matches
  intent, or that a distractor is genuinely unhelpful. Those are semantic judgments, so the freeze
  authority is a human and is deliberately separate from the authoring and corpus-provenance
  authorities used in D8.2 and D8.6.

  Making approval external to the candidate bytes also removes the self-approval loop: the
  implementing agent cannot both produce the bytes and declare them frozen.

Rejected alternative:
: Treat a fully green contract suite as the freeze condition. It would convert "the agent's own
  invariants hold" into "the ground truth is correct", which is exactly the substitution this
  portfolio argues against.

Trade-off:
: The dataset stays unusable for qualification, seed-pack import, preflight, and experiments until
  a human finishes the checklist. Schedule risk is accepted in exchange for an auditable freeze.

Failure modes:
: an agent claiming freeze from green tests; approval recorded against a digest that no longer
  matches the bytes; the reviewer approving structure without opening the component files; and
  review feedback leaking back into the sealed corpus authoring lane.

Validation evidence:
: `tests/contract/test_successor_dataset_freeze.py` proves manifest-component-predecessor binding,
  dataset `2.0.0` immutability, preserved evaluator/metric/risk/split semantics, complete source
  digest and visibility closure with `demo-lifecycle-checklist-014` retained as an uncited
  distractor, six tampering rejections, version-only substitution rejection, create-only
  qualification receipt-v2 and seed v3 with rollback, `receipt-v1` replay support, v1/v2 dispatch
  separation, wheel packaging of both bundles, and that the checklist quotes the exact candidate
  digests.

Reviewer resolution:
: All 30 retrieval cases carry `role: Executive`, while the grounded cases span `employee`,
  `Executive`, and `hr_manager`. The reviewer accepted this as a constraint-induced limitation:
  `retrieval-dataset-v1` permits only `Executive` or `HRManager`, `HRManager` maps to
  `HRPractitioner`, and all 14 sealed sources are visible to `HRPractitioner`, so no valid forbidden
  source exists for that role while forbidden-visibility applicability remains unchanged. This
  freeze therefore claims Executive retrieval visibility fixtures, not multi-role retrieval
  execution evidence.

Likely follow-ups:

- "Why not freeze automatically once tests pass?" — Green tests prove internal consistency, not
  ground-truth correctness. Freezing on them would let the evaluation system certify itself.
- "What stops an approval from drifting off the bytes?" — The checklist quotes the integrated
  digest, all three component digests, and the three predecessor digests, and a contract test
  asserts those exact strings are present.
- "Is dataset 2.0.0 affected?" — No. Its bytes, digests, and `receipt-v1` replay are asserted
  immutable, and both bundles ship in the wheel.
- "Why a third distinct authority?" — Authoring owner, corpus-provenance reviewer, and successor
  dataset reviewer answer different questions; collapsing them would recreate self-approval.

### D8.8 Qualify the frozen successor once without exposing local paths

Decision:
: Issue #37 actual qualification: **SUCCEEDED_ONCE**.

Evidence:
: On 2026-07-23 the read-only qualifier ran exactly once against the unchanged
  `braincrew-independent-hr-corpus@1.0.0` sealed content digest
  `sha256:5f0c254b3dc64b23470029b1004106dc078a9602062da8fa8041623bf91fb7e4` and exact
  `braincrew-evaluation-dataset@3.0.0` integrated digest
  `sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d`.
  The parsing, retrieval, and grounded component digests remained
  `sha256:33e17fbb4d3f5485df1482de37e472e1b20fceef922c9b1dda90f8d9dfc25f73`,
  `sha256:9687ead24590cab1b9d244ef876f226545a1fb1aa2013c50e4be7a63430c8408`, and
  `sha256:f76a9a1fa9a6a4b467f76ce7649dc7c15f5ad7c615d6cbb20ed3394e486d94b2`.
  The create-only pair uses `corpus-qualification-receipt-v2` and
  `braincrew-evaluation-dataset-3.0.0`.

- Receipt logical digest: `sha256:c564b1442c135fef5d5430b313914951e2b5ab4cc7e0fd0bbbdefb0b928ea6ce`
- Qualification receipt file digest: `sha256:8843c87597db779ece932585445bae9dbdf9b5f26f4f81a7b9d069a1699968ed`
- Import logical digest: `sha256:9df8dbd212c6e0253b3c58feb392869bffb226d816805ee7ed166072596003bd`
- Import manifest file digest: `sha256:b1899d6be6017a2485d93c67066023a87f8aaa78b0b63012fb9f8d8a040f3821`

Validation:
: Replay reproduced the receipt and import digests, redaction checks passed, historical receipt-v1
  compatibility remained green, and the sealed input tree was unchanged. The CLI was repaired
  through RED/GREEN so qualification and replay summaries retain only safe file names rather than
  local absolute paths.

Stop:
: No retry, repair, AX import, database, service, snapshot, preflight, or experiment execution was
  performed. The next operator-controlled step is AX Issue #37; Braincrew baseline/candidate work
  remains unauthorized.

### D8.9 Keep qualification identity separate from consumer file bytes

Decision:
: Newly created `import-manifest.json` files use newline-free canonical JSON because AX imports
  require byte-for-byte canonical form. Qualification receipts keep their existing canonical JSON
  plus one trailing line feed contract.

What was wrong:
: Braincrew PR #55 appended one trailing line feed to the import manifest. The parsed payload was
  correct, but AX PR #42 compares the file to exact canonical JSON bytes and therefore rejected it
  with `AX_SEED_PACK_CANONICAL_BYTES_INVALID`.

Why this does not change qualification identity:
: The qualification receipt logical digest remains
  `sha256:c564b1442c135fef5d5430b313914951e2b5ab4cc7e0fd0bbbdefb0b928ea6ce`;
  its file digest remains
  `sha256:8843c87597db779ece932585445bae9dbdf9b5f26f4f81a7b9d069a1699968ed`;
  and the import logical digest remains
  `sha256:9df8dbd212c6e0253b3c58feb392869bffb226d816805ee7ed166072596003bd`.
  Only the import file digest changes from historical PR #55
  `sha256:b1899d6be6017a2485d93c67066023a87f8aaa78b0b63012fb9f8d8a040f3821`
  to AX-canonical
  `sha256:e00c7036bd67f93347957215fddc4185a18eb2e62e90bfb58657f0b7598f20ac`.

Compatibility and failure modes:
: Replay accepts the new exact-canonical import bytes and the historical canonical-plus-one-line-feed
  PR #55 bytes. Receipt-v1 remains supported. Leading or trailing spaces, pretty printing, multiple
  line feeds, a newline-free receipt, and every other non-canonical form fail closed.

Validation:
: TDD first reproduced the trailing-line-feed mismatch. Read-only loading through exact AX SHA
  `e25f333b55fca34118a954a17e5e0cd88dc7ea39` then accepted the repaired manifest with 14 sources
  and 11,528 total source bytes while database and provider configuration were absent.

Rejected alternative:
: Loosen AX to normalize whitespace. That would weaken AX's tamper-evident publication contract and
  would move a Braincrew producer defect into the consumer.

Stop:
: The existing external qualification artifacts are immutable. This implementation did not
  republish or requalify a pack and did not run AX changes, database or provider access, snapshots,
  dry-run, apply, service verification, baseline, or candidate work.

Likely follow-ups:

- "Why support the old import bytes at all?" — Replay is evidence verification, so it must continue
  to verify the already published PR #55 artifact while new publication follows AX's exact contract.
- "Why is one line feed allowed for imports but not arbitrary whitespace?" — It is the single known,
  digest-pinned historical representation. Accepting any broader normalization would hide tampering.
- "Why keep the receipt line feed?" — AX does not consume that file, its byte digest is already part
  of qualification evidence, and changing it would unnecessarily change qualification identity.

### D9. Use layered verification and an evidence-driven ten-day sequence

Decision:
: Deliver schemas, metric goldens, properties, adapter contracts, state and storage tests, fixture E2E, live Verification, dashboard checks, and clean-container reproduction in dependency order.

Why:
: Passing unit tests alone cannot prove that the published experiment came from a compatible live SUT, that the metrics are mathematically correct, or that the dashboard preserved the evidence. Each layer validates a different claim.

Schedule rationale:
: Contracts and dataset cases begin before UI work. A baseline is run before candidate improvement. The dashboard is built from validated artifacts only after the evidence pipeline exists. Submission QA and storytelling occupy dedicated final days instead of being treated as leftover work.

Frozen first comparison:
: The existing AX API supports an immediate `evidence_limit=3` baseline and `evidence_limit=5` candidate while both retrieve with `top_k=5` and hold SUT SHA and other contracts constant. This guarantees an honest answer-context configuration experiment without changing retrieval measurement opportunity; a failed candidate remains valid evidence.

Same-SHA schedule guard:
: Day 8 reuses the AX SUT SHA pinned for the baseline and freezes only the candidate run configuration. Pinning a new AX commit would create a different, separately versioned product-code experiment and cannot be substituted into `candidate-plan-v1`.

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
- "Why choose evidence limit as the first candidate?" — It is already executable through the current API, keeps retrieval depth identical, and isolates whether transferring two more evidence items improves grounding enough to justify latency, token, and cost changes. It is not misrepresented as a code improvement.
- "Why does Day 8 not pin a new candidate SHA?" — The frozen first comparison changes only `evidence_limit`; both runs must record the same AX SHA. A code-change candidate requires a new candidate-plan version and a separate comparison.
- "How do two engineers get the same metric?" — Metric contract v2 freezes case-level formulas, the claim-proposition catalog, exact alternative matching, macro aggregation, duplicate and rank rules, zero-denominator behavior, and unrounded gate comparison, with hand-calculated goldens for every primary metric.

### D10. Bind the evaluation plane to the SUT through the receipt contract, not through pinned identifiers

Decision:
: The live preflight derives the evaluation principal and the case-to-attachment mapping from the AX handoff receipt, pinning one value — the independently reviewed receipt's SHA-256 — instead of seven literals. Braincrew Issue #38's recorded "receipt consumer only" role is confirmed as a binding architectural commitment. Locked in [the receipt-derived binding decision](../decisions/2026-07-26-preflight-receipt-derived-binding.md).

Why:
: The pinned literals were not stale, they were wrong by construction. AX generates attachment IDs and the contract forbids caller-forcing them, so a Braincrew constant naming an AX-generated identifier is wrong at authoring time and stays wrong. Measured on 2026-07-26 against the applied corpus: zero of six pinned attachment UUIDs existed, and the pinned owner resolved to a demo Executive in a different tenant who had never been an evaluation principal. Pinning the receipt digest makes the binding right by construction rather than right by accident of today's data.

Rejected alternative:
: Re-pin the seven literals to today's values. It buys one green run and re-arms the same failure on any future provisioning, and it quietly contradicts the receipt-consumer-only role. Also rejected: harvesting the mapping from the live database, which is the tautology below; adding a caller-forced attachment ID to AX, which weakens a safety property in the system under test to make a flag flip; and committing a copy of the receipt, which creates a second artifact that can drift from the reviewed original.

Trade-off:
: Deriving at run time is an abstraction, and the textbook objection is abstraction for a single use case. Accepted because it makes the code match an architecture that is already written down — Issue #38 is already recorded as a receipt consumer and the SUT Adapter contract is already the documented connection between the repositories. The cost is a run-time input and a digest check; the alternative's cost is a guaranteed repeat failure.

Known failure modes:
: Reading the receipt without verifying its digest would have all of this design's complexity and none of its safety. Any fallback to the previous literals on a missing or mismatched receipt would silently restore the behaviour being removed. Treating "the six UUIDs" as one set would fix the wrong half, because `attachment_id` is a probe address while `approval_id` is a provenance stamp and the two sets are disjoint.
: Implementation exposed a fourth mode the decision had not anticipated. The guard that validates a captured artifact runs inside a Pydantic model validator, which accepts no keyword arguments and has no receipt, so deleting the literals left it with nothing to validate against. The obvious repair is a trap: carrying the derived mapping inside the artifact makes the artifact certify itself, because the pinned digest covers the receipt's bytes and not the derived mapping — an artifact that probed the wrong attachments would simply declare its own mapping and pass, deleting a real check while looking like a refactor. Pydantic validation context carries the binding instead and refuses when it is absent.

Validation evidence produced:
: The receipt is create-only, passed Stage 11 independent review with its digests bound, and carries every value the design consumes. Live measurement confirmed the mismatch on all three axes, and `git merge-base` confirmed the pinned SUT commit is a superseded ancestor rather than a fictional value.
: Implemented and merged into `develop` as squash commit `dfc41ff` through [PR #69](https://github.com/DHChe/braincrew-datateam-portfolio/pull/69), closing [Issue #67](https://github.com/DHChe/braincrew-datateam-portfolio/issues/67). Each of the seven failure conditions has a test that observes the refusal rather than the success path — `tests/contract/test_preflight_receipt_binding.py` — and the digest is verified before the receipt is parsed, so no window exists in which unverified content is trusted. Independent review confirmed by **mutation testing** that each of the two fail-closed guards fails its test when disabled, and an assertion-level comparison against the base found all 66 pre-existing assertions preserved in order, with three added and none removed or modified. Repository gates — `ruff format`, `ruff check`, `mypy` over 65 source files, 364 tests, `git diff --check` — were reproduced independently three times rather than accepted from a single report.

Validation evidence still required:
: `live_preflight` captures live HTTP parse observations and the AX runtime was stopped by Stage 12, so neither this design nor any alternative can be validated end to end without a separately authorized runtime start. Controlled tests can proceed without one; the live capture cannot.
: The pinned digest's **own correctness** is also outside what any in-repository test can establish, because copying the receipt in is forbidden. It rests on the Stage 11 independent review plus manual SHA-256 recomputation by three separate reviewers, and a typo in that constant would leave all 364 tests green. Of the 37 principal-path tests, **33 override the pinned constant and 4 do not** — and of those 4, only one actually reaches a comparison against the real pinned value (`test_receipt_digest_mismatch_refuses_without_literal_fallback`); the other three refuse earlier, before the digest is compared. The overrides are unavoidable, since no hermetic fixture can hash to the pinned digest without being a byte copy of the receipt. This is a structural limit of the design, stated rather than hidden.

Likely follow-ups:

- "Isn't deriving from a file just moving the hardcoding?" — What is pinned changes from seven values that are wrong by construction to one digest that is verified at run time. The literals were never checked against anything; the digest is.
- "What stops this from being self-confirming?" — The receipt's digest is committed into Braincrew source **before** the observation, and the receipt itself is create-only and independently reviewed. Binding the digest is the control; reading the file is not. This project met the self-comparison failure twice before catching it a third time here — a regenerated inventory compared against its own generator, and a `cmp -s` between two runs by the same party.
- "Why not derive the SUT commit too, since the receipt carries it?" — Because it would delete a real check. `receipt.repository.commit_sha` is an observed fact; `PINNED_AX_SHA` is a Braincrew-side review decision. Requiring them to match fails when someone presents a receipt produced at an unreviewed commit.
- "Why is the flag still `false`?" — It is a prose claim, not a computed value; it appears nowhere in `src/`. This decision supplies the mechanism for two of the five things a `true` flag would have to prove, and the runtime needed for the rest is stopped.
- "Was anything deliberately left broken?" — Yes, and knowingly. `FROZEN_DATASET_VERSION = "2.0.0"` is the **integrated** manifest version and points at `dataset_manifest_v2.json`, while the AX corpus is labelled `braincrew-evaluation-dataset-3.0.0`. That label is **not** a foreign name that happens to collide: `corpus_qualification.py` declares it as a literal alongside Braincrew's own `DATASET_ID` and `DATASET_VERSION = "3.0.0"`, pointing at Braincrew's own `dataset_manifest_v3.json`. Same namespace, same authority — so this is a **real representation defect**, and it is recorded as one. It stayed out of scope in Issue #67 not because the value is right but because raising one constant changes the *case set*: integrated v2's parsing component is `parsing_cases_v1.json`, whose verification documents are `synthetic-rule-015…020`, while integrated v3's is `parsing_cases_v2.json`, whose verification documents are all `demo-*` — the two share **no document at all**. The digest comparison currently blocks the mismatch fail-closed, so nothing is silently wrong; the correct fix is a separate dataset-identity design, not a constants sweep.
- "Your tests override the pinned digest — doesn't that defeat the control?" — Thirty-three of the thirty-seven principal-path tests do, and they must: no hermetic fixture can hash to the pinned digest without being a byte copy of a receipt that must not be copied in. Four do not, and exactly **one** of those reaches a comparison against the real pinned value — the test that watches the control refuse a mismatched receipt. The other three refuse before the digest is compared, so they exercise the fail-closed paths rather than the pin. What no test establishes is that the pinned value itself is correct. That rests on independent review and manual recomputation, and the record says so rather than letting a green suite imply otherwise.
- "How do you know the refusal tests aren't passing for the wrong reason?" — Independent review disabled each fail-closed guard in turn and confirmed its test fails. That also surfaced a fragility worth naming: both mutations still raised, merely with a different message, so the tests are load-bearing **only** because of their `match=` strings. Removing `match=` would let both guards die behind a green suite, which is why the commit carries that as an explicit directive to future modifiers.
- "What did the review process actually catch that the gates did not?" — Two blockers the implementer did not see. The two fail-closed guards were correct but unobserved by any test, so the mechanism's gate could have been "simplified" away while 360 tests stayed green. And an acceptance file had replaced `subprocess.run` wholesale, so fourteen call sites still read as real `braincrew-eval` invocations while running in-process — real entry-point coverage had silently gone to zero while the test source still claimed it. The reviewer additionally corrected an overstatement in the implementer's own summary. None of this was visible from passing gates, which is the argument for independent reproduction rather than report-reading.
- "Why did the SUT commit not get re-pinned at the same time?" — Because it is a different kind of assertion and folding it in would have deleted a real check. `receipt.repository.commit_sha` is an observed fact; `PINNED_AX_SHA` is a Braincrew-side review decision. The applied commit `2bcaee34…` has been reviewed as the **provisioning** execution commit but never as the SUT commit **for evaluation**, and that review is a separate, still-open decision. That review has since been done — see [D11](#d11-review-the-sut-commit-as-a-subject-of-evaluation-not-as-a-record-of-provisioning).

### D11. Review the SUT commit as a subject of evaluation, not as a record of provisioning

Decision:
: `2bcaee3495fd7b3f624398819575cd86a5a15c47` is accepted as the AX SUT commit **for evaluation**, and `PINNED_AX_SHA` plus the packaged Adapter contract move to it. Locked in [the SUT-commit review](../decisions/2026-07-26-ax-sut-commit-for-evaluation-review.md); carried out by Issue #71.

Why:
: The pin was a superseded ancestor while the substrate and the reviewed receipt were both at `2bcaee34…`, so **no artifact captured against today's substrate could be constructed at all.** The commit had already been reviewed — but as the *provisioning execution* commit, which asks whether an operator ran reviewed write steps at a known clean checkout. The SUT question is different: is Braincrew willing to pin the covered evaluation read paths to this code and publish only observations that frozen corpus, provider and receipt evidence support? Answering the first does not answer the second.

Rejected alternative:
: Keep `72805930…`. It blocks every real artifact without preserving any evaluation-relevant boundary — the evaluation route, service, schemas, parser, retrieval query path and authorization logic have **empty diffs** across the whole five-commit range. Also rejected: deriving the SUT commit from the receipt, which deletes the check that fails when someone presents a receipt from an unreviewed commit; and folding in the dataset-version defect, which would mix SUT code identity with dataset identity in one diff.

Trade-off:
: The accepted commit contains substantial provisioning code that evaluation never reads, so the reviewed surface is larger than the surface that matters. Accepted because the runtime must match the applied substrate exactly, and because the range was classified file by file against six evaluation-observable axes rather than by what commit titles claimed. Commit titles are not evidence.

Known failure modes:
: The approval is **exact, not forward-compatible** — any later AX commit touching parser selection, text normalization, chunking, span offsets, principal lookup, permissions, embedding lineage, retrieval ranking, answer shaping, or the evaluation routes and schemas needs a new range review rather than a constants sweep. Writer-path changes in the range can alter stored vectors under concurrent writes, so reproducibility depends on frozen corpus and provider evidence, not on the Git pin alone.
: The re-pin also **deliberately turns one refusal off**: the reviewed receipt now passes the repository-commit comparison. That protection is not deleted or derived away — it is discharged by the completed review, and every other commit still refuses.

Validation evidence produced:
: The nine evaluation read surfaces have empty diffs across the range; `retrieval/service.py` changes only `embed_pending_seed_vectors`, leaving search, ranking, scoring and ordering untouched; `sources/materialization.py` changes exactly two lines, an import and one lock call. The implementation is **11 insertions and 11 deletions across 9 files** — the whole diff is the value, never the shape of a check.
: **Atomicity is enforced by tests rather than by convention.** Desynchronising the two pinned points fails hard in both directions — 38 failures when the source constant is reverted, 44 when the packaged contract is, each reporting `configured AX SHA does not match ax-http-v1 contract`. A partial sweep cannot go green.

Validation evidence still required:
: No AX runtime was started or queried, so nothing here proves a running server corresponds to the reviewed checkout; the controlled runtime-start procedure has to establish that link. No parsing, retrieval or grounded-answer benchmark was run. `braincrew_preflight_ready` stays `false`: this makes artifacts *constructible*, not *captured*.

Likely follow-ups:

- "What was the real risk in a find-and-replace across 39 lines?" — Not what the ticket predicted. It warned the unreviewed-commit negative test would be *silently* converted into something meaningless. Measured, it fails **loudly**: the test fed a constant equal to the new pin, so the receipt passed the gate and the assertion reported `DID NOT RAISE` — one failure out of 364. **The danger was never detection; it was the repair decision.** Deleting the test, weakening its `match=`, or re-pointing the constant at the new pin would each have turned the suite green while removing the general protection.
- "So what stops the next re-pin from making the same mistake?" — The fix that outlasts the change is the **rename**, not the new value. `APPLIED_AX_SHA` described what the constant *was* at one moment in history, which is exactly why it rotted when history moved. `UNREVIEWED_AX_SHA` describes the *invariant the test needs*, so the next person re-pointing it at the pin is visibly contradicting the name. The chosen value is a real unreviewed AX commit rather than a fabricated hex string.
- "Isn't a documentation-only decision separated from its implementation just overhead?" — It is what let the implementation be 22 lines. The decision absorbed the range review, the rejected alternatives, and the scope boundaries; the ticket carried five explicit requirements; the implementation had nothing left to decide. The measurable result is a diff where every changed line is the same substitution.
- "Why is the old SHA still all over the documentation?" — Because those are records of what was locked at the time. Rewriting them would turn history into a claim that it always said `2bcaee34…`. Independent review enumerated every surviving occurrence and confirmed each is intended preservation; the code carries zero.

### D12. Compose the two identity axes into a third schema, and bind both halves to one principal

Decision:
: `live-verification-preflight-artifact-v2` is a **third** schema alongside the two existing ones, carrying the frozen v3 dataset identity, three role-visible corpus observations and the six reviewed parse observations in one create-only artifact, and cross-checking each role's `contributing_versions` against `corpus_qualification.SEED_VERSION`. The principal-attachment contract is **not** subsumed. Locked in [the v2 contract decision](../decisions/2026-07-27-live-verification-preflight-artifact-v2-contract.md); carried out by Issue #77.

Why:
: The model was never the obstacle — `LivePreflightArtifact` already carried all three fields and the generic branch forbade neither. **Nothing produced the combination:** `AxHttpAdapter.corpus_identity()` had zero callers in `src/`, and the principal-attachment contract rejected corpus observations outright. So the work was a capture path plus an artifact contract, not a cross-check. Framing it as "just verify the three roles include the qualified contribution" understates it by an order of magnitude, which is why the ticket said so before implementation began.

Rejected alternative:
: Subsume the principal-attachment contract into v2. Its narrowness is itself load-bearing evidence — it exists to say *this capture is only the six probes, by the reviewed subject, and nothing else*. Folding it in would put all thirteen of its refusals up for re-derivation inside one change. Also rejected: pinning expectations on `corpus_id`, `corpus_digest`, `inventory_count` or `counts`. No frozen value exists for them; they are genuinely runtime-observed, and inventing one is not a check.

Trade-off:
: Two construction routes now reach the same model — v2 builds its payload by dumping the principal artifact and re-validating, because `build_live_preflight_artifact` still derives `schema_version` from `capture_contract is not None`. Accepted for this ticket and recorded rather than hidden. Accepted also: a v2 artifact whose **both** halves sit consistently on some other canonical tenant validates, because the rule is *agreement between the halves* and no frozen tenant value exists to pin against.

Known failure modes:
: The first implementation bound the six parse probes to one tenant and reviewed subject and left the three corpus observations bound to **nothing** — moving all three to a different tenant *and* subject was accepted and replayed clean, and a corpus observation with **zero HTTP attempts** was accepted, asserting a role-visible corpus identity with no evidence any request was issued. Fixed by mirroring the parse-side request validator and folding the corpus tenants into the **same** `tenant_ids` set, which can only tighten: the rule is `len(tenant_ids) != 1`, and threading only ever adds elements.
: Six reachable clauses inside the corpus attempt validator still have no test. Five mirror an identical pre-existing parse-side gap — measured, not assumed. **One falls below the standard its own sibling sets:** a failed request must not claim a response correlation id, the privacy clause the parse half demonstrably tests. Carried as a follow-up covering both halves, because fixing one side leaves the asymmetry it was measured against.

Validation evidence produced:
: All eight identity mutations that were **accepted** before the repair are **refused** after it, re-run from the original probe script rather than a rewritten one. The two deliberate canaries — a response naming a different tenant's corpus, and one reporting an empty inventory — are still accepted, proving the fix did not overshoot into invented expectations.
: **Thirty-five mutations across four sweeps** established that every structural defence in the new contract is observed by a test. All thirteen pre-existing refusals still fire on the v2 path. Gates: Ruff, mypy over 65 source files, **387 passed** (from 370, with zero test deletions).

Validation evidence still required:
: Every result comes from `httpx.MockTransport`. **Nothing was captured**, no AX runtime was started, and no live network call was made. `braincrew_preflight_ready` stays `false`; a live runtime answering real parse probes needs a separately authorized start, and AX #37 remains an open formal blocker of Issue #38.

Likely follow-ups:

- "You wrote the ticket and it contained a false claim — how is that not disqualifying?" — The ticket asserted the corpus-observation refusal was "currently observed by tests." It had **zero** coverage: one `git grep` hit, in `src/` only. Independent review caught it; the correction is a comment on the issue and the body is preserved so the error stays visible. The instruction it supported was right and was followed, and the implementation's new test is the **first** that has ever observed that refusal — the change closed a hole the ticket wrongly believed was already closed. The system that caught it is the point: a claim written by the person with the most interest in it was measured by someone else.
- "How do you know your tests are real and not decoration?" — By deleting the thing they defend. The five-line reuse that carried the reviewed-subject binding, single-tenant rule, frozen timeout, probe-set completeness, and the parse-evidence, span and attempt checks for the **entire** v2 contract could be removed with the suite still at `370 passed`. Reading it would never have shown that; disabling it did. This is the **fifth** instance of that shape recorded here, and every one was found by mutation.
- "Why is the corpus response barely validated compared with the request?" — Because the request is ours and the response is the SUT's. We can pin every field we send, and we have. Pinning what AX returns for `inventory_count` or `corpus_digest` would freeze an observation into an expectation and turn a genuine measurement into a tautology — the exact failure this repository has recorded four times over.

### D13. Make the readiness verdict a judgment, which meant reversing a decision locked the same day

Decision:
: The v2 preflight carries `readiness: Literal["READY", "NOT_READY"] | None`, scoped to that schema, and **may retain one typed blocker when the verdict is negative**. Corpus fetch failures become a typed `LIVE_CORPUS_IDENTITY_FAILED` blocker rather than an escaping adapter exception. Locked in [the readiness verdict decision](../decisions/2026-07-27-live-verification-readiness-verdict.md); carried out by Issue #80. This **deliberately reverses** [D12](#d12-compose-the-two-identity-axes-into-a-third-schema-and-bind-both-halves-to-one-principal)'s rule that a v2 artifact may not retain blockers.

Why:
: Issue #38 asks the artifact to report `READY`. The obvious implementation would have been a **constant, not a judgment**: measured before the work, a v2 artifact could exist *only* on complete success — every failure path produced no artifact at all — so `Literal["READY"]` would have been true in every artifact that could ever exist, unobservable by any test. That is the tautology shape this repository has recorded five times, the most recent one in this very contract two cycles earlier. Criteria 4 and 6 turned out to be one problem: a verdict needs something to say when it is negative, and criterion 4 already named it — a stable typed blocker.

Rejected alternative:
: A separate report layer computing readiness from the artifact — with no artifact there is nothing to compute from, and "the corpus endpoint was down" still surfaces as a bare traceback. Also rejected: keeping the schema success-only and declaring readiness implicit, which fails criterion 4 and makes the *absence* of evidence the carrier of meaning.

Trade-off:
: A field on a shared model that serves three schemas needed an explicit scoping rule, which is a clause that exists only to say where a field does *not* belong. Accepted because the repository already had the precedent — `capture_contract` is refused on the generic schema by name — and because the alternative was measured to be worse: a genuinely blocked v1 capture with `"readiness": "READY"` inserted **replayed clean** and reported `{"blocker_count": 1, "readiness": "READY"}`, the exact contradiction v2 refuses.

Known failure modes:
: **A coverage justification can expire without anyone being wrong.** D12's decision left six attempt-evidence clauses untested and justified it explicitly — *"the validator's call site is observed: detaching it turns three tests red."* This change added a **second** call site, where detaching turned **zero** red. Two of the re-opened clauses were the headline findings of the two prior reviews: the one-tenant-across-both-halves rule, and the privacy clause forbidding a failed request from claiming a response correlation id. Disabling the corpus-blocker tenant fold left the suite **fully green at 405 passed**.
: The reversal itself is a strict narrowing — `if blockers: raise` became `if readiness == "READY" and blockers: raise` — so a `READY` artifact is still validated by exactly the path D12 locked. The relaxation of `dataset_identity` on the negative side is compensated by three branches, each observed by a test, not dropped.

Validation evidence produced:
: `NOT_READY` is a **real discriminator**, established by capture rather than by reading the type: four distinct shapes, three negative, all surviving serialization and replay. The strongest is a partial failure — two genuine corpus observations coexisting with a typed blocker for the third role — **a state no success-only schema could represent**. Forcing the verdict positive in source turns **16** tests red, and the logical digest covers the verdict, so a flipped `READY` fails replay.
: The reversed rule's test was **renamed and re-scoped, not deleted**. Across two review rounds, 30 clauses were disabled one at a time; the three survivors that admitted concrete forgeries were closed by tests, with the source left unchanged because it was already correct.

Validation evidence still required:
: Everything above comes from `httpx.MockTransport`. **Nothing was captured**; no AX runtime was started. `braincrew_preflight_ready` stays `false` — the preflight can now *report* a verdict, which is not the same as the verdict ever having been `READY` against a live runtime.

Likely follow-ups:

- "You reversed a decision you locked the same day — doesn't that mean the first one was wrong?" — No, and the distinction matters. D12's refusal was **correct for a success-only schema**. What changed was the requirement, not the reasoning. The tell that it was handled as a reversal rather than a mistake is the test: renamed and re-scoped to the new rule, not deleted. Deleting a test whose rule has changed is how a repository loses a protection while its suite stays green.
- "Why does a `READY` artifact still say nothing about how much corpus AX returned?" — Because `corpus_id`, `corpus_digest`, `inventory_count` and `counts` are runtime-observed and no frozen expectation exists for them. **A `READY` artifact is compatible with an empty inventory**, and that is deliberate: pinning an observation as an expectation converts a measurement into a tautology. Two canary tests hold that line.
- "How would you catch this class of problem earlier next time?" — By treating a coverage justification that names a structural fact as **expiring when that fact changes**. The rule now written down: adding a call site to a validator whose coverage rests on "the call site is observed" inherits the obligation to observe the new one. Nobody was wrong here; a true statement quietly stopped applying.

### D14. Make the capture runnable before running it, and derive every identity an operator would otherwise type

Decision:
: A committed `capture-live-verification` command produces the create-only v2 artifact and exits `0` for `READY`, `3` for `NOT_READY` (artifact written), `2` for no artifact. Six inputs are **derived** rather than typed — `captured_at`, the Evaluation Plane SHA, `sut_commit_sha`, the frozen v3 dataset validation, and the **subject, attachment mapping and tenant** from the reviewed receipt. Locked in [the capture command decision](../decisions/2026-07-27-live-verification-capture-command.md); carried out by Issue #82.

Why:
: The two preceding merges built the artifact and gave it a verdict but left **no way to run it** — no `src/` caller, no CLI command, v2 absent from the replay dispatch. The artifact is meant to be cited as the evidence Issue #38 reached `READY`, and this project has already repaired a defect of exactly that shape: AX PR #53, where evidence was produced by **reimplementing** a runbook's generator instead of running it, and whose check passed only because it compared that script against itself. The authorized runtime start is expensive and manual, so it should happen once — after the entry point exists.

Rejected alternative:
: Collapsing `NOT_READY` into the CLI's universal exit `2`. All 23 other failure sites mean *we produced nothing*; `NOT_READY` means the artifact **was** written, is valid, and is exactly the evidence the negative verdict was built to produce. Merging them destroys the distinction between "we captured a refusal" and "we failed to capture" — what an operator needs most when the runtime is live. Also rejected: pinning a reviewed-tenant constant, which would be redundant with the receipt-digest pin that already fixes the receipt's bytes.

Trade-off:
: The tenant is bound at the **entry point**, not in the **artifact contract**. Three barriers close the operator hazard — the tenant is not a parameter at all, `--tenant-id` is gone with a **signature-level** test preventing its return, and altering the receipt's tenant changes bytes the pinned digest refuses. But the *subject* has a validator-level binding the tenant does not, so calling the inner capture directly with an arbitrary tenant still yields an artifact that validates and replays `READY`. Accepted because the ticket put validator changes out of scope, and recorded because **Issue #38's "binds the exact tenant identity" clause is satisfied by the capture path, not by the artifact in isolation.**

Known failure modes:
: Before the fix, two captures identical except for the tenant — one on a tenant nobody had ever reviewed — **both returned `READY` and replayed `READY` forever**. The realistic harm was a false negative on a once-only run: a mistyped-but-valid UUID yields 404s → `NOT_READY`, and the runtime plan forbids repairing mid-run, so **an operator typo becomes a preserved, create-only, replayable artifact that reads exactly like AX genuinely failing.**
: The command runs from a dirty worktree unless refused, stamping a `HEAD` that does not describe the code that ran — and replay validates the SHA's *format*, never its relationship to a tree. Every other artifact-producing path in the repository records `dirty_worktree`; this one discarded it. Now refused before capture.

Validation evidence produced:
: The unreviewed-tenant capture is **impossible to express**: passing a tenant is a `TypeError`, not a rejected value; a signature-level assertion fails on reintroduction even if no behaviour changes; and altering the receipt trips the pinned-digest gate. The dirty-worktree refusal fires before capture and turns a test red when removed. All three exit codes are reachable and mutation-proven. Gates: **416 passed**, mypy over 65 source files.

Validation evidence still required:
: **Nothing has been captured.** Every observation still comes from `httpx.MockTransport`; no AX runtime was started. `braincrew_preflight_ready` stays `false`. The authorized runtime start remains a separate decision, and AX #37 and AX #43 remain open blockers of Issue #38.

Likely follow-ups:

- "Why spend a whole cycle on a CLI wrapper?" — Because the runtime start is manual, authorized separately, and expensive, and an artifact captured by a typed snippet cannot be cited as the evidence that a gate passed. The cycle also **found two defects that a snippet would have carried into the live run**: an unbound tenant and an unrefused dirty worktree. Neither would have been visible once the artifact existed.
- "Your two panes disagreed about whether the suite passed — how do you know which was right?" — Both were. The test asserted on framework-rendered output that Typer splits into separately styled fragments, so it passed where Rich emitted no escapes and failed where it did. The instructive part is the **wrong inference**: colour was blamed, but `NO_COLOR=1` suppresses colour and **not bold**, so the coupling survives it. Measured across three environments. The fix strips CSI sequences unconditionally, which removes a dependency `NO_COLOR` never would have.
- "What stops the next test from being environment-coupled?" — The rule this produced: every pre-existing CLI test in this repository asserts on **application-emitted** strings from `typer.echo`, which are plain. This was the first to assert on **framework-generated** output. They are different classes, and only the second needs the strip.

### D15. Run the live capture once, hold it against pre-existing records, and let the reviewer own the verdict

Decision:
: Phase 1 of the runtime plan executed once on 2026-07-27 under stage-by-stage user authorization: read-only preconditions, `docker compose start` of the exact Stage 9 containers, one committed-command capture (`READY`, digest `sha256:fe38499e…e128e3`), Stage 12-order stop, and an independent review of the artifact itself — the fifth condition `braincrew_preflight_ready` requires. The flag moved to `true` only after that review returned `APPROVE`.

Why:
: The capturing pane must not accept its own capture as evidence — the same rule the team applies to worker reports. And the artifact's numbers cannot warrant themselves: replay proves integrity and contract validity, not the corpus figures. Their warrant is the cross-check against **Stage 11 records that predate the capture** — the six approval IDs match exactly, 166 matches the post-B total, and Employee's 130 is the `employee_visibility_invariant` re-observed at a byte-identical corpus digest.

Rejected alternative:
: Flipping the flag on capture success alone — it would make the capturing party the judge of its own evidence. Also rejected: recreating containers with `docker compose up`, which would have broken container-identity continuity with the recorded Stage 9 boundary; `start` reuses the same containers, and all three IDs matched byte-for-byte.

Trade-off:
: Holding the run until the exposed `OPENAI_API_KEY` was revoked cost minutes on an idle runtime; accepted because revocation, not replacement, closes an exposure, and the capture needed no OpenAI path. The one-shot `migrate` container starting as a compose dependency was a plan deviation, reported with evidence it applied nothing rather than absorbed into the success.

Known failure modes:
: A capture-side overclaim survived into the evidence set — "never observed before" for a fact Stage 11 had observed a day earlier — and was caught by the reviewer, not the author. Corrected in a supplementary file without rewriting the reviewed originals. An opened precondition (the key hold) was closed in conversation but initially recorded nowhere; an auditor could not close the loop until the disposition was written down.

Validation evidence produced:
: Reviewer-independent replay; exact set-match of the six `tenant-upload-v1` approval IDs against the receipt and Stage 11; the 36-record Employee gap reconciled to zero (12 tenant records + 24 pre-existing invisible demo records); sanitation checked twice by different methods (longest string 107 chars, no paths, no tokens, no raw text); create-only verified against the live artifact (duplicate capture exits 2).

Validation evidence still required:
: **No baseline or candidate has run and no quality claim exists.** Issue #15 remains separately authorized. The artifact does not verify its own corpus numbers, does not bind the tenant in-contract, and asserts rather than observes `sut_commit_sha` — each limit is recorded where the flag is defined.

Likely follow-ups:

- "You finally got `READY` — what does it actually license?" — Running Issue #15's pinned baseline/candidate experiment, and nothing else. It is a preflight verdict: the substrate, principal, dataset identity and probe evidence are in the reviewed state. It says nothing about answer quality, and the workflow stopped at `READY` by construction.
- "What would have happened if a role had been missing the seed version?" — A create-only `NOT_READY` artifact with one typed blocker, preserved and analyzed — and the work would have moved to AX. The negative verdict exists precisely so that outcome is evidence, not a traceback, and repairing inputs mid-run to convert it is the failure mode both governing tickets name.
- "Why believe the runtime you started is the code you reviewed?" — Three legs: the AX checkout was verified clean at the pinned SHA read-only before start; the containers were the byte-identical Stage 9 set, not recreations; and the schema version matched the pre-B archived dump. The artifact's `sut_commit_sha` alone would not carry this — that is written down as a limit, not discovered later.

### D16. When the thing you must attest is unobservable, carry the warrant — then pin that it reports what the check returned

Decision:
: The live experiment capture records a `SutStateWarrant` — the method (`read-only-git-check`), its subject (repository, checkout name, timestamp) and the values the check returned — instead of a bare `sut_dirty` boolean. `execution_mode` widened to `"fixture" | "live"` at the run layer **except on the parsing axis**, which stays fixture. Locked in [the live-experiment decision](../decisions/2026-07-27-live-experiment-capture-and-the-unobservable-warrant.md); carried out by Issue #85.

Why:
: The comparison gate refuses when either side's worktree is dirty, and Braincrew can check its own. **The SUT's dirtiness is not observable over HTTP** — the adapter sends only tenant, user and role headers. Emitting `sut_dirty=False` would manufacture a clean-state claim from nothing, the same failure D14 and D15 record for `sut_commit_sha`. A live manifest should not be able to exist without saying, in its own bytes, where its belief comes from.

Rejected alternative:
: Defaulting the flag to `false`; omitting the field, which would silently fail the gate's dirty refusal; and probing the server for its own identity, which is a real gap but an AX-side change rather than something to invent under time pressure.

Trade-off:
: The warrant attests to a **directory**, not to the server that answered — nothing binds `--sut-checkout` to `--base-url`. Accepted because the limit is pre-existing and already locked, and #85 improves on it by moving the check from a human runbook step into the command. Also accepted: `checkout_path` is a basename with the contract still permitting any string — the third instance of a binding living at the call site rather than in the contract, after the tenant and the SUT commit.

Known failure modes:
: **The honesty machinery was not earned.** Independent review ran eleven mutations; seven guards were load-bearing and the four survivors were, without exception, the ones carrying the honesty claim — including neutering the execution-claim validator entirely, which **survived all 433 tests**. The decisive pair: fabricating the warrant instead of calling git was *caught*; calling git, **discarding the result** and recording constants was *not*. A test pinned that the check is invoked; nothing pinned that the warrant reports what it returned.
: Three more, all closed: every live failure produced a traceback and exit 1 because `AxHttpFailure` subclasses `RuntimeError` and escaped the CLI's `except` tuple, with zero of seventeen new tests exercising a transport failure; the `logical_digest` could not be recomputed from the file it was stored in, because `captured_at` was the sole hand-serialized field; and widening `execution_mode` without widening `version` made a *fixture parser declaring live execution* the only newly-reachable parsing state — asserted by a test as intended.

Validation evidence produced:
: All four blocking findings closed and verified by the reviewer re-running its own eleven mutations plus end-to-end probes that do not reuse the implementer's tests; no previously-caught guard came unpinned. **442 passed**, mypy over 67 source files. The digest pre-image is now **derived** from the model dump rather than retyped, with a round-trip test that recomputes from the written file the way a reader holding only that file would.

Validation evidence still required:
: **No experiment ran and no quality claim exists.** Everything is `httpx.MockTransport`. Phase 1 of #15 remains a separate decision and is additionally blocked by #86.

Likely follow-ups:

- "A warrant is just a string you wrote — why is it better than a boolean?" — Because a boolean asserts a fact with no account of its origin, while a warrant asserts the fact *and* names the method and subject that produced it, so a reader can judge the claim rather than accept it. But that is only true once a test pins that the recorded values are the check's **output**. Until then it is worse than a boolean, because it reads as evidence. That gap existed here and review found it.
- "Why revert the parsing widening instead of binding version to execution_mode?" — Because the capture does not need it. Six of the thirty Verification cases are parsing and are deliberately fixture-carried, so the only state the widening enabled was a false one. Reverting removes the reachable falsehood; a validator would have preserved an axis nothing uses.
- "You found a blocker for the very ticket this unblocks — is that a planning failure?" — It is the planning working. #86 is a contradiction between the design specification and its own implementation, invisible until something tried to produce a real mixed-category run. The specification supplies both the contradiction and its resolution: it declares per-case metric *applicability* as a first-class field and fixes Recall@5's Verification denominator at nine, while one function demands that metric from all thirty cases.

### D17. Carry applicability instead of inferring it, and recognise conformance rather than call it a contract change

Decision:
: `ExperimentCaseResult` carries `applicability: RetrievalApplicability` — required, no default — and the confound check skips a metric only when **both** runs declare it inapplicable. An explicit `Literal`-keyed map resolves `authority_priority` → `authority_ordering`, a validator refuses an inapplicable metric that still carries a value, and applicability drift between runs raises its own mismatch error. Locked in [the conformance decision](../decisions/2026-07-27-confound-applicability-conformance.md); carried out by Issue #86.

Why:
: The confound check demanded three retrieval metrics from all 30 Verification case pairs, which the 21 non-retrieval cases structurally cannot supply, so a real comparison was `INVALID` by construction and Issue #15 could not produce a decision. **The evaluator's correct behaviour was what triggered it** — the evaluator computes a metric only when the case declares it applicable, and the comparison layer read that deliberate omission as missing. Two layers disagreed about what an absent metric means, and the layer that knew never told the layer that asked.

Rejected alternative:
: Inferring applicability from the absence of a metric — that would let a genuinely missing metric masquerade as a non-retrieval case, destroying the control while looking like a fix. Also rejected: fixing only the function, leaving the design-document sentence that produced the defect standing for the next implementer.

Trade-off:
: A required field was added while `schema_version` stayed `experiment-run-summary-v1`. My first justification was that no stored artifact breaks; **independent review rejected that reasoning** — it is a *migration* fact showing the change is cheap now, and it would not justify keeping a version name if the contract's meaning had changed. The correct reason is stronger: the specification's unchanged description of v1 **already** required comparison to fail closed on differing per-case applicability. The code was under-implementing a contract it already had, so this is conformance, not redefinition.

Known failure modes:
: The confound metric is named `authority_priority` while the applicability field is `authority_ordering`. A silent key miss would make that metric **permanently inapplicable** — a disabled control wearing the appearance of a fix. Both sides of the map are now `Literal`-typed so a rename fails type-checking rather than skipping quietly.
: A metric declared inapplicable could still carry a value, and the skip meant a difference in that value was never compared. Closed by a validator; neutering it turns three tests red.

Validation evidence produced:
: A realistic mixed pair — 6 parsing + 9 retrieval + 15 grounded, with the 21 non-retrieval cases declaring the retrieval metrics inapplicable — now produces **`FAIL`**: a gate outcome computed from evidence, with the confound control **still armed on all 9 retrieval cases**. Each of the three states was established by mutation, not reading. Gates: **449 passed**, mypy over 67 source files.

Validation evidence still required:
: That `FAIL` is arithmetic over synthetic fixture values, not a measurement. **No experiment has run and no quality claim exists.** Phase 1 of Issue #15 remains a separate decision.

Likely follow-ups:

- "You removed a check — how is the comparison not weaker?" — The check was never removed; it was scoped to the cases it can apply to, using a field the dataset already declares and the evaluator already honours. On the 9 retrieval cases it fires exactly as before, verified by mutation on both the missing-value branch and the differing-value branch. What changed is that 21 cases which cannot have a retrieval metric are no longer failed for not having one.
- "Why amend the specification rather than just the code?" — Because the specification is where the defect came from. One sentence declared the metrics mandatory per case; the code implemented that faithfully. Leaving it standing would recreate the defect the next time someone implemented from the spec. The same document already contained its own resolution — applicability as a first-class per-case field, and a Recall@5 Verification denominator of nine rather than thirty.
- "How did a contradiction survive in a frozen specification?" — Because nothing had ever tried to produce a real mixed-category run. The fixtures exercised retrieval-bearing cases only, so the contradiction was unreachable until a live capture forced the question. That is an argument for building the thing that produces the evidence early, which is what the two preceding tickets did.

### D18. Exclude what cannot be measured, record the exclusion, and distrust a test whose inputs are all identical

Decision:
: The run summary carries `cost_usd: Decimal | None` with a bidirectionally-validated, **derived** measurement status, and a latency whose definition is a `Literal` type. The owner decided the release comparison runs on **quality and latency**, with cost **excluded and the exclusion carried** in a `CostDecisionWarrant` the gates consult. Relative deltas are quantised to the contract's scale before the range check. Locked in [the operational-measurement decision](../decisions/2026-07-28-operational-measurement-and-the-cost-exclusion.md); carried out by Issue #89.

Why:
: `latency_ms` and `cost_usd` were required with `ge=0`, so the cheapest way to satisfy the validator was `0` — and those values feed `baseline_p95_latency_ms` and `baseline_mean_cost_usd` in a **published** artifact. A zero written to pass a validator becomes a measured-looking figure in recruiter-facing output. The repository had answered this shape three times already (`sut_dirty`, `sut_commit_sha`, the readiness verdict) and never by defaulting.

Rejected alternative:
: Writing `0` for cost — the only plausible source, `provider_metadata`, is free-form and unvalidated, so reading a schema out of it would assert a structure AX has not promised. Also rejected, by the owner: keeping `INVALID` on unmeasured cost, which converts *"we could not measure cost"* into *"the comparison is invalid"* and would have made a release decision unreachable until AX exposed usage data.

Trade-off:
: Quantisation rounds. Excluding cost means the release verdict rests on quality and latency alone, and the artifact must carry that fact so no reader infers cost was evaluated and passed. **One of gate 2's six primary metrics also cannot move**: `evidence_span_recovery` is computed from fixture parsing observations because `evidence_limit` cannot affect parsing, so its macro delta is identically `0` in every pair. The warrant is carried in the compared provenance, and the fact must be stated wherever the comparison is presented.

Known failure modes:
: **Resolving the cost blocker did not deliver a reachable verdict.** With *real* measured latency, every pair was still `INVALID`: `Decimal` division yields 28 **significant** digits, so a ratio below 1 in magnitude lands at exponent −29 while the Parquet contract requires −28 or greater. Reproduced at `0.164083 ms → 0.15525 ms`. The range check was correct; producing a value it must reject was the bug.
: **The acceptance test passed only because it injected a synthetic clock** giving baseline and candidate identical tick sequences, so all 24 latencies were exactly 1 ms and every delta was exactly `0`. A broken pipeline looked green.
: The mirror defect: per-case deltas were range-checked while **the aggregate the gates actually read was not**, and a published value at exponent −30 was observed. Per-case failed closed; the aggregate failed open.

Validation evidence produced:
: The same real-world ratio now quantises to exponent −28 and fits; the aggregate routes through the same quantise-then-check helper; the cost exclusion is asserted by test alongside a decision in `{PASS, FAIL}` with all gates non-`INVALID`; and `test_run_summary_refuses_zero_cost_under_an_unmeasured_warrant` pins the original trap. Across two review rounds, no existing assertion was relaxed anywhere in a 24-path diff, and the four golden comparison fixtures changed **0 of 15 cases** each.

Validation evidence still required:
: **No experiment has run and no quality claim exists.** Phase 1 of Issue #15 remains a separate decision, and whether the live answer path needs a generation provider is an AX-side fact to be settled by a single-case probe rather than guessed at.

Likely follow-ups:

- "You excluded cost from a release gate — isn't that lowering the bar?" — The bar is what the evidence can support. Cost was never measured; the alternative was to call an otherwise-valid quality comparison `INVALID` because one dimension was unavailable, which reports a measurement failure as an evaluation failure. The exclusion is carried in the artifact with its reason, the gates still enforce cost when it *is* measured, and a reader cannot conclude from the artifact that cost was evaluated and passed.
- "How did a broken pipeline pass its own acceptance test?" — The test injected identical clock ticks into both runs, so every latency delta was exactly zero and the range path was never exercised. **An injected value that is the same everywhere removes the variation the code exists to handle.** The rule now recorded: keep the deterministic test, but at least one test must carry values that genuinely differ across cases and runs.
- "Why is one of your six primary metrics always zero?" — Because parsing is fixture-carried and the experiment's only variable is evidence packaging, which cannot affect parsing. It is disclosed rather than quietly averaged in: the provenance names the fixture adapter version, and the limitation is written where the comparison is presented. Removing the metric would have been the other honest option; hiding the constant zero was not.

### D19. When the same defect returns five times, stop fixing instances and change the type

Decision:
: Five review rounds on Issue #89 each found one more instance of a single shape — **a producer emitting a `Decimal` its consumer contract refuses** (F1 per-case delta, F2 the aggregate the gates read, H8 `_score`, J1 the grounded value, and an open fifth at `run_summary.py:211-212, 241-242`). The decision is that the sequence ends with **one annotated type**, `ParquetDecimal` = `Annotated[Decimal, BeforeValidator(quantise), AfterValidator(assert_fits)]`, applied at all four contracts — and that it is **deliberately deferred to its own ticket** rather than bolted onto a ticket already at five review rounds. Recorded in [the operational-measurement decision](../decisions/2026-07-28-operational-measurement-and-the-cost-exclusion.md) §9.

Why:
: The root cause is nameable and is not carelessness. **The fit check lives on the consumer; the type at every producer boundary is a bare `Decimal`.** No type in the codebase means "a Decimal that fits the published scale", so correctness at five-and-counting sites depends on a person remembering to call `_quantize_parquet_decimal`, while mypy, the contracts and the linters stay silent when they do not. Every new producer is a fresh draw. Four consecutive rounds each closed an instance and none closed the class.

Rejected alternative:
: Quantising instance 5 now. It closes one site and leaves the generator running — and instance 5 is precisely the one that goes live the day the cost exclusion is lifted, because a per-token cost is exactly the kind of small non-terminating value that lands below 0.1 and therefore at exponent −29.

Trade-off:
: Deferring means shipping with a known-unreachable defect. It is unreachable for an *accidental* reason worth stating plainly: the only in-repo producer divides by `10⁶`, and division by a power of ten is exact, so the value carries at most 6 decimal places; and `cost_usd` is hardcoded `None`. The two contracts agree because of the divisor and because cost is absent — **nothing enforces the relationship and nothing pins it.**

Known failure modes:
: `OperationalMeasurement` accepts exponent −29 and −30 while `ExperimentCaseResult` refuses them; a refusal there aborts the whole 30-case build. Separately, `_quantize_parquet_decimal` fixes **scale, not magnitude** — it returns `1E+30` unchanged — so the new type must carry both halves, and it returns exactly `0` below the publication scale, making a sub-resolution delta indistinguishable from no change.

Validation evidence produced:
: The gap is reproduced, not inferred: `1/30` and `1/300` are accepted by the producing contract and rejected by the consuming one. **And the reason the check matters at all was measured rather than assumed** — DuckDB **silently truncates** an over-scale decimal (`exp −29 → −28`, `equal=False`) and raises only on over-magnitude, so `exponent >= -28` is defending against silent corruption of published evidence, with `replay_comparison_artifact` the only backstop that would notice.

Likely follow-ups:

- "Why ship with a known defect?" — Because it cannot be reached and the fix that *would* close it is a contract change across four models. Shipping the point fix would have closed the fifth instance and left the sixth to be found by the sixth review round. The defect is written down with its reachability condition, which is the difference between a deferred fix and an unknown one.
- "How do you know this is the last instance?" — I don't, and that is the argument for the type. The enumeration that found instance 5 listed producers rather than checking the two the repair touched; that method can be re-run, but a type makes re-running it unnecessary.

### D20. An approval is only as safe as its statement of what it did not check

Decision:
: Independent review approved Issue #89 while explicitly listing six CI gates it **could not execute** — `node_modules` was absent and the review was constrained offline — and named the specific risk: all four TypeScript/JSON paths in the diff are in Prettier's scope, so an unformatted file would fail CI unseen. The orchestrator then ran the full frontend job locally rather than treating the approval as complete.

Why:
: **`prettier --check` failed on two files this ticket had modified**, both clean at `HEAD`, so the ticket introduced them and CI would have rejected the merge. The failure was invisible to every gate the review *could* run: ruff, mypy and 497 pytest tests were all green, and so were eslint, tsc, vitest and the Next.js build.

Rejected alternative:
: Treating `APPROVE` as a merge signal. The verdict was correct on everything it covered; the merge risk lived entirely in the part it disclaimed.

Trade-off:
: Reproducing a full CI job locally costs a dependency install and several minutes. It is worth it exactly when the review was scoped away from part of the diff — not as a routine step.

Known failure modes:
: The orchestrator's own verification was wrong once here too: checking "did only whitespace change?" by stripping whitespace and comparing reported a **false** semantic difference, because the strip also removes spaces **inside string literals** (`replaceAll("_", " ")` collapses to `replaceAll("_","")`). **When a check fails, suspect the check before the subject.** The sound method — diff the file against its pre-format backup — showed two pure line-wraps, matching the preview exactly.

Validation evidence produced:
: All seven CI steps reproduced locally and green: ruff format/check, mypy (70 source files), pytest (497), `prettier --check` ("All matched files use Prettier code style!"), eslint, `tsc --noEmit`, vitest (6), `next build` (3/3 static pages), and the Playwright browser smoke test (2 passed).

Likely follow-ups:

- "Isn't a formatting failure trivial?" — The failure is trivial; **the mechanism that hid it is not.** A reviewer running every gate available to it, finding nothing, and approving is the normal case. What made this recoverable was that the review stated its blind spot in a form specific enough to act on — naming the gates, the tool, and the paths at risk. "I reviewed everything" would have produced a red CI run instead.

### D21. Treat a role as a closed external identity, and do not normalize execution evidence back into the expectation

Decision:
: Braincrew maps the dataset alias `hr_manager` to AX's provisioned reader role, `HRPractitioner`, and validates every mapped or pass-through value against the locally declared closed AX wire-role set. The live capture requires AX's corpus-identity responses to confirm exactly the canonical roles required by retrieval and grounded Verification cases. `GroundedObservation.executed_role` records the adapter request role and is compared directly with the canonical role expected from the case. Locked in [the canonical AX role decision](../decisions/2026-07-28-canonical-ax-role-and-executed-role-evidence.md); carried out by Issue #91 and corrected after Cycle 110 review.

Why:
: `HRManager` exists nowhere in the pinned AX backend or frontend, while AX's role literal is exactly `Executive | HRAdmin | HRPractitioner | Employee`. The controlled probe sent GA-003, GA-006 and GA-009 as each candidate: `HRPractitioner` and `HRAdmin` both reached the answer path and selected five evidence items; `HRManager` was rejected before retrieval. Visibility therefore could not choose between the two valid HR roles. Provisioning and semantics could: AX provisions `HRPractitioner` as the corpus identity, the receipt records it as the parse reader, and reserves `HRAdmin` for approval and write authority the evaluation never exercises.

Rejected alternative:
: Mapping to `HRAdmin` — same measured visibility, wrong authority semantics and no corpus-identity provisioning. Also rejected: renaming the dataset role, which changes the dataset digest and invalidates prior provenance; adding `HRManager` to AX, which reshapes the SUT around a harness mistake; deriving the closed set from a live AX response or database, which makes a pre-request guard depend on the runtime it is supposed to protect; and a separate literal `LEGACY_FIXTURE_ROLES` comparison, which preserves v1 persona discrimination by giving `executed_role` two different meanings across fixture and live paths.

Trade-off:
: Braincrew now carries a local copy of AX's four-role wire contract. A reviewed AX role change requires an explicit matching update here. Importing product internals would couple repository histories, while live derivation would make controlled tests and pre-request refusal impossible; visible maintenance is the smaller cost. The superseded v1 fixture dataset — not the frozen manifest v3 → grounded v2 live dataset — also has five historical reader-persona aliases, so they map explicitly to `HRPractitioner` and its synthetic observation fixture records that wire identity. This preserves the dataset digest and 43 tests' golden outcomes, but collapses six personas to one wire identity and no longer detects swaps among them.

Known failure modes:
: The old default `.get(role, role)` silently promoted any unknown dataset role to a supposed AX identity. Cycle 109 removed double normalization in the evaluator but left the live producer deriving `executed_role` from the same case; M4 restored that derivation and all 505 tests passed. The repair therefore records the adapter's actual request role and separately requires AX-reported corpus roles to match the complete dataset requirement. Unsupported roles deliberately abort the run instead of becoming case scores. This is the seventh recorded instance of the repository's recurring self-comparison or wrong-subject guard shape, plus a correction to the first locked explanation that mistakenly declared it fixed.

Validation evidence produced:
: The original mapping and closed-set mutations remain independently killed. The repair adds a controlled adapter divergence: GA-003 is actually requested as the wrong-but-valid `Employee` role, the captured request evidence records it, and evaluation emits `SYS-GROUNDED-ROLE-MISMATCH`. M4 — replacing that evidence with `canonical_ax_role(case.role)` — must now make the named acceptance test fail. A copied retrieval case using `hr_manager` proves canonicalization before both corpus and retrieval requests, and AX corpus responses are compared as a complete evidence map against the independently derived required-role map. The dataset remains byte-identical; no AX runtime or Docker service is used.

Validation evidence still required:
: **No experiment has run and no answer-quality claim exists.** This settles which role the harness sends, not whether the dataset author meant practitioner or approver: both roles see the same evidence on these cases, so that intent is not recoverable from the corpus. Nor does the v1 compatibility map recover what each historical persona author intended. All successful probes still hit the separate citation-contract blocker after retrieval.

Likely follow-ups:

- "Why not ask AX which roles it supports at runtime?" — The harness must reject an invalid identity before sending it. A live lookup also makes a controlled unit contract depend on the stopped runtime and risks verifying the request with a neighbouring response rather than an independent expectation.
- "How can you claim `HRPractitioner` is correct if `HRAdmin` sees the same evidence?" — I cannot recover the dataset author's noun choice from visibility. The decision is narrower: `HRPractitioner` is AX's provisioned reading identity and matches the receipt's reader role; `HRAdmin` adds approval/write semantics this evaluation does not exercise.
- "Didn't you already have a role-mismatch test?" — Yes, for an artificially different role. It did not distinguish the live-path tautology because test observations defaulted to the raw dataset alias and the evaluator normalized both operands. The new tests pin the boundary itself and each clause dies under an isolated mutation.
- "Does AX confirm the role on each answer response?" — No. The answer endpoint exposes no role. The per-case evidence is the adapter request actually constructed; AX independently confirms the complete required role set through the corpus-identity endpoint. The decision keeps those strengths separate.

### D22. Separate the commit that produced the receipt from the commit under test, and warrant their divergence

Decision:
: `REVIEWED_PROVISIONED_AX_SHA` names the AX commit that produced the byte-digest-pinned receipt, while `PINNED_AX_SHA` names the SUT commit under test. They may differ only when a code-pinned `ReceiptSutContinuityWarrant` binds the exact pair and carries the reviewed Git-diff result. The current warrant binds receipt commit `2bcaee3` to under-test commit `1ead133`, records the identical `backend/src` tree through `d793097`, names `backend/src/ax_engine/answers/service.py` as the sole subsequent source change, and records that the change does not affect receipt-bound provisioning state. Locked in [the separate AX commit meanings decision](../decisions/2026-07-30-separate-provisioned-and-under-test-ax-commits.md); implemented by Issue #94.

Why:
: One `PINNED_AX_SHA` previously meant both "the commit this experiment executes" and "the commit that produced this provisioning receipt." The first legitimate re-pin made those meanings diverge. Keeping equality would reject a still-valid reviewed receipt with a false "unreviewed commit" message; accepting both SHAs as a set would say what passes without carrying why it is safe. Preflight cannot observe Git history at check time, so D16's warrant rule applies.

Rejected alternative:
: A growing `{old, new}` allow-list, because it does not encode the reviewed relation; two renamed constants without an enforced relation, because the next re-pin would silently inherit the conclusion; receipt-coverage-derived validity, because the current parser ignores the digest fields Issue #94 says exist and the external receipt bytes were not inspected here; ancestry alone, because descendants can change provisioning; and regenerating the create-only receipt, because the existing receipt remains valid and regeneration would discard provenance.

Trade-off:
: Every future divergent re-pin must re-measure and replace a fixed warrant. That visible maintenance burden is intentional. The warrant is still an attestation rather than runtime proof, but it names the method, subjects, tree outputs and changed path, is bound to both exact constants, and is asserted as a complete payload in tests.

Known failure modes:
: A receipt from any commit other than the reviewed provisioned-at SHA fails before HTTP with a provisioning-specific error. A new under-test pin without a matching warrant fails with a continuity-specific error. Preflight artifacts and live capture independently refuse a SUT SHA that is not the under-test pin. The receipt byte-digest control remains untouched. The important honesty risk is a decorative method name whose returned values are not pinned; the acceptance test therefore compares the full warrant payload.

Validation evidence produced:
: The cycle 115 implementer reported that TDD first exposed the old conflation, but preserved no durable raw red output; that statement is process history, not independently reproducible evidence. The load-bearing evidence is mutation-based: six isolated cycle 115 mutations turned their named tests red and restored green, covering the receipt commit, exact warrant binding, preflight pin, live-capture pin, acceptance reason, and changed-path evidence. Cycle 117 added direct mutation coverage for all six model-validator clauses. Cycle 119 added loader-level acceptance coverage for the future same-reviewed-commit branch; isolated mutations separately killed its required `same-reviewed-commit` reason and its required lack of a continuity warrant, then restored green. Full gates passed: Ruff and mypy over 70 files, **521 pytest tests**, Prettier, ESLint, TypeScript, **7 Vitest tests**, static Next.js build, **2 Playwright tests**, and `git diff --check`. No Docker service, live endpoint, or experiment was used.

Validation evidence still required:
: Independent pane 3 review must challenge the provisioning-impact judgment and reproduce the mutation evidence. The warrant does not prove behavioural equivalence — `1ead133` is intentionally a different SUT and remains subject to evaluation — and it does not bind a checkout directory to the server that answers.

Likely follow-ups:

- "Isn't `provisioning_state_affected=False` just another assertion?" — Alone it would be. The warrant also carries the comparison method, exact commits, identical tree outputs and the sole changed path, and the test pins that complete result. That is the distinction D16 required.
- "Why not trust receipt digests instead?" — The current parser does not consume them, and the receipt lives outside this repository. A future schema can make digest coverage authoritative, but this ticket cannot derive safety from fields it neither parses nor verified.
- "Does the receipt now prove `1ead133` is behaviourally equivalent?" — No. It proves only that the already-reviewed provisioning state remains applicable. The answer-service observability change is exactly why `1ead133` is the new SUT under test.

### D23. Preserve a broken answer path as operational evidence, but never score it as answer quality

Decision:
: Every live grounded observation carries a typed `AnswerPathHealth` derived from AX's
  `provider_metadata.llm_call_succeeded` and `failure_reason`. A failed call is captured as
  `available=false` with the exact failure reason, then refused by grounded evaluation, coverage,
  and the completed-30-case run-summary gate. A successful
  `answer_mode="insufficient_evidence"` remains `available=true`, counts in the fixed denominator,
  and may become comparison input. Locked in [the operational measurement decision](../decisions/2026-07-28-operational-measurement-and-the-cost-exclusion.md#12-issue-92--preserve-answer-path-failure-evidence-but-refuse-a-quality-verdict);
  implemented by Issue #92.

Why:
: AX can return HTTP 200, a contract-valid `insufficient_evidence` answer, provider and model
  identity, yet report that the LLM call failed. Treating that fallback as a cautious answer turns a
  machinery outage into apparent quality evidence. Refusing every `insufficient_evidence` answer
  would make the opposite error: a successful abstention is the safety behavior the product is
  supposed to exhibit. The warrant carries the source fact so the two cases remain distinguishable.

Rejected alternative:
: Refusing the whole capture, because it discards the durable evidence needed to diagnose the
  outage; setting only `available=false`, because it would be unsafe without proving how unavailable
  cases affect denominators and comparison input; a 100%-failure guard, because the measured probe
  was already 92% broken; and a percentage threshold, because no measured or contractual basis
  justifies one. The locked 30-case Verification denominator supplies the defensible boundary: any
  machinery failure prevents a quality comparison.

Trade-off:
: Braincrew may persist a replayable capture that can never produce a quality verdict. That is a
  useful distinction, not a partial success: the capture proves what arrived, while absence of a run
  summary proves quality was not measured. The raw AX failure label is duplicated in
  `answer_path.failure_reason` and `error` so legacy availability semantics and the new typed warrant
  cannot diverge.

Known failure modes:
: `provider_metadata` is still free-form. Missing success, a failed call without a reason, or a
  successful call with a reason aborts capture. Braincrew does not prove AX's internal execution; it
  records the AX-reported result. `unsafe_provider_output` remains ambiguous between invalid
  citations and a forbidden-phrase safety rejection, so the artifact preserves that label without
  pretending to know which condition occurred. A future AX schema change must be reviewed rather
  than defaulted.

Validation evidence produced:
: Two controlled `httpx.MockTransport` acceptance paths pin the distinction. When every call reports
  failure, the artifact preserves `answer_mode="insufficient_evidence"` and `provider_error`, quality
  coverage is zero, the dataset run is `INVALID`, and `build_experiment_run_summary` refuses it.
  When every call succeeds and legitimately abstains, all grounded cases are `COMPLETED` and the
  30-case summary is produced. Contract tests require typed answer-path health on every live
  grounded batch. Isolated mutations separately kill the consumed success field, consumed failure
  reason, success/reason model relations, observation binding, live-batch requirement, successful
  abstention treatment, failure-reason mapping, unavailable-case invalidation, coverage exclusion,
  and summary barrier; each restore is digest-checked. The complete local suite is 531 pytest tests.

Validation evidence still required:
: Independent pane 3 review must reproduce the load-bearing mutations and challenge whether
  preserving a failed capture is the right operational boundary. No live experiment has run, no AX
  runtime was started, and no answer-quality claim follows from the stopped-runtime Phase 1 probe.

Likely follow-ups:

- "Why not score the fallback as a bad answer?" — Because the call did not produce an answer to
  assess. Scoring it conflates system availability with answer quality and contaminates the metric
  denominator.
- "Why is one failure enough to block the comparison?" — The release artifact requires exactly 30
  scored Verification cases. There is no evidence-backed threshold for treating missing quality
  evidence as representative, and the observed failure rate shows why a whole-run-only rule is
  inadequate.
- "How can a reader distinguish abstention from outage?" — Both may carry
  `answer_mode="insufficient_evidence"`. The successful abstention has
  `answer_path.llm_call_succeeded=true`, no failure reason, and `available=true`; the outage has
  `llm_call_succeeded=false`, an exact failure reason, and `available=false`.
- "Does `provider_error` prove the provider was unreachable?" — It proves only the AX-reported
  failure category. Braincrew preserves that evidence and refuses a quality conclusion; it does not
  infer an unobserved provider mechanism.

Cycle 123 correction:
: The binary description above is incomplete and is superseded here. The warrant is derived from
  all three AX facts: `llm_call_performed`, `llm_call_succeeded`, and `failure_reason`. It accepts
  performed success (`true`, `true`, `null`), performed failure (`true`, `false`, non-empty reason),
  and an unperformed call (`false`, `null`, non-empty reason). AX may emit the third state's success
  value as explicit `null` or omit it; Braincrew preserves either as `null` only when the performed
  flag is explicitly `false`. Missing performed state, performed-without-outcome,
  unperformed-with-Boolean-outcome, and inconsistent reason combinations abort capture. Strict
  Booleans prevent `1` and string values from crossing this boundary.

Cycle 123 validation addition:
: Cycle 122 independently measured partial failure at 1/15 and 5/15 calls; both runs were `INVALID`
  and summary publication was refused by the coverage floor, any-invalid-case propagation, and the
  required scored-case count. Exhaustive state enumeration found no counterexample to deriving
  availability solely from `llm_call_succeeded is true`: the deleted two-state availability
  validator was redundant, and the corrected model accepts exactly the three states above. Focused
  cycle 123 mutations separately proved the nullable outcome, both strict Boolean fields, each
  three-state relation, the failure-reason relations, and consumption of the explicit performed
  flag. No live AX runtime or experiment was used.

Cycle 124 correction:
: A complete AX call-site census supersedes cycle 123's three-state count. AX commit
  `1ead1331166538e417027a7064179f15c5cfbf61` emits four distinct shapes: performed success,
  performed failure with a reason, unperformed with a reason, and unperformed without a reason.
  The last shape comes from ordinary retrieval-level abstention at `service.py:71` and `:87`; no
  provider call was needed and no machinery failure was reported. It remains `available=true` with
  `error=null`, while either reason-bearing state remains unavailable.

Cycle 124 design defense:
: Availability is derived from the reported failure evidence:
  `answer_quality_available == (failure_reason is null)`. `answer_mode` remains preserved and
  scored, but it is not an availability input because both normal and failed paths can return
  `insufficient_evidence`; the reason is what distinguishes them in the enumerated source. The
  rejected alternative is treating every unperformed call as unavailable, which converts AX's
  safest ordinary abstentions into outages and violates Issue #92's measurable-abstention half.
  Adding answer-mode-specific availability rules was also rejected as duplicated AX control flow
  without a stronger source fact.

Cycle 124 validation addition:
: `tests/fixtures/ax_answer_path_emission_states_v1.json` records the exact AX commit, source digest,
  enumeration date, four direct metadata sites, five template-result sites, and four distinct
  shapes. Contract tests consume that census, and acceptance tests drive both ordinary no-call
  answer modes through capture, evaluation, and the fixed 30-case summary. Exhaustive model
  enumeration accepts exactly four states. Focused mutations independently kill omission of the
  fourth census shape, the narrowed failure-reason clause, both availability directions, and the
  live capture's use of the derived availability. No AX runtime or live experiment was used.

Cycle 125 census-binding defense:
: The census commit must equal `PINNED_AX_SHA`. A future re-pin fails
  `test_ax_answer_path_census_matches_commit_under_test` until the source is re-enumerated at the
  new SUT commit. Strict equality is appropriate because the census has no legitimate cross-commit
  use: a same-digest `service.py` does not prove the new commit was examined. A divergence warrant
  or growing allow-list was rejected because it would preserve stale evidence without Issue #94's
  genuine provisioning-versus-SUT split. The check is local and needs no AX checkout in CI.

### D24. Compare role-visible corpus digests across runs, not across visibility classes

Decision:
: A live run keeps one scalar `corpus_id`, requires it to be identical across every required role,
  and records `corpus_digests_by_role` for the exact AX-confirmed role set. Comparison requires the
  entire role-to-digest mapping and the scalar ID to match between baseline and candidate. Fixture
  summaries retain one explicitly unscoped `corpus_digest` and no role map. Locked in
  [the per-role corpus identity decision](../decisions/2026-07-31-corpus-identity-per-role-across-runs.md);
  implemented by Issue #101.

Why:
: AX measured one `corpus_id` for Executive, Employee and HRPractitioner, but Employee's visible
  digest excluded six tenant uploads. The former within-run equality check made every dataset run
  spanning those visibility classes impossible. The control exists to prevent baseline/candidate
  corpus drift, so equality belongs per role across runs.

Rejected alternative:
: Accepting any count of identities, because it deletes the control; binding only the shared ID and
  frozen contribution, because it demotes digest drift to evidence; restricting to one visibility
  class, because it changes the evaluated dataset; and hashing the role map back into one scalar,
  because it hides the split and silently changes `corpus_digest` semantics.

Trade-off:
: Every required role is now part of experiment compatibility, so a legitimate role-set change
  invalidates comparison and needs a new matched pair. The artifact grows slightly. In return, a
  reader can see the visibility split and no role can disappear through intersection comparison.

Known failure modes:
: A different within-run `corpus_id` or AX-confirmed role coverage aborts capture. A missing, extra
  or changed role digest between runs produces
  `SYS-COMPARISON-CORPUS_DIGESTS_BY_ROLE-MISMATCH`; an ID change produces
  `SYS-COMPARISON-CORPUS_ID-MISMATCH`; all gates become `INVALID`. Fixture/live digest shapes are
  mutually exclusive, preventing synthetic fixture evidence from masquerading as role-scoped AX
  observation.

Validation evidence produced:
: T-ACCEPT drives the measured Employee digest split through `httpx.MockTransport`, completes
  capture and asserts all three role digests. T-REFUSE changes Employee's digest only between two
  summaries and asserts the named compatibility violation plus `INVALID` gates. Mutations of the
  new W1 equality protection, B1, mode-scoped required provenance, and per-role map-shape clauses
  killed their named tests; B1 produced three red cases and the shape validator produced two. W2
  and B2 are pre-existing guards, re-confirmed. Every source and diff hash was restored before the
  next mutation. The pre-edit baseline was 552 tests. Final gates passed: Ruff and mypy over 71
  files, 562 pytest tests, Prettier, ESLint, TypeScript, 7 Vitest tests, the static Next.js build,
  2 Playwright tests, and `git diff --check`. Cycle 129's full independent pane 3 review and cycle
  131's scoped pane 3 re-review of the repair both returned `APPROVE` with no blocking defect.
  Cycle 134's pane 2 full-diff pre-commit audit found no blocking code/spec defect but returned
  `NOT SAFE TO COMMIT` on four durable-record and commit-message findings, including the stale
  review status here. The status entry itself was audited by pane 2, not pane 3, whose weekly
  budget was exhausted.

Validation evidence still required:
: Live AX runtime validation remains unperformed: no real experiment or answer request ran, no
  provider cost was measured, and no answer-quality claim follows.

Likely follow-ups:

- "Why is `corpus_id` not repeated in the role map?" — W1 already proves one ID across all roles;
  repeating it would duplicate a value, not add independent evidence.
- "Why not compare only roles present in both runs?" — That would let missing coverage vanish.
  Exact role-set equality is part of the confound control.
- "Why does a fixture retain a scalar?" — Its digest describes hand-authored observations with no
  role-executed evidence. A role key would invent provenance.
- "Does this bless Employee's narrower visibility?" — No. It records the measured SUT behaviour and
  compares like with like; the AX policy itself is out of scope.

### D25. Give the unrepeatable capture a replay path, and state its claim as a closed list

Decision:
: `replay_live_experiment_capture` re-opens the two observation files a capture manifest names and
  refuses unless six enumerated conditions hold: strict manifest validation, both files parse,
  declared content digests and case counts reproduce, case identities equal the declared live
  partition, adapter versions and the grounded SUT commit SHA agree with the manifest, and the
  manifest reproduces its own logical digest — with the recomputed value returned, not the stored
  one. `CaptureArtifactReference.file_name` is constrained at the contract to a bare filename. Locked
  in [the capture replay decision](../decisions/2026-08-01-live-capture-replay-and-its-enumerated-claim.md);
  implemented by Issue #106.

Why:
: The 2026-07-31 capture is the one artifact in the chain that cannot be regenerated, and it was the
  only one with no replay. Measured: `replay` refused it at exit 2, while the *evaluation* artifact
  built from it replayed at exit 0. The only committed code that cross-checks a manifest against its
  observation files sits behind a `COMPLETED`/30-scored gate in `run_summary.py` that this `INVALID`
  run cannot pass, so artifact integrity was coupled to answer quality. Its integrity rested on an
  uncommitted script that recomputed digests with the functions that produced them.

Rejected alternative:
: Narrowing the claim instead of adding the provenance comparisons, because the facts are recorded on
  both sides precisely so they can be compared and the check is six lines; enforcing the sibling
  constraint at the replay site rather than the contract, because that refuses the escape instead of
  making it unrepresentable; returning the stored logical digest, because equality holds only while
  the comparison above it does; and relaxing `run_summary.py`'s gate to reach the existing
  cross-check, because that gate protects comparison inputs and the correct fix is a separate
  integrity path.

Trade-off:
: The `file_name` constraint narrows `live-experiment-capture-v1`, so any future layout placing
  observation files in a subdirectory needs a contract change. Provenance comparison runs before the
  digest comparison, so a doubly-faulty artifact is described by the provenance fault — no false
  accept is possible, but the message can name the less fundamental problem. The constraint binds the
  file *name*, not the resolution *target*: a bare-named symlink still reads outside the directory.

Known failure modes:
: Every refusal **this function raises** is a typed `ValueError` surfacing as CLI exit 2 with no
  traceback, including a missing sibling file. That is not an absolute about the command: a
  pathologically nested manifest still raises `RecursionError` inside the CLI's own pre-dispatch
  `json.loads`, which exits 1 with a traceback — a pre-existing defect on every schema, not one this
  change introduced, and now a follow-up. The replay cannot detect a forgery in which the manifest and
  every observation file were fabricated together consistently — inherent to any scheme where one
  party controls the manifest. Three reciprocal facts are compared; a fourth (`executed_role` against
  the manifest's role keys) and two declared bounds (`retrieval_top_k`, `evidence_limit`) are not.
  `executed_role` is unreachable from the capture path; the two bounds could in principle be exceeded
  by an AX response and are deferred because the real capture's margins are wide.

Validation evidence produced:
: Independent review constructed six forged triples in which every stored digest is internally
  consistent; all six were accepted, and cycle 139 returned `REQUEST CHANGES`. pane 1 reproduced the
  blocking case against the **real** capture: a grounded file declaring the fixture adapter and a
  different SUT commit, under a manifest still declaring a live run, replayed at exit 0 — and once
  the fixture adapter is declared, the contract no longer requires answer-path health, so all fifteen
  `answer_path` records including the twelve `unsafe_provider_output` ones could be deleted and it
  still replayed at exit 0. After the repair, cycle 141 re-ran that harness unchanged: **the four
  forgeries the repair targets are refused**, each with a distinct message naming the right fact, and
  **two remain accepted** — one inconclusive when built, and a `run_id` disagreeing with the file
  names it points at, which is a recorded follow-up. Mutation verification ran
  one clause at a time with each restore proved by SHA-256; review checked all twenty labels against
  `a373e64` byte-identity and found every one correct. pane 1 measured, on real-capture copies
  outside the repository: the untouched triple replays to `sha256:775a8529…` at exit 0 with 9 and 15
  observations, seven isolated forgeries each refuse at exit 2 with their own message, and an eighth —
  `run_id` changed alone — is accepted, reproducing the deferred follow-up. Gates
  reproduced solo by pane 1: Ruff, mypy, **581 pytest tests**, `git diff --check`, `schemas/` clean.
  The six npm and Playwright gates were run by pane 2 and their irrelevance verified by pane 3
  against the gate input globs; pane 1 did not run them.

Validation evidence still required:
: No live AX runtime was started and none was needed. Nothing here bears on AX's answer path, the
  `unsafe_provider_output` conflation, or the twelve unscoreable grounded cases. No candidate run
  exists, so there is still no comparison, no gate decision and no answer-quality claim.

Likely follow-ups:

- "Why enumerate the claim instead of saying it verifies consistency?" — Because "mutually
  consistent" is unbounded: every review round found one more reciprocal fact, and each read as a
  defect against the stated claim. A closed list is true, checkable line by line, and finishable.
- "Doesn't this just recompute digests with the same code again?" — No. The manifest is a pointer;
  nothing re-opened the files it points at. The new check reads them and compares what both sides
  independently record.
- "Then what stops a fabricated capture?" — Nothing in this artifact, and that is stated rather than
  hidden. The defence against wholesale fabrication is the create-only capture path and the SUT state
  warrant, not the replay.
- "Why is the exit-0 case not enough evidence on its own?" — A stronger replay makes exit 0 carry
  more weight with a reader, so the gap between what it proves and what a reader infers widens. That
  is the argument for the enumerated claim, not against the check.

### D26. Refuse a drifted parsing observation instead of scoring it zero, and version the evaluator so published evidence still replays

Decision:
: `parsing-quality-v2` is the evaluator for every fresh evaluation. Under it, an available parsing
  observation that claims at least one evidence span and whose span `source_text_digest` values do not
  overlap the case's expected spans is refused with
  `PARSE_OBSERVATION_DOCUMENT_IDENTITY_MISMATCH`, and no metric is computed. `parsing-quality-v1` is
  reachable **only** from stored provenance on the two replay paths; no fresh route can select it.
  Locked in [the parsing drift decision](../decisions/2026-08-01-parsing-drift-refusal-and-evaluator-versioning.md);
  implemented by Issue #118.

Why:
: Parsing was the only one of three evaluator families with no drift detector — retrieval refuses on
  `RETRIEVAL_QUERY_MISMATCH`, grounded on `SYS-GROUNDED-ROLE-MISMATCH`, parsing refused nothing except
  a failure the SUT self-reports. So an observation made against a different document scored
  `0.0000` and was reported `SCORED`: a number that reads as a measurement and is not one. It is in a
  published artifact. The control that settles causation — same observations, same evaluator, correct
  dataset version — returns `1.0000` on all five metrics.

Rejected alternative:
: Accepting supersession and letting the published artifact stop replaying, because losing the
  verifiability of existing evidence to fix a defect is the wrong trade in this repository; keeping a
  dataset-version-keyed selector for fresh runs, because replay is served independently by the
  stored-version dispatch and the selector's only effect was to keep the defect producible — review
  demonstrated it by emitting a fresh `COMPLETED` artifact with 20 `SCORED` cases and aggregate
  `0.0000`; refusing whenever no expected span is recovered, because an observation that claims no
  spans has recovered nothing *and that is a measurement*; and authoring v2-consistent observations,
  which is out of scope and separately unreachable since the v3 Verification artifact cannot be
  rebuilt at `HEAD`.

Trade-off:
: A second evaluator version exists and must be dispatched from stored provenance forever. Fresh runs
  on older manifests now stamp v2 and therefore produce different digests than before — measured
  behaviourally identical on the legitimate path, all five metrics unchanged. And one overlapping
  document digest is sufficient to pass, so a document partially rewritten while retaining one
  expected span's source text is not detected.

Known failure modes:
: The guard detects total document-identity drift, not partial rewriting. It has never run against a
  real AX parse response, because no live parsing observation exists in this repository — the
  SUT-assigned span id shape it protects against is anticipated, not observed. **And the published
  2026-07-31 artifact still recomputes six `SCORED 0.0000` cases under its stored v1 dispatch.** That
  is what preserving replayability means: this work stops new false zeros, it does not remove the
  published one.

Validation evidence produced:
: Independent review returned `REQUEST CHANGES` on two findings neither implementation nor
  orchestration had seen — the guard refusing a legitimate zero-recovery observation of the *correct*
  document, and fresh runs on two of three committed manifests having no guard at all, demonstrated by
  producing a fresh false-zero artifact. A scoped re-review then found a second misdiagnosis: a correct
  document carrying a SUT-assigned span id, which is what the live path would produce
  (`live_preflight.py:789` copies AX's span id). That finding changed the predicate's basis from a
  `(span id, digest)` tuple to the document digest alone, measured to refuse all six published drift
  cases identically. Measured by pane 1 on the final tree: correct-digest-with-SUT-id **scores** with
  structure and metadata retained; zero recovery **scores**; a different document digest is
  **refused**; the v3 probe refuses every case with aggregate `None`; the legitimate v1 path is
  `COMPLETED` at `1.0000`; and both real artifacts still replay — `sha256:9435c9da…` and
  `sha256:775a8529…`, the latter being Issue #106's criterion, which must not regress and did not.
  Gates reproduced solo: Ruff, mypy, **589 pytest tests**, `git diff --check`, `schemas/` clean.

Validation evidence still required:
: No AX runtime was started and none was needed. Nothing here bears on the AX answer path or the
  twelve unscoreable grounded cases. No candidate run exists, so no comparison, no gate decision and
  no answer-quality claim.

Likely follow-ups:

- "Why version the evaluator instead of just fixing it?" — Because `replay_dataset_run_artifact`
  recomputes from the stored observation snapshot, so changing the evaluator changes what a stored
  artifact reproduces to. Without versioning, the only live artifact this project owns would stop
  replaying.
- "Doesn't a second version fragment the evaluator?" — It does, and the cost is accepted. The
  alternative was destroying the verifiability of published evidence.
- "Why is the published zero still there?" — Because it is what the run actually recomputes under the
  evaluator it was produced with. Rewriting it would be falsifying evidence to look better.
- "Why not detect partial rewriting too?" — Widening the predicate is what produced both
  misdiagnoses review had to remove. The bound is stated instead.

### D27. Stop tests writing to tracked files, and accept a production affordance only because its safety was proved as a conjunction

Decision:
: `_schema_directory()` consults a `BRAINCREW_SCHEMA_DIRECTORY` environment variable when non-empty —
  four lines of production source — so the sealing drift test can point its **subprocess** at a copy
  in `tmp_path` instead of mutating the tracked `schemas/` directory. Locked in
  [the schema directory override decision](../decisions/2026-08-01-schema-directory-override-and-tracked-file-containment.md);
  implemented by Issue #97.

Why:
: The drift test mutated tracked files and restored bytes captured at its start. A second run that
  captured its "original" inside the first run's drift window wrote the **drifted** bytes back as
  pristine — **both `finally` blocks completing normally** — leaving a self-consistent
  `(schema, digest)` pair that every recompute-and-compare check accepts. In a repository whose commit
  gate is `git status`, that could be committed beside real work; it nearly was. `seal()` runs the CLI
  in a subprocess, so an in-process `monkeypatch` could not reach it and a production affordance was
  unavoidable.

Rejected alternative:
: A CLI flag, because it puts a test-only need into `--help` permanently; a file lock, because tests
  would still write to tracked files and an interrupted writer remains a hazard; dropping the
  subprocess test for an in-process one, because the test exists to prove drift fails closed *through
  the real CLI*; and threading the directory as a parameter, which collapses back into flag-or-variable
  since the CLI is a separate process. No precedent existed — `git grep os.environ -- src/braincrew`
  returned nothing before this change, and that is recorded rather than glossed.

Trade-off:
: The repository gains its first test-facing environment affordance, and an operator whose tracked tree
  is drifted can point elsewhere and obtain a green seal. That is self-inflicted rather than
  adversarial, requires deliberate action, and is independently detected by the direct tracked-directory
  assertion and by `git status`. The sealing receipt records pinned constants, not directory-read
  digests, so it stays truthful either way.

Known failure modes:
: **The safety case is a conjunction, not a single property.** `_verify_vendored_schemas()` iterates
  over `EXPECTED_SCHEMA_DIGESTS` rather than over directory contents, so extra files in an override
  directory are never inspected — measured: a pristine copy plus an attacker-supplied extra schema is
  **accepted**. That hole is unreachable only because `_schema_directory()` has exactly one
  production call site and is used **only for verification**; the other two conjuncts are that the
  expectation is a code constant and that `corpus_authoring.py` resolves its own schemas path, out of
  the variable's reach. A future change that *loads* a schema
  from that directory re-opens it. The `except OSError` clause's mutation was not independently
  reproduced.

Validation evidence produced:
: Independent review constructed ten input shapes against the override, plus a no-override baseline — empty string, whitespace,
  empty directory, partial directory, a file rather than a directory, pristine copy, pristine plus an
  extra file, symlink, relative path, and a **self-consistent drift** — and found no input where the
  override changes the outcome rather than the location; the self-consistent drift, which is the
  laundering attack the affordance would have to permit to be dangerous, is refused. Removing the four
  lines turns three tests red with `assert 0 == 2`, proving the subprocess genuinely consumes the
  variable. And review injected a delay inside the drift window and **`SIGKILL`ed `pytest` there** —
  the exact shape the defect was found by, running no `finally` — with the tracked bytes unchanged.
  pane 1 reproduced the self-consistent-drift refusal, the extras acceptance, the single call site and
  the receipt's use of constants. Gates: Ruff, mypy, **592 pytest tests**, `git diff --check`,
  `schemas/` clean. Per-clause mutation: each digest comparison neutralised alone turned exactly one
  named test red.

Validation evidence still required:
: Nothing here touches AX, the answer path, or any evaluation result. It is repository hygiene with no
  bearing on any claim about the SUT.

Likely follow-ups:

- "Isn't a test-only environment variable a smell?" — Yes, and it is recorded as one. The alternative
  was tests that corrupt tracked files under concurrency, which is worse in a repository whose commit
  gate is `git status`.
- "Why is it safe if extra files are ignored?" — It is not safe because of that; it is safe because
  nothing ever loads a schema from that directory. Say the conjunction, not the shortcut.
- "Could an operator abuse it?" — Only against themselves, and two independent checks catch it.
- "What breaks the safety case?" — A second consumer of `_schema_directory()`. That is why the single
  call site is written down as a property to preserve rather than an incidental fact.

### D28. Record an unreported discard predicate as unknown rather than false, and re-argue the continuity warrant instead of transplanting its conclusion

Decision:
: The under-test AX pin moves to `3bb27f8` — the commit that split a citation-contract violation from
  an unsafe-provider-output block — and `AnswerPathHealth` gains both predicates as
  `StrictBool | None` with `Field(default=None, exclude_if=lambda value: value is None)`. The reviewed
  provisioning continuity warrant is **re-derived** from the new AX diff rather than bumped. Locked in
  [the discard-predicate and continuity-warrant decision](../decisions/2026-08-01-unreported-discard-predicate-and-re-argued-continuity-warrant.md);
  implemented by Issues #121 and #122.

Why:
: Upstream, one `failure_reason` label had covered two distinct causes. Braincrew is the measuring
  instrument, so when its subject grows a distinction the instrument must record it or silently
  collapse the two causes on every future run. But the **already published** 2026-07-31 capture
  contains **12 of 15** grounded observations discarded under that single label by pre-split AX, and
  no amount of re-reading can say which cause fired. `None` therefore has to mean *unknown* — a third
  state, not a synonym for `False`.

Rejected alternative:
: Defaulting both predicates to `False`, which would make every rebuild of the published capture
  assert that **not one** of those 12 discards was a citation-contract violation — a claim with no
  evidence behind it, manufactured by a default value, in a repository whose whole proposition is that
  its claims are measured. Also rejected: making the fields required, which stops the published record
  loading at all; `default=None` **without** `exclude_if`, which is right in Python and wrong on the
  wire because `model_dump` would emit `null` keys and change the bytes of published evidence; bumping
  `under_test_sha` while keeping the old `changed_paths`; changing the historical `failure_reason`
  label, which AX deliberately preserved; and re-capturing immediately, which costs a provider run and
  answers a different question — a *new* run's predicates, not the published run's.

Trade-off:
: The contract now carries two fields that are absent from most records, so a consumer must handle
  three states rather than two. That asymmetry is the point: it is the honest shape of the evidence.
  The cost is that `None` is easy to coerce to `False` by accident in any future consumer, which is why
  it is written into the upstream commit's `Directive:` and into this card.

Known failure modes:
: **A future `.get(key, False)` re-creates the defect in one character.** The mapper reads
  `provider_metadata.get("citation_contract_violation")` with no default precisely so an unreported
  predicate stays `None`; supplying a default silently converts *unknown* into *measured false*.
  Equally, removing `exclude_if` does not fail loudly — it changes the serialized bytes of records
  already published, so the failure surfaces as a replay-digest mismatch far from its cause. A
  continuity warrant carried forward instead of re-argued fails the same way: it reads as true, passes
  every existing check, and under-reports the diff it warrants. That last one nearly happened here —
  `changed_paths` grew from one path to two because `answers/contracts.py` is new to this diff.
  Separately, five test files that had each carried their own SHA literal now import the pin, which
  **deletes five independent witnesses**: measured by moving the pin constant and the packaged YAML
  together, 87 tests fail and not one of the five is among them. Four witnesses remain — three files
  keeping literals plus the census `commit_sha` — and converting any of those four to a derived value
  would look like removing a duplicate while removing the last check.

Validation evidence produced:
: All **15/15** stored `AnswerPathHealth` objects round-trip through the new model with **zero byte
  differences**, each dumping exactly the three legacy keys and acquiring neither new one;
  `canonical_digest` over the rebuilt set is `sha256:e3ff0964…`. The published capture manifest still
  replays to `sha256:775a8529…` and the published evaluation artifact to `sha256:9435c9da…`. All three
  warrant tree SHAs were re-derived from the AX checkout rather than from the previous warrant, and the
  production diff is exactly two paths — the commit's test file is excluded because `changed_paths` is
  a claim about production source. `None` and `False` are distinguishable at every layer; `StrictBool`
  rejects `1`; `extra="forbid"` still raises. Mutating `PINNED_AX_SHA` alone turns **164 tests red**,
  including `ValueError: configured AX SHA does not match ax-http-v1 contract` — a guard in production
  source, not merely in the suite — and removing the citation mapper line alone turns the named capture
  test red, which also proves that test is not looping over an empty collection. Both restorations were
  proven byte-identical by SHA-256. Gates: ruff, mypy clean, **598 passed**.

Validation evidence still required:
: **The 12 unknown discards stay unknown.** This change stops new measurements from collapsing the two
  causes; it cannot recover which cause fired in a run taken before the split existed. Only a
  diagnostic re-capture against `3bb27f8` can — a live provider run, with cost, gated on explicit
  owner authorization.

Likely follow-up questions:
: *"Why not just re-run and fill in the blanks?"* Because the published artifact is create-only; a new
  run produces a new artifact with its own predicates and leaves the old record's unknowns intact by
  construction. *"Isn't an optional field that is usually absent a smell?"* It would be if the absence
  were incidental. Here absence carries information — it marks a record as predating the distinction —
  and collapsing it into `False` is precisely the error the upstream ticket removed. *"How do you know
  the byte-identity claim holds for records you did not test?"* It was not sampled: all 15 objects in
  the published capture were rebuilt and compared.

### D29. Let a status header make a current claim only when a separate record can refute it

Decision:
: `Last updated` in the delivery-status header is a current-state claim. It must equal the maximum of every dated
  `### YYYY-MM-DD` heading between `## Transition history` and the following
  `## Transition record format`, and every `###` heading in that bounded region must start with such
  a date. The acceptance test compares that maximum with the
  independently hand-written header, without assuming newest-first file order. Locked in
  [the status-currency decision](../decisions/2026-08-02-status-currency-derived-from-transition-history.md);
  implemented by Issue #103.

Why:
: The header is the first currency claim a reader sees, while the transition entries are the file's
  append-only record. Keeping both is useful only if they cannot quietly diverge. A literal test pin
  had turned a real update into a red suite and then frozen the lie for a week; deriving the check
  converts the matching edit into an enforceable obligation without rewriting the historical record.
  Cycle 178 found that using only the top heading still let a later out-of-order dated entry pass, so
  the comparison now takes the maximum of the whole visible date set.

Rejected alternative:
: Re-pinning a new literal date, because the next append would recreate the same silent-staleness
  failure; calling the field a snapshot or removing it, because the history shows it has been a
  current-state field and those alternatives remove reader-visible orientation rather than maintain
  its truth; and using Git commit time, because the document exposes entry dates rather than commit
  metadata and the two can legitimately differ.

Trade-off:
: A contributor still makes two manual edits when appending a transition record. The system does not
  generate the header; it makes disagreement fail before publication. That is preferable to a hidden
  formatter that could make a status claim look current without an explicitly reviewed history entry.
  The test now accepts ordering as presentation rather than a correctness premise, but it requires
  every Transition `###` heading to be date-shaped.

Known failure modes:
: Forgetting the header after adding a later dated entry anywhere in the history, changing the header
  without changing the maximum entry date, or adding an unparseable `###` entry each makes the named
  acceptance test red. The guard would become a tautology if it derived both sides from one value, so
  it must keep the document header and transition-date set as separate inputs. A date range heading is
  a surviving loud limitation: `### 2026-08-03 – 2026-08-04` is captured as `2026-08-03`, so a header
  of `2026-08-04` fails even when a reader could call it true. No range headings exist today; use one
  heading date and put any multi-day span in the body until a range grammar is deliberately added.

Validation evidence produced:
: The Cycle 176 first-heading check passed with a later `2026-08-05` entry inserted below the top
  `2026-08-02` entry; the Cycle 178 maximum-date check made that same mutation red. It also rejected a
  stale header, an unparseable Transition heading, and an altered Issue #47 checkpoint token. The
  sequential final gates passed: formatting, lint, typing, and **598** tests. The per-mutation restore
  hashes and command evidence are recorded in the Cycle 178 report; no Git lifecycle action occurred.

Likely follow-up questions:
: *"Why not show the commit date instead?"* A transition can record work done on one day and land on
  another; this header orients readers to the latest visible record, which they can verify from the
  file itself. *"Does the test update the date automatically?"* No. It fails closed when two authored
  statements disagree, preserving review of both the record and its currency claim.

### D30. Make the clean container prove committed fixture behavior, not inaccessible live evidence

Decision:
: The Issue #16 image starts from a pinned Python 3.12 base, installs a pinned `uv`, and runs `uv sync
  --frozen --all-groups` before the Python gates and Issue #6 fixture benchmark. It excludes host Git
  metadata, local environment files, Python caches and bytecode, and dashboard `.next`/`out` build
  outputs at every depth, from its build context. Its `ax-live-verification-evidence/` pattern is
  defensive only — at the time of this decision the owner-held live artifacts sat outside the
  repository and were never in the context to exclude; four of them were published under D31
  later the same day. Its Git snapshot is
  constructed inside the image only because the fixture acceptance test verifies its own Git provenance.
  The container runs with no host mount and may be run with `--network none`.

Why:
: A clean fixture check catches undeclared local Python state without pretending it can validate bytes
  that are deliberately outside the repository. The fixture test needs a repository identity, but copying
  the developer's `.git` directory would turn host metadata into hidden input. An image-local snapshot
  preserves the test's self-consistency check while making its identity explicitly non-publishable.

Rejected alternative:
: **Superseded in part 2026-08-02 by D31 — the second rejection below, copying the artifacts
  into the repository, was reversed the same day. Its stated ground was that publication is an
  owner decision and that a separate review was needed; the owner decided and the review
  returned PUBLISHABLE with no redaction, discharging both. The bind-mount and
  byte-identical rejections still stand. The text below is left unchanged.**
  Bind-mount the checkout or published-live-artifact directory, because a host mount defeats clean
  environment evidence and would make unpublished owner-held evidence part of routine automation; copy
  the artifacts into the repository, because publication is an owner decision and the artifacts may
  contain evidence that needs a separate review; and call a fresh live rerun byte-identical, because a
  live SUT/provider observation is new evidence rather than replay of fixed bytes.

Trade-off:
: **Superseded 2026-08-02 by D31 — the owner authorised publication the same day, the four reviewed
  artifacts now live in `evidence/`, and the image replays them. The sentences below described the
  state before that authorisation and are left unchanged.** The image validates only the committed
  fixture path and deliberately cannot discharge Issue #16's stored-live-artifact criterion. It
  creates a synthetic Git commit inside the image, so the ephemeral
  fixture artifact identifies that snapshot rather than a publication candidate. This is sufficient for
  test behavior, not for a release claim.

Known failure modes:
: Removing the image-local Git snapshot makes the fixture acceptance test fail before it can compare
  provenance; allowing `.git`, `.env`, nested Python caches or bytecode, dashboard build output, or
  live-artifact paths into the context would reintroduce hidden or sensitive host input; and a CI
  definition can drift or fail until it runs on a pull request. Docker's default Linux policy does not
  permit Bubblewrap's user namespace, so the three authoring-boundary tests skip when `bwrap` is absent
  and fail when it is installed. The image therefore does not request privileged or security-relaxed
  execution merely to run them. Gitleaks is an automated secret/credential scan, not a substitute for the
  existing publishability contracts or an assertion that unpublished live evidence is safe to publish.

Validation evidence produced:
: On 2026-08-02, `docker build --no-cache --tag braincrew-evaluation-fixture:cycle180-final .` and
  `docker run --rm --network none braincrew-evaluation-fixture:cycle180-final` completed the fixture
  gates: Ruff format/check, mypy, `595 passed, 3 skipped`, and the ten-test Issue #6 benchmark. Removing
  the image-local `.git` after its synthetic commit made `30` provenance-related tests fail, then
  restoring `Dockerfile` reproduced SHA-256
  `77c883f08179db35ced106dfaefa71b1b146830312e3f8def979eebc8332f856`. Bubblewrap's direct
  user-namespace probe was refused by Docker's default kernel policy, so no privilege or security
  relaxation was requested. The GitHub Actions workflow remains unverified until a pull request executes
  it.

Likely follow-up questions:
: *"Why not make the container replay the live artifact?"* It cannot honestly do so while the artifact
  is intentionally external; treating its absence as an invitation to copy it would change an owner
  decision. *"What can be byte-identical?"* Replay of an already stored artifact's logical values and
  gate decision; a fresh provider/SUT run is a new measurement and must be reported that way.

### D31. Publish reviewed stored-live evidence as a fixed replay boundary

Decision:
: The owner authorized four 2026-07-31 stored-live evidence files, with no redaction, for placement
  under `evidence/`. The capture manifest and its grounded and retrieval observations are siblings
  because the manifest pins bare file names and content digests; the evaluation artifact has its own
  directory. The test invokes the existing `replay` CLI and pins the capture logical digest
  `sha256:775a85295fb5db2f9cfb6e1aa5504206ea3b629a032452932ca685a7ab1a5049` and evaluation logical
  digest `sha256:9435c9daaa21e4e3129dad997a9dff79717452a2c1f112acfd7a95ba3e80f6fb` as literals.

Why:
: Issue #16 needs a clean environment to replay published evidence without hidden host input. Fixed
  bytes permit a reviewer to recompute the stored 15-grounded/9-retrieval capture and `INVALID`
  evaluation result. The same fixed boundary deliberately preserves the distinction between replay and
  a fresh AX/provider observation.

Rejected alternative:
: Reformatting the JSON, because a changed byte breaks the evidence's stored identity; separating the
  two capture observations, because the manifest deliberately requires sibling bare-file references;
  copying any of the other 33 source files, because their publication status was not authorized; and
  treating a replay as a new live rerun, because it cannot measure mutable external behavior.

Trade-off:
: Publication permanently fixes the historical evaluation digest, the 242 recorded corpus digests, AX
  commit `1ead133`, and dataset `3.0.0`. A later corpus change will no longer match the published
  artifact. That is the intended reproducibility property, not a silent limitation.

Known failure modes:
: A single changed expected digest digit makes the acceptance test fail; a single changed byte in a
  copied evaluation artifact makes `replay` refuse the stored logical digest. A fresh live run can still
  differ, and Issue #15 remains open, so this card must never upgrade stored replay into a current
  live-quality or release claim. The owner-approved publishability review applies only to the four
  candidates; it does not make the other source-directory files safe to publish.

Validation evidence produced:
: SHA-256 compared every destination file directly to its read-only source. The new test was RED while
  the files were absent, then GREEN with the literal digests. Host gates reported Ruff and mypy clean,
  `599 passed`, and the eleven-test Issue #6 file passed; the no-network image reported `596 passed,
  3 skipped`, then the same eleven-test file passed. No Docker Compose call, AX container contact, or
  live SUT/provider invocation occurred.

Likely follow-up questions:
: *"Does this prove the live result is still true?"* No. It proves the published stored evidence
  replays faithfully. *"Why keep an `INVALID` artifact?"* Its invalid state is part of the historical
  evidence and prevents a reader from mistaking it for a successful live quality result. *"Why not
  publish the rest later?"* Each candidate needs its own review and explicit owner authorization.

### D32. Bind a live parser response to the frozen document before using it as evaluation input

Decision:
: Issue #131 adds a dedicated six-case `live-parsing-capture-v1` path. It sends only AX's read-only
  parse-observation request, converts response fields to `parsing-observation-v1`, and labels the
  batch `ax-sut-http-v1`. The manifest carries AX's parser name/version, a SUT state warrant, the
  actual Evaluation Plane dirty flag, dataset-v3 identity, and the document-to-attachment mapping.
  Every response must reproduce the frozen document's complete text, digest, and span bounds before
  it can be written. The existing 24-case live capture and the fixture-only parsing-run provenance
  stay unchanged.

Why:
: The six v3 parsing cases were fixture-carried because `af18c5e` correctly rejected a false state in
  which a fixture parser was merely relabelled live. AX now exposes an observation endpoint, so the
  correct repair is not a wider old provenance literal but a new artifact with an independently checked
  document identity. The converter never reads `case.expected`: answer-key data is an evaluator input,
  not evidence of what AX parsed.

Rejected alternative:
: Reuse or relabel the old fixture because its source digests identify different documents; widen
  `ParsingAdapterProvenance.execution_mode` because that recreates the fixture-as-live lie rejected in
  `af18c5e`; derive headings, metadata, table, list, or spans from the expected answer because that
  lets an exam grade itself; query AX for a mapping and accept its answer as proof because the lookup
  and asserted fact share the same unverified source; or create the missing v3 attachments now because
  that mutates the runtime data outside this cycle's authority.

Trade-off:
: The path needs a separately supplied, versioned v3 document-to-attachment mapping. That is an
  operational precondition, but it is not trusted by itself: a wrong mapping fails the returned
  content/digest check. Capturing nothing is preferable to recording six observations against the
  wrong documents. The observed AX instance currently has only the older attachment set, so this
  ticket has no new live bundle or re-evaluation result yet.

Known failure modes:
: Mismatched attachment IDs, document text/digests, span digest/bounds/text, truncated text, missing
  parser identity, and conflicting parser identities all refuse before writes. A clean SUT warrant
  cannot prove that its checkout is the server answering the base URL; that observability limit from
  D16 remains explicit. A successful future capture supplies parser observations, not a release or
  general live-quality claim.

Validation evidence produced:
: RED first: importing the absent converter failed. GREEN: the acceptance test poisons all six expected
  headings and metadata and confirms the batch records only mocked AX output, exactly six read-only
  parse requests, and `ax-sut-http-v1`. A separate test returns another frozen document and verifies
  the converter refuses it. CLI tests pin receipt-derived principal identity, a versioned mapping input,
  truthful dirty-state recording, and no caller-supplied tenant option. Full repository gates and the
  live re-evaluation remain reported in the cycle evidence; the latter is blocked until v3 attachments
  exist.

Likely follow-up questions:
: *"Why not use the existing fixture?"* It is valid evidence about another document, not this one; the
  v2 guard correctly refuses the substitution. *"Why is a supplied mapping safe?"* It is only a route
  to a GET endpoint; AX must then return the exact frozen text and digest or the capture writes nothing.
  *"Did this make parsing pass?"* No. It makes the measurement path honest; current runtime inputs
  still prevent the measurement.

### D33. Re-pin the SUT only after reading every changed production path again

Decision:
: The under-test AX commit moves from `3bb27f8` to `5b0f5f2`, together with the packaged
  `ax-http-v1.yaml` identity. The existing receipt remains at `2bcaee3`, with `d7930978` as the last
  provisioning-equivalent commit, so `REVIEWED_PROVISIONING_CONTINUITY_WARRANT` must name all three
  source paths in the newly reviewed range: `answers/contracts.py`, `answers/service.py`, and
  `attachments/jobs.py`. It is not a copied two-path conclusion.

Why:
: A pin is an assertion about the subject under test (SUT, the system being measured), while the receipt
  proves an older provisioning event. The warrant is the bridge between them, and a bridge is credible
  only after its entire new span is inspected. The new attachment-pipeline diff adds
  `_headings_from_text()` and records `"headings"` in `AttachmentExtraction.page_or_section_map` only
  inside `if extraction is None:`. It does not update an existing extraction, backfill old rows, or
  alter approvals, materialization, corpus state, migrations, seeds, principals, or receipt production.
  Therefore `provisioning_state_affected=False` is warranted for the already provisioned state, while
  remaining explicitly limited: a future fresh extraction at `5b0f5f2` does record a new headings fact.

Rejected alternative:
: Change only `under_test_sha`, because it would hide `attachments/jobs.py` while still passing the
  current structural validator; infer headings at read time or backfill existing rows, because AX's own
  decision keeps parse observations as stored facts; and convert remaining hardcoded test literals into
  imports, because that removes independent witnesses rather than eliminating a duplicate.

Trade-off:
: The warrant remains a human-reviewed statement about a bounded source diff rather than a runtime proof
  that a server or future extraction is equivalent to the receipt-backed state. The exact range and the
  `jobs.py` limitation are recorded so the next re-pin must inspect the next diff again.

Known failure modes:
: Moving `PINNED_AX_SHA` without the YAML contract raises the production binding error. Moving the pin
  while retaining the old two-path warrant under-reports the reviewed diff and may still pass existing
  checks. The answer-path census source hash alone cannot prove that the new commit was enumerated, so
  its SHA-256 and line-level call-site census are rechecked by hand whenever the pin changes.

Validation evidence produced:
: Ruff format checked 72 files, Ruff lint passed, mypy found no issue in 72 source files, the full suite
  reported `608 passed`, and the fixture gate reported `11 passed`. Moving only the source pin made the
  full suite `171 failed, 437 passed`, and a direct `AxHttpAdapter` construction raised the production
  message `configured AX SHA does not match ax-http-v1 contract`; restoring
  `live_preflight.py` reproduced SHA-256
  `d0af2fd177b71990a837c23bd7c334276bcf33496176f10cf02fbcd6478fb4e5`. Reverting only the warrant
  to its prior two paths made the exact receipt-binding assertion fail (`1 failed, 607 passed`), then
  reproduced that same SHA-256 after restoration. No live AX, provider, attachment, container, or Git
  lifecycle operation is part of this decision.

Likely follow-up questions:
: *"Does adding headings affect provisioning?"* It affects future fresh extraction output, not the
  receipt-backed state: the changed code creates a map only when no extraction exists and does not
  backfill old rows. *"Why retain literal test pins?"* They are deliberately independent alarms; a test
  derived from the pin cannot detect a pin that moved incorrectly.

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
