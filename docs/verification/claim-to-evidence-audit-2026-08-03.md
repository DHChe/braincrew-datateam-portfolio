# Claim-to-evidence audit — 2026-08-03

**Scope:** Cycle 203, pane 2. This audit walks README.md top to bottom as it stood at develop a37ac04a451bf1e0139a1ffc555b1fe9bf6e9729. It records evidence rather than changing README prose.

**Indexing note (Cycle 206):** The `Where it appears` line references and original
claim wording below remain indexed to the pre-Cycle-204 README. The Cycle 204
resolution and Cycle 206 delta appendices record later README repairs; no full
re-walk is claimed.

## Method and classification

A material claim is a factual result, capability, provenance assertion, boundary, or release/status assertion a reader could rely on. Closely coupled clauses share one row only when one evidence set establishes the complete proposition. Repeated claims receive their own row when their README location gives them a distinct reader-facing role.

Yes means the primary evidence or executable/source contract is in this repository. No — owner-held means the primary measurement is explicitly outside the repository, even when a decision record here accurately describes it. No — public GitHub identifies a separately verifiable public upstream fact. No — unsupported/stale identifies an assertion that is not currently traceable to sufficient evidence or is contradicted by the current checkout. Categories are mutually exclusive and count the strongest primary evidence for each claim.

| Classification | Count |
| --- | ---: |
| Claims audited | 59 |
| Primary evidence in this repository | 35 |
| Primary evidence owner-held outside this repository | 15 |
| Primary evidence in public GitHub | 3 |
| Unsupported or stale | 6 |

## README claim inventory

