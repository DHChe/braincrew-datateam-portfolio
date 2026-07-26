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
- "Why did the SUT commit not get re-pinned at the same time?" — Because it is a different kind of assertion and folding it in would have deleted a real check. `receipt.repository.commit_sha` is an observed fact; `PINNED_AX_SHA` is a Braincrew-side review decision. The applied commit `2bcaee34…` has been reviewed as the **provisioning** execution commit but never as the SUT commit **for evaluation**, and that review is a separate, still-open decision.

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
