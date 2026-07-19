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