| Claim | Where it appears | Evidence | In-repository? |
| --- | --- | --- | --- |
| C01. This is an evidence-first evaluation plane for a Korean HR/labor RAG system. | README.md:1-3 | docs/decisions/2026-07-18-evaluation-scope-and-skill-flow-lock.md; frozen synthetic Korean case bundles under datasets/. | Yes |
| C02. AX_portfolio is a separate SUT connected by a versioned HTTP contract. | README.md:5-7 | src/braincrew/ax-http-v1.yaml; docs/decisions/2026-07-18-evaluation-scope-and-skill-flow-lock.md. | Yes |
| C03. Only executed and reproducibly verified results are claimed. | README.md:7-9 | AGENTS.md Golden Rules; locked evaluation-scope decision. | Yes |
| C04. Three recorded live measurement sessions at `1ead133` → `3bb27f8` → `5b0f5f2` consistently refuse an answer-quality verdict without evidence. | README.md:15-17 | The published 2026-07-31 capture manifest directly records `1ead133`; the 2026-08-02 `3bb27f8` and 2026-08-03 `5b0f5f2` measurements remain explicitly owner-held in their decision records. | Yes |
| C05. The 2026-07-31 capture first surfaced the refusal. | README.md:19-20 | evidence/capture-baseline-2026-07-31/issue-15-phase1-baseline-2026-07-31.capture-manifest.json; docs/decisions/2026-08-01-live-capture-replay-and-its-enumerated-claim.md. | Yes |
| C06. The 2026-08-03 same-commit re-capture at 5b0f5f2 completed parsing 6/6 and retrieval 9/9, without creating an answer-quality claim. | README.md:20-23 | docs/decisions/2026-08-03-same-commit-30-case-run-and-grounded-coverage-correction.md records the external run and SHA-256 digests. | No — owner-held |
| C07. Thirteen of fifteen grounded cases were citation-contract discards, two other paths supplied no evidence, and both runs are INVALID with zero cited coverage. | README.md:25-32 | Same-commit decision, measured-external-run table and recorded-misattribution section. | No — owner-held |
| C08. The published 2026-07-31 run has twelve old-label discards; the 2026-08-03 thirteen-and-zero result is owner-held, and neither yields quality evidence. | README.md:34-43 | evidence/capture-baseline-2026-07-31/ and evidence/eval-baseline-2026-07-31/; same-commit decision’s external-artifact path and results. | No — owner-held |
| C09. AX #60 is closed and previously conflated citation-contract and safety causes. | README.md:47-52 | AX #60, read 2026-08-03: CLOSED, closed 2026-08-01. | No — public GitHub |
| C10. AX #61 is closed and previously hid discarded provider answers despite a 294-line no-warning HTTP-200 capture window. | README.md:53-55 | AX #61, read 2026-08-03: CLOSED; detailed capture measurement is recorded in the upstream issue/decision trail. | No — public GitHub |
| C11. AX commit 3bb27f8 closes both upstream issues and 5b0f5f2 descends from it with additive predicates. | README.md:57-61 | Public AX commit 3bb27f870d244fbc8debba91eb408e825caa9e03 and AX issue history. | No — public GitHub |
| C12. No live comparison exists because comparison.py requires both runs COMPLETED; the dashboard retains a golden fixture rather than live comparison data. | README.md:63-66 | src/braincrew/comparison.py:427-428; dashboard/data/dashboard-export-v1.json; same-commit decision. | Yes |
| C13. A later frontend cycle will label the fixture on the page. | README.md:65-67 | Contradicted by current dashboard/components/dashboard-explorer.tsx and the Cycle 203 live-mode test: the label already exists. | No — unsupported/stale |
| C14. The parsing barrier was real, but the 2026-08-02 grounded failure already existed and was misattributed; re-capture cannot cure the SUT answer path. | README.md:69-73 | Same-commit decision’s recorded-misattribution section and external 2026-08-02 artifact reference. | No — owner-held |
| C15. The parsing matrix entry correctly bounds live parsing to 6/6 structural completion, not a parser-quality score. | README.md:79-86 | Same-commit external run table; parsing-boundary decisions. | No — owner-held |
| C16. The retrieval matrix entry correctly bounds live retrieval to 9/9 completion and separates earlier nine-case metrics. | README.md:79-86 | Same-commit external run table and historical live-capture records. | No — owner-held |
| C17. The grounded-answer matrix entry is unmeasurable because both same-commit runs are INVALID with zero coverage. | README.md:79-86 | Same-commit external run table. | No — owner-held |
| C18. The operational matrix entry records latency but no provider-cost value. | README.md:79-86 | Same-commit external artifacts described by the decision; docs/decisions/2026-07-28-operational-measurement-and-the-cost-exclusion.md. | No — owner-held |
| C19. The comparison/release matrix entry has fixture reproduction but no compatible live comparison. | README.md:79-86 | src/braincrew/comparison.py:427-428; same-commit external run states; fixture acceptance test. | No — owner-held |
| C20. Agent trajectory remains planned, unimplemented, and unclaimed. | README.md:79-86 | Scope-lock decision sections 1, 3, and 9: no Agent-quality claim without a real execution path, no first-release Agent evaluator, and `TRJ-*` reserved and unused as a failure-taxonomy code. | Yes |
| C21. Parsing capability is evaluated through 6/6 owner-held live cases. | README.md:94-103 | Same-commit external run table. | No — owner-held |
| C22. Retrieval capability is evaluated through 9/9 owner-held live cases. | README.md:94-103 | Same-commit external run table. | No — owner-held |
| C23. Grounded answer/visibility/abstention is evaluated but has no answer-quality result. | README.md:94-103 | Same-commit external baseline and candidate evaluations. | No — owner-held |
| C24. Operational latency is evaluated but provider cost is not. | README.md:94-103 | Same-commit external artifacts and cost-exclusion decision. | No — owner-held |
| C25. The stored 2026-07-31 capture and evaluation can be replayed, without validating live AX. | README.md:94-103 | Four files under evidence/; tests/acceptance/test_cli_fixture_gate.py; docs/decisions/2026-08-02-published-live-evidence-replay.md. | Yes |
| C26. Live comparison/release is not evaluated because compatible 2026-08-03 runs are INVALID. | README.md:94-103 | Same-commit external artifacts; src/braincrew/comparison.py:427-428. | No — owner-held |
| C27. No trajectory capability, run, or artifact is claimed. | README.md:94-103 | Scope-lock decision sections 1, 3, and 9: no Agent-quality claim without a real execution path, no first-release Agent evaluator, and `TRJ-*` reserved and unused as a failure-taxonomy code. | Yes |
| C28. No live answer-quality, comparison, or release verdict is claimed. | README.md:105-115 | Same-commit decision; comparison refusal code; explicit scope decision. | Yes |
| C29. The dashboard PASS is fixture evidence with placeholder SHAs, and the page says so. | README.md:105-115 | dashboard/data/dashboard-export-v1.json; dashboard/components/dashboard-explorer.tsx; tests/frontend/e2e/dashboard.spec.ts. | Yes |
| C30. Stored-artifact replay and a fresh live rerun make different reproducibility claims. | README.md:105-115 | docs/decisions/2026-08-01-live-capture-replay-and-its-enumerated-claim.md; docs/decisions/2026-08-02-published-live-evidence-replay.md. | Yes |
| C31. Agent evaluation is not claimed; `TRJ-*` is an unused reserved failure-taxonomy code. | README.md:105-115 | Scope-lock decision sections 1, 3, and 9: no Agent-quality claim without a real execution path, no first-release Agent evaluator, and `TRJ-*` reserved and unused as a failure-taxonomy code. | Yes |
| C32. The diagram’s dataset is a frozen 100-case synthetic dataset. | README.md:121-140 | datasets/dataset_manifest_v3.json, including case_count: 100, source_type: synthetic, version and digests. | Yes |
| C33. The plane uses an HTTP SUT adapter, normalized observations, evaluators, and preflight checks. | README.md:121-140 | src/braincrew/ax-http-v1.yaml; src/braincrew/live_preflight.py; adapter and evaluator modules. | Yes |
| C34. Canonical JSON/replay, JSON-plus-Parquet comparison, and three ordered release gates are implemented. | README.md:121-140 | src/braincrew/result_store.py; src/braincrew/comparison.py:378-428 and 780-850. | Yes |
| C35. The repository has 14 CLI commands. | README.md:142-147 | rg -n @app.command src/braincrew/cli.py finds 15 commands, from run through export-dashboard. | No — unsupported/stale |
| C36. All four evaluator families are versioned in live-capture provenance. | README.md:142-147 | Published 2026-07-31 capture manifest `provenance.evaluator_versions` contains grounded, operational, parsing, and retrieval; the separate three-entry `adapter_versions` object is not this claim. | Yes |
| C37. The adapter contract is frozen, schema-digested, SUT-pinned, and mock-tested. | README.md:142-147 | src/braincrew/ax-http-v1.yaml; AX adapter contract tests; live-capture contract modules. | Yes |
| C38. Create-only artifacts and comparison Parquet are implemented as described. | README.md:142-147 | src/braincrew/result_store.py; src/braincrew/comparison.py; comparison/replay tests. | Yes |
| C39. Corpus sealing/qualification, a static dashboard, and 610 Python tests exist. | README.md:142-147 | src/braincrew/corpus_sealing.py; src/braincrew/corpus_qualification.py; dashboard/; Cycle 203 pytest output: 610 passed in 38.41s. | Yes |
| C40. Replay recomputes accepted stored digests; the authoring-independence receipt is create-only without a replay route; the live-capture replay claim is deliberately enumerated. | README.md:149-154 | src/braincrew/result_store.py; docs/decisions/2026-08-01-live-capture-replay-and-its-enumerated-claim.md. | Yes |
| C41. Live capture cannot be identically regenerated because provider calls cost money; its replay claim has six stated conditions and limits. | README.md:151-154 | Enumerated live-capture replay decision, sections 1-3. | Yes |
| C42. Insufficient evidence makes a run INVALID, and incompatible runs refuse comparison. | README.md:156-157 | src/braincrew/comparison.py:427-428 and 644-646; evaluator/contract refusal tests. | Yes |
| C43. Dataset V3 is synthetic, CC0-1.0, reviewed, sealed, qualified, versioned/digested, split 70/30, and allocated 20/30/40/10. | README.md:161-163 | datasets/dataset_manifest_v3.json; datasets/DATASET_CARD_V3.md. | Yes |
| C44. The source corpus was evaluation-blind under a capability sandbox, with an independence receipt bound into dataset provenance. | README.md:165-167 | Corpus authoring/qualification contracts and tests/acceptance/test_cli_corpus_authoring_boundary.py; dataset manifest sealing and provenance digests. | Yes |
| C45. No customer, employee, or company document is in the repository. | README.md:169 | No repository-wide documented scan, attestation, or review record establishes this negative claim. | No — unsupported/stale |
| C46. The documented Python quality and fixture-gate commands run successfully, including 610 tests. | README.md:173-184 | Cycle 203 current-checkout output: uv sync audited 29 packages; Ruff format/check passed; mypy passed; 610 passed in 38.41s; fixture gate 11 passed; focused replay 1 passed, 10 deselected. | Yes |
| C47. The fixture demo runs 100 cases and replay recomputes the same digest. | README.md:186-202 | Cycle 203 retry with the fixture’s required SUT SHA wrote demo.json as COMPLETED and replay returned the same sha256:49bb1a97c25ae762bde4d6b69331fb5062e6f60f5865392efa7dda5c6408dfaa. | Yes |
| C48. The README demo is self-sufficient with an arbitrary 40-hex replacement. | README.md:189-198 | First current-checkout run with the README’s live SHA failed: Invalid dataset observations: --sut-sha does not match grounded observation SUT SHA. It only passes with fixture SHA c318b2192006bdb36a5bd5b3a2bc403425b45701, which the README does not state. | No — unsupported/stale |
| C49. The demo is fixture-mode determinism evidence, not a live benchmark. | README.md:200-202 | Cycle 203 generated artifact recorded run.execution_mode: fixture and sut.executed: false; replay output above. | Yes |
| C50. The container is lockfile-based, network-isolated, mount-free, and its context excludes local metadata/caches/build output. | README.md:204-215 | Dockerfile; .dockerignore; clean-container decision. Current Docker execution was intentionally not run in Cycle 203. | Yes |
| C51. The image runs the listed fixture gates, replays the four reviewed files, handles Bubblewrap skips as described, does not execute AX, and labels hosted CI unverified until PR execution. | README.md:217-224 | Dockerfile; .github/workflows/python-ci.yml; clean-container and published-live-evidence decisions. | Yes |
| C52. Container replay is stored-artifact integrity evidence, not a live-quality/release result. | README.md:226-229 | docs/decisions/2026-08-02-published-live-evidence-replay.md; fixture replay acceptance tests. | Yes |
| C53. V3 has no complete offline run with committed observations; the old V1 bundle gives INVALID with 34/100 scored because of query/coverage drift. | README.md:231-243 | docs/status/braincrew-delivery-workflow.md:1358-1361; docs/decisions/2026-08-01-parsing-drift-refusal-and-evaluator-versioning.md. | Yes |
| C54. The repository-map paths hold the listed source, dataset, dashboard, decision, interview, status, and specification material. | README.md:247-257 | Current tree inspection of the named paths. | Yes |
| C55. The most recent ticket had exactly five blocking findings, one code and four prose, with the stated audit behavior. | README.md:261-267 | No named ticket, audit artifact, or exact five-finding record is linked from this paragraph; the exact count and allocation were not traceable in the current checkout. | No — unsupported/stale |
| C56. Worker reports are independently reproduced; guards are mutation-verified; durable records are append-only. | README.md:268-274 | AGENTS.md multi-pane rules; docs/status/braincrew-delivery-workflow.md; append-only decisions. | Yes |
| C57. The first release is incomplete with the stated 5/1/3/1 acceptance-status accounting. | README.md:278-292 | docs/status/braincrew-delivery-workflow.md current checkpoint and design-spec acceptance accounting. | Yes |
| C58. The current live answer-quality block is thirteen citation violations plus two non-evidentiary paths. | README.md:294-297 | Same-commit external-run artifacts and decision. | No — owner-held |
| C59. This repository is “Licensed work in progress.” | README.md:299-300 | git ls-files found no tracked LICENSE/LICENCE file or linked licensing decision for the repository itself. | No — unsupported/stale |

## Unsupported or stale claims and recommended repair

1. **C13 — future frontend label.** The source already labels fixture evidence. Remove the future-tense sentence or update it to name the existing label and its evidence.
2. **C35 — 14 CLI commands.** Source currently exposes 15 app commands. Correct the count after deciding whether all 15 belong in the reader-facing capability count.
3. **C45 — no customer/employee/company document.** Add a bounded provenance/contents attestation or replace the absolute negative with a statement limited to reviewed dataset and evidence directories.
4. **C48 — 40-hex demo placeholder.** State the fixture SHA required by tests/fixtures/grounded_observations_v1.json, or derive it rather than asking the reader for an unexplained value.
5. **C55 — five blocking-finding history.** Link the precise ticket/audit record and its five findings, or remove the count/allocation.
6. **C59 — licensed work in progress.** Add the repository license and link it, or remove the statement.

## Reproduction guide: commands run in this checkout

The following commands were executed serially on this checkout. They prove the current working environment only; they do not prove a clean clone, a fresh virtual environment, hosted CI, or Docker execution.

| Command | Actual result |
| --- | --- |
| uv sync --frozen --all-groups | Exit 0 — Audited 29 packages in 3ms |
| uv run ruff format --check . | Exit 0 — 72 files already formatted |
| uv run ruff check . | Exit 0 — All checks passed! |
| uv run mypy | Exit 0 — Success: no issues found in 72 source files |
| uv run pytest -q | Exit 0 — 610 passed in 38.41s |
| uv run pytest tests/acceptance/test_cli_fixture_gate.py -q | Exit 0 — 11 passed in 3.01s |
| uv run pytest tests/acceptance/test_cli_fixture_gate.py -q -k test_replay_recomputes_the_same_logical_digest_and_gate_decision | Exit 0 — 1 passed, 10 deselected in 0.34s |
| README run-dataset demo with live SHA 5b0f5f2… | Exit 2 — Invalid dataset observations: --sut-sha does not match grounded observation SUT SHA |
| README run-dataset demo retried with required fixture SHA c318b219… | Exit 0 — COMPLETED, logical digest sha256:49bb1a97c25ae762bde4d6b69331fb5062e6f60f5865392efa7dda5c6408dfaa |
| README replay demo | Exit 0 — re-derived the same logical digest |
| npm ci | Exit 0; emitted EBADENGINE because current npm is 10.9.8 while package.json requires >=11.0.0, and reported four high-severity dependency vulnerabilities. |
| npm run format:check | Exit 0 — all matched files use Prettier style |
| npm run lint | Exit 0 |
| npm run typecheck | Exit 0 |
| npm test -- --run | Exit 0 — 2 files, 8 tests passed |
| npm run build | Exit 0 — static Next.js build generated 3 pages |
| npx playwright install --with-deps chromium | Exit 0 |
| npm run test:e2e | Exit 0 — 2 Playwright tests passed; emitted the inherited NO_COLOR/FORCE_COLOR warning |

## Reproduction gaps and requirements

- **Clean clone / fresh environment:** not verified. This checkout already had the intended Cycle 200–202 edits, an existing Python environment, and installed Node dependencies. A valid clean-environment rehearsal requires a new clone and the pinned/currently supported Node and npm versions.
- **Frontend package-manager compatibility:** npm ci completed, but observed npm 10.9.8 does not meet package.json’s >=11.0.0 engine declaration. A clean-environment claim remains unverified until rerun with npm 11 or later.
- **Docker build and run:** not run. Cycle 203 explicitly excludes container operations. Verification requires a Docker-capable host and authorization to execute the documented docker build and docker run commands.
- **Hosted CI:** not run. The repository defines the workflow, but a pull-request workflow result is the required external evidence.

## Scope retained

No README, evidence, runtime, container, attachment, provider, or Git lifecycle state was changed by this audit. The fixture demonstration used a disposable /tmp directory and was removed after replay verification.

## Cycle 204 resolution — 2026-08-03

Cycle 204 changes the reader-facing README without altering this audit's original classifications or
totals.

- **C13 repaired:** README names the existing fixture label and links its end-to-end assertion.
- **C35 repaired:** README now says 15 CLI commands, re-counted from `@app.command` decorators.
- **C45 repaired:** README limits the document boundary to named dataset, publication-review, and
  secrets-CI records.
- **C48 repaired:** README supplies the fixture's recorded SUT SHA and distinguishes it from the
  live pin in a disposable working command.
- **C55 repaired:** README removes the untraceable five-finding allocation and links this audit.
- **C59 remains open:** the repository-license owner decision is unchanged; README:299-300 is
  intentionally untouched.

## Cycle 206 delta — 2026-08-03

The original Cycle 203 inventory retains its pre-Cycle-204 line index. This
appendix records the later reader-facing repairs without presenting the old index
as current.

- **B1 / C04:** README now names the three measured SUT commits
  (`1ead133` → `3bb27f8` → `5b0f5f2`). C04 moves from owner-held to
  in-repository because the published 2026-07-31 manifest directly establishes
  the formerly omitted first commit; the later two measurements remain labelled
  owner-held.
- **B3 / C20, C27, C31:** README and these evidence cells now point to the
  scope-lock decision's unused `TRJ-*` failure-taxonomy reservation. No
  source-level trajectory extension point is claimed.
- **N1 / C36:** C36 moves from owner-held to in-repository because the published
  capture manifest carries all four evaluator-version entries. It does not rely
  on the separate three-entry adapter-version object.
- **B2:** The uncommitted decision, dossier, and status additions now describe
  the shipped fixture label in completed, not future, terms.

## Cycle 207 delta — 2026-08-03, C59 resolved by the owner

**C59 is closed by removal, not by adding a licence.** The owner decided not to grant a licence for this
repository.

The former `README.md` sentence "Licensed work in progress." asserted a licensed status that no tracked
file established — `git ls-files` matches no `LICENSE` or `LICENCE` path, re-measured at this cycle and
returning `0`. The sentence now states the true position instead: no licence is granted, the default
applies and all rights are reserved.

The replacement also draws a distinction the original blurred. The **repository** carries no licence
grant; the **evaluation dataset** declares its own, and that declaration is checkable in-repository —
`datasets/dataset_manifest_v3.json` records `provenance.source_type = synthetic` and
`provenance.license = CC0-1.0`, both re-measured at this cycle.

This closes the last of the six unsupported-or-stale findings from the original 2026-08-03 inventory.
The original rows above are unchanged; C59's row records what was true when the audit was written.

**Still open, and not licence-related** — recorded here so that "all audit findings are closed" is not
read as "nothing is unverified":

- `package.json` declares `engines.npm >= 11.0.0`; the environment that ran these gates has `10.9.8`.
  The frontend chain passes anyway because the declaration is advisory without `engine-strict`, but the
  chain has not been exercised on npm ≥ 11.
- `docker build` and `docker run` were not executed by any pane in this release.
- The hosted CI workflow requires a pull request to execute and remains unverified until one runs.
- A clean clone and a fresh virtual environment were not created; every command above was run in this
  working checkout.
