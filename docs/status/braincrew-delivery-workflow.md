# Braincrew Portfolio Delivery Workflow Status

Last updated: 2026-08-02

## Purpose

This file is the durable checkpoint for the portfolio delivery flow. Update it whenever a canonical skill phase starts, completes, becomes blocked, or changes so the current route does not depend on conversation memory.

## Locked route

```text
research and AX_portfolio context
  -> setup or verify Matt Pocock workflow skills
  -> grill-with-docs when unresolved requirements remain
  -> optional time-boxed prototype for a concrete runnable uncertainty
  -> handoff
  -> to-spec
  -> to-tickets with dependency edges
  -> fresh-context implementation per ready ticket with TDD
  -> code review per ticket
  -> full benchmark and submission verification
```

`to-spec` is the implementation-facing specification and PRD-equivalent for this project. Do not run `to-prd` in parallel unless the locked route is explicitly changed. Use `writing-plans` or `ralplan` only as a named supporting step for a concrete unresolved gap, not as a silent replacement for `to-spec` or `to-tickets`.

## Current checkpoint

- **Current state, 2026-08-02 (#134, AX pin and continuity warrant).** [Issue
  #134](https://github.com/DHChe/braincrew-datateam-portfolio/issues/134) is implemented locally and
  remains uncommitted. The AX pin and packaged contract now name `5b0f5f2`, and the three-path
  continuity warrant has been independently reviewed. Cycle 191 adds only the accompanying
  append-only documentation; no source, test, fixture, AX, evidence, or Git state changes in this
  checkpoint. #131's implementation has since merged as `4279ba9`; current `HEAD` is `227442b`,
  while Issue #131 remains open because its approved v3-attachment and parsing-capture acceptance
  criteria are unmet. The #131 bullet below is deliberately left intact as a dated record of its
  earlier local-pre-merge state.
- **The bullet below is an earlier dated record and is not current state.**
- **Current state, 2026-08-02 (#131, live parsing capture).** [Issue
  #131](https://github.com/DHChe/braincrew-datateam-portfolio/issues/131) is implemented locally and
  remains uncommitted. `capture-live-parsing` converts only AX's read-only parse-observation response
  after proving that its returned text, digest, and spans match the frozen dataset-v3 document; it does
  not read the parsing answer key. The current AX runtime has only the six older `synthetic-rule-*`
  attachments, not v3's six `demo-*` documents, so no new parsing bundle or baseline/candidate
  re-evaluation has been written. Creating those attachments would change runtime data and is out of
  scope. No container-state command, answer/retrieval capture, `evidence/` write, or Git write occurred.
  One read-only search during the cycle transiently swept `evidence/` into its scan results; nothing
  there was created, modified, copied or staged, and its four files remain byte-identical. It is
  recorded because the sentence above is a list of negatives, and a reader checking only that list
  would not otherwise learn that the path was read at all.
  See the 2026-08-02 (#131) Transition history entry below.
- **The bullet below is an earlier dated record and is not current state.**
- **Current state, 2026-08-02 (#16, stored-live replay publication).**
  [Issue #16](https://github.com/DHChe/braincrew-datateam-portfolio/issues/16) is implemented locally
  and remains uncommitted: the owner-authorized four-file stored-live evidence set now sits under
  `evidence/`, byte-identical to its read-only source, and the existing CLI replays both published
  artifacts from a clean, network-isolated container. Host gates reported `599 passed` and the Issue #6
  file reported `11 passed`; the container reported `596 passed, 3 skipped`, then `11 passed`. This
  proves stored-artifact integrity and replay only, not current live AX quality, a release decision, or a
  fresh byte-identical rerun; Issue #15 remains open. CI definitions still await a pull-request run. No
  Git lifecycle action, Docker Compose invocation, AX-container contact, or live SUT/provider execution
  occurred. See the new 2026-08-02 (#16) Transition history entry below.
- **The bullets below are earlier dated records and are not current state.**
- **Current state, 2026-08-01 (#121, #122).**
  [Issue #121](https://github.com/DHChe/braincrew-datateam-portfolio/issues/121) and
  [Issue #122](https://github.com/DHChe/braincrew-datateam-portfolio/issues/122) — re-pinning the
  under-test AX commit to `3bb27f8` and recording AX's two new discard predicates without disturbing
  published evidence — are **implemented, reviewed `APPROVE` with no blocking finding, one review
  finding applied, and uncommitted**: fourteen source and test files plus three documents on `develop`
  at `d2b3c29`, `uv run pytest -q` reproducing **598 passed**, `git status --short schemas/` empty.
  Issue [#97](https://github.com/DHChe/braincrew-datateam-portfolio/issues/97) merged earlier today as
  `d2b3c29`. **Nothing is committed for #121 or #122**; the step that remains is the Git Lifecycle
  Proposal Gate. The diagnostic re-capture that would resolve the twelve unknown discards is a live
  provider run and remains a hard stop pending explicit owner authorization. See the
  2026-08-01 (#121, #122) entry at the top of Transition history.
- **The bullet below is the earlier dated record and is not current state.**
- **Current state, 2026-08-01 (#97).**
  [Issue #97](https://github.com/DHChe/braincrew-datateam-portfolio/issues/97) — the tracked-`schemas/`
  corruption hazard that has been serialising every test run all day — is **implemented, reviewed
  `APPROVE` with no blocking finding, and uncommitted**: five files on `develop` at `a2f5b02`,
  `uv run pytest -q` reproducing **592 passed**, `git status --short schemas/` empty. Issues
  [#118](https://github.com/DHChe/braincrew-datateam-portfolio/issues/118) and
  [#106](https://github.com/DHChe/braincrew-datateam-portfolio/issues/106) merged earlier today as
  `a2f5b02` and `be206ff`, and the repository's first `README.md` as `d6b98ec`. **Nothing is committed
  for #97**; the steps that remain are the pre-commit audit and the Git Lifecycle Proposal Gate. Once
  it lands the implementable frontier is **one issue, #103**. See the 2026-08-01 (#97) entry at the top
  of Transition history.
- **The bullet below is the earlier dated record and is not current state.**
- **Current state, 2026-08-01 (instrument freeze and #118).** Instrument-improvement work is
  **frozen**: [#108](https://github.com/DHChe/braincrew-datateam-portfolio/issues/108)–[#115](https://github.com/DHChe/braincrew-datateam-portfolio/issues/115)
  are parked with a resume condition, and the implementable frontier is two issues once #118 is set
  aside as in flight — #97 and #103.
  [Issue #106](https://github.com/DHChe/braincrew-datateam-portfolio/issues/106) merged as `be206ff`
  and the repository's first `README.md` merged as `d6b98ec`.
  [Issue #118](https://github.com/DHChe/braincrew-datateam-portfolio/issues/118) — parsing refusing a
  drifted observation instead of scoring it zero — is **implemented, reviewed, repaired, re-reviewed
  `APPROVE`, and uncommitted**: eleven implementation files on `develop` at `d6b98ec`, `uv run pytest -q` reproducing
  **589 passed**, `git status --short schemas/` empty. **Nothing is committed for #118**; the steps
  that remain are the pre-commit audit and the Git Lifecycle Proposal Gate. Against the design
  specification's ten acceptance criteria the release stands at **four met, one met for fixture
  evidence only, four not met, one not separately assessed** — the engine is far along and the
  evidence is not. See the 2026-08-01 instrument-freeze entry at the top of Transition history.
- **The bullet below is the earlier dated record and is not current state.**
- **Current state, 2026-08-01 (after merge).**
  [Issue #106](https://github.com/DHChe/braincrew-datateam-portfolio/issues/106) is **merged and
  closed** — `be206ff` on `develop`, PR #107 squash-merged with both CI jobs green. Re-verified on the
  merged `develop` by pane 1: ruff format and check clean, mypy clean, **581 passed**, tree and
  `schemas/` clean, and the real 2026-07-31 capture replaying through the committed CLI at exit 0 to
  `sha256:775a8529…`. GitHub did not auto-close the issue from the `Closes #106` line because the
  merge target is `develop` rather than the default branch; it was closed explicitly with the outcome
  recorded. The branch `feat/issue-106-live-capture-replay` was deleted from `origin` and locally
  after confirming `be206ff`'s tree is identical to the branch tip. **Eight follow-ups were filed
  individually** — [#108](https://github.com/DHChe/braincrew-datateam-portfolio/issues/108),
  [#109](https://github.com/DHChe/braincrew-datateam-portfolio/issues/109),
  [#110](https://github.com/DHChe/braincrew-datateam-portfolio/issues/110),
  [#111](https://github.com/DHChe/braincrew-datateam-portfolio/issues/111),
  [#112](https://github.com/DHChe/braincrew-datateam-portfolio/issues/112),
  [#113](https://github.com/DHChe/braincrew-datateam-portfolio/issues/113),
  [#114](https://github.com/DHChe/braincrew-datateam-portfolio/issues/114) and
  [#115](https://github.com/DHChe/braincrew-datateam-portfolio/issues/115) — four `ready-for-agent`
  and four `needs-triage`, because four of them require a judgement before any code is written.
  **Nothing is in flight.**
- **The bullet below was written before that merge and is preserved as the pre-merge record.** It
  says nothing is committed and names the Git Lifecycle Proposal Gate as the only remaining step,
  which was true when it was written and stopped being true when the owner authorized the merge. It
  is superseded rather than rewritten, which is this file's discipline; the bullet above is the
  current state.
- **Current state, 2026-08-01.** [Issue #106](https://github.com/DHChe/braincrew-datateam-portfolio/issues/106)
  is **implemented, reviewed `REQUEST CHANGES`, repaired, re-reviewed `APPROVE` with no blocking
  finding, audited before commit — that audit returned `NOT SAFE TO COMMIT` twice, both times on
  pane 1's own records and never on the code, and both rounds were reproduced and corrected — and
  uncommitted.** Working tree on `develop`, base **`a373e64`**; `git status --short` names **five
  files — three source, two documentation — plus the untracked decision document**, and
  `git status --short schemas/` is empty. `uv run pytest -q` reproduces **581 passed**. The first
  live capture — the one artifact in this project that cannot be regenerated — can now be verified by
  committed code, and **what that verification establishes is a closed list of six conditions rather
  than a general claim of consistency.** Independent review broke the first implementation, and
  pane 1 reproduced the break against the real capture. **Nothing is committed**; the only step that
  remains is the Git Lifecycle Proposal Gate. See the 2026-08-01 entry at the top of
  Transition history.
- **The bullet below is the earlier dated record and is not current state.**
- **Current state, 2026-07-31 night.** #101 is **merged and closed** (`f9d9cfd`, PR #104). The AX
  runtime was opened and closed again under stage-by-stage authorization, and **the first live
  experiment capture in this project's history succeeded**. The runtime run began from a `develop`
  clean at `f9d9cfd` reproducing **562 passed**; the only working-tree change afterwards is this
  status entry itself. **X1 is measured**, and the twelve misclassifiable inputs it found are why
  Issue #92's repairs were needed rather than merely prudent. **No answer-quality claim follows from
  the capture** — twelve of fifteen grounded cases produced no quality evidence at all. The next
  blocker is in AX's answer path, not in Braincrew. See the 2026-07-31 night entry at the top of
  Transition history.
- **The bullet below was written into the commit that exercised the Git authorization, and is kept
  as that record.** It says no commit or pull request existed yet, which was true when written.
- **Current state, 2026-07-31 evening.** [Issue #101](https://github.com/DHChe/braincrew-datateam-portfolio/issues/101)
  is **implemented and approved twice**, on branch `feat/issue-101-corpus-identity-per-role` cut
  from `develop` at **`61fe64c`**. **The owner authorized commit → push → pull request**; the merge
  into `develop` is a separate authorization, conditional on both CI jobs passing. This entry is
  written into the commit that exercises that authorization, so at the moment of writing no commit
  and no pull request exist yet. `uv run pytest -q` reproduces **562 passed**;
  `git status --short schemas/` is empty. See the 2026-07-31 evening entry at the top of Transition
  history.
- **The bullets below this one are earlier dated records, preserved unedited.** They are not
  current state; the bullet immediately following still names Issue #94 as the last merge and #92
  as the next ticket, and both have since merged (`998708e`, `2331963`). Transition history remains
  the authoritative record of what has landed.
- Active phase: **nothing is in flight.** [Issue #94](https://github.com/DHChe/braincrew-datateam-portfolio/issues/94)
  merged into `develop` as **`3822daf`** (PR #96, both CI jobs green) and is `CLOSED`. `develop` is
  clean and reproduces **521 passed**. The next ticket is
  [#92](https://github.com/DHChe/braincrew-datateam-portfolio/issues/92), **not** the live
  measurement — see the 2026-07-31 entry in Transition history for why the ordering is a real
  dependency rather than a preference.
- **Read the entries below with their dates, not as current state.** This section was not kept
  current between 2026-07-28 and 2026-07-31: the bullet immediately following still reads
  "Active phase" for Issue #86, and Issues #89, #91 and #94 all merged after it without being
  recorded here. They are preserved unedited because they record what was believed on their dates;
  **Transition history is the authoritative record of what has actually landed.** This is the same
  defect class as a stale blocker list — a status field that reads as current when it is not — and
  it was corrected rather than rewritten.
- Superseded phase, recorded 2026-07-27: **[Issue #86](https://github.com/DHChe/braincrew-datateam-portfolio/issues/86) is
  implemented, reviewed `APPROVE` with no blocking finding, and published for merge into `develop`
  under explicit user authorization** (commit → push → pull request → squash merge). Branch
  `fix/issue-86-confound-applicability`, cut from `af18c5e`. **This removes the last code blocker on
  Issue #15.** Locked in
  [the conformance decision](../decisions/2026-07-27-confound-applicability-conformance.md),
  defended as card **D17**.
  - **The defect, and why it was sharp.** `_confound_violations()` demanded three retrieval metrics
    from all 30 Verification case pairs, which the 21 non-retrieval cases structurally cannot supply
    — so a real comparison was `INVALID` by construction. **The evaluator's *correct* behaviour was
    what triggered it:** it computes a metric only when the case declares it applicable, and the
    comparison layer read that deliberate omission as missing. `comparison.py` referenced
    applicability **zero** times.
  - **It was conformance, not a contract change.** The orchestrator's first justification — "no
    stored artifact breaks" — was **rejected by review** as a migration fact rather than a reason.
    The correct reason: the specification's unchanged description of `experiment-run-summary-v1`
    already required comparison to fail closed on differing **per-case applicability**. The code was
    under-implementing a contract it already had.
  - **The specification was amended too**, because the code was not the origin: line 258 declared the
    metrics mandatory per case, while lines 181, 183 and 240 of the same document supplied the
    resolution — applicability as a first-class per-case field and a Recall@5 Verification
    denominator of **9**, not 30.
  - **What it establishes:** a real mixed 6 + 9 + 15 comparison now **reaches a decision** (`FAIL`
    computed from evidence) with the confound control **still armed on all 9 retrieval cases** —
    not merely un-refused. **449 passed.**
- Preceding phase, merged as **`af18c5e`** (PR #87): **[Issue #85](https://github.com/DHChe/braincrew-datateam-portfolio/issues/85) was
  implemented, reviewed `REQUEST CHANGES`, repaired, re-reviewed `APPROVE` with no blocking finding,
  and published for merge into `develop` under explicit user authorization** (commit → push → pull
  request → squash merge). Branch `feat/issue-85-live-experiment-capture`, cut from `515d9c9`.
  **Phase 0 of Issue #15**: a committed command that issues live `retrieve`/`answer` and a run
  contract that can say it was live. Locked in
  [the live-experiment decision](../decisions/2026-07-27-live-experiment-capture-and-the-unobservable-warrant.md),
  defended as card **D16**.
  - **Why it was needed.** `READY` made #15 the only licensed step, and #15 could not start:
    **zero production callers** of `retrieve`/`answer`, and the run-artifact contracts pinned
    `execution_mode: Literal["fixture"]`, so a live run was **unrepresentable** — while
    `ExperimentProvenance` in `comparison.py` already permitted `"live"`. The same shape #38 had that
    morning, one layer up.
  - **The trap and the answer.** The comparison gate refuses a dirty SUT, but **SUT dirtiness is not
    observable over HTTP**. Rather than default `sut_dirty=False`, the artifact carries a
    `SutStateWarrant` naming the method, its subject and the values the check returned.
  - **What review caught.** Eleven mutations; seven guards load-bearing; the **four survivors were
    without exception the ones carrying the honesty claim**, including neutering the execution-claim
    validator, which survived all 433 tests. The decisive pair: fabricating the warrant was *caught*;
    calling git, **discarding the result** and recording constants was *not*. Plus: every live
    failure produced a traceback and exit 1 (`AxHttpFailure` subclasses `RuntimeError`); the
    `logical_digest` could not be recomputed from its own file; and the parsing widening made only a
    *false* state reachable. All closed, **442 passed**.
  - **Correction to the orchestrator's ticket, by the implementer:** the 30 Verification cases are
    6 parsing + 9 retrieval + 15 grounded, so live calls are **24, not 30**. Parsing cases carry no
    query. The manifest now encodes the partition explicitly.
- **Newly blocking Phase 1 of #15:**
  [Issue #86](https://github.com/DHChe/braincrew-datateam-portfolio/issues/86) — `_confound_violations()`
  demands retrieval metrics from all 30 case pairs, which the 21 non-retrieval cases structurally
  cannot supply, so a real comparison is `INVALID` by construction. **The contradiction is in the
  design specification, and so is its resolution:** that document declares per-case metric
  **applicability** as a first-class field (line 181) and fixes Recall@5's Verification denominator at
  **9** (line 240), while line 258 demands the metric from every case. Scoping the check is the spec
  being applied, not relaxed.
- Preceding phase: **Phase 1 of the authorized live runtime capture executed on 2026-07-27, and
  `braincrew_preflight_ready` is now `true`.** Under explicit stage-by-stage user authorization, the
  stopped AX runtime was started (the same containers Stage 9 created — all three container IDs
  byte-identical), the committed `capture-live-verification` command ran **once** against
  `http://127.0.0.1:18000`, and the runtime was stopped again in the Stage 12 order with the volume
  set unchanged at 114.
  - **Result: exit 0, `readiness=READY`, 3 corpus + 6 parse observations, 0 blockers.** Logical
    digest `sha256:fe38499e27215c23a43bfeb0f0893f152d18613ef5188fdfeba46ec207e128e3`, reproduced
    through the committed CLI replay by the capturing pane **and independently by the reviewer**.
    All three roles truthfully include `braincrew-evaluation-dataset-3.0.0` in
    `contributing_versions`; Employee's narrower 130-record view is Stage 11's
    `employee_visibility_invariant` re-observed at the same byte-identical corpus digest. Artifact
    and evidence live **outside** the repository (`ax-live-verification-evidence/`, 9 files); the
    repository records this digest and outcome, not the bytes.
  - **All five conditions the flag requires now hold**, the fifth — independent review of the
    captured artifact — by the cycle-88 `APPROVE` with no blocking finding. The reviewer corrected
    the evidence set's one overclaim: the seed-in-all-three-roles *fact* was first observed by Stage
    11 on 2026-07-26; what is first here is its capture through a committed command into a
    contract-validated, replayable artifact.
  - **Scope of the claim, exactly:** replay proves integrity and contract validity, **not** the
    corpus numbers (their warrant is the Stage 11 cross-check); the tenant is bound by the capture
    path, not the artifact contract; `sut_commit_sha` is an assertion whose warrant is the Step 1
    read-only checkout verification. No baseline or candidate ran; **no quality claim exists**;
    Issue #15 remains separately authorized. One deviation is recorded, not hidden: the one-shot
    `migrate` container started as a compose dependency and applied nothing (zero alembic upgrade
    lines; schema version byte-identical to the pre-B archived dump).
  - AX topology after this: **AX #43 and AX #37 are `CLOSED`** with the evidence; Braincrew #38's
    formal blocker list is empty and its seven criteria are being assessed for closure.
- Preceding phase, merged as **`6ec3abc`** (PR #83): **[Issue #82](https://github.com/DHChe/braincrew-datateam-portfolio/issues/82)**
  — reviewed `REQUEST CHANGES`, repaired, re-reviewed `APPROVE` (scoped). Branch
  `feat/issue-82-capture-command`, cut from `7f3f1bf`. **Phase 0** of the capture: a committed
  `capture-live-verification` command, so the AX runtime start happens **once** rather than twice.
  Locked in
  [the capture command decision](../decisions/2026-07-27-live-verification-capture-command.md),
  defended as card **D14**.
  - **Why it was needed.** The two preceding merges built the artifact and gave it a verdict but left
    no way to run it — no `src/` caller, no CLI command, v2 absent from the replay dispatch. The only
    way to capture was to type Python into a terminal, and this project has already repaired a defect
    of exactly that shape (AX PR #53).
  - **What the cycle caught that a snippet would have carried into the live run.** `--tenant-id` was
    an unbound operator keystroke: two captures identical except for the tenant, one on a tenant
    nobody had reviewed, **both returned `READY` and replayed `READY` forever**. And the command ran
    from a dirty worktree, stamping a `HEAD` that does not describe the code that ran. Both fixed.
  - **Where the tenant binding lives, and it matters for what #38 may claim.** The tenant is bound at
    the **entry point** — not a parameter at all, `--tenant-id` gone with a signature-level test
    preventing its return, receipt bytes pinned. It is **not** bound in the artifact contract the way
    the subject is. So #38's AC1 "binds the exact tenant identity" is satisfied **by the capture
    path, not by the artifact in isolation.**
  - **Verification:** Ruff, mypy over 65 source files, **416 passed**, reproduced independently, plus
    a colour/width environment matrix.
- Preceding phase, merged: **[Issue #80](https://github.com/DHChe/braincrew-datateam-portfolio/issues/80)**
  as squash commit **`7f3f1bf`** (PR #81), closed manually. Branch
  `feat/issue-80-preflight-readiness-verdict`, cut from `87c0fc4`. The v2 preflight now carries
  `readiness: READY | NOT_READY`, scoped to that schema, and **may retain one typed blocker when the
  verdict is negative**. This **deliberately reverses** the same-day rule that a v2 artifact may not
  retain blockers; the reversal and its reasoning are locked in
  [the readiness verdict decision](../decisions/2026-07-27-live-verification-readiness-verdict.md)
  and defended as card **D13**.
  - **Why a verdict could not just be added.** Measured first: a v2 artifact could exist *only* on
    complete success, so `Literal["READY"]` would have been a **constant, not a judgment** — true in
    every artifact that could ever exist and unobservable by any test. Issue #38 criteria **4** and
    **6** turned out to be one problem: a verdict needs something to say when it is negative, and
    criterion 4 already named it.
  - **Verification.** Ruff, mypy over 65 source files, **409 passed** (387 → 405 → 409), reproduced
    independently by the orchestrator. Across two review rounds **30 clauses were disabled one at a
    time**; the three survivors that admitted concrete forgeries were closed by tests with the source
    left unchanged. `NOT_READY` is reachable through **three** real capture paths, and forcing the
    verdict positive in source turns **16** tests red.
  - **Criteria 4 and 6 are now addressed *in code*. They are not thereby met *in evidence*.**
- Preceding phase, merged: **[Issue #77](https://github.com/DHChe/braincrew-datateam-portfolio/issues/77)**
  as squash commit **`87c0fc4`** (PR #79), closed manually. `live-verification-preflight-artifact-v2`
  exists as a **third** schema and a `src/` capture path composes the frozen v3 dataset identity,
  three role corpus observations and the six reviewed parse probes into one create-only artifact.
  - *These bullets are written to stay true across their own merge.* The checkpoint went false the
    moment its work merged — twice — so it now states the authorized transaction rather than a
    pre-merge waiting state, and the squash commit is filled in here once known.
  The contract is locked in
  [the v2 contract decision](../decisions/2026-07-27-live-verification-preflight-artifact-v2-contract.md).
  - **What the review cycle actually caught.** The first implementation bound the six parse probes to
    one tenant and reviewed subject and left the three corpus observations bound to **nothing** —
    moving all three to a different tenant *and* subject was accepted and replayed clean, and a
    corpus observation with **zero HTTP attempts** was accepted. Separately, the five-line reuse that
    carried every parse-side protection into the v2 contract could be **deleted with the suite green
    at `370 passed`**. Both are fixed; the second is now the fifth instance of the self-comparison /
    unobserved-line shape this repository has recorded, and every one was found by mutation.
  - **Verification.** Ruff, mypy over 65 source files, **387 passed** (from 370, zero test
    deletions), `git diff --check` clean — reproduced independently by the orchestrator, not taken
    from a worker report. Re-review ran **35 mutations across four sweeps**; all eight identity
    mutations that were accepted before the repair are refused after it, and the two deliberate
    canaries still pass, proving the fix did not overshoot into invented expectations.
  - **This closes the last code blocker on #38's own criteria, and #38 still cannot close.** What
    remains is operational, not implementable: an authorized AX runtime start, and the AX issue
    topology below. Known gaps carried forward deliberately are in §8 of the v2 contract decision.
- **What merged since the last checkpoint, and what each one deliberately did not do.**
  `origin/develop` was `354d5b3` at the previous entry and is now `d429cb1`.
  - `931d404` (#72) — repaired this checkpoint after it went stale on a merge. **The same failure
    recurred two cycles later**, which is why this section is now rewritten as part of dispatching a
    cycle rather than after reporting one.
  - `2a2f469` (#73, Issue #71) — `PINNED_AX_SHA` and the packaged Adapter contract both now name
    `2bcaee3495fd7b3f624398819575cd86a5a15c47`, the commit `354d5b3` (#70) had reviewed and accepted
    **as an evaluation SUT**, which is a different assertion from the provisioning review it already
    had. Artifacts against today's substrate are now *constructible*. They are still not *captured*.
  - `a846058` (#74) — separated the two identity axes Issue #38 had compressed into one sentence, and
    corrected that issue's self-contradictory acceptance clause. The analysis is
    `docs/decisions/2026-07-27-dataset-identity-axis-analysis.md`.
  - `d429cb1` (#76, Issue #75) — **Option C, as locked by the owner in that decision's §18.** The
    manifest now decides what the dataset is; the receipt decides which sources get probed. Frozen
    integrated identity moved to `3.0.0`, and the probe set was detached from manifest membership.
    The two halves were atomic: the v3 parsing component's documents and the receipt's six
    attachments overlap **0 of 6**, so either half alone fails every capture closed.
- **The dataset-identity work is no longer blocked on a human decision.** §18 of the axis analysis is
  that decision, and #75 implemented it. **§10 of the same document predates §18 and still reads
  "Recommendation, not decision" — it is preserved as history and must not be followed.**
- **`braincrew_preflight_ready` remains `false`, and Issue #77 will not change that.** It builds the
  artifact shape and proves it against controlled transports; it captures nothing. Live HTTP parse
  capture still requires a **separately authorized AX runtime start**, stopped since Stage 12.
- **Still blocked, and blocked on issue topology rather than code:** Issue #38 formally lists
  [AX #37](https://github.com/DHChe/AX_portfolio/issues/37) — the operator-controlled snapshot gate —
  among its blocking issues. Verified `OPEN` on 2026-07-27, as is the linked
  [AX #43](https://github.com/DHChe/AX_portfolio/issues/43). The SUT-commit decision's §10 directed
  this be reconciled alongside the dataset decision, not after it; it had been omitted from the
  record twice by the time #72 was written, and it is repeated here so a third omission is harder.
- Resolved, and recorded so it is not re-opened: the duplicated literal `"2.0.0"` formerly at
  `live_preflight.py:951` is **gone** — #75 deleted `_verification_cases` outright and the literal
  went with it, so there is no longer a version string that can drift from the named constant.
- Completed earlier, unchanged by the above: **the twelve-stage live apply ran to completion on
  2026-07-26 and the runtime boundary is stopped.** AX-B was applied against the live cluster under
  explicit stage-by-stage user authorization. The corpus moved from `14/77/77/154` to
  `20/83/83/166`; six tenant sources, six approvals, one conversation, and six blobs now exist. No
  quality claim of any kind follows from this — see the exclusions bullet.
- Completed phase: **Stage 10 — the AX-B live apply.** Handoff receipt
  `10-ax-b-handoff.json`, schema `ax-evaluation-parse-source-handoff-v1`, `state=COMPLETED`,
  `completion_confirmed=true`, logical digest
  `sha256:33108cb53fa12c7167bd33af9f2256a420afd7576b535d9debb2b89ffcd20977`, executed at pinned AX
  commit `2bcaee3495fd7b3f624398819575cd86a5a15c47` with a clean checkout. One conversation, six
  ordered AX-generated attachment IDs, six unique approval IDs, all six `scan=clean`,
  `parser=utf8-text/stdlib-1`, `materialized`, provider `fake-deterministic` at 1536 dimensions.
  - **The one unprovable precondition held.** `HRAdmin` approval permission could not be pre-probed —
    the corpus-identity probe exercises a different authorization path — so it was first verified by
    the real first approval request, after durable upload and extraction state already existed. All
    six approvals succeeded. Had it failed, the only authorized response was to stop the worker and
    preserve the partial state.
- Completed phase: **Stage 11 — independent post-apply verification, `PASS`.**
  `11-post-b-verification.json`, schema `ax-ab-post-b-verification-v1`. Deltas measured directly in
  the database, not inferred from the receipt: `+6` seed sources, chunks, spans, tenant sources,
  attachments and extractions, and `+12` vectors (one chunk plus one evidence span per source, each
  embedded). The six new `tenant-upload-v1:<approval_id>` version rows are exactly the receipt's six
  AX-generated approval IDs — set difference empty in both directions. Provider containment
  confirmed: `tenant_provider_transfer_policies` still holds zero rows, and the only provider adapter
  in today's audit events is `fake-deterministic`.
  - Review finding carried forward: **the seven-delta table is not a complete account of what the
    apply changed.** It omits one `conversation_threads` row, twelve `background_jobs`, six
    `tenant_source_approvals`, thirty-seven `audit_events`, and six blob files totalling 514 bytes.
    All are expected for a correct apply; all are now recorded in the artifact, because an auditor
    reading the delta table alone would miss them.
  - Review finding carried forward: **the Stage 8 provider-coverage query is no longer a valid
    post-B invariant.** It now reports twelve uncovered vectors, which is an artifact of the query's
    scope rather than provider drift — the new tenant vectors are attributed through `provider.use`
    events the query does not count. Containment was confirmed by the checks that do bind.
- Completed phase: **Stage 9 and Stage 12 — the runtime boundary was started and stopped.** Stage 9
  brought up `backend`, `worker` and `clamav` with the external override, verified the attachment
  blob bind, loopback-only API, both required worker job types, and zero policies that could
  authorize `openai`. Stage 12 stopped the worker first, then backend and ClamAV, with PostgreSQL,
  Redis and Neo4j left running at restart count zero and the Docker volume set unchanged at 114.
  `database_or_blob_cleanup_performed` and `volume_removal_performed` are both `false`.
- Completed phase: **three AX runbook and test defects found and repaired mid-flight**, each
  independently adjudicated before the fix and re-reviewed after it:
  - AX [PR #53](https://github.com/DHChe/AX_portfolio/pull/53), `db2b4454e66e6d46e9708ebdcaa3b1f5e56cfc8b` —
    the Stage 7 evidence scope did not close. A blob inventory had been produced by *reimplementing*
    the runbook's generator instead of running it, embedding an absolute path the privacy rule
    forbids, and its regeneration check passed only because it compared that script against itself.
    The superseding inventory was produced by the runbook's own generator and confirmed by an
    independent second-party run.
  - AX [PR #54](https://github.com/DHChe/AX_portfolio/pull/54), `da4078c` — `develop` had gone
    permanently red at `2026-07-26T03:00:00Z`. Tests built state on a frozen clock, requested a
    fourteen-day activation, then executed against the real clock; that expiry passed. The same
    commit passed at 00:23Z and failed at 05:39Z. Follow-ups filed as AX
    [#55](https://github.com/DHChe/AX_portfolio/issues/55) and
    [#56](https://github.com/DHChe/AX_portfolio/issues/56).
  - AX [PR #57](https://github.com/DHChe/AX_portfolio/pull/57), `d793097` — Stage 9's bind-mount
    assertion could not pass on Docker Desktop for macOS, which reports a `/host_mnt` prefix. The
    configuration was correct; the assertion was wrong. Path identity was proved read-only by
    directory metadata rather than by writing a marker into a blob root that had to stay empty.
- Completed phase: **the conforming Stage 8 independent review**, `08c-ax-b-dry-run-review.json`,
  schema `ax-ab-ax-b-dry-run-review-v1`, `decision=APPROVED`, written by a reviewer other than the
  operator. Two earlier review artifacts are retained unmodified: a `FAIL`, and a `PASS` that used
  the wrong contract vocabulary. Neither was edited or translated; the conforming review supersedes
  them at a distinct create-only path.
- Completed phase: **AX Issue #48 — the no-write dry-run contract for AX-B.** The contract was
  authored by independent review, published as a locked ticket, then **audited by its own author**
  against the question "could an implementation satisfy every acceptance checkbox and still be
  wrong?". That audit found fourteen items; **six were adopted into a published amendment before
  implementation landed**, so the semantics were pinned rather than discovered late. The
  implementation merged as AX PR #49, squash commit
  `2bcaee3495fd7b3f624398819575cd86a5a15c47`, and AX Issue #48 is now `CLOSED`/`COMPLETED`.
- Completed phase: **the twelve-stage live apply runbook**, merged as AX PR #50, squash commit
  `92681d3cb388eb95b7002e2013344914e035b196`. AX PR #51 then merged as squash commit
  `38a29fae8f90095bf3699bfa8cdab109bd3780fe`, recording that a database dump alone is not a
  recovery point.
- Completed phase: **authorized live operational preparation.** Executed by the orchestrator under
  explicit user authorization, read plus external-write only. Measured results:
  - The **post-import/pre-A database snapshot now exists**, at sha256
    `d1b5acb445504f2f22d10c92a19e8ea65967aa543fdc43f4bf3ea59ec296f2b7`.
  - **Cluster globals were captured**, at sha256
    `74adc2d0ccbfb44b01ae39bd0ead8ec996a867e2978fee5d8aec3c09a4e53625`.
  - The **attachment blob volume was observed with zero entries**, establishing the pre-A blob
    baseline while it is still free to establish.
  - `tenant_provider_transfer_policies` holds **zero rows**, so a non-`fake` embedding adapter
    **fails closed** rather than transmitting source text to an external provider.
  - The **target-tenant baseline was measured live as exactly `14/77/77/154` with zero attachments.**
    This converts a long-standing *unverified prose assumption* — previously recorded in
    documentation only — into a **measurement**.
  - An **isolated restore rehearsal succeeded** in one second with zero errors and reproduced live
    state on nine verification checks.
- Material finding from that preparation: **`pg_dump` alone is not a recovery point.** The restored
  `ax_seed_operator` role lost `SELECT` on the attachment tables, because its access comes from
  membership in the cluster-level predefined role `pg_read_all_data`, which a database-scoped dump
  does not capture. The recovery point is therefore an **ordered procedure — apply globals first,
  restore, reconcile, verify — not a file pair.**
- Independent audit of that operational evidence: pane-3 review returned **`EVIDENCE OVERSTATED`**,
  on three specific grounds — an undocumented role pre-creation step the clean restore depended on,
  a `globals.sql` with no recorded digest, and a live-cluster replay that the fresh-target rehearsal
  could not surface. **All five corrections were applied.** This is recorded because the honest
  version of the record includes the correction, not only the result.
- Completed phase: **AX-B Issue #45 implementation, two-axis review, repair, and merge.** AX-A
  [PR #46](https://github.com/DHChe/AX_portfolio/pull/46) merged as
  `fe16c0cedc1e64856d9e107e111665d0ba2e444d` and closed Issue #44. AX-B
  [PR #47](https://github.com/DHChe/AX_portfolio/pull/47) then squash-merged into AX `develop` as
  `cf3ae42915833778bc9838780b7d21a5c89327ec`, and AX Issue #45 is now `CLOSED`/`COMPLETED`. The
  matching Braincrew documentation change squash-merged into `develop` as
  `f411fae5b5feedd7a3fa4bf49ad4f8aed3e0416f`. All required checks passed on both pull requests:
  Braincrew Python and frontend; AX Backend Ruff, compile, tests, and `uv` lock; the disposable
  Docker workflow gates; frontend typecheck, build, and Playwright; the repository command gates;
  and the routine-rotation PostgreSQL required gate. Both merged feature branches and their remotes
  are deleted. This is **code completion only** — see the exclusions bullet below.
- Resolved specification defect: **the locked "one six-file multipart request" instruction was not
  executable.** Pre-implementation review found that AX enforces `MAX_FILES_PER_OPERATION = 5` per
  upload request, with an existing test pinning the six-file rejection. The authorized resolution was
  **two bounded requests of five and one into one target-owned thread**, recorded in
  [the request-split decision](../decisions/2026-07-25-ax-b-bounded-upload-request-split.md) and
  requiring zero AX source change. The AX Issue #45 body amendment was authorized and applied on
  2026-07-25 for its Build paragraph, acceptance checkbox 2, and the `PARSE_SOURCE_UPLOAD_FAILED`
  trigger clarification. The previously deferred footer edit **has now also been applied**, pinning
  the superseding decision at Braincrew commit `f411fae5b5feedd7a3fa4bf49ad4f8aed3e0416f`; the
  published body was refetched and verified against the intended text. No amendment remains
  outstanding.
- Explicit exclusions still in force. This bullet previously said "AX-B has not been applied live";
  **that is now superseded** and the corrected state is recorded here rather than by rewriting
  history:
  - **The apply happened.** Live attachments, extractions, approvals, materializations, corpus
    identities, parse observations, and an operational handoff receipt all now exist. The corpus is
    `20/83/83/166`, not `14/77/77/154`.
  - **No quality result is claimed.** Nothing about parsing accuracy, retrieval quality,
    grounded-answer quality, or any benchmark follows from a successful apply. The apply proves that
    six reviewed files traversed the real lifecycle and produced the exact expected rows — nothing
    about how well the system answers anything.
  - **`braincrew_preflight_ready` is `false`, re-measured against the applied corpus on 2026-07-26.**
    An earlier draft of this bullet said the flag "has not been re-evaluated"; it has now been
    measured, and that softer wording was wrong. Of the two recorded blocking causes, exactly one
    cleared:
    - **Cleared — absent live parse state.** `thread_attachments` and `attachment_extractions` both
      moved 0 → 6, and the evaluation subject `26d7eebf-…` exists and is active in the AX tenant.
    - **Not cleared — the principal/tenant binding conflict.** `live_preflight.py` pins
      `ACTIVE_OWNER_USER_ID = 22222222-…`, which resolves to `executive@hanbit.example` in tenant
      `11111111-…` — a demo Executive in a **different tenant**, never an evaluation principal. Of
      the six pinned attachment UUIDs, **zero** exist live: AX generates attachment IDs and the
      contract forbids caller-forcing them, so those literals were wrong before the apply and remain
      wrong after it. Re-running the apply would not fix this and is separately forbidden, because
      `stage_files` de-duplicates by content hash and a retry returns existing IDs while creating no
      rows.
    - **A third pin, not previously recorded, also blocks.** `PINNED_AX_SHA = 72805930…` is enforced
      in the `LivePreflightArtifact` validator, so **no preflight artifact captured against today's
      substrate can even be constructed.** That commit is a real ancestor of the applied
      `2bcaee34…` — superseded, not fictional — and it appears in 36 places across 13 files, several
      of them contract tests. Re-pinning it is its own reviewed change, not a line in a constants
      refresh.
    - **The flag is a prose claim, not a computed value.** It appears nowhere in `src/`. Making it
      `true` is therefore an assertion about evidence, and the only machinery that could justify it
      is `live_preflight.py`, which captures **live HTTP** parse observations — impossible while the
      AX runtime is stopped by Stage 12. Braincrew Issue #38 remains blocked.
    - **What `true` would have to prove**, recorded so a future refresh cannot lower the bar: a live
      runtime answered real parse probes; the evaluation principal was accepted and authorized for
      parsing as a principal chosen for that purpose; the six reviewed sources parsed to the frozen
      **expected** evidence rather than merely to something; the capture was bound to a reviewed,
      pinned SUT commit; and the artifact passed independent review. A mapping harvested from
      whatever the database currently holds and then compared against itself would go green while
      proving only that the code can read its own inputs.
    - **Explicitly out of scope of any such refresh:** `FROZEN_DATASET_VERSION = "2.0.0"`. It sits
      beside an AX corpus labelled `braincrew-evaluation-dataset-3.0.0`, which is a **name
      collision, not a mismatch** — the preflight validates Braincrew's own manifest. Bumping it
      would silently re-point the evaluation plane at a different case set.
  - **The embedding vectors are deterministic fakes.** The provider adapter was
    `fake-deterministic` throughout, by design and verified. The model string
    `text-embedding-3-small` and the 1536 dimensions are contract values, not evidence that any
    external embedding service was used or is usable.
  - **The recovery path remains unproven against the live cluster.** The Stage 2 rehearsal restored
    into a prepared fresh target. Replaying `globals.sql` against a cluster that already has those
    roles would error, so the remedy proven on a fresh target is not the remedy live would need.
- Known gaps carried forward from review (accepted, not defects): the deferred partial-coverage
  rows recorded in the AX verification document — the wrong-SHA half of `PARSE_SOURCE_REPOSITORY_DIRTY`;
  the receipt-invalid, tenant-mismatch, and wrong-`x-ax-roles` triggers of
  `PARSE_SOURCE_PRINCIPAL_INVALID`; the `parser_version` half of `PARSE_SOURCE_PARSER_MISMATCH`; and
  the untested secondary triggers of `PARSE_SOURCE_APPROVAL_FAILED`,
  `PARSE_SOURCE_OBSERVATION_FAILED`, and `PARSE_SOURCE_CORPUS_IDENTITY_FAILED`. Each code is
  implemented and has at least one asserted negative test; only the additional conditions named in
  the ticket text are untested. Also carried forward: no test couples the orchestrator's assumed HTTP
  response shapes to AX's real route projections, so a future projection change would not be caught
  by the AX-B suite.
- Completed phase: research, role comparison, and Data Team red-team assessment.
- Completed phase: portfolio direction and evaluation boundaries locked.
- Completed phase: `brainstorming` design loop, independent specification review, and PR #1 merge into `develop`.
- Completed phase: `setup-matt-pocock-skills`; GitHub Issues was selected, the five canonical triage labels were configured, and the single-context domain-document rules were recorded.
- Completed phase: `to-spec`; the user approved the CLI-to-gate, AX Adapter, and dashboard-export test seams, and implementation specification Issue #4 was published with the `ready-for-agent` label.
- Completed phase: `to-tickets`; the user approved 12 vertical implementation slices, GitHub Issues #6 through #17 were published as sub-issues of #4, and 22 native dependency edges were recorded.
- Completed phase: Issue #6 implementation with `test-driven-development`; ten acceptance cases cover CLI execution, deterministic rerun and replay, append-only collision handling, invalid and tampered input, complete artifact-envelope validation, dataset-digest boundaries, path traversal, and commit identity validation.
- Completed phase: Issue #6 ticket-scoped code review; both the standards and specification axes passed with zero unresolved blockers after review-driven TDD repairs.
- Completed phase: the user approved the Issue #6 Git lifecycle proposal; Lore commit `b63b2f9` was pushed to `origin/feat/issue-6-cli-immutable-gate`, and PR #20 was opened against `develop`.
- Completed phase: PR #20 passed its Python quality check and was merged into `develop` as `230f90f`; Issue #6 was closed and removed from the implementation frontier.
- Completed phase: Issue #7 implementation with `test-driven-development`; controlled HTTP tests and live synthetic smoke cover the pinned Adapter boundary without claiming quality.
- Completed phase: Issue #7 ticket-scoped code review and `verification-before-completion`; both review axes have zero unresolved blocker and every fresh local gate passed.
- Completed phase: Lore commit `3aa7264` was pushed to `origin/feat/issue-7-ax-http-contract`; draft PR #21 was opened against `develop`, its first Python quality gate passed, and its remote merge state was `CLEAN` with no review comment or change request.
- Completed phase: PR #21 passed its required Python quality check, merged into `develop` as `0d137a6`, and closed Issue #7.
- Completed phase: Issue #8 implementation with `test-driven-development`; 20 versioned parsing cases, exact metric goldens, fixture CLI/result-store execution, and fail-closed `INVALID` behavior are implemented.
- Completed phase: Issue #8 ticket-scoped `code-review`; Standards and Spec axes both passed with zero remaining finding after a bounded duplication refactor and re-review.
- Completed phase: Issue #8 `verification-before-completion`; every required local gate and the installed-console-script fixture run passed with fresh evidence.
- Completed phase: the user approved the Issue #8 Git lifecycle proposal for one Lore commit, committed-state verification, branch push, and pull-request creation; merge remains excluded.
- Completed phase: PR #22 merged Issue #8 into `develop` as merge commit `c549c255c55e97639b6261d9414fb0abfa64026e`, and Issue #8 is closed.
- Completed phase: Issue #9 implementation with `test-driven-development`; the 30-case dataset, deterministic retrieval evaluator, fixture CLI/result-store path, exact provenance, and pinned-AX synthetic smoke are implemented and documented.
- Completed phase: Issue #9 ticket-scoped `code-review`; the separate Standards and Spec axes passed with zero remaining finding after review-driven RED/GREEN repairs.
- Completed phase: Issue #9 `verification-before-completion`; every required repository gate and the installed 30-case fixture CLI create/replay path passed with fresh evidence.
- Completed phase: the user approved the Issue #9 Git lifecycle proposal for one Lore commit, committed-state verification, branch push, and review-ready pull-request creation; merge remains excluded.
- Completed phase: PR #23 merged Issue #9 into `develop` as merge commit `b67929a0546d32d6ffafc7b801028c9c53fc2d6a`, and Issue #9 is closed.
- Completed phase: Issue #10 grounded-claim implementation with `test-driven-development`; every contract, evaluator, run, and CLI behavior was observed RED before its minimal implementation or repair.
- Completed phase: Issue #10 ticket-scoped `code-review`; separate Standards and Spec axes passed with zero unresolved blocker after review-driven RED/GREEN repairs.
- Completed phase: Issue #10 `verification-before-completion`; every required repository gate and installed grounded fixture CLI create/replay check passed with fresh evidence.
- Completed phase: PR #24 squash-merged Issue #10 into `develop` as `c4ae62f1d1dfa905f34a02dbb5fa647affe8076c`, and Issue #10 is closed.
- Completed phase: Issue #11 implementation with `test-driven-development`; the 50-case fixture, deterministic mode/abstention/visibility evaluators, hard-failure evidence, immutable artifacts, and replay compatibility checks are implemented and documented.
- Completed phase: Issue #11 ticket-scoped `code-review`; separate Standards and Spec axes passed with zero unresolved finding after four review-driven RED/GREEN repairs.
- Completed phase: Issue #11 `verification-before-completion`; every required local gate and installed 50-case fixture create/replay check passed with fresh evidence.
- Completed phase: PR #25 passed its required Python quality check, squash-merged Issue #11 into `develop` as `c6cd5920ed7b46798618734c7c55977b89c9d9af`, and Issue #11 is closed.
- Completed phase: Issue #12 implementation with `test-driven-development`; the strict 100-case registry, dataset card, fail-closed mutation validation, immutable full-fixture artifact, deterministic replay, and existing 20/30/50-case compatibility are implemented and documented.
- Completed phase: Issue #12 ticket-scoped `code-review`; separate Standards and Spec axes pass with zero unresolved finding after nine review-driven RED/GREEN repairs and two structural consolidations.
- Completed phase: Issue #12 `verification-before-completion`; every required pre-commit repository gate and installed 100-case fixture create/replay check passes with fresh evidence.
- Completed phase: PR #26 passed its required Python quality check, squash-merged Issue #12 into `develop` as `eb252e4c32d1ea2167f0cc31371423541dc3b315`, and Issue #12 is closed.
- Completed phase: Issue #13 implementation with `test-driven-development`; comparison contracts, compatibility and confound checks, ordered release gates, JSON/Parquet evidence, DuckDB rebuild, deterministic replay, and PASS/FAIL/INVALID fixture paths are implemented and documented.
- Completed phase: Issue #13 ticket-scoped `code-review`; separate Standards and Spec axes pass with zero unresolved finding after review-driven storage-boundary repair and fail-closed comparison-contract RED/GREEN cycles.
- Completed phase: Issue #13 `verification-before-completion`; every required environment, quality, full-regression, installed-CLI comparison/replay, deterministic-digest, Parquet, DuckDB, diff, branch-base, and upstream-state check passes with fresh evidence.
- Completed phase: the authorized Issue #13 local Lore commit was created and its clean committed state passed every required repository and installed-CLI verification.
- Completed phase: Lore implementation commit `2ac9508fd3ec39b94ecbecd6c9f03adb41e64ac1` was pushed to `origin/feat/issue-13-experiment-comparison`; review-ready [PR #27](https://github.com/DHChe/braincrew-datateam-portfolio/pull/27) was opened against `develop`, and its first Python quality gate passed with remote merge state `CLEAN` and no review comment or change request.
- Completed phase: PR #27 review-driven TDD repair; the confirmed shallow-freeze defect was observed RED and repaired GREEN, while the non-finite-decimal suggestion was disproved against the locked Pydantic behavior and retained as a regression check.
- Completed phase: PR #27 repair re-review; separate Standards and Spec axes report zero unresolved finding.
- Completed phase: PR #27 review-repair `verification-before-completion`; every repository gate and installed-CLI PASS/FAIL/INVALID comparison, replay, deterministic-digest, and DuckDB-cache check passes with fresh evidence.
- Completed phase: review-repair commit `0bd3dc1dd067aa162342a65641a14341db237228` was pushed without force and its replacement Python quality gate passed.
- Completed phase: PR #27 expanded six-thread review-driven TDD repair; all four additional confirmed defects and the single-axis overflow preservation defect were observed RED before minimal GREEN.
- Completed phase: PR #27 expanded repair re-review; separate Standards and Spec axes report zero unresolved finding.
- Completed phase: PR #27 expanded repair `verification-before-completion`; every required repository gate and installed-CLI PASS/FAIL/INVALID comparison, replay, deterministic-digest, and DuckDB-cache check passes with fresh evidence.
- Completed phase: expanded review-repair Lore commit `f802bf815b758557d84fbcc240af21b6ab38ed0d` was pushed without force; local, remote, and PR heads match; its replacement Python quality gate passed; all six review threads have evidence-backed replies and are resolved; GitHub reports merge state `CLEAN`.
- Completed phase: PR #27 passed its required Python quality gate and squash-merged Issue #13 into `develop` as `52e85ecc303291e0145ac0867c807e9579b04800`; GitHub reports PR #27 `MERGED` and Issue #13 `CLOSED/COMPLETED`.
- Completed phase: fetched `origin/develop` points exactly to `52e85ecc303291e0145ac0867c807e9579b04800`; the Issue #13 local branch, remote branch, and dedicated worktree are absent.
- Completed phase: Issue #14 passed review and verification, and PR #28 merged into `develop` as `e33de765dc54ac76159f249525456d5ab4e63667`.
- Completed prerequisite: AX Issue #33 is `CLOSED/COMPLETED`; AX PR #39 merged the reviewed generic seed-pack dry-run and exact schema bytes as `47673b83a9fb431f2bad550781db18c7bee8b67e`.
- Completed predecessor: Braincrew PR #39 merged Issue #31 into `develop` as `df5891378732a653511e7fa37aae53ac56883672`; Issue #31 is `CLOSED/COMPLETED`.
- Completed predecessor: Braincrew PR #40 merged Issue #32 into `develop` as `9502f21e10ece832cd2c1bc369d2b5d0f9f1fb94`; Issue #32 is `CLOSED/COMPLETED`, cleanup is complete, and it no longer carries `ready-for-agent`.
- Completed predecessor: Braincrew PR #41 merged Issue #33 into `develop` as `fdbb732ee05a9de5270c91a82f0930da0413107b`; Issue #33 is `CLOSED/COMPLETED`, has no `ready-for-agent`, and its local branch, remote branch, and dedicated worktree are absent.
- Completed predecessor: Braincrew PR #43 merged Issue #42 into `develop` as `93c8e8dabab855b7f2f700df73cd04ce38995f29`; Issue #42 is `CLOSED/COMPLETED` and no longer carries `ready-for-agent`.
- Cleanup checkpoint: Issue #42's dedicated worktree and local/remote feature branches still exist and are clean. Cleanup is therefore pending rather than complete; no cleanup mutation is part of Issue #34.
- Completed predecessor: Braincrew PR #44 merged Issue #34 into `develop` as `67d7c104757f60194e59df20240ac47f8be9c027`; Issue #34 is `CLOSED/COMPLETED`, has no `ready-for-agent`, and its dedicated worktree plus local/remote feature branches are removed.
- Completed predecessor: PR #49 merged Issue #47 into `develop` as `4d80b9b8950f4d7356a9aa9806f492ae79126dab`; required Python and frontend checks succeeded, `develop` resolves to that merge commit, and Issue #47 is `CLOSED`.
- Current frontier: Issue #35 is `CLOSED/COMPLETED`; Issue #46 is `CLOSED` after PR #48; Issue #47 is `CLOSED` after PR #49. Issue #36 authoring, manual review, sealing, and replay are complete on `feat/issue-36-independent-corpus-authoring`; the open issue carries `ready-for-agent` and now stops at its Git Lifecycle Proposal Gate. Qualification remains unstarted and belongs to the later Issue #37 lane. #46 and #47 are native sub-issues of #30. Draft PR #29 and `feat/issue-15-live-verification` remain untouched and read only.
- Issue #36 execution evidence: clean execution SHA `8e669db46b698b8791739feee910ba1b561a0936`; authorization digest `sha256:9eabf4fff6de5bf54065c8d4bd657eda4ebeb06c630ad45f53fe41c36457a1a7`; authoring-tool digest `sha256:8ba07d07d35ac359a04f0d2f2e3b30062569b3f883e2d6a16e918aa218af6d3e`; independence receipt digest `sha256:28a22cb6f1c0d35ced80d43dc727699cecae388a8012f6a292d618719371cf7f`; and 14 exact source digests were bound without source text.
- Manual-review and sealing evidence: `DHChe-corpus-provenance-reviewer` approved all 14 exact source digests on `2026-07-23` in `Asia/Seoul`; sealed content digest `sha256:5f0c254b3dc64b23470029b1004106dc078a9602062da8fa8041623bf91fb7e4`, provenance digest `sha256:eb43fc824cd54bf10e8805b5fdeb1915bcaac368cb458ce8981a481cd7d4fce1`, and sealing receipt digest `sha256:bc508b6001facbef67bacd7e0c1d4d5123f04bc1e33d2849b5e7d455183df62b` reproduced through one successful replay.
- Clean baseline evidence: frozen sync, Ruff format/lint, strict mypy, full pytest, `git diff --check`, and clean status passed before the first Issue #47 RED.
- RED/GREEN evidence: the authoring capability test first failed because the sandbox exposed `ax-synthetic-seed-pack-v1` instead of the content schema. Six provenance-sidecar contract cases then failed because sealing allowed missing evidence and had no sidecar CLI, v2 receipt, or replay binding. Minimal GREEN exposes only the content schema plus its pinned digest, requires an external immutable canonical sidecar, creates `corpus-sealing-receipt-v2`, and replays v2 sidecar bindings while retaining v1 receipt replay.
- Contract evidence: the 10,680-byte brief remains frozen at `sha256:121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3`. The content schema governs staged `corpus-manifest.json` authoring; the pack schema is post-qualification only. The sidecar binds the sealed digest plus every source identity/digest to synthetic origin, owner, CC0 assignment, reviewer/date/timezone, approved decision, and canonical digest; reviewer identity must differ from the authoring owner. Missing, pending, mismatched, mutable sealing input, tampered, symlinked, or staging-contained evidence fails closed. Replay validates canonical bytes and digest independent of normalized filesystem write bits.
- Selected source-order contract: **source-first evaluation freeze**.
- Rejected alternative: pre-existing, evaluation-independent exact source bytes or generator.
- Reason: no independently versioned, provenance-bearing artifact predates the evaluation-specific freeze.
- Failure mode: frozen evaluation identifiers, digests, or qualification feedback reach authoring.
- `braincrew-evaluation-dataset@2.0.0` remains immutable and is not a target for authoring or qualification in this lane.
- A successor dataset version greater than `2.0.0` is required after the new corpus version is sealed.
- The successor qualification receipt must bind that successor dataset version and digest to the unchanged sealed corpus digest.
- Qualification remains read-only and cannot return feedback, identifiers, or digests to authoring.
- Leakage-review evidence: fresh independent author and reviewer contexts used only the approved non-evaluation inputs. Reviewer `/root/sanitized_blind_reviewer` was denied all tests, prior digests, prior review evidence, and downstream documents; it approved the exact brief bytes above with zero material findings. The adjacent digest declaration and durable review record match those committed bytes.
- Scope lock: Issue #47 changes only the authoring schema pin, provenance-sidecar sealing/replay contract, deterministic fixture tests, and synchronized design/status/interview records. Corpus source bytes, actual Issue #36 authoring or sealing, qualification, preflight, experiment, AX/DB/service calls, dependencies, PR #29, and `feat/issue-15-live-verification` remain excluded.
- Review evidence: two ticket-scoped reviewers found the initial v2 sealed-corpus qualification regression: `provenance-review.json` was correctly allowlisted for replay but not the initial qualification revalidation. The acceptance test first failed with `CORPUS_PACK_SCHEMA_INVALID`; the minimal allowlist repair then passed it together with all six provenance-sidecar contracts (`7 passed`). Both reviewers re-reviewed that repair with zero remaining blockers.
- PR #49 review repair: three new regression tests first proved that a self-reviewed sidecar sealed, replay rejected a byte-identical sidecar after write-bit normalization, and the canonical design still instructed v1/pack-schema behavior. Minimal GREEN rejects identical author/reviewer identities, limits read-only enforcement to external sealing input, replays sealed canonical bytes independent of normalized filesystem write bits, and synchronizes the canonical design. Focused contract/workflow tests passed `43`, and the full repository suite passed `320`.
- Data-creation proposal gate: **APPROVED_FOR_NEW_SESSION**.
- Approval baseline: `5cec187af3e2d5b95b35f6e6f81fee55a73d5409`.
- The execution SHA must be the clean `origin/develop` commit containing this approval record,
  descend from that baseline, and reproduce approved brief digest
  `sha256:121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3`.
- Authoring owner: `codex-issue-36-authoring-agent`.
- Manual provenance reviewer: `DHChe-corpus-provenance-reviewer`. This human approval authority
  must differ from the authoring owner.
- External lifecycle root: `/Users/astralpig/braincrew-issue-36-authoring`.
- Exact lifecycle targets are
  `/Users/astralpig/braincrew-issue-36-authoring/authorization/data-creation-authorization.json`,
  `/Users/astralpig/braincrew-issue-36-authoring/tool/author-corpus`, empty
  `/Users/astralpig/braincrew-issue-36-authoring/staging`, absent
  `/Users/astralpig/braincrew-issue-36-authoring/receipts/authoring-independence-receipt.json`, absent
  `/Users/astralpig/braincrew-issue-36-authoring/review/provenance-review.json`, and absent
  `/Users/astralpig/braincrew-issue-36-authoring/sealed`. The staging target must be empty; all
  other create-only targets must be absent. All targets must be outside the repository and must not
  be symbolic links.
- Create-only authorization record:
  `/Users/astralpig/braincrew-issue-36-authoring/authorization/data-creation-authorization.json`
  uses schema `corpus-data-creation-authorization-v1`. It binds approval authority `DHChe`, the
  exact execution SHA, authoring-tool SHA-256, four exact input digests, all lifecycle target paths,
  authoring owner, manual reviewer, and its own canonical digest. The authorization record is
  create-only and must exist before authoring. Launch must reject any authorization-record
  mismatch.
- Allowed authoring inputs are exactly
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
  credentials, network, database, AX, and qualification feedback remain denied.
- No source byte may be created before the clean execution SHA and external authoring tool SHA-256
  are recorded and revalidated. The new-session agent may pin those dynamic values under the
  user's delegated approval without reopening the policy decision.
- Author, then review, then seal, then replay. The independence receipt and provenance sidecar are
  create-only; sealing starts only after the manual reviewer approves every exact source digest;
  qualification remains a later ticket.
- No automatic retry, in-place repair, overwrite, alternate input, feedback-driven second pass, or
  cleanup after failure is authorized. A dirty or wrong SHA, digest drift, denied capability
  success, non-empty staging, existing target, unsupported sandbox, nonzero authoring exit, empty
  or invalid output, manual rejection, sidecar mismatch, sealing failure, or replay failure stops
  the lifecycle immediately.
- RED contract tests must first prove the entry pins, restricted inputs, create-only targets,
  distinct owner/reviewer authority, exact order, and every stop condition before any source-byte
  authoring attempt.
- Completed phase: Issue #36 external authoring, manual review, sealing, and replay.
- Completed gate: **Issue #53 successor dataset review gate.** The source-first successor candidate
  `braincrew-evaluation-dataset@3.0.0` exists as local uncommitted bytes with integrated digest
  `sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d`. Its card and
  `docs/reviews/2026-07-23-issue-53-successor-dataset-review.md` checklist now read `FROZEN` and
  `APPROVED`, respectively. All eight checklist items are checked and `Decision: APPROVED` is
  recorded. The freeze authority is
  `DHChe-successor-dataset-reviewer`, which is distinct from the authoring owner and from
  `DHChe-corpus-provenance-reviewer`.
- Completed verification: independent Standards review found zero actionable findings. Independent
  Spec review found two documentation-contract defects; both were reproduced by a new failing
  contract test and repaired before all 22 successor tests and all 342 repository tests passed.
- Completed phase: **Issue #37 read-only successor qualification.**
  Issue #37 actual qualification: **SUCCEEDED_ONCE**. The create-only
  `corpus-qualification-receipt-v2` and
  `braincrew-evaluation-dataset-3.0.0` import manifest bind the exact sealed corpus and frozen
  dataset bytes. Replay, redaction, sealed-tree immutability, and historical receipt-v1
  compatibility checks pass.
- Receipt logical digest: `sha256:c564b1442c135fef5d5430b313914951e2b5ab4cc7e0fd0bbbdefb0b928ea6ce`
- Qualification receipt file digest: `sha256:8843c87597db779ece932585445bae9dbdf9b5f26f4f81a7b9d069a1699968ed`
- Import logical digest: `sha256:9df8dbd212c6e0253b3c58feb392869bffb226d816805ee7ed166072596003bd`
- Import manifest file digest: `sha256:b1899d6be6017a2485d93c67066023a87f8aaa78b0b63012fb9f8d8a040f3821`
- Exact inputs: sealed content
  `sha256:5f0c254b3dc64b23470029b1004106dc078a9602062da8fa8041623bf91fb7e4`;
  dataset integrated digest
  `sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d`.
  No retry, repair, AX import, database, service, snapshot, preflight, or experiment execution was
  performed.
- Active implementation: **Issue #56 AX-canonical import publication bytes.** Braincrew PR #55's
  import manifest has the correct logical identity but a trailing line feed that exact AX PR #42
  rejects. Newly created import manifests now use newline-free canonical JSON; qualification
  receipts retain canonical JSON plus one trailing line feed.
- Preserved identities: receipt logical
  `sha256:c564b1442c135fef5d5430b313914951e2b5ab4cc7e0fd0bbbdefb0b928ea6ce`,
  receipt file
  `sha256:8843c87597db779ece932585445bae9dbdf9b5f26f4f81a7b9d069a1699968ed`, and
  import logical
  `sha256:9df8dbd212c6e0253b3c58feb392869bffb226d816805ee7ed166072596003bd`.
  The import file digest changes only from historical PR #55
  `sha256:b1899d6be6017a2485d93c67066023a87f8aaa78b0b63012fb9f8d8a040f3821`
  to AX-canonical
  `sha256:e00c7036bd67f93347957215fddc4185a18eb2e62e90bfb58657f0b7598f20ac`.
- Compatibility boundary: receipt-v1 and both the historical PR #55 import bytes and new exact
  canonical import bytes replay successfully. Other whitespace and non-canonical representations
  fail closed. Exact AX SHA `e25f333b55fca34118a954a17e5e0cd88dc7ea39` accepted the new bytes
  read only with 14 sources and 11,528 total source bytes; no database or provider was available.
- Completed phase: Issue #56 was merged into `develop` as
  `508c8674ea055c024d76e0535d5d7e27a068fc50` through PR #57, releasing the AX-canonical import
  bytes for operational use.
- Completed phase: **AX Issue #37 sealed-pack import applied once** into the local AX PostgreSQL
  at AX SHA `e25f333b55fca34118a954a17e5e0cd88dc7ea39`. Steps 1 through 6 of the AX importer
  design's operational sequence are complete; steps 7 through 9 are deferred with a recorded
  reason.
- Completed phase: **AX Issue #37 follow-up scope lock.** The canonical decision
  `docs/decisions/2026-07-24-ax-evaluation-principal-and-parse-restoration-scope-lock.md`
  records two dependent AX contracts: AX-A provisions one deterministic target-tenant local/test
  evaluation subject, and AX-B re-provisions the six reviewed parse sources through the normal
  attachment lifecycle. It preserves `validated_evaluation_principal`, tenant isolation, and
  Braincrew Issue #38 as a receipt consumer.
- Completed phase: the two locked contracts were published as
  [AX-A Issue #44](https://github.com/DHChe/AX_portfolio/issues/44) and dependent
  [AX-B Issue #45](https://github.com/DHChe/AX_portfolio/issues/45).
  [Braincrew Issue #38](https://github.com/DHChe/braincrew-datateam-portfolio/issues/38) now records
  both blockers and remains a receipt consumer only.
- Review result: **[Braincrew PR #59](https://github.com/DHChe/braincrew-datateam-portfolio/pull/59)
  passed the two-axis documentation review and merged into `develop` as
  `95826ee95f0ac9a8bd84eed149dff47dc834aa47`.** AX-A later passed its required checks and merged;
  the active delivery gate is now the separate AX-B Issue #45 fresh-session handoff. HTTP boundary
  verification, the strict parse observations, and the Braincrew preflight handoff did not run, so
  `braincrew_preflight_ready` is `false` and Braincrew Issue #38 remains blocked. The recorded
  causes are both the principal/tenant binding conflict and absent live parse state:
  SELECT-only review found zero users in the imported tenant and zero rows in
  `thread_attachments` plus `attachment_extractions`. AX's
  `validated_evaluation_principal` requires one query to satisfy `Tenant.id`, `User.id`, and
  `User.is_active` together, while the Braincrew live preflight pins a fixed owner user that
  belongs to a different tenant and six stale attachment UUIDs. These are deferred structural and
  state dependencies, not a failed import.
- Completed local phase: **AX-A Issue #44 `test-driven-development` and independent code
  review.** The implementation keeps the fixed evaluation-principal UUID
  `26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe`, creates only one active target-tenant `User`, and does
  not add `Role`/`UserRole` persistence, an `AuditEvent`, a migration, or evaluation route/auth
  changes. The final review repairs reserve the receipt path before mutation, require exact locked
  replay fields and JSON types, recover only an exact concurrent insert, bind Git evidence to the
  AX checkout, and validate the stored user both before and after the commit attempt. A
  pre-commit failure rolls back and removes the reservation; an unprovable commit or post-commit
  confirmation retains the empty reserved path as evidence. Fresh verification passed `63`
  targeted tests and the full AX backend suite (`1553 passed, 75 skipped`), plus changed-file
  format, full Ruff lint, compile, and whitespace checks. The broad format baseline still reports
  `62` unrelated pre-existing files. No live apply or database/service/container/credential
  operation occurred.
- Completed Git integration: the reviewed AX-A change was committed as
  original implementation `99c6300e02498f18763806002c748dd58fe64c04`, demo-label repair
  `6dc396638787a87f681dac77992deb0760c73a33`, and final fail-closed repair
  `6499e1b42730f72bf03db769a3f95cb186f1fb07`. All five required checks passed, six review threads
  were resolved with evidence, and
  [AX PR #46](https://github.com/DHChe/AX_portfolio/pull/46) squash-merged into `develop` as
  `fe16c0cedc1e64856d9e107e111665d0ba2e444d`. Issue #44 closed automatically.
- Security status: `OPENAI_API_KEY` rotation is **RESOLVED** by user confirmation. No secret was
  inspected or retained during the scope-lock work.
- Next workflow action: **decide whether to authorize the live AX-A then AX-B apply, on an accurate
  statement of what is now proven and what is not.** The eight preconditions recorded in section 7 of
  the independent recovery analysis are **all resolved**, so the basis for the earlier
  `NOT SAFE YET` verdict is gone. That verdict rested on two blockers, and both are closed: the
  missing post-import/pre-A recovery point now exists and has been rehearsed, and the scope lock's
  ordered AX-B dry-run step — which the merged tool could not perform — is implemented by AX Issue
  #48. **This is not the same as declaring the operation safe.** Two items remain **explicitly
  unproven** and must be carried into any authorization decision:
  1. **Restore into the LIVE cluster.** The rehearsal ran against a fresh, empty target. Replaying
     `globals.sql` against the live cluster is *not* the operation that was proven: the live cluster
     already holds all three roles, so every `CREATE ROLE` would conflict. Dropping `ax` also
     requires zero active connections and a session connected to another database.
  2. **Blob recovery.** No archive contains blobs. This is trivial today because the volume is
     empty — and it becomes **permanently non-reconstructable once AX-B runs**, because the blob key
     is a random UUID whose only mapping is the `thread_attachments` row.
  The live apply remains a distinct, separately authorized action and **must not** be started from
  this file. Braincrew Issue #38 stays blocked and starts only after both sanitized AX receipts and
  live HTTP observations exist and pass independent review; until then `braincrew_preflight_ready`
  is `false` and no `READY` artifact may be published.

### Copy-ready fresh-session handoff — AX-B Issue #45

AX PR #46 is merged, Issue #44 is closed, and this status file records the exact AX-A merge SHA
`fe16c0cedc1e64856d9e107e111665d0ba2e444d`. AX-B is a new bounded implementation ticket, so fresh
context reduces accidental reuse of AX-A assumptions and keeps live operational execution outside
code completion.

**This prompt is spent and is retained only as the historical record of what was dispatched.** The
work it launched is complete: AX PR #47 squash-merged as
`cf3ae42915833778bc9838780b7d21a5c89327ec` and Issue #45 is closed. Do not re-dispatch it as
written. One instruction inside it was superseded during execution — the six sources are uploaded as
**two bounded requests of five and one** into one target-owned conversation, per
[the request-split decision](../decisions/2026-07-25-ax-b-bounded-upload-request-split.md) — and the
published Issue #45 body now carries that correction directly:

```text
$test-driven-development

Work in repository DHChe/AX_portfolio at /Users/astralpig/portfolio/AX_portfolio. Read AGENTS.md,
fetch origin, verify that origin/develop contains the recorded AX-A merge SHA and is clean, then
create feat/issue-45-evaluation-parse-sources from that verified base.

Implement https://github.com/DHChe/AX_portfolio/issues/45 exactly. Required sources are AX
AGENTS.md; Issue #45 and its dependency Issue #44; the merged AX-A provisioning and receipt code;
the existing upload, scan/extract, approval, materialization, strict parse-observation, and corpus
identity paths; backend/tests/integration/test_evaluation_api.py; and
docs/decisions/2026-07-24-ax-evaluation-principal-and-parse-restoration-scope-lock.md in the
Braincrew repository.

In scope: local/test-only ax-evaluation-parse-sources orchestration,
ax-evaluation-parse-source-handoff-v1, the exact six reviewed .txt names and SHA-256 digests from
Issue #45, one target-owned conversation, six AX-generated attachment IDs, exact utf8-text /
stdlib-1 extraction, company_reference / hr_only / policy-version-1 approval, fake-deterministic
materialization, expected 20/83/83/166 counts, six strict HRPractitioner parse responses, three
singleton-role corpus identities, sanitized create-only replay, and contract tests.

Preserve tenant/owner isolation, the merged AX-A subject, request-scoped singleton x-ax-roles,
existing HTTP/services/jobs as the only mutation boundary, and the distinction between external
reviewed_synthetic provenance and AX tenant-upload synthetic=false, demo_company=false,
corpus_mode=tenant classification.

Out of scope: direct table writes, caller-forced attachment IDs, migrations, parser/chunker/
visibility/provider/auth changes, provenance-flag rewrites, corpus re-import, automatic cleanup or
restore, live operational execution, Braincrew scoring or READY, credentials, and remote Git
actions. Do not access a live database, service, container, blob store, provider, or secret during
code completion.

Follow RED-GREEN-REFACTOR and record the expected failing reason before minimal implementation.
Run:
uv lock --project backend --check
uv sync --project backend --locked --group dev
uv run --project backend ruff format --check backend/src/ax_engine/evaluation backend/tests
uv run --project backend ruff check backend/src backend/tests
uv run --project backend python -m compileall -q backend/src backend/tests backend/alembic
uv run --project backend pytest -q backend/tests/unit/test_evaluation_parse_source_bundle.py backend/tests/integration/test_evaluation_parse_source_cli.py backend/tests/integration/test_evaluation_parse_source_lifecycle.py backend/tests/integration/test_evaluation_api.py
uv run --project backend pytest -q backend/tests
git diff --check
git status --short

Synchronize any locked design decision with the Braincrew decision and interview defense dossier.
Do not claim live attachment, corpus identity, parse observation, snapshot recovery, or Braincrew
READY. Request independent code review after local GREEN. Stop at the AX Git Lifecycle Proposal
Gate with no commit, push, PR, merge, live apply, checkpoint, or operational receipt. Report
changed files, RED/GREEN evidence, verification, remaining risks, and the exact reviewed HEAD SHA.
```

이 프롬프트는 먼저 AX-A 병합 SHA를 기저로 확인해 의존성을 고정하고, 여섯 파일의 입력
계약과 정상 AX 수명주기만 구현 범위에 둔다. 동시에 live DB·blob·worker 실행과 자동 복구를
금지해 코드 완성과 운영 적용을 분리한다. 사용자가 해야 할 일은 AX-A 병합 기록 뒤 새
세션을 여는 것뿐이며, 다음 에이전트는 로컬 TDD·독립 리뷰·검증을 자동 수행하고 Git
수명주기 제안 게이트에서 멈춘다. 완료 조건은 Issue #45 계약 테스트와 전체 AX 게이트가
통과하고 독립 리뷰 차단점이 0개인 상태다. 그 다음 단계는 별도 승인된 커밋·PR이며,
live 운영 적용이나 Braincrew Issue #38 시작이 아니다.

## Transition history

### 2026-08-02 (#134) — a re-pin records the whole reviewed source diff, not a copied conclusion

- **Cycle 189 moved the under-test AX pin from `3bb27f8` to `5b0f5f2` locally, with the packaged
  `ax-http-v1.yaml` contract moved in the same change.** The production guard still rejects a configured
  SHA that differs from the packaged contract; the four historical literal witnesses and the fifth
  witness added by #131 remain literal, independent checks rather than imports of `PINNED_AX_SHA`.
- **The receipt-continuity warrant was re-argued from `d7930978` to `5b0f5f2`.** The reviewed production
  diff has three paths: `answers/contracts.py`, `answers/service.py`, and `attachments/jobs.py`; AX test
  paths are deliberately excluded. `jobs.py` adds a pure heading extractor and writes its result only
  while creating an absent `AttachmentExtraction`. It neither updates an existing extraction nor changes
  approval, materialization, corpus, migration, seed, principal, or receipt-production state. The
  `provisioning_state_affected=False` conclusion is bounded to the existing receipt-backed provisioning
  state; future newly extracted attachments intentionally gain a headings fact.
- **The answer-path census was re-enumerated against the real AX file.** `answers/service.py` has the
  same SHA-256 at both commits (`972f15c9d68da856c163d830fdef849d915d05bb08f83dd642bade37a20cd47d`),
  and all named metadata/template call sites remain the same. Its commit identity and enumeration date
  now name `5b0f5f2` and `2026-08-02`; this hand check is necessary because the suite does not read the
  AX checkout.
- **Sequential validation passed.** Ruff format checked 72 files, Ruff lint passed, mypy found no issue
  in 72 source files, the full suite reported `608 passed`, and the fixture gate reported `11 passed`.
  Moving the source pin alone made the suite `171 failed, 437 passed`; an isolated production-adapter
  construction raised `configured AX SHA does not match ax-http-v1 contract`. Restoring the source
  reproduced its pre-mutation SHA-256. Reverting only the warrant to its two old paths made the exact
  receipt-binding assertion fail (`1 failed, 607 passed`), then restoring it reproduced the same SHA-256.
  No AX runtime, attachment, provider, live capture, evaluation, comparison, container operation,
  `evidence/` edit, or Git write was performed in this cycle. The next action is independent Cycle 190
  review; only after that and explicit owner authorization does the Git Lifecycle Proposal Gate apply.

### 2026-08-02 (#15, #131, AX #63) — the live experiment ran, said "no difference", and refused to score itself

- **Both live runs executed against AX `3bb27f8`.** Preflight `READY` with 0 blockers; baseline
  (`evidence_limit=3`) and candidate (`evidence_limit=5`), 24 live cases each, exit 0. The runtime was
  started and returned container-by-container to its prior state. Artifacts are outside the repository
  in `/Users/astralpig/ax-live-verification-evidence/run-2026-08-02/`, unreviewed for publication.
- **The comparison's answer is "no difference".** The two runs differ only in `evidence_limit`. Every
  one of 15 grounded cases reached an identical answer-path verdict, the same single case succeeded
  (`VA-008`), all 9 retrieval results were identical, and 1 of 15 answers differed textually.
- **The historical discard label was misleading, and this corrects it.** All 13 discards carry
  `citation_contract_violation=True, unsafe_provider_output=False`. **Not one is a safety block.** The
  pre-split label read as a guardrail firing; it was the answer failing its own citation contract.
  This answers [#125](https://github.com/DHChe/braincrew-datateam-portfolio/issues/125).
- **The run is `INVALID` and that is the guard working.** 11 of 30 scored; the six Verification parsing
  cases refuse with `PARSE_OBSERVATION_DOCUMENT_IDENTITY_MISMATCH`, the #118 guard declining a v1
  bundle against v3 documents. `build-run-summary` then refuses, so no comparison artifact exists —
  acceptance criterion 3 producing INVALID rather than a positive claim.
- **AX #63 merged as `5b0f5f2` under an owner-approved scope exception.** Extraction now records
  markdown headings. Verified independently: the same function reproduces the expected headings for
  **20 of 20** parsing cases from document text alone, and live it returned exactly the four headings
  dataset v3 expects for `demo-pay-policy-005`.
- **Measured, and it is what saves the 48 provider calls: an unapproved attachment does not move the
  corpus digest.** 130 / 166 / 166 for Employee, Executive and HRPractitioner — unchanged before
  upload, after upload, after the AX change, and after deleting the test attachments. The digest covers
  embedded `seed_vector_records`, created only at materialization, which only `approve` triggers.
  **The 2026-08-02 captures survive; no re-capture is needed.**
- **Two orchestrator false alarms, both caught by re-measuring, both reported to the owner before
  correction.** First: six corpus documents were reported as newly exposed by publication; a
  title-wise search found all 13 already tracked. Second: identical Executive and HRPractitioner
  digests were reported as a defect; the count had spanned two tenants while the service filters on
  one. Both share a shape — aggregating without the scoping condition. A third, milder instance
  followed: a repository status check run from the wrong working directory.
- **What blocks the next step.** Braincrew pins AX `3bb27f8`; AX head is `5b0f5f2`. Capturing parsing
  at the new commit while the existing observations sit at the old one would place two SUT commits in
  one run, which #15 forbids. A re-pin comes first, in the shape of #121. Attachments extracted before
  AX #63 return empty headings permanently — there is no re-extract route — so the six v3 documents
  must be uploaded fresh. `evidence_spans` remains unmeasured and is the next gate after the re-pin.


### 2026-08-02 (#131) — live parser observations need an independently bound document, and the current runtime has none to bind

- **[Issue #131](https://github.com/DHChe/braincrew-datateam-portfolio/issues/131) is implemented
  locally and remains uncommitted.** The new `capture-live-parsing` command uses AX's existing
  read-only `GET /v1/evaluation/attachments/{attachment_id}/parse-observation` contract for exactly
  the six dataset-v3 Verification parsing cases. Its response converter creates a
  `parsing-observation-v1` batch with adapter version `ax-sut-http-v1`; headings, metadata, table,
  list, spans, parser name, and parser version come from AX's response, never `case.expected`.
- **The artifact has a separate truth boundary.** `live-parsing-capture-v1` binds the frozen dataset,
  the six document-to-attachment identities, the SUT state warrant, the observed Evaluation Plane
  dirty flag, and a create-only sibling observation digest. It does not change the existing 24 live /
  6 fixture `capture-live-experiment` partition or widen the fixture-only
  `ParsingAdapterProvenance`; `af18c5e`'s rejection of a fixture falsely labelled live still applies
  to that old artifact shape.
- **No live parsing artifact was produced.** Read-only runtime inspection found only the older six
  `synthetic-rule-015` through `synthetic-rule-020` approved attachments. None corresponds to v3's
  `demo-terms-guide-002` through `demo-conduct-policy-007` documents, and the endpoint accepts only
  attachment IDs. Creating a matching attachment or altering runtime data is prohibited for this
  cycle, so the capture and reuse-only baseline/candidate re-evaluation remain blocked by an input
  precondition rather than replaced with a fixture or a fabricated mapping.
- **The new guard is executable.** The first acceptance test was RED before the converter existed;
  its GREEN form poisons all six answer-key headings and metadata and still observes only AX-response
  values through exactly six GET parse calls. A second test supplies another frozen document and
  confirms refusal. A CLI test fixes receipt-derived principal identity, a versioned attachment map,
  and truthful Evaluation Plane dirtiness. No answer/retrieval request, provider invocation,
  container-state command, `evidence/` write, Git write, dataset-v3 change, or
  `parsing-quality-v2` change occurred.
- **Next.** An explicitly authorized AX data-provisioning step must make the six v3 documents approved
  attachments and issue the corresponding versioned mapping. Only then may this command capture the
  six parser observations and re-evaluate the already-stored 24 retrieval/grounded observations; a
  resulting `INVALID` decision remains an honest terminal measurement, not a reason to widen scope.

### 2026-08-02 (#16) — reviewed stored-live evidence becomes a clean replay boundary

- **The owner-authorized publication is implemented locally and remains uncommitted.** Exactly four
  reviewed 2026-07-31 files now live under `evidence/`: a capture manifest with its two sibling
  observation files, plus the baseline evaluation artifact. The manifest's bare-file references decide
  the sibling layout. SHA-256 compared every destination directly to the read-only source; no JSON was
  reformatted, reserialized, or reindented.
- **The existing replay path now has a literal regression guard.** The new Issue #6 acceptance test
  replays the capture to `sha256:775a85295fb5db2f9cfb6e1aa5504206ea3b629a032452932ca685a7ab1a5049`
  with 15 grounded and 9 retrieval cases, and the evaluation artifact to
  `sha256:9435c9daaa21e4e3129dad997a9dff79717452a2c1f112acfd7a95ba3e80f6fb` with `run_state`
  `INVALID`. It first failed while the artifacts were absent; changing one expected digit later made the
  named test fail, and changing one byte in a temporary artifact copy made replay refuse its digest.
- **Clean-container evidence now includes the stored artifacts.** Neither `.gitignore` nor
  `.dockerignore` matches `evidence/`. The Braincrew-only `--network none` image built successfully and
  reported Ruff and mypy clean, `596 passed, 3 skipped`, then `11 passed` for the Issue #6 file. This
  included no Docker Compose call, AX-container contact, host mount, or live SUT/provider run.
- **Issue #16 moves only as far as the evidence permits.** Clean stored-artifact replay, byte identity,
  the replay-versus-rerun documentation boundary, and the owner-approved four-file publication scope
  are met locally. Hosted CI remains unverified until a pull request runs it. Issue #15 remains open, so
  the rule that a fresh live rerun is not byte-identical remains a documentation boundary rather than a
  new live-execution demonstration. The other 33 source-directory files remain outside the reviewed
  publication scope and were neither copied nor quoted.
- **Three statements below, under this same Transition history, now read as stale and are deliberately
  not corrected.** The earlier 2026-08-02 (#16) entry and the 2026-07-31 record describe the published
  live artifacts as owner-held outside the repository, which stopped being true when the owner
  authorised publication later on 2026-08-02. This section is append-only; editing a dated entry so it
  matches a later state would falsify the record. The correction of record is this entry and
  [the published live evidence replay decision](../decisions/2026-08-02-published-live-evidence-replay.md).

### 2026-08-02 (#16) — a clean container verifies fixtures while the published-live boundary stays explicit

- **Issue #16 remains open for its published-live-artifact criteria.** Issues #13 and #14 are closed,
  but #15 is open; no live run, AX service, or provider was started here. The owner-held published live
  artifacts remain outside this repository pending a publication decision and were neither inspected,
  copied, nor added to the build context.
- **The unblocked fixture path is implemented locally.** A Dockerfile pins the Python 3.12 base and `uv`,
  synchronizes `uv.lock` with `--frozen --all-groups`, and runs Python quality gates plus the Issue #6
  fixture benchmark without a host mount or runtime network. `.dockerignore` excludes Git metadata,
  local environment files, Python caches and bytecode, and dashboard `.next`/`out` build outputs at every
  depth. The external-artifact pattern is defensive only: that directory lies outside the repository, so
  nothing was excluded on its account.
- **CI now names what it can actually see.** The Python job separates the full suite, Issue #6 fixture
  benchmark, and fixture replay digest check; a dedicated container job runs the same fixture-only path;
  the existing frontend job retains static-dashboard checks; and Gitleaks scans tracked history. These
  are CI definitions, not claims that a GitHub Actions run has already passed. Review noted that the
  Gitleaks action is the one new job carrying an external condition — `gitleaks-action@v2` requires a
  `GITLEAKS_LICENSE` for organisation-owned repositories — so its first pull-request run is what
  establishes whether it can run here at all.
- **Validation is in progress.** The clean container must build and pass its isolated gates without a
  privilege or security-policy exception. On Docker's default Linux policy, the three Bubblewrap-dependent
  authoring-boundary tests skip because user namespaces are unavailable; installing Bubblewrap makes them
  fail rather than making the container more complete. The workflow YAML remains unverified until a pull
  request runs. The decision record and defense card D30 distinguish stored-artifact replay from a fresh
  live rerun and preserve the owner decision boundary.
- **Completion update, measured 2026-08-02.**
  `docker build --no-cache --tag braincrew-evaluation-fixture:cycle180-final .` succeeded, then
  `docker run --rm --network none braincrew-evaluation-fixture:cycle180-final` completed Ruff format
  and check, mypy, `595 passed, 3 skipped`, and the ten-test Issue #6 fixture gate. The three skips name
  the unavailable OS sandbox backend. A one-clause mutation that removed the image-local `.git` after its
  synthetic commit made `30` provenance checks fail (`565 passed, 3 skipped`); restoring `Dockerfile`
  reproduced SHA-256 `77c883f08179db35ced106dfaefa71b1b146830312e3f8def979eebc8332f856`. Bubblewrap's
  direct user-namespace probe was denied by Docker's default kernel policy, so no privileged or
  security-relaxed run was requested. This completes only the fixture portion; CI and external
  published-live-artifact criteria remain pending their separate conditions.

- **Correction to the 2026-08-01 (#121, #122) entry above and to commit `52ae146`, both left
  unchanged.** Those records describe the published live artifacts as `.gitignore`d benchmark output.
  Measured 2026-08-02 during Issue #16 review: `git check-ignore -v ax-live-verification-evidence`
  matches nothing, `.gitignore` names only `artifacts/`, and the directory is
  `/Users/astralpig/ax-live-verification-evidence/` — **outside the repository entirely**, so no ignore
  rule applies to it. The consequence stated there is unaffected: a clean environment still cannot see
  those files, which is why the container validates fixture evidence only. The commit message is
  immutable and the entry above is append-only history; this pointer is the correction of record.

### 2026-08-02 (#103) — the status header is current only when its latest visible transition date agrees

- **[Issue #103](https://github.com/DHChe/braincrew-datateam-portfolio/issues/103) is implemented
  locally; no Git lifecycle action has been performed.** `Last updated` is a current-state field, not
  a preserved Issue #47 snapshot. It now names the maximum date among Transition history entries — the
  record a reader can inspect inside this append-only file — rather than a repository commit timestamp
  that the file does not show.
- **The coupling is derived, not re-pinned.**
  `test_delivery_status_records_the_published_review_repair_and_new_frontier` captures every dated
  `### YYYY-MM-DD` Transition heading, requires every `###` entry here to start with such a date, and
  compares the independently hand-written header with the maximum date. A later entry inserted out of
  order, a changed header, or an unparseable entry turns the test red; no literal date remains in the
  test and the guard does not depend on newest-first file order. The scanned region is bounded at both
  ends, `## Transition history` to `## Transition record format`. Review found and pane 1 reproduced
  that an unbounded scan let an example `### 2099-01-01` heading in the format section carry a matching
  false `Last updated: 2099-01-01` to green, while rejecting a legitimate undated `### Required fields`
  subheading there; the bound closes the first and removes the second.
- **The historical record is intact.** No existing Transition entry was rewritten or deleted, and the
  test's Issue #47-era Current checkpoint assertions remain unchanged. The last recorded move was
  `2026-07-24` to `2026-07-25` in `f411fae`; that commit's `Rejected:` and `Directive:` concern AX's
  five-file upload cap, not this header's semantics. The decision and failure modes are recorded in
  [the status-currency decision](../decisions/2026-08-02-status-currency-derived-from-transition-history.md)
  and defense card **D29**.
- **Cycle 178 validation is complete.** The prior first-heading check passed after a later
  `2026-08-05` entry was inserted below the `2026-08-02` heading, proving that the old guard was
  fail-open. The strengthened guard made that mutation, a stale `2026-08-01` header, and an
  unparseable `### current` heading RED, then restored the status byte-for-byte after each mutation.
  The Issue #47 checkpoint mutation also remained RED. Sequential `ruff format --check`, `ruff check`,
  `mypy`, and `pytest -q` gates passed (598 tests); no Git lifecycle action has been performed.

### 2026-08-01 (#121, #122) — an unreported predicate is recorded as unknown, and the warrant is re-argued rather than transplanted

- **Both issues are implemented and reviewed `APPROVE` with no blocking finding.** Uncommitted at the
  time of writing: fourteen source and test files on `develop` at `d2b3c29`, plus this status entry,
  the decision document, and dossier card **D28**. `uv run pytest -q` reproduces **598 passed**
  (baseline 592). Locked in
  [the discard-predicate and continuity-warrant decision](../decisions/2026-08-01-unreported-discard-predicate-and-re-argued-continuity-warrant.md).
- **What the change is.** AX `3bb27f8` split a citation-contract violation from an unsafe-provider
  block, two causes that had shared one `failure_reason` label. Braincrew now records both predicates
  as `StrictBool | None` with `exclude_if=lambda value: value is None`, so a record that never reported
  them dumps byte-identically to the day it was written. **`None` means unknown, not false** — the
  published 2026-07-31 capture holds **12 of 15** grounded observations discarded under the old single
  label, and defaulting to `False` would have asserted that none of them was a citation-contract
  violation, a claim with no evidence behind it.
- **The warrant was re-derived, not bumped.** `changed_paths` grew from one path to two because
  `backend/src/ax_engine/answers/contracts.py` is new to this diff. Bumping `under_test_sha` alone
  would have produced a warrant that reads as true, passes every existing check, and under-reports the
  diff it warrants.
- **Verification the orchestrator reproduced rather than accepted.** Both published artifacts still
  replay (`sha256:775a8529…`, `sha256:9435c9da…`); all 15 stored `AnswerPathHealth` objects round-trip
  with zero byte differences; the three warrant tree SHAs and the census source hash were re-derived
  from the AX checkout; mutating the pin alone turns 164 tests red including a production-source guard
  binding the pin to the packaged contract; removing the citation mapper line alone turns the named
  capture test red, which also proved that test was not looping over an empty collection. Independent
  review added four further mutations and searched every JSON file in the repository for the two new
  keys — 17 hits, all in the census fixture, none in published evidence.
- **One review finding was applied.** The new capture test looped over its observations with no count
  assertion and would have passed while asserting nothing had the collection been empty. It now pins
  15.
- **A deliberate loss of independent witnesses is written down.** Five test files that had each carried
  their own SHA literal now import the pin. Measured: moving the pin constant and the packaged YAML
  together fails 87 tests and **none of the five is among them**. Four witnesses remain. The trade
  bought structural impossibility of a partial re-pin; the cost is recorded so the next person does not
  convert one of the remaining four thinking it a duplicate.
- **Two orchestrator errors, both caught by the review rather than by the orchestrator.** The review
  brief quoted Issue #94's `Directive:` as *"bind the exact commits, do not degrade to a constant-only
  assertion"* — **that sentence is not in the commit**; the real directive forbids comparing the two
  constants to each other and requires the warrant's import-time construction property be kept. The
  brief also named two files as keeping SHA literals when there are three, and the omitted one turned
  out to be the largest witness at 71 failures. Both are the same failure as the AX #60 defect earlier
  in the day: paraphrasing a decision record from memory instead of reading it. The existing rule
  requires marking brief claims `measured` or `inferred`; that discipline was applied to the evidence
  table and not to the prose around it.
- **What is still not established.** The twelve unknown discards stay unknown; only a live diagnostic
  re-capture against `3bb27f8` can resolve them, and that costs a provider run. The two replay digests
  were each produced once — the published artifacts are `.gitignore`d benchmark output, so independent
  review could not locate them and verified the substance by other means instead. The census `sha256`
  is compared against a code constant, never against the AX working tree, so its accuracy depends on a
  hand re-enumeration at every re-pin.
- **Next action.** Git Lifecycle Proposal Gate for #121 and #122. No commit, push, pull request, or
  merge has been made.

### 2026-08-01 (#97) — the hazard that had been serialising every run all day is closed, and the affordance that closes it is safe for a reason nobody had stated

- **[Issue #97](https://github.com/DHChe/braincrew-datateam-portfolio/issues/97) is implemented and
  reviewed `APPROVE` with no blocking finding.** Uncommitted at the time of writing: five files on
  `develop` at `a2f5b02` — two source and test, plus three documents, one of them the new decision
  artifact this ticket's third acceptance criterion required. `uv run pytest -q` reproduces
  **592 passed**. Locked in
  [the schema directory override decision](../decisions/2026-08-01-schema-directory-override-and-tracked-file-containment.md),
  defended as card **D27**.
- **What the defect was, and why it mattered here.** The sealing drift test mutated the **tracked**
  `schemas/` directory and restored bytes captured at its start. A second run capturing its "original"
  inside the first run's drift window wrote the **drifted** bytes back as pristine — **both `finally`
  blocks completing normally** — leaving a self-consistent `(schema, digest)` pair that every
  recompute-and-compare check accepts. Only the code-pinned constant or `git status` could detect it.
  This repository's commit gate **is** `git status`, and the corruption nearly went in beside Issue
  #94's work. **It has been a live constraint on every cycle since**, forcing pane 1 to serialise every
  test run by hand.
- **The fix, and the judgement it required.** `seal()` runs the CLI in a **subprocess**, so an
  in-process `monkeypatch` cannot reach the code under test — which is why containing a test needed
  four lines of *production* source: a `BRAINCREW_SCHEMA_DIRECTORY` override consulted by
  `_schema_directory()`. This repository is right to be wary of production affordances that exist only
  for tests, and #97 demanded the decision artifact name why it was acceptable.
- **The obvious safety argument is incomplete, and independent review found the hole in it.** The
  argument — that the override cannot weaken anything because the selected directory is still checked
  against the code-pinned `EXPECTED_SCHEMA_DIGESTS` — is sound but insufficient:
  `_verify_vendored_schemas()` iterates over **that constant**, not over the directory's contents, so
  extra files are never inspected. **Measured: a pristine copy plus an attacker-supplied extra schema
  is accepted.** The hole is unreachable only because `_schema_directory()` has **exactly one
  production call site** and is used **only for verification** — there is no second consumer to steer.
  **The safety case is a conjunction, and it is contingent**; a future change that *loads* a schema
  from that directory re-opens it. That is written into the decision document as a property to
  preserve rather than left as an incidental fact.
- **What review measured that pane 1 and pane 2 did not.** Ten input shapes against the override, plus a no-override baseline —
  empty string, whitespace, empty directory, partial directory, a file rather than a directory,
  pristine copy, pristine plus an extra file, symlink, relative path, and a self-consistent drift —
  with **no input found where the override changes the outcome rather than the location.** Removing
  the four lines turns three tests red with `assert 0 == 2`, proving the subprocess genuinely consumes
  the variable rather than passing for an unrelated reason. **And the demonstration that the ticket's
  goal is actually met:** review injected a delay inside the drift window and **`SIGKILL`ed `pytest`
  there** — the exact shape #97 was found by, and one that runs no `finally`. The tracked bytes were
  unchanged, because nothing is written to them any more.
- **What pane 1 measured itself.** Ruff, mypy, **592 passed**, `git diff --check`,
  `git status --short schemas/` empty. A drifted-but-**self-consistent** override directory is refused
  with `AX_SCHEMA_DRIFT` — the laundering attack the affordance would have to permit to be dangerous;
  the extras acceptance above; the single call site; that `corpus_authoring.py` resolves its own
  `source_root / "schemas"` untouched by the variable; and that the sealing receipt records
  `EXPECTED_SCHEMA_DIGESTS` constants rather than directory-read digests, so it stays truthful
  regardless of where verification looked.
- **Recorded rather than discovered later.** The variable is a **test-only bridge, not an operator
  feature**, and is deliberately undocumented outside the decision document and the source. No
  precedent existed — `git grep os.environ -- src/braincrew` returned nothing before this change, and
  that is stated rather than glossed. And the irony is named: the fix for *"tests corrupt the tracked
  schemas directory"* is an override that lets any process **ignore** that directory. On net the
  property is strictly better, because tests no longer write to it at all.
- **Also closed cheaply.** #97 recorded three `returncode == 2` assertions it had **not** audited, any
  of which could in principle be satisfied by an unrelated `AX_SCHEMA_DRIFT` failure. All three were
  identified and judged not weak, each for a structural reason — one never enters schema verification,
  and two return at a create-only branch before it. None was changed.
- **Not claimed.** Nothing here touches AX, the answer path, or any evaluation result. It is
  repository hygiene, and it moves no acceptance criterion. Its value is that a class of silent
  tracked-file corruption is gone and the manual serialisation it forced can stop.
- **Next.** Pre-commit audit of this entry and the documents beside it — pane 1 does not review its own
  writing — then the Git Lifecycle Proposal Gate.

### 2026-08-01 (instrument freeze, README, and a false measurement removed) — the owner redirected from polishing the instrument to moving the evidence, and the first thing that move found was a published zero that was never a measurement

- **The owner asked how far the plan had got, and the answer required correcting an earlier report.**
  Against the design specification's ten acceptance criteria the release stands at four met, one met
  for fixture evidence only, four not met and one not separately assessed. The engine is far along
  and the evidence is not: **one live retrieval measurement exists and no live answer-quality
  measurement does.** pane 1's first progress report counted the 100-case dataset as delivered on the
  strength of its frozen manifest; a measured probe showed the current `v3` dataset **has no complete
  offline run at all** — run against the only committed observation bundles it returns `INVALID` with
  34 of 100 scored.
- **Instrument work was frozen.** Of 52 issues at the freeze, 22 came from the original plan and 30 emerged during
  delivery, and over the preceding four days every completed ticket improved the measuring instrument
  while none produced a measurement. [#108](https://github.com/DHChe/braincrew-datateam-portfolio/issues/108)–[#115](https://github.com/DHChe/braincrew-datateam-portfolio/issues/115)
  were **parked, not closed** — the measurements they record are not withdrawn — with a resume
  condition written on each: reconsider once the instrument is being used rather than tuned. The
  implementable frontier went from fifteen issues to two.
- **The repository has a `README.md` for the first time**, merged as `d6b98ec` (PR #117). It was
  written **after** a measured claim inventory rather than before one, deliberately: pane 2 produced
  the inventory — every claim, the command that checks it, the actual output, and a verdict — with no
  README prose in existence, so claims could not be retrofitted to the writing. Three audit rounds
  then found **three blocking overclaims**, all in pane 1's prose, each reproduced before acceptance:
  *"every artifact is create-only and replayable"*, which one command falsified with the same error
  string Issue #106 had just spent five cycles eliminating; an accounting of ten acceptance criteria
  that named eight; and a diagram attributing Parquet to a stage that emits none — disproved by the
  README's own documented command.
- **The audit's judgement on the README's framing, which pane 1 had asked for because it could not
  judge it:** the opening is earned, because the refusal to score twelve broken cases rests on
  captured answer-path health, a contract that requires it for live batches, and locked decision D23
  — not on arithmetic. But the document *undersold the build*, so a paragraph of provable scale was
  added, every figure measured before it was written.
- **A scope analysis was tested by refutation before anything was built on it, and pane 1's
  recommendation was destroyed.** pane 1 proposed authoring six parsing observations and committing
  the live capture so the `v3` Verification partition would reproduce offline. Review refuted it:
  `build_dataset_run_artifact`'s live-provenance check (`dataset_run.py:317`) requires a live run's `evaluation_plane_sha` to equal the current commit, the
  capture pins `f9d9cfd`, and `verification_only` requires both batches live — so **the v3
  Verification artifact cannot be rebuilt at `HEAD` by anyone**, and committing the fixtures makes it
  worse in either direction. The recommendation's deliverable was an out-of-tree procedure pinned to a
  historical commit. **Review proposed a fourth option nobody had: fix the evaluator and author
  nothing.**
- **What the analysis did establish, and it closes a gap open since the first live capture.** The
  parsing aggregate of `0.0000` in the published 2026-07-31 evaluation is explained: the run used
  `parsing_observations_v1.json` — **byte-identical for all twenty case IDs** — against v2 documents.
  `parsing-015`'s observation span `"3년 | 16일"` does not occur in `demo-terms-guide-002`. The
  control that settles it, proposed and run by review after pane 1 failed to think of it: the same
  observations against the correct dataset version score **`1.0000`** on all five metrics.
- **[Issue #118](https://github.com/DHChe/braincrew-datateam-portfolio/issues/118) is implemented,
  reviewed `REQUEST CHANGES`, repaired, re-reviewed `APPROVE`, and refined once more.** Parsing was
  the only one of three evaluator families with no drift detector, so it reported a false zero as a
  measurement. It now refuses, as `parsing-quality-v2`, with `parsing-quality-v1` reachable only from
  stored provenance so published artifacts still replay. Locked in
  [the parsing drift decision](../decisions/2026-08-01-parsing-drift-refusal-and-evaluator-versioning.md),
  defended as card **D26**. **Uncommitted at the time of writing**, eleven files on `develop` at
  `d6b98ec`.
- **Review found two misdiagnoses in the guard, and a bypass that meant the guard never ran at all —
  none of which implementation or orchestration had seen.**
  It refused a legitimate zero-recovery observation of the **correct** document — the same
  one-code-two-causes defect this project filed against its own SUT as `AX#60`. Fresh runs on two of
  three committed manifests had **no guard at all**, demonstrated by emitting a fresh `COMPLETED`
  artifact with 20 `SCORED` cases and aggregate `0.0000`: the defect, still producible. And the
  predicate misdiagnosed a **correct** document carrying a SUT-assigned span id — which is exactly
  what the live path produces, since `live_preflight.py:789` copies AX's span id. That last finding
  moved the predicate from a `(span id, digest)` tuple to the document digest alone, measured to
  refuse all six published drift cases identically.
- **The sentence most likely to be written down wrongly later, so it is written here.** The published
  2026-07-31 artifact **still recomputes six `SCORED 0.0000` parsing cases** under its stored v1
  dispatch. That is what preserving replayability means. This work stops **new** evaluations from
  producing a false zero; it does **not** remove the false zero from published evidence.
- **What pane 1 measured itself.** Ruff, mypy, `pytest -q` **589**, `git diff --check`,
  `git status --short schemas/` empty. Both blocking findings reproduced before acceptance, and the
  second misdiagnosis reproduced independently. On the final tree: correct-digest-with-SUT-id
  **scores** with structure and metadata retained; zero recovery **scores**; a different document
  digest is **refused**; the v3 probe refuses every case with aggregate `None`; the legitimate v1 path
  is `COMPLETED` at `1.0000`; and both real artifacts still replay — `sha256:9435c9da…` and
  `sha256:775a8529…`, the latter being Issue #106's criterion, **which pane 2 did not report and
  pane 1 had to check.**
- **Two errors of pane 1's own, corrected rather than buried.** It wrote an acceptance criterion into
  #118 requiring a fresh run to reproduce a historical digest — unachievable, because a logical digest
  binds the evaluation-plane commit and dirty state, and reaching it would require fabricating
  provenance. pane 2 refused and was right; the criterion is corrected in a comment on the issue so
  the next implementer is not pushed toward the same fabrication. And pane 1 dispatched a repair to a
  pane with 20% context remaining, then interrupted and reset it before work was lost.
- **Not claimed.** No AX runtime was started at any point. No live parsing observation exists in this
  repository, so the guard has never run against a real AX parse response. Nothing here bears on the
  AX answer path or the twelve unscoreable grounded cases. No candidate run, so no comparison, no gate
  decision, no answer-quality claim.
- **Next.** Pre-commit audit of this entry and the durable documents beside it — pane 1 does not
  review its own writing — then the Git Lifecycle Proposal Gate.

### 2026-08-01 (merge) — Issue #106 merged as `be206ff`; eight follow-ups filed, and the checkpoint that named the Git gate as the only remaining step is now superseded

- **[Issue #106](https://github.com/DHChe/braincrew-datateam-portfolio/issues/106) merged as
  `be206ff`** (PR #107, squash, both CI jobs green — `frontend` and `python`) and is `CLOSED`. The
  owner authorized commit, push and pull-request creation in one step and the merge in a second, and
  the branch deletion in a third. Nothing was staged with `git add -A`; the six paths were named
  explicitly and `git status --short` was confirmed immediately before committing.
- **Re-verified on the merged `develop` by pane 1**, not carried over from the pull request: ruff
  format and check clean, mypy clean, **581 passed**, tree clean, `git status --short schemas/`
  empty. The real 2026-07-31 capture replays through the committed CLI at **exit 0**, reproducing
  `sha256:775a85295fb5db2f9cfb6e1aa5504206ea3b629a032452932ca685a7ab1a5049` with 9 retrieval and 15
  grounded observations — the acceptance criterion #106 set, now measured on the branch that ships it.
- **The remote CI measured what pane 1 could not.** The six npm and Playwright gates were the one
  claim resting on an inference rather than a pane 1 measurement — that no changed path lies inside a
  gate's input glob. The `frontend` job ran them and passed, so the inference is now backed by an
  independent execution rather than only by reading `package.json`.
- **The branch was deleted from `origin` and locally**, after confirming that `be206ff`'s tree is
  identical to the pre-squash branch tip `8dfb718`. A squash merge leaves the branch tip a
  non-ancestor, so `git branch -d` refuses it; the force delete was taken only after the tree
  comparison came back empty.
- **Eight follow-ups filed individually**, at the owner's instruction, rather than as one bundle.
  `ready-for-agent`: [#108](https://github.com/DHChe/braincrew-datateam-portfolio/issues/108)
  (`executed_role` unchecked — the fourth reciprocal fact),
  [#109](https://github.com/DHChe/braincrew-datateam-portfolio/issues/109) (the `retrieval_top_k` and
  `evidence_limit` bounds), [#110](https://github.com/DHChe/braincrew-datateam-portfolio/issues/110)
  (`fixed_retrieval_config_digest` not recomputed, which review called the strongest available
  follow-up) and [#115](https://github.com/DHChe/braincrew-datateam-portfolio/issues/115) (the CLI's
  `RecursionError` escape, **pre-existing on every schema and not introduced here**).
  `needs-triage`, because each needs a judgement before code:
  [#111](https://github.com/DHChe/braincrew-datateam-portfolio/issues/111) — review's own
  reassessment is that #106 made it *less* serious and it may deserve closing rather than fixing;
  [#112](https://github.com/DHChe/braincrew-datateam-portfolio/issues/112) — byte-canonicality, where
  the current behaviour is defensible and the check must be proved not to reject the only live
  artifact this project has; [#113](https://github.com/DHChe/braincrew-datateam-portfolio/issues/113)
  — a return-shape divergence whose fix ripples into `replay_run_artifact`'s signature;
  [#114](https://github.com/DHChe/braincrew-datateam-portfolio/issues/114) — where the 9/15 split
  should be asserted, not whether.
- **A staleness this file created and then had to correct, recorded because it is the same defect
  class twice in one day.** The pre-merge checkpoint said *"Nothing is committed; the only step that
  remains is the Git Lifecycle Proposal Gate."* Cycle 144's audit had already blocked on a
  Current-checkpoint claim that decayed the moment the step it named completed, and supplied
  deliberately stale-proof replacement wording. That wording survived re-auditing — and then the
  merge falsified it anyway, because *"the only step that remains"* is a claim about the future and
  no phrasing makes a future claim durable. **The lesson is not better wording.** A
  Current-checkpoint bullet that names a pending step is stale from the moment that step completes,
  and the only remedy is that the action which completes it also updates the record. That is what
  this entry is.
- **Not claimed, and unchanged by the merge.** No AX runtime was started at any point in this work.
  Nothing here bears on AX's answer path, the `unsafe_provider_output` conflation, or the twelve
  unscoreable grounded cases. No candidate run exists, so there is still no comparison, no gate
  decision and no answer-quality claim. The replay makes the capture *checkable*; it does not make it
  *correct*, and two of the six forgeries independent review built are still accepted — recorded in
  the decision document, card D25 and #111.
- **Next.** Nothing is in flight. The frontier is #15 Phase 1's remaining work and the eight
  follow-ups above; the two AX tickets filed on 2026-07-31 against `DHChe/AX_portfolio` (#60, #61)
  remain outside this repository's control.

### 2026-08-01 — The unrepeatable capture gets a replay path; review broke the first one against the real artifact, and the claim was enumerated rather than described

- **[Issue #106](https://github.com/DHChe/braincrew-datateam-portfolio/issues/106) is implemented,
  reviewed `REQUEST CHANGES`, repaired, re-reviewed `APPROVE` with no blocking finding, and its claim
  narrowed in a third cycle.** Working tree on `develop`, base **`a373e64`**, **nothing committed** —
  this entry is written before the Git Lifecycle Proposal Gate, so at the moment of writing no commit,
  branch or pull request exists. Cycles 138 (implementation), 139 (independent review), 140 (repair),
  141 (scoped re-review) and 142 (claim precision). No AX runtime was started and none was needed.
- **Why the ticket existed, measured by pane 1 on `a373e64` against the real artifacts.** The first
  live capture — 24 live AX calls, unrepeatable because the provider calls cost money — was the one
  artifact in the chain with no replay. `braincrew-eval replay` refused the capture manifest at
  **exit 2** (`unsupported artifact schema: live-experiment-capture-v1`) while replaying the
  *evaluation* artifact built from it at **exit 0**. **The reproducible half replayed; the
  irreproducible half did not.**
- **And the one committed cross-check was unreachable for this run.** `run_summary.py` recomputes both
  observation content digests and compares case counts, but an earlier clause returns first unless the
  evaluation is `COMPLETED` with 30 of 30 scored. This run is `INVALID` with 18 of 30, because of the
  twelve `unsafe_provider_output` cases. `build-run-summary` therefore exits 2 on it. The gate is
  correct; the consequence was that **artifact integrity was coupled to answer quality.** Until this
  work, the artifact's integrity rested on an uncommitted script that recomputed digests with the same
  functions that produced them.
- **The independent review broke the first implementation, and pane 1 reproduced it on the real
  capture.** pane 3 built six forged triples in which every stored digest is internally consistent;
  **all six were accepted**, one of them demonstrated through the committed CLI at exit 0 and the rest
  at the function. The blocking class: the manifest and the observation files each
  record the same facts independently — adapter version, SUT commit — and nothing compared them.
  pane 1 then rebuilt pane 3's forgery against a scratch copy of the **real** 2026-07-31 capture. A
  grounded file declaring `fixture-grounded-sut-v1` and SUT `bbbb…`, under a manifest still declaring
  `execution_mode: live` and warrant `1ead1331…`, replayed at **exit 0**.
- **The second reproduction is why it was blocking rather than untidy.** Once the grounded batch
  declares the fixture adapter, its contract no longer requires answer-path health — so **all fifteen
  `answer_path` records were deleted, including the twelve `unsafe_provider_output` records that are
  the entire X1 measurement**, digests recomputed, and it replayed at **exit 0** again. A capture
  stripped of the only evidence of AX's answer-path failure was reported as successful under a
  manifest that still said the run was live. **Exit 0 on that input is worse than refusing to replay
  at all**, because the refusal is honest and the exit 0 is an affirmative false assurance.
- **The repair, and what it now establishes.** Three reciprocal facts are compared, the file-name
  reference is constrained at the contract to a bare filename so directory escape is unrepresentable
  rather than merely refused, and the **recomputed** logical digest is returned rather than the stored
  one — the last found by pane 1 independently of review. Locked in
  [the capture replay decision](../decisions/2026-08-01-live-capture-replay-and-its-enumerated-claim.md),
  defended as card **D25**.
- **The claim is now a closed list, and that is the substantive half of the decision.** #106's first
  wording said the replay verifies the manifest and its observation files are *"mutually consistent."*
  That phrase is unbounded: cycle 141 immediately found a **fourth** reciprocal fact
  (`executed_role` against the manifest's role keys) and two declared bounds (`retrieval_top_k`,
  `evidence_limit`) it does not cover. Each round would find one more, and each would read as a defect
  against the stated claim. The claim is therefore enumerated — six named conditions — which is true,
  checkable line by line, and finishable. **The reviewer's own recommendation, adopted.**
- **What it does not establish, stated rather than hidden.** It does not re-run AX and cannot. It does
  not detect a forgery in which the manifest and every observation file were fabricated together
  consistently — inherent to any scheme where one party controls the manifest. It does not compare
  every fact both sides record; three are compared and three known others are follow-ups.
  `executed_role` is **unreachable** from the capture path, because it comes from the adapter the
  capture itself built; the `retrieval_top_k` and `evidence_limit` bounds **could** be exceeded by an
  AX response and are deferred only because the real capture's margins are wide — 0 to 1 candidates
  and 0 to 1 citations against limits of 5 and 3.
- **What the re-review left open, because "approved" is not "closed".** Cycle 141 re-ran its
  cycle-139 forgery harness unchanged: **four of the six forgeries are now refused**, each naming the
  right fact; **two are still accepted** — one that was inconclusive when built, and a `run_id`
  disagreeing with the file names it points at, which is the deferred follow-up. pane 1 reproduced
  that second acceptance against the real capture: `run_id` changed alone and rehashed replays at
  **exit 0**. The first wording of the decision document, of **card D25 — the recruiter-facing
  dossier** — and of the commit message all said *every* forgery was refused; this entry was silent on
  the post-repair outcome until now. **Cycle 143's pre-commit audit returned `NOT SAFE TO COMMIT` on
  it** — a false statement about the outcome of the reviewer's own review, in the one sentence a
  reader uses to conclude the repair is complete, and the decision document contradicted itself two
  sections later by listing the same gap as a follow-up.
- **What pane 1 measured itself, and what it did not.** Run by pane 1, solo: ruff format and check,
  mypy, `pytest -q` **575** after cycle 138 and **581** after cycle 140, `git diff --check`,
  `git status --short schemas/` empty throughout, and `HEAD` unmoved at `a373e64` with no stash and no
  new Git object. Against copies of the real capture outside the repository: the untouched triple
  replays to `sha256:775a8529…` at exit 0 with 9 and 15 observations; a case identity swapped with all
  digests rehashed, a grounded adapter disagreement, the `answer_path`-stripped variant, a grounded
  `sut_commit_sha` changed alone, a retrieval `adapter_version` changed alone, a missing sibling file
  and a `sub/` file name each refuse at **exit 2** with their own message and no traceback. An eighth
  probe — `run_id` changed alone — is **accepted at exit 0**, which is the deferred follow-up above,
  measured rather than assumed. **Not run by pane 1:** the six npm and Playwright gates. pane 2 ran them green and pane 3 verified
  independently that no changed path lies inside any of their input globs — **an inference from the
  gate configuration, not a measurement of the gates.**
- **Attribution corrected by review, and it is the rule this repository added on #101.** pane 1's
  cycle-141 brief labelled the fixture-adapter and `answer_path` forgeries *"pane 1's cycle-139
  forgery."* They are **pane 3's** constructions, made while pane 1's findings were deliberately
  withheld from it; pane 1 rebuilt them independently against real data afterwards. The accurate
  label is *pane 1's independent re-run, on the real capture, of pane 3's forgery*, and it is used
  that way above.
- **Two errors in pane 1's own briefs, found by review and adopted.** *"Five replay functions in
  `result_store.py`"* is wrong — two functions, five schema versions handled inline; the repository's
  other replay functions live in four other files, and two of the review's findings came from
  comparing against those. And the npm-gate premise was stated as *"zero JS/TS files changed"* when
  Prettier and ESLint run over **directories**, so the load-bearing premise is that no changed path
  lies inside a gate's input glob.
- **A dispatch-mechanism defect, diagnosed only partly.** pane 2 reported that its cycle-138 brief
  arrived **truncated**, and cmux's paste counter read 4206 characters against a 6972-character file.
  The work covered the whole brief, so the truncation is more likely a rendering artifact than a lost
  payload, and **it is not settled.** Every brief from cycle 139 onward is written to a file and
  dispatched as a one-line pointer, which removes the failure class rather than diagnosing it.
- **Not claimed.** No AX runtime was started. Nothing here bears on AX's answer path, the
  `unsafe_provider_output` conflation, or the twelve unscoreable grounded cases. No candidate run, so
  no comparison, no gate decision, no answer-quality claim. The replay makes the capture *checkable*;
  it does not make it *correct*.
- **The pre-commit audit found two blocking defects, both in pane 1's own writing, and neither in the
  code.** Cycle 143 audited this entry, the decision document, card D25 and the commit message —
  pane 1 does not review its own writing. It returned **`NOT SAFE TO COMMIT`** on the false
  *"every forgery is refused"* claim above, and on a Current-checkpoint bullet that said
  `git status --short` named **three** files when it names five plus an untracked one, **including the
  file the sentence is written in.** pane 1 reproduced both before accepting them. Six further
  non-blocking corrections were adopted, one of which the auditor traced to **its own** cycle-141
  wording losing a qualification. Append-only discipline was confirmed clean: zero deletions, no
  dossier card renumbered, no historical entry edited, and `Last updated: 2026-07-25` untouched with
  its pinned test passing inside the 581.
- **Next.** A scoped re-audit of these corrections, then the Git Lifecycle Proposal Gate. The
  follow-ups this work deliberately did not take are enumerated in the decision document and need the
  owner's authorization before any are filed.

### 2026-07-31 (night) — The first live experiment capture succeeded, X1 says #92 was urgent, and the next blocker is inside AX's answer path

- **[Issue #101](https://github.com/DHChe/braincrew-datateam-portfolio/issues/101) merged as
  `f9d9cfd`** (PR #104, both CI jobs green) and is `CLOSED`. Re-verified on the merged `develop`:
  ruff and mypy clean, **562 passed**, tree and `schemas/` clean. GitHub did not auto-close the
  issue from the `Closes #101` line because the merge target is `develop` rather than the default
  branch; it was closed explicitly with the outcome recorded.
- **The runtime boundary was opened and closed again under stage-by-stage authorization**, and the
  containment checks were run **before** starting anything, which is the check that would have
  caught the 2026-07-28 break at the moment it happened. All values matched record 16 exactly:
  `EMBEDDING_PROVIDER=fake` on both containers, `APP_ENV=local`, bind `127.0.0.1:18000` only, OpenAI
  key SHA-256 first-8 `90891895`, container IDs `1929eafc8f5e`/`fc4cb4f8ffc9`, volumes **114**,
  AX clean at `1ead133` = `PINNED_AX_SHA`. **No container was created or destroyed.**
- **Two deviations from the recorded procedure, both disclosed before acting rather than after.**
  `docker start <container>` was used instead of `docker compose start` — identical effect, and it
  removes compose-file and env resolution entirely, so recreation is structurally impossible rather
  than merely unlikely. And the proposed "commit the status doc before opening the runtime" stage was
  **dropped as unnecessary**: the capture guard reads `dirty_worktree`, the tree was already clean at
  `f9d9cfd`, and committing then would have produced a commit describing its own merge — the
  opposite of this repository's `61fe64c` pattern.
- **The recorded health-check error was not repeated.** Record 16 documents a `*healthy*` substring
  match that reported success while the backend was `unhealthy`. Exact-equality comparison was used
  instead, the backend genuinely read `unhealthy` for 200 seconds, and a direct `/health/ready` query
  confirmed the cause was the staged start — four dependencies `ready`, `worker`
  `stale_or_missing` — exactly as record 16 diagnosed.
- **The preflight passed**: exit 0, `READY`, 0 blockers, 3 corpus + 6 parse observations, logical
  digest `sha256:48e29415…`, replayed through the committed CLI to the identical digest. The
  handoff receipt's SHA-256 matched the code-pinned constant.
- **The first live experiment capture in this project's history succeeded**: exit 0, three
  artifacts, **24 live calls** (9 retrieval + 15 grounded answer). Provider cost was incurred and is
  **unmeasured**.
- **#101 was exercised successfully against the authorized live local AX runtime** — `APP_ENV=local`,
  loopback `127.0.0.1:18000` only. This is not production-deployment evidence. The live artifact
  carries `corpus_digest: null` and
  `corpus_digests_by_role` for all three roles, with Employee's `sha256:85b57bb2…` distinct from
  Executive and HRPractitioner's `sha256:ecba4eea…` under one identical `corpus_id`. The visibility
  split is preserved rather than flattened, which is what the decision required.
- **X1 is measured, and the answer is urgent.** Across the 15 grounded cases: **12** returned
  `llm_call_performed=true, llm_call_succeeded=false, failure_reason="unsafe_provider_output"` →
  `available=false`; **2** were healthy answers; **1** was an ordinary retrieval-level abstention with
  no provider call. **What is observed:** all fifteen return HTTP 200 and are contract-valid, and
  pre-#92 code would have recorded twelve of them as `insufficient_evidence` abstentions and scored
  them as answer quality. **What is not observed:** no candidate run exists, so the uniform-zero
  `evidence_limit` 3-vs-5 difference and the published PASS remain the *conditional* failure mode
  #92's commit message described — a matching candidate run would be needed to exhibit it. The
  contribution of this capture is that the twelve misclassifiable inputs are now **measured**
  rather than hypothesised; the PASS itself is not. Cycle 124's widening is also exercised: the
  single `performed=false` case is correctly `available`, not classified as an outage.
- **The first live retrieval-quality measurement: Recall@5 = 17/18 = `0.9444`**, MRR@10 = 2/3,
  authority priority 1/1, `COMPLETED`, zero hard failures, all 9 cases returning 5 candidates.
  Produced by the committed evaluator over the captured observations, with no additional provider
  calls. **The evaluator refused the first invocation** — *"run ID and SUT SHA must match the
  dataset run"* — because it binds an evaluation to the capture it claims to evaluate.
- **This weakened pane 1's own hypothesis — but it does not refute it, and pane 1's first wording
  said it did.** pane 1 had proposed that `EMBEDDING_PROVIDER=fake` made retrieval semantically
  meaningless and thereby caused the answer failures. The Recall@5 measurement covers
  `retrieval-022`–`030`; the twelve failed answers are `GA-001`–`GA-010`, `VA-006` and `VA-010` —
  a **disjoint** set of cases with different queries, whose internal retrieval Braincrew never
  observed, and all twelve carry template `source_texts: []` because they fell through to the
  fallback. So a system-wide "fake embeddings make retrieval useless" concern is weakened, while
  **what evidence the failed answer calls actually received remains unmeasured.** This is a
  labelled hypothesis, not a finding. It is recorded rather than deleted because it is why the
  retrieval measurement was made, and because pane 1 wrote "refuted" and the audit caught it.
- **Grounded answers are `INVALID`, and no quality claim follows.** Only 3 of 15 cases were
  evaluable, all three hard-failed, and **`citation_precision_cases` and `claim_support_cases` are
  both zero** — no case contributed answer-quality evidence. Run state `INVALID`, 18 of 30 scored.
  **The gate worked**: the evaluator refused to produce a verdict from insufficient evidence instead
  of scoring twelve broken cases as abstentions.
- **The next blocker is in AX, and the evaluation plane is what found it.**
  `failure_reason="unsafe_provider_output"` is emitted by a **disjunction** at
  `answers/service.py:184-186`: either the strict citation validator `_citations_valid` rejected the
  answer, **or** the Korean forbidden-phrase blocklist `_provider_output_unsafe` fired. **The
  disjunction is measured; which predicate fired for the twelve is not, and neither branch can
  currently be ranked above the other from this run.** AX logs nothing — 294 backend lines across
  the capture window, zero errors or warnings, every request 200 — and the observation record does
  not carry the provider's raw response, so the discarded output is unrecoverable. The defect that
  **is** established regardless of which branch fired: one `failure_reason` string is emitted for
  two unrelated causes, so a consumer that records it verbatim, as Braincrew does, reports a safety
  event for what may be a grounding failure. Two AX tickets are proposed in the evidence: split the
  conflated reason, and log the discard.
- **New gaps this run created, recorded rather than fixed.** The committed `replay` CLI **refuses**
  the capture artifact (`unsupported artifact schema: live-experiment-capture-v1`), so its integrity
  rests on recomputing digests with the same code that produced them — weaker than the preflight's
  independent replay, and labelled as such. The parsing aggregate is `0.0000` on all three metrics;
  it used the **fixture** adapter so it says nothing about AX, and why it is zero was not
  established. `cost_measurement_status` is **present in the capture provenance with the value
  `null`** — not absent, as pane 1 first wrote — which the comparison layer treats as missing
  provenance; whether the run-summary builder supplies it was not verified end to end.
- **Not claimed.** No answer-quality claim about AX. No candidate run, so no comparison, no gate
  decision, no release judgment. Provider cost incurred and unmeasured. Nothing about AX parsing.
- **Next.** A candidate run now would spend provider cost to break the same twelve cases again, so
  it is not the next step. File the two AX tickets, then decide whether the citation contract or the
  model is the thing to change. Evidence outside the repository:
  `20-runtime-boundary-post-101-2026-07-31.json`, `21-first-live-capture-and-x1-2026-07-31.json`,
  `22-unsafe-provider-output-diagnosis-2026-07-31.json`, plus the capture and evaluation artifact
  directories.

### 2026-07-31 (evening) — Issue #101 answered its design question and was approved twice; corpus identity is now compared per role between runs

- **[Issue #101](https://github.com/DHChe/braincrew-datateam-portfolio/issues/101) is implemented,
  reviewed `APPROVE` with no blocking defect, repaired, and re-reviewed `APPROVE`.** Branch
  `feat/issue-101-corpus-identity-per-role`, cut from `develop` `61fe64c`, tree clean at cut.
  **The owner authorized commit → push → pull request; the merge is a separate authorization,
  conditional on both CI jobs passing.** Cycles 128 (implementation), 129 (independent review), 130
  (repair), 131 (scoped re-review), 132 (a precision fix plus an audit of pane 1's own status
  entry), 133 (an overclaim that audit found), 134 (a pre-commit audit that returned **NOT SAFE TO
  COMMIT** on four records-level blockers) and 135 (closing them). No AX runtime was started and no
  live call was made; the ticket is a Braincrew code change and needed none.
- **The decision.** *"Baseline and candidate ran against the same corpus"* means the corpus identity
  AX reports **for each required principal role** is equal **between the two runs**. It does **not**
  mean one identity **across roles within** a run: a *visible* corpus digest is a function of the
  principal's visibility, so AX's `employee_visibility_invariant` makes cross-role equality
  structurally unsatisfiable for any role set spanning visibility classes — which this dataset's is.
  Locked in [the per-role corpus identity decision](../decisions/2026-07-31-corpus-identity-per-role-across-runs.md),
  defended as card **D24**.
- **The control was scoped, not deleted, and two within-run invariants stay armed:** `corpus_id`
  must still be identical across every required role (AX measurably returns one for all three, so a
  difference means genuinely different corpora rather than a visibility slice), and the AX-confirmed
  role evidence must cover exactly the required dataset roles. The reviewer hunted for an input
  where two genuinely different corpora compare compatible — mixed fixture/live pairs, role-swapped
  digests, missing and extra keys — and **found none**.
- **The field shape is an `execution_mode`-keyed exclusive choice.** A `live` summary carries
  `corpus_digests_by_role` and no scalar; a `fixture` summary carries one unscoped `corpus_digest`
  and no role map, because its observations are hand-authored and no role scoping occurred. It is
  therefore structurally impossible for a live artifact to collapse the split or for a fixture to
  invent role-scoped provenance. `_compatibility_violations` compares the whole mapping, so a
  changed digest, a missing role, or an extra role all produce
  `SYS-COMPARISON-CORPUS_DIGESTS_BY_ROLE-MISMATCH` and an `INVALID` comparison.
- **The independent review found a defect pane 1 had not.** pane 1 withheld its own findings from
  the reviewer's brief — the reviewer had the ticket, the diff and pane 2's report, but not pane 1's
  conclusions. It then reported that the new field validator `validate_corpus_digests_by_role` was
  protected by **nothing**: replacing its body left the suite at **560 passed**. pane 1 had not
  looked at that function's coverage at all, and reproduced the result independently afterwards
  (row 9 of the reproduction record). That was the one literal miss against #101's
  *"mutation-verify per clause"* criterion, and it is now closed by two named tests.
- **The mutation table was corrected rather than defended.** Of the four rows first reported, **two
  mutated lines byte-identical to `61fe64c`** — they prove pre-existing guards are armed, not that
  the new work is protected. They are now labelled *"pre-existing guard, re-confirmed"*, B1's count
  is corrected from one red test to **three**, and the reviewer's own discovery — the mode-scoped
  required-provenance clause, which **is** new and **is** armed — was added as a fifth row. The
  table is stronger after the finding than before it.
- **What pane 1 reproduced itself, and what it did not.** Ran by pane 1: ruff format/check and mypy
  clean; `pytest -q` **560** after cycle 128 and **562** after cycle 130; the B1 mutation (3 named
  tests red); the validator mutation both before and after the repair; the mode-scoped fifth-row
  mutation; the dossier revert as a single addition-only hunk with zero deletions; direct
  `ExperimentProvenance` probes; `git status --short schemas/` empty throughout — each restore
  verified by SHA-256 rather than by a passing test. **Not run by pane 1:** the `552` pre-edit
  baseline, which is pane 2's; the six npm/Playwright gates, which pane 2 ran and pane 3
  independently reproduced; and the W1, W2 and B2 mutations, which are pane 2's and pane 3's.
  The itemised record with commands and outputs is
  `cycle128-133-pane1-reproductions.md` in the local evidence directory
  `~/ax-issue-45-review/` — **outside this repository and not committed**, like every other
  evidence artifact in this project. It exists
  because cycle 132's audit found this bullet's earlier wording attributed the whole list to pane 1
  with no artifact anyone could check.
- **Recorded and deliberately not fixed here.** `contributing_versions` — the field proving each
  role's corpus actually contains the frozen dataset — is still not carried into provenance, so no
  single command binds it (`capture-live-verification` checks it; `capture_live_experiment` does not
  require a preflight artifact). Not a regression, and the reviewer agreed it is scope creep into a
  ticket that has answered its design question. **Follow-up on #15.**
- **An open question this ticket deliberately did not settle: this file's own `Last updated` field
  says `2026-07-25` and is wrong.** Entries were added on 07-27, 07-28, 07-30 and 07-31 without it
  moving. Cycle 132's audit flagged it and pane 1 changed it — which turned
  `test_delivery_status_records_the_published_review_repair_and_new_frontier`
  (`tests/acceptance/test_corpus_provisioning_workflow_order.py:399`) **red**: that test pins the
  literal string `Last updated: 2026-07-25` alongside a block of Issue #47-era Current-checkpoint
  content it exists to preserve. **pane 1 reverted its own edit** rather than change a pinned
  assertion inside a ticket that is not about it, and rather than resolve a judgment it has an
  interest in — the question is whether the *check* is wrong, and pane 1 authored the change under
  dispute. **The auditor's finding is acknowledged, not rejected.** The owner chose to separate it:
  it is now [Issue #103](https://github.com/DHChe/braincrew-datateam-portfolio/issues/103), which
  must decide whether `Last updated` is a current-state field or part of the preserved Issue #47
  snapshot, and must prefer whichever option cannot silently go stale again.
- **A finding against pane 1's own conduct.** The repair brief handed pane 2 an *unreproduced*
  factual claim — that an empty role key is not caught downstream — and it landed in a durable
  decision document as an assertion. The reviewer reproduced it: the claim is true and in fact
  **stronger** than stated, since such a pair is decided `PASS` rather than merely uncaught. The
  failure mode is the one `AGENTS.md` already forbids in the worker → orchestrator direction, run in
  the orchestrator → worker direction, where the topology did not name it. **The owner authorized
  adding the rule**, and it is in this commit: `AGENTS.md`'s orchestration topology now binds the
  orchestrator in the same direction it already binds workers, and requires a brief to mark each
  load-bearing claim as measured or inferred and to say who measured it.
- **Recorded elsewhere, by the owner's decision.** `contributing_versions` is a follow-up comment on
  [#15](https://github.com/DHChe/braincrew-datateam-portfolio/issues/15#issuecomment-5141346809)
  with three costed options, not a change here. The `Last updated` question is
  [#103](https://github.com/DHChe/braincrew-datateam-portfolio/issues/103).
- **Not claimed.** No experiment has run. No baseline, no candidate, no answer call, no provider
  cost, no quality claim. T-ACCEPT drives the capture through `httpx.MockTransport`; T-REFUSE is an
  in-memory comparison over two constructed run summaries and uses no transport at all. Neither
  touches a live AX, and every quality observation in this repository still comes from
  `httpx.MockTransport`. **The earlier wording of this bullet said both controlled tests used
  `MockTransport`, which was false for T-REFUSE** — found by pane 2's cycle-132 audit of pane 1's
  own entry, after two review cycles had passed over the same sentence in the decision document
  without catching it.
- **Next, after this merges:** #15 Phase 1 has no known blocker. Re-run the preflight, then the
  24-case capture — and **record X1 during it**, the distribution of AX answer-path emission shapes
  across the 15 grounded cases, which decides whether #92's three repair cycles were urgent or
  insurance.

### 2026-07-31 — Issue #92 merged; the runtime ran, the preflight passed, and the baseline capture found a fourth blocker

- **[Issue #92](https://github.com/DHChe/braincrew-datateam-portfolio/issues/92) merged as `998708e`**
  (PR #99, both CI jobs green) and is `CLOSED`. Re-verified on the merged `develop`: **552 passed**,
  tree clean. `CLAUDE.md` then merged as `2331963` (PR #100) — see below for why that was on the
  critical path.
- **The runtime boundary was opened under authorization, and the start method was the load-bearing
  part.** The final containers carry `EMBEDDING_PROVIDER=fake` and `AX_API_PORT=18000`, set in an
  ephemeral shell on 2026-07-28 and present in **no committed configuration**. `docker compose start`
  reuses them; `up` would recreate and silently restore `EMBEDDING_PROVIDER=openai` and bind 8000 —
  the containment break record 09 measured. Containment was verified **before** starting anything, by
  inspecting the stopped containers: `fake` on both, bind `127.0.0.1:18000` only, `APP_ENV=local`,
  OpenAI key SHA-256 first-8 `90891895` (the rotated key). After start: `/health/ready` = `ready`,
  volumes **114** unchanged, port 8000 closed, AX checkout clean at `1ead133` = `PINNED_AX_SHA`.
- **The preflight passed: exit 0, `READY`, 0 blockers**, 3 corpus + 6 parse observations, logical
  digest `sha256:ed05713c…`, replayed through the committed CLI to the identical digest.
  **This is the first time Issue #94's continuity warrant has been exercised against a live AX**: the
  receipt produced at `2bcaee3` was accepted against SUT `1ead133`. Before #94 that combination
  failed with a message asserting the receipt came from an *unreviewed* commit, which was false.
  Scope: it proves the warrant admits the pair it was written for; that it refuses a wrong pair is
  held by contract tests and seventeen mutations, not by this run.
- **The baseline capture was refused twice, and both refusals were guards working.** First: *"live
  capture requires a clean committed Evaluation Plane"* — an uncommitted owner instruction in
  `CLAUDE.md`. The fix was to commit it, not to relax the guard, which exists so a live artifact
  names exactly one committed Evaluation Plane state. Second, and this is the finding:
  *"corpus identity differs across dataset roles"*.
- **Blocker D, filed as [#101](https://github.com/DHChe/braincrew-datateam-portfolio/issues/101), and
  it is a design conflict rather than a defect in either system.** `live_experiment.py:436` requires
  one identical visible corpus digest across the dataset roles. Measured live: Executive and
  HRPractitioner both return `sha256:ecba4eea…` with the dataset plus six tenant uploads, while
  **Employee returns `sha256:85b57bb2…` with the frozen dataset only**. `corpus_id` is identical for
  all three. Employee's narrower view is AX's `employee_visibility_invariant` behaving correctly — a
  *visible* corpus digest **must** differ for a role with narrower visibility — so the invariant is
  structurally unsatisfiable for any role set spanning visibility classes, which this dataset's is.
  The preflight passes because it checks something different: that every role's
  `contributing_versions` includes the frozen dataset. Both checks are individually sound; they
  disagree about what *"the same corpus"* means when visibility is role-dependent.
- **Why nobody found it before:** the 2026-07-28 probes aborted at blocker A, the role mapping,
  before reaching corpus-identity binding. #91 fixed that, so this line became reachable for the
  first time today. **No answer call was made and no provider cost was spent** — both refusals happen
  before any retrieval or answer request.
- **The boundary was closed** in the recorded order (worker → backend → clamav, all `Exited (143)`),
  datastores left running as on every prior boundary, volumes **114** unchanged, no listener on
  `127.0.0.1:18000`. Same reasoning as 2026-07-28: #101 is controlled-test work needing no runtime,
  so holding a write-capable service open would serve no purpose. No container was created or
  destroyed this session.
- **X1 is still unmeasured** — the distribution of AX answer-path emission shapes across the 15
  grounded cases, which #92's review named as the question deciding whether its three repair cycles
  were urgent or insurance. The capture refuses before any answer request. Record it during the first
  capture that actually reaches the answer path, rather than spending provider calls on a probe that
  produces no artifact.
- **#15's blocker list was corrected a second time the same day**: `#101` added, with an append-only
  note. It is now the only open blocker.
- Evidence outside the repository: `16-runtime-start-and-preflight-2026-07-31.json`,
  `17-blocker-D-corpus-identity-across-roles.json`, `18-runtime-stop-2026-07-31.json`.
- **Not claimed.** No experiment has run. No baseline, no candidate, no quality claim. Every quality
  observation in this repository still comes from `httpx.MockTransport`.

### 2026-07-31 — An independent audit of pane 1's own entries found four errors; they are corrected here, not rewritten above

- Cycle 126 named pane 1's four status entries **"the largest single gap in this approval"** and did
  not reach them. pane 3 was out of weekly budget, so cycle 127 asked **pane 2** — which did not
  write them — to audit them and report bluntly without editing. The rule that the orchestrator does
  not review its own writing has been enforced on every worker in this ticket; pane 1 is not exempt
  from it. The entries above are left intact and corrected here.
- **Error 1, and it is the third instance of one failure mode.** The cycle-121 entry says
  `provider_metadata` "appears in exactly **three** places in `src/`", and the cycle-122 entry
  "corrected" that to *three lines across two files*. Both are wrong as written. At `eac588b`,
  `git grep provider_metadata -- src/` returns **four lines across three files**: `ax_http_adapter.py:356`,
  `live_experiment.py:500-501`, **and `src/braincrew/ax-http-v1.yaml:147`**. pane 1 measured
  `src/braincrew/*.py` and wrote `src/`. The load-bearing half — that the three answer-path fields
  were read nowhere — is independently **verified**. But this is the same failure that cost
  `ax-http-v1.yaml` in the #94 cycle and cost a fifth annotation location in cycle 117: **the scope
  pane 1 measures keeps being narrower than the scope pane 1's words claim, and twice it has been
  the same file.** The durable fix is to state the exact command beside the count, or to grep with no
  path filter.
- **Error 2 — a true fact bound to the wrong function and the wrong call sites.** The cycle-123 entry
  and pane 1's cycle-123 brief both attribute the omitted `llm_call_succeeded` at `service.py:676-678`
  to `_reference_only_fallback`, "whose two call sites `:146` and `:173` are normal answering modes".
  Measured: `:676` is inside **`_historical_ambiguity_result`** (defined at `:630`).
  `_reference_only_fallback` is defined at `:576`, is the function called from `:146`/`:173`, and
  **explicitly passes `llm_call_succeeded=False`** with a required `failure_reason: str`. The
  emission shape pane 1 described is real; the function and callers it named are not. pane 2's own
  cycle-124 AST census had this right at the time.
- **Error 3 — routes reported as shapes.** The cycle-124 entry says "all six AX wire shapes probed".
  The state space has **four** shapes; the six probed lines are emission *routes*, two pairs of which
  collapse to the same shape. In a record whose subject is a state space, calling a route a shape is
  a factual error, not loose phrasing.
- **Error 4 — the design analogy, already adjudicated.** The cycle-125 entry frames the unbound
  census relation as "Issue #94's defect returning" and names #94 as the repair pattern. Cycle 126
  adjudicated that wrong: #94's warrant licenses a divergence that is *legitimate*, whereas a census
  commit differing from the commit it claims to describe is **always** invalid. The finding was
  right; the analogy was not.
- **What the audit could not verify, and why that is worth recording.** Several intermediate claims —
  the 521 / 531 / 547 / 551 pass counts, the per-cycle doc numstats, cycle 122's 1-of-15 and 5-of-15
  partial-failure probe, and pane 1's own false-alarm probe — are **unverifiable now**, because the
  uncommitted intermediate trees were discarded. Contemporaneous reports corroborate them but are not
  independent reproduction. Only the endpoints have present measurements: `eac588b` independently
  collects **521** tests, and the current suite freshly passes **552**. A durable record that cites a
  number from a tree nobody kept is corroborated, not verified, and should say so.
- **A constraint violation pane 2 caused, detected, reversed and disclosed rather than relabelled.**
  While attempting an independent replay of the historical `eac588b` suite, a Git-aware fixture
  persisted `core.worktree` and a test-local `[user]` identity into `.git/config` — **Git
  configuration writes, which the brief forbade**. pane 2 noticed because `git status --short`
  unexpectedly went empty, refused to accept the affected gate results, discarded two otherwise-green
  gate sequences, repaired the configuration and reran everything. pane 1 verified the repair
  independently: `core.worktree` unset, no local `user.email`/`user.name`, toplevel back to
  `/Users/astralpig/braincrew`, `git diff --cached HEAD` clean, HEAD still `eac588b`, and the same
  seven modified plus two untracked paths. **Reporting it rather than quietly passing is the
  behaviour this topology depends on**, and it is recorded as such.
- **X2 is closed**: the census's per-shape `failure_reason` is renamed `failure_reason_example`, so an
  evidence artifact cannot be misread as an enumeration of AX's reason vocabulary — AX emits at least
  five distinct reason strings, including `reference_overclaim`. `schema_version` deliberately not
  bumped: the artifact is uncommitted and has no consumer to migrate. 552 passing, unchanged.

### 2026-07-31 — Cycle 126 approved Issue #92, reversed its own earlier position, and found pane 1's cycle-125 direction wrong

- **`APPROVE`, no blocking findings**, on the consolidated 121 + 123 + 124 + 125 delta. Three
  non-blocking: **X1**, **X2**, **X3**.
- **The reviewer attacked the enumeration rather than confirming it, and derived it independently
  from AX source without reading the census first — matching on every row.** It closed the question
  that would have been W1's *third* instance: the dangerous `(performed=True, succeeded=False,
  reason=None)` shape is **unreachable**, because `_reference_only_fallback` declares
  `failure_reason: str` with no default, and both sites passing `provider_attempted=True` also pass a
  reason. It also confirmed `ProviderMetadata` is constructed at exactly **one** site in all of
  `backend/src`, so no emission route bypasses the four call sites.
- **The reviewer reversed its own cycle-122 generalization, and said why in a way worth keeping.**
  Its "not performed ⟹ unavailable" recommendation came from a **biased sample of two states that
  both happened to carry a `failure_reason`**; it had never seen `:71`/`:87`. pane 2 was right to
  refuse to extend it. `failure_reason is None` is judged "a semantic rule, not a coincidence of the
  current shapes": a reason string present means something went wrong, absent means it did not. And
  the two boolean fields are not decorative — they carry wire-output validation and the reader-facing
  distinction between "no call attempted" and "call attempted and failed".
- **pane 1's cycle-125 direction was judged wrong, and pane 2's answer right.** Naming #94 as the
  pattern was imprecise: #94's warrant exists where two commits *legitimately* differ, whereas a
  census commit differing from the commit under test is **always** an error, so a warrant would
  license a divergence that is never valid. pane 2's counter — a matching file digest cannot prove a
  newly pinned commit was *examined* — was called the clearest evidence in the ticket that pane 2 was
  reasoning rather than complying.
- **The cost of pane 1 standing in for the gate, measured rather than asserted.** The reviewer's
  verdict on the three directed repairs: cycle 123 "correct but incomplete" — pane 1 passed the
  reviewer's own over-broad generalization through unexamined, so it survived an extra cycle because
  the party reviewing it had already endorsed it; cycle 124 "the best direction in this ticket";
  cycle 125 "right problem, wrong pattern". Net judgment: correct trade under the actual budget,
  honestly disclosed, with one measurable cost.
- **X1 is the ticket's remaining real risk and it is a measurement, not a defect.** Nobody has
  settled whether the evaluation's configuration actually reaches any non-success shape for the 15
  grounded cases. If every case takes `:217`, these three repair cycles are insurance; if any takes
  `:71`, the abstention half is load-bearing on day one. The recommendation is to record the observed
  shape distribution **during** the authorized #15 Phase 1 runtime start, where it costs nothing.
- **What the approval does not cover, in the reviewer's own words.** Dimension 6 — pane 1's four
  status entries — was **not reached at all** and is named "the largest single gap in this approval".
  Cycle-121 mutation row **M7** remains unreproduced by any party. Sentence-level factual checking of
  the decision document and D23 was not done; only append-only structure was verified (147/0, 129/0,
  182/0, zero deletions in `docs/`).
- Cycle 127 is dispatched for **X2** — the census records one representative `failure_reason` per
  shape while AX emits several, which could be misread as an enumeration of AX's vocabulary in an
  artifact whose purpose is to be read as evidence — and for the gap above: **pane 2 independently
  checks pane 1's four status entries**, because pane 3 is out of weekly budget, pane 2 did not write
  them, and the rule that the orchestrator does not review its own writing has been enforced on every
  worker in this ticket. pane 2 checks and reports; it does not edit this file.

### 2026-07-31 — The state space is closed and verified; one unbound relation remains, and it is #94's defect returning inside #92

- **Cycle 124 closed the class, and pane 1 verified every claim independently.** pane 2 ran an
  AST-assisted read-only census of AX at `1ead133`, found all nine call sites — four
  `_provider_metadata`, five `_template_result` — and reduced them to **four** distinct wire shapes.
  pane 1's own derivation matched exactly, with no disagreement on any row. All six shapes were
  probed through `_answer_path_health` and behave as designed. **551 passed**, eleven gates green
  solo, docs append-only (132/0, 121/0), HEAD unchanged, `schemas/` clean.
- **The census provenance is real, not asserted.** pane 1 computed the AX source file's SHA-256
  independently: `681956917adb17453b8ace3e03dc6da9422177850286be2582f9ff3bacf2c702`, byte-for-byte
  the value pinned in `tests/fixtures/ax_answer_path_emission_states_v1.json`.
- **The design call, and it reverses a generalization the cycle-122 reviewer had made.**
  `performed=False, succeeded=None, reason=None` is a **measurable abstention**, not an outage.
  Those branches return before provider execution because retrieval or packaging already established
  that a generated answer was not warranted — no failure is reported. pane 2 disagreed explicitly
  with generalizing *"not performed means unavailable"* beyond the two reason-bearing states the
  reviewer had examined, and pane 1 agrees with the reasoning: classifying the most ordinary
  abstention AX has as an outage would have failed Issue #92's second acceptance criterion quietly,
  which is worse than the abort it replaced. Availability now reduces to
  `failure_reason is None` across all four states.
- **One relation is still missing, and it is Issue #94's defect reappearing inside #92.** The census
  pins `source.commit_sha = 1ead1331…`; Braincrew separately pins `PINNED_AX_SHA = 1ead1331…`.
  **Nothing binds them** — pane 1 measured that neither the census artifact nor its test references
  `PINNED_AX_SHA` at all. They agree today by coincidence of authorship. On the next re-pin nothing
  forces re-enumeration, so the state model would claim coverage of an AX version it never examined,
  and an unrepresentable shape aborts the whole capture — the exact failure three cycles have been
  spent closing. Note also what the census test proves: it asserts the JSON's fields against literals
  in the test file, so it proves the JSON has not changed, **not** that the enumeration is still true
  of AX. The binding to `PINNED_AX_SHA` is what would carry freshness.
- Cycle 125 is dispatched for that one relation, with the #94 decision named as the pattern: bind
  them, or allow divergence only under a warrant that binds the exact pair and carries measured
  evidence. Widening the check to accept both values is excluded by the standing standard #94
  recorded.
- **Review sequencing, chosen deliberately under budget.** pane 3 is at ~11% of its weekly
  allowance. Rather than review a moving artifact three times, cycle 126 will be **one consolidated
  independent review** of the whole 121 + 123 + 124 + 125 delta. The cost is that pane 1 has now
  directed three repairs on its own verification findings, so the review brief must say exactly what
  pane 1 directed and why, and invite the reviewer to say that direction was wrong.
- Still unreached by any pass and carried forward: cycle 121's mutation rows M7, M9 and M11;
  sentence-level factual checking of the decision document's new sections and card D23; and **W2**,
  whether the evaluation's configuration actually selects any of these AX paths — the question that
  decides whether these gaps are urgent or merely correct.

### 2026-07-31 — The W1 repair works, and the same defect returned in a more ordinary path; cycle 124 closes the class instead of the instance

- **Cycle 123 repaired W1 and pane 1 verified it at the layer that matters.** `AnswerPathHealth` now
  models three states with `llm_call_performed` read as a source fact rather than inferred, and both
  AX wire shapes — explicit `null` and **key omitted** — are accepted through `_answer_path_health`
  with `available=False` and AX's own reason preserved. Contradictions, coerced booleans and a
  missing performed flag are refused. 531 → **547 passed**, all eleven gates green solo, docs
  append-only (92/0, 94/0), HEAD unchanged, `schemas/` clean.
  - A caution for future readers: pane 1's first probe called `AnswerPathHealth` **directly** and saw
    the omitted-key case refused, which looked like a gap. It is not — `_answer_path_health` supplies
    every key via `.get()`, so the reachable path always passes an explicit `None`. Probing the
    wrong layer produced a false alarm; the capture-layer probe is the one that answers the question.
- **Then the same defect returned, and pane 1 found it while verifying the repair.**
  `_template_result` declares `failure_reason: str | None = None`, and **two of its five call sites
  omit the argument** while also leaving `provider_attempted` at its `False` default:
  `service.py:71` (guarded by `retrieval.answer_mode in {INSUFFICIENT_EVIDENCE, OUT_OF_SCOPE}`) and
  `service.py:87` (guarded by `not evidence`). Both emit
  `performed=False, succeeded=None, failure_reason=None`, which Braincrew refuses with *"call without
  success requires a failure reason"* — so `capture_live_experiment` raises and **the whole capture
  aborts**, exactly W1's failure mode. Both confirmed empirically through `_answer_path_health`.
- **This instance is worse than W1's.** Those are not degraded or blocked paths: `:71` is AX deciding
  *at retrieval* that evidence is insufficient or the query is out of scope — and `out_of_scope` is a
  legal value in Braincrew's own `_answer_mode` set — while `:87` is simply "nothing packaged". **No
  LLM call was attempted because none was needed.** These are the most ordinary abstentions AX has,
  and they are the *cautious answer* half of the distinction Issue #92 exists to preserve.
- **The design question this forces, and it is not the obvious one.** Cycle 123 derives `available`
  from `llm_call_succeeded is True`, so merely admitting the fourth shape would make a
  retrieval-level abstention **unavailable** — violating Issue #92's second acceptance criterion for
  the most common abstention there is. That would be the ticket's other half failing quietly, which
  is worse than the abort. Whether *"no LLM call was needed"* is a measurable abstention or a
  machinery failure is left to the implementer to decide and pane 3 to challenge.
- **The method change is the point of the cycle.** Two cycles, two instances of *"AX emits a shape
  the model cannot represent, so the capture aborts"*. Fixing the fourth shape by hand invites a
  fifth, so cycle 124 requires the state space to be **derived from AX's source and proven covered**,
  with a test derived from the enumeration rather than from the two known instances. This is defence
  card **D19** applied — stop fixing instances and change the type — at instance two rather than five.
- pane 1 handed over its **complete** enumeration of all four `_provider_metadata` call sites and all
  five `_template_result` call sites, with its adjudication beside every row and an instruction to
  re-derive and adjudicate independently. That is the census discipline the #94 cycle taught: a
  curated list is how the last two gaps survived.
- Not yet reached by any pass and carried forward: cycle 121's mutation rows M7, M9 and M11;
  sentence-level factual checking of the decision document's new section and card D23; and **W2**,
  whether the evaluation's configuration actually selects any of these AX paths — still unresolved by
  static inspection, and the thing that decides whether these gaps are urgent or merely correct.

### 2026-07-31 — Cycle 122 returned REQUEST CHANGES: AX's answer-path field has three states and the implementation modelled two

- Cycle 121 (pane 2) implemented Issue #92 as a typed `AnswerPathHealth` warrant plus the
  **pre-existing** refusal chain — case evaluator → grounded coverage → integrated state →
  run-summary input check. `grounded_evaluator.py`, `grounded_run.py`, `run_summary.py` and
  `comparison.py` are unmodified. 521 → **531 passed**, all eleven gates green (pane 1 re-ran them
  solo).
- **The trap pane 1 named did not materialise, and the review proved it rather than assuming it.**
  `available=False` is not silently denominator-dropped. pane 1 mutated `grounded_run.py`'s
  availability term to `and True` and the acceptance test died with its own message,
  *"failed calls must not enter grounded quality coverage"*.
- **The reviewer settled the case nobody had tested.** Both acceptance tests drive every case to the
  same outcome, so **partial** failure was unexplored — and rejected-alternative #4 rested on the
  claim that any missing quality evidence blocks publication. The reviewer drove 1-of-15 and 5-of-15
  failures end to end: both `INVALID`, both `REFUSED` at run-summary. It also measured *why*, which
  neither pane had recorded: all four grounded coverage floors are **exactly saturated**, so losing
  any single case breaches one — with two further independent mechanisms behind it. The zero margin
  is logged as **W4**, a follow-up.
- **Two more of pane 2's judgments were upheld under stronger evidence than either pane had used.**
  The validator pane 2 deleted as redundant was proven redundant by an exhaustive state-space search
  over `(llm_call_succeeded, failure_reason, available, error)` — only two states are reachable and
  the relation holds in both, zero counterexamples. And where pane 1's brief worried that two
  mutations died via a *validator* rather than a test's own assertion, the reviewer mutated the thing
  that matters — reverting both derivation lines to the shipped bug, which constructs cleanly and
  trips no validator — and the acceptance test's **own assertion** killed it.
- **W1, blocking, and pane 1 verified every link in the AX source directly.**
  `AnswerPathHealth.llm_call_succeeded: bool` cannot represent *"no LLM call was attempted"*, and AX
  emits exactly that as `None`: `answers/service.py:543` is
  `False if provider_attempted else None`, reached with `provider_attempted=False` from
  `blocked_no_safe_provider` at `:120`; and `_reference_only_fallback` at `:678` omits the argument
  entirely, taking the `:725` default of `None`. Its two call sites, `:146` and `:173`, are **normal
  answering modes in the main flow, not crash paths**. Measured against the working tree: both AX
  states and a missing key are **refused**, so `capture_live_experiment` raises and **all 24 live
  cases produce nothing**.
- Three things compound it. It is **pane 2's rejected alternative #1 happening involuntarily** — that
  option was rejected for *"discarding the diagnostic artifact"*, which is what the code now does on
  a reachable input, contradicting the decision document's own rationale. It lands on a **one-shot**
  authorized runtime start. And the field that would disambiguate it, `llm_call_performed`, is the
  third of the three unread fields Issue #92 names: pane 1 confirmed mechanically that it is read
  **zero times in every file under `src/braincrew/`**, and that
  `{"llm_call_performed": False, "llm_call_succeeded": True}` is currently accepted as fully healthy.
- Cycle 123 is dispatched: model the third state, bind it by reading `llm_call_performed` rather than
  inferring it, treat *not performed* as an answer-path failure carrying AX's own `failure_reason`,
  and refuse the contradictory combination. `StrictBool` (**W3**) folds in — the coercion the reviewer
  found is direction-safe, so it is hygiene, not a hole.
- **W5 is pane 1's own, and is a wording imprecision rather than a false claim.** The cycle-121 entry
  below says `provider_metadata` "appears in exactly three places in `src/`". Measured precisely: at
  `eac588b`, before implementation, it appears on **three lines across two files**
  (`ax_http_adapter.py` ×1, `live_experiment.py` ×2); the reviewer measured the post-implementation
  tree and read "places" as loose. The entry does scope itself with "Pre-dispatch", and its
  load-bearing half — that the three fields were read nowhere — was true. The old entry is left
  intact and corrected here.
- **Reviewer budget was the binding constraint and the review says so.** It reached dimensions 1, 3,
  4, 5, 7, 8, part of 2 and part of 6, and named what it did not reach: mutation rows M7, M9 and M11;
  sentence-level factual checking of the decision section and D23; and **W2**, whether the
  evaluation's AX configuration actually selects those two paths — which it identifies as the single
  most useful thing a next pass could settle, since it decides whether W1 is urgent or merely correct.

### 2026-07-31 — Issue #92 implementation dispatched (cycle 121)

- Phase: [Issue #92](https://github.com/DHChe/braincrew-datateam-portfolio/issues/92) — a run where
  every LLM call fails would publish as a valid comparison — is **in implementation** on
  `feat/issue-92-answer-path-health`, cut from `develop` at `eac588b` (verified equal to
  `origin/develop`, clean, **521 passing**). The standing three-pane team is adopted: pane 2
  implements from `/Users/astralpig/ax-issue-45-review/brief-cycle121-issue92.md`, pane 3 reviews in
  cycle 122, pane 1 owns this file.
- **The crux, restated so it cannot be halved.** Two failure modes must stay distinguishable:
  `llm_call_succeeded: False` means the machinery failed and the observation is not evidence about
  answer quality at all; `llm_call_succeeded: True` with `answer_mode: insufficient_evidence` means
  the machinery worked and AX chose to abstain, which is a real, measurable and **desirable**
  outcome. The cheapest implementation of "fail closed" refuses every abstention and destroys the
  second half, so the ticket requires **both** acceptance tests.
- Pre-dispatch, pane 1 verified independently: the guard is now at `live_experiment.py:500-503`
  (the ticket cites 496-500, which moved with #94 — the code is unchanged); `provider_metadata`
  appears in exactly **three** places in `src/`, so `llm_call_performed`, `llm_call_succeeded` and
  `failure_reason` are read **nowhere**; `_answer_mode` accepts `insufficient_evidence` as legal;
  and `GroundedObservation` already carries `available`/`error`.
- **The trap named in the brief**, because it is the most likely way this ticket goes wrong:
  `available=False` is the obvious hook, and if an unavailable case is silently dropped from a
  denominator downstream, a wholly broken run becomes a *smaller* comparison rather than a refused
  one — the same defect in different clothes. The implementer must establish what the evaluator and
  comparison layers actually do with an unavailable observation and report it either way.
- The framing choice — refuse the whole capture, a typed warrant with the comparison layer refusing
  a quality conclusion, or a justified threshold — is deliberately left to the implementer to argue
  and pane 3 to challenge. `CostDecisionWarrant` (`comparison.py:284`) is named as the closest
  structural precedent, alongside the ticket's own warning that silently tolerating a fully broken
  provider is not obviously the right reading of the warrant pattern.
- **Reviewer budget is the binding constraint this cycle.** pane 3 is at ~87% of its weekly
  allowance. Review will run as fewer, larger passes rather than many small ones. Recorded because
  it changes how the gate is operated, not whether it applies.
- Completion condition: implementation → independent cycle-122 review → repair if needed →
  re-review → Git Lifecycle Proposal to the owner. Workers hold no Git write authority. The AX
  runtime stays stopped; this is a Braincrew code change.

### 2026-07-31 — Issue #94 merged and closed; #92 is the only open blocker on #15, and #15's blocker list had gone stale a second time

- **[Issue #94](https://github.com/DHChe/braincrew-datateam-portfolio/issues/94) merged into
  `develop` as `3822daf`** (PR #96, python and frontend CI both green), squash-merged with the
  branch deleted, and closed as `COMPLETED`. Re-verified on the merged `develop`: ruff, mypy and
  **521 passed**, working tree clean, `schemas/` clean. The pins now read
  `PINNED_AX_SHA = 1ead1331…` (under test) and `REVIEWED_PROVISIONED_AX_SHA = 2bcaee34…`
  (the receipt's commit).
- The commit was made under the precondition cycle 120 attached: `git status --short schemas/`
  confirmed empty, and **sixteen explicitly named paths staged** rather than `git add -A`.
- **A stale blocker list, found while deciding what comes next — and it is a recurrence.** #15's
  list read `#7, #12, #13, #38`, and **all four are now `CLOSED`**, so #15 read as *ready* to any
  issue-list reader. Meanwhile #92 was open and says "Blocks #15 Phase 1" in its own body, and #94
  said "Blocks: #15". Both dependencies existed only in the **blocking** issues' prose, never in
  the blocked issue's list. #15 already carries a 2026-07-27 correction note describing exactly this
  failure, which did not prevent it happening again. #92 is now listed, and a second correction note
  was appended rather than the first being edited.
- **Why #92 must precede the live measurement, as a dependency rather than a preference.** The
  24-case measurement exists to separate how much of AX's abstention is contract over-reach from how
  much is genuine under-citation — a question **about abstentions**. #92 is precisely the inability
  to tell `llm_call_succeeded: False` (the machinery failed, so the observation is not evidence
  about answer quality at all) from a legitimate `insufficient_evidence` abstention. Running the
  measurement first would spend an authorized AX runtime start to obtain 24 abstentions that cannot
  be classified. This repository has met the shape twice: the latency test that passed only because
  an injected clock gave both runs identical ticks, and the three blockers that stopped #15 Phase 1
  before it ran.
- **Follow-up filed:** [#97](https://github.com/DHChe/braincrew-datateam-portfolio/issues/97) — a
  test writes drift into the **tracked** `schemas/` directory, so two concurrent full-suite runs can
  leave it durably corrupted with a **self-consistent** `(schema, digest)` pair that only
  `EXPECTED_SCHEMA_DIGESTS` or `git status` can detect. It needs a production-source schema-directory
  override, because `seal()` runs the CLI in a subprocess and an in-process monkeypatch cannot reach
  it. The procedural mitigation landed immediately in `AGENTS.md` instead of waiting: no two panes
  run full suites concurrently in one shared tree, verify `git status` after any concurrent or
  interrupted run, and stage explicit paths when committing.
- **`Current checkpoint` was corrected, not rewritten.** It had listed Issue #86 as the active phase
  since 2026-07-27 while #89, #91 and #94 merged past it. The stale bullets are preserved with their
  dates and a pointer naming Transition history as authoritative — the same defect class as the
  stale blocker list, handled the same way.
- **Next:** #92 in a fresh session with the three-pane topology adopted. Deliberately not started
  here: the independent reviewer pane was at ~87% of its weekly budget, and #92 is a design-decision
  ticket of the same shape as #94, which took six cycles and three review rounds. Starting it with a
  reviewer that may run dry mid-ticket would degrade exactly the gate that caught T1, U1 and U2.

### 2026-07-30 — Issue #94 approved after six review cycles; the adjudication corrected pane 1's framing and added a commit precondition

- **Cycle 120 returned `APPROVE` on the cycle 119 delta with no blocking finding. U1 and U2 are
  closed, and Issue #94 has no open blocking finding.** The reviewer mutated **both** halves of the
  new U1 test separately — including the warrant half pane 1 had not checked — and each killed
  exactly the named test. It also derived its own mechanical `PINNED_AX_SHA` census before reading
  pane 2's column and reached the same 13 rows, adjudicating individually the three
  "historical record, leave" calls the brief had flagged as the ones that would be wrong quietly.
- **Why the ticket's evidence survives the concurrency defect, which is a better reason than "out of
  scope".** The load-bearing evidence here is **mutation** evidence, and mutation evidence is immune
  to this pollution mode: a test passing for an unrelated reason cannot produce a pass → fail → pass
  signal, it would stay green and be recorded as a survivor. Across cycles 115–120 the ticket rests
  on **seventeen** isolated mutations, every one killing exactly its intended case. The single
  survivor is provably semantically equivalent and is recorded so nobody later re-reports it as a
  gap. Independently: this pollution manifests as *failures*, never passes, so a zero-failure solo
  suite is itself evidence that no drift window was open during it.
- **The adjudication corrected pane 1 on the mechanism, and it is worse than pane 1 said.** No
  interruption is required. `test_schema_drift_fails_closed_even_if_declared_digest_is_also_changed`
  captures the tracked schema bytes, writes drift, and restores the captured bytes in a `finally`; a
  second run that captures its "original" inside the first run's drift window writes the **drifted**
  bytes back as pristine. Both `finally` blocks complete and the tree stays corrupted — and the
  corrupted `(schema, digest)` pair is **self-consistent**, so any recompute-and-compare check
  passes. Only the pinned `EXPECTED_SCHEMA_DIGESTS` constant or `git status` can detect it. pane 1's
  own reproduction had left exactly that pair modified, which corroborates the explanation. pane 1
  was wrong about the cause twice — `__pycache__`, then "interrupted mid-test" — and both times its
  own measurement exposed the error, which is why the recusal was the right call.
- **A precondition adopted for this commit, not a code change:** confirm `git status --short
  schemas/` is empty immediately before committing, and commit **explicitly named paths** — never
  `git add -A` or `git commit -a`. Committing a drifted schema beside its matching drifted digest
  inside this ticket would be worse than any finding in six cycles, because this ticket's whole value
  is evidentiary integrity.
- **Three follow-ups, none blocking:** the shared-`schemas/` test defect needs an env-var or flag
  override for the schema directory in production source, because `seal()` runs the CLI in a
  subprocess and an in-process monkeypatch cannot reach it — squarely outside Issue #94. A topology
  rule the reviewer proposed and pane 1 accepts: no two panes run the full suite concurrently in one
  shared working tree, and after any concurrent or interrupted run, verify `git status` before
  trusting the tree or reporting a gate result. And V1, a precision note requiring no action: the new
  U1 test's field assertions are pre-empted by validator refusal, so its operative contribution is
  reaching the branch at all — which is exactly what U1 asked for.
- **A question worth carrying forward,** in the reviewer's words: it had judged this ticket by running
  the suite and never asked until cycle 120 **whether any test in this repository writes to tracked
  files**. That is worth asking in any repository whose commit gate is `git status`.

### 2026-07-30 — Cycle 119 closed U1 and U2; a reproduction found a shared-`schemas/` test-isolation defect, routed to independent adjudication

- Cycle 119 (pane 2) closed **U1** with `test_reviewed_provisioning_receipt_is_accepted_for_same_reviewed_sut`,
  which monkeypatches `PINNED_AX_SHA` to the provisioned SHA and asserts the loader returns a
  `same-reviewed-commit` binding with **no** warrant, and closed **U2** by appending the fifth
  supersession annotation. 520 → **521 passed**. **No production code changed in cycle 117 or 119** —
  `live_preflight.py` is byte-identical to the snapshot pane 1 took before dispatching cycle 117,
  and pane 3's own cycle 116 digest record agrees.
- pane 1 reproduced U1's kill directly: corrupting the same-commit branch's `acceptance_reason`,
  which left **520 green** before this cycle, now fails the named test. All docs remain append-only
  (0 deletions), `521` replaced `520` in both current-evidence documents, and the tree is exactly
  the delta.
- **pane 1 fixed its own census method rather than only the instance.** U2 existed because pane 1
  had grepped every occurrence and then hand-picked four into the brief's table. Cycle 119's brief
  handed over the **complete 13-row census** with pane 1's adjudication beside each row and an
  instruction to adjudicate every row independently. pane 2 agreed on all 13 and confirmed no
  occurrence was missed.
- **A finding pane 1 declined to resolve itself.** pane 2 reported one unrelated test failing during
  a run that overlapped another pytest invocation, and called it non-reproducing. pane 1's first
  hypothesis — concurrent `__pycache__` deletion — was **refuted by its own probe**. Two concurrent
  **full** suites then reproduced it heavily (26 and 24 failures), dominated by
  `AX_SCHEMA_DRIFT`. The mechanism is in the source: `_verify_vendored_schemas()` digest-checks the
  repository's own `schemas/` directory, and `tests/contract/test_corpus_pack_sealing.py` writes a
  drifted schema into that shared path and restores it in a `finally`, so a concurrent run observes
  the window. **pane 1's own reproduction left two tracked `schemas/` files modified**; pane 1
  restored them with `git checkout -- schemas/` and re-verified the tree. That is recorded here
  rather than omitted.
- Neither `schemas/` nor the mutating test is in this ticket's diff. pane 1 **recused itself**: it
  wants the answer to be "pre-existing, out of scope" because that permits the authorized commit,
  and it had already been wrong once about the cause. Cycle 120 receives the measured facts as
  inputs, four candidate verdicts rather than two, and an explicit invitation to call the framing
  biased. The sharpest version of the risk is the one pane 1 named against its own interest: in a
  three-pane shared working tree, a run interrupted mid-test can leave tracked files modified in a
  repository whose commit gate is `git status`.
- Completion condition: cycle 120's delta verdict on U1/U2 plus its adjudication. If no blocking
  finding, pane 1 executes the owner-authorized commit → push → pull request → squash merge into
  `develop`. HEAD is still `d74065f`; nothing is committed.

### 2026-07-30 — Cycle 118 re-review closed T1–T5 and found U1: an untested branch in the same function

- Cycle 117 (pane 2) closed T1 with six validator test functions producing nine cases, 511 → **520
  passed**, and closed T2–T5 as append-only annotations and rescoped claims. **No production code
  changed** — pane 1 confirmed `live_preflight.py` byte-identical to a snapshot it took before the
  repair dispatch, and pane 3 independently confirmed the same digests against its own cycle 116
  record rather than against any cycle 117 artifact.
- Cycle 118 (pane 3, delta-scoped) returned **APPROVE, no blocking findings**, and judged T1
  **closed and exceeded**: it ran the six clauses as **nine isolated branch mutations** and each
  killed **exactly one case and nothing else**, so the clause-to-test mapping is one-to-one in both
  directions. That is the per-clause evidence pane 1 could not supply — pane 1's own mutation had
  neutralised each validator whole, which is the collective shape this project has banned since
  cycle 104. The two independent methods reconcile exactly: 6 + 3 whole-validator kills = the 6 and
  3 clauses each validator contains.
- **T3 came out stronger than the framing pane 1 supplied.** The 2026-07-26 AX-SUT decision §8 had
  already written the successor design four days early — "the honest model may need separate
  `REVIEWED_HANDOFF_PRODUCER_SHA` and `PINNED_SUT_SHA` values plus an explicit compatibility
  review. It must not silently loosen the current equality or derive B from A." Issue #94 is that
  prescription implemented, differing only in the constants' names. The reviewer recorded this as
  corroboration for the design rather than as a scoping nuance that merely escaped falsification.
- **U1, and it is nobody's single miss.** The loader's `same-reviewed-commit` branch is
  **unreachable and untested**: it requires the receipt commit to equal both
  `REVIEWED_PROVISIONED_AX_SHA` and `PINNED_AX_SHA`, which cannot hold while they differ.
  Corrupting that branch's `acceptance_reason` leaves all **520** tests green — measured by pane 3
  and independently reproduced by pane 1. It fails closed and becomes live on the first future
  re-pin that re-provisions at the SUT commit. pane 2 built it, pane 1 briefed it, pane 3 approved
  it in cycle 116; none of the three tested it.
- **U2 is a census failure in pane 1's brief, for the second cycle running.** A fifth stale
  operative location exists at `2026-07-26-ax-sut-commit-for-evaluation-review.md:229` — "exact
  `PINNED_AX_SHA` equality rejects a different receipt or artifact", which now names the wrong
  constant for the receipt half. pane 2 annotated exactly the four locations pane 1's brief table
  listed. pane 1 had grepped every occurrence and then hand-picked four into the table: the
  derivation was mechanical, the **adjudication** was not. In cycle 115 the same failure shape cost
  `ax-http-v1.yaml`, which pane 2 caught. U3 is a precision note: clause 3b protects the refusal
  *message*, not the refusal — without it an invalid binding crashes rather than being accepted.
- **An approval-scope limit the reviewer recorded rather than let stand implied:** `format:check`
  enumerates its targets and `docs/` is not among them, so "all eleven gates green" carries **no
  information** about the four documentation files that are most of this delta. Their correctness
  rests on human reading only.
- **Waiting on the owner:** whether to close U1 (~10 lines) and U2 (2 lines, append-only) in a
  cycle 119 before committing, or commit as reviewed and file them. The reviewer recommends the
  latter but named the tension plainly: U1 is the same "an unprotected check is decorative" class
  that decided the T1 call. Nothing is committed; HEAD is still `d74065f`.

### 2026-07-30 — The owner chose to close T1 inside the ticket; repair cycle 117 dispatched

- Presented with the Git Lifecycle Proposal and an explicit scope choice, **the owner chose to
  repair before committing**: close T1 (per-clause unit tests for the two new Pydantic
  validators) together with the cheap T2–T5 documentation lines, have pane 3 re-review only the
  delta, and then commit → push → pull request → squash merge into `develop`. The reasoning that
  decided it: an unprotected check is decorative by this repository's own standard, and that
  standard should apply to the commit being made rather than to a later one. Same shape as the
  owner's cycle-107 choice to close K1 in-ticket.
- The entry below is left intact deliberately. Its "waiting on the owner" state was true when
  written and is the record that the proposal gate was honoured rather than assumed.
- Cycle 117 is dispatched to pane 2 from
  `/Users/astralpig/ax-issue-45-review/brief-cycle117-issue94-repair.md`. Six validator clauses
  each need their own test and their own isolated mutation. pane 1 verified all four T3/T4
  documentation facts directly against the files before asking for any edit, including the
  nuance that the 2026-07-26 AX-SUT decision's "one SUT constant" held **"for this cycle"** — a
  correctly scoped claim whose scope ended, not a claim that was wrong.
- Completion condition: six clause mutations killed individually, all eleven gates green, the
  pytest count corrected in both documents that quote it, then cycle 118's delta re-review with
  no blocking finding. Nothing is committed yet.

### 2026-07-30 — Cycle 116 review returned APPROVE with no blocking finding; the Git proposal is with the owner

- Cycle 115 (pane 2) delivered Issue #94: `PINNED_AX_SHA` now means only the commit under test
  (`1ead133`), `REVIEWED_PROVISIONED_AX_SHA` names the receipt's commit (`2bcaee3`), and a
  code-pinned `ReceiptSutContinuityWarrant` must bind the exact divergent pair for the receipt
  to be accepted — with four condition-specific refusals replacing the misleading "unreviewed
  AX commit" message. The implementer also caught a census gap in the orchestrator's brief:
  `src/braincrew/ax-http-v1.yaml` pins the under-test SHA and was re-pinned with the rest.
- Cycle 116 (pane 3, briefed blind to pane 1's observations) returned **APPROVE**: all eight
  review dimensions pass, zero blocking findings, five non-blocking (**T1–T5**). The reviewer
  reproduced all six per-clause mutations with matching red modes, added two probes of its own,
  re-measured every Git fact the continuity warrant attests (read-only, in the AX checkout),
  and read the +22/−2 AX diff itself — so `provisioning_state_affected=False` is supported by
  the reviewer's own reading, not only attested. Restore was proven by file digests and a final
  511-test green run.
- **T1, which pane 1's own reading had missed:** the two new model validators are unprotected
  in isolation — an outright deletion of `require_reason_for_divergence` or
  `require_measured_continuity` leaves all 511 tests green. The loader checks (the operative
  runtime gate) are each mutation-protected; the validators are the future-facing half of the
  rule. pane 1 independently confirmed T1 (validator neutralised → 511 passed → byte-identical
  restore → 511 passed, `git diff --check` clean). T2: the warrant schema can only express
  today's divergence shape and fails closed on any other — safe direction, unrecorded limit.
  T3: supersession pointers are forward-only; the 2026-07-26 receipt-binding decision still
  carries now-stale operative text with no appended annotation. T4/T5: documentation
  completeness and an unpreserved TDD-red claim whose evidential load the reproduced mutation
  table carries instead.
- After the reviewer finished, pane 1 re-verified the working tree byte-restored (the same 13
  modified + 1 new file, +250/−26) and the full suite green post-restore.
- **Waiting on the owner:** the Git Lifecycle Proposal, presented with an explicit scope
  choice — close T1 (and the cheap T2/T3/T4 documentation lines) in repair cycle 117 with a
  delta re-review before commit, or commit as reviewed and file the follow-ups. No commit
  exists yet; nothing is pushed.

### 2026-07-30 — Issue #94 implementation dispatched (cycle 115)

- Phase: [Issue #94](https://github.com/DHChe/braincrew-datateam-portfolio/issues/94) —
  separate the two meanings of `PINNED_AX_SHA` (commit under test vs commit the provisioning
  receipt was produced at), state and enforce the divergence rule, re-pin to `1ead1331` — is
  **in implementation** on `feat/issue-94-separate-pin-meanings`, cut from `develop` at
  `d74065f` (verified equal to `origin/develop`, clean tree).
- The standing three-pane team is adopted per the session-close entry below: pane 2 implements
  from the brief at `/Users/astralpig/ax-issue-45-review/brief-cycle115-issue94.md`, pane 3
  reviews independently in cycle 116, pane 1 owns this file for the cycle.
- Pre-dispatch, pane 1 independently re-verified the ticket's two measured claims in the AX
  checkout (`/Users/astralpig/portfolio/AX_portfolio`, `develop` at `1ead133`, clean):
  `git diff --stat 2bcaee3..1ead133 -- backend/src` is exactly one file (+22/−2), and the
  `backend/src` tree hash is identical at `2bcaee3` and `d793097` (`846c06ba…`).
- The framing choice the ticket demands (two constants + rule, receipt-coverage validity, or
  ancestry) is deliberately left to the implementer to argue and pane 3 to challenge, with the
  rejected alternative recorded in a new decision document and defence card D22. One known
  discrepancy is flagged in the brief: the parsed receipt model carries no digests
  (`extra="ignore"`), so the ticket's receipt-coverage framing needs the real receipt inspected
  first.
- Completion condition: implementation → independent cycle-116 review → repair if needed →
  re-review → Git Lifecycle Proposal to the owner. No commit exists yet; workers hold no Git
  write authority. After that merge: re-pin → re-run the preflight → the 24-case measurement
  AX #58 exists to make possible.

### 2026-07-28 (session close) — Issue #91 merged, a live probe blocked #15 before it ran, and the first evaluation-found defect was fixed in the product

**Where to resume: [Issue #94](https://github.com/DHChe/braincrew-datateam-portfolio/issues/94).** Everything below is recorded so that does not depend on conversation memory. A copy-ready start prompt, including the three-pane topology a fresh session would otherwise discard, is at `/Users/astralpig/ax-issue-45-review/NEXT-SESSION-PROMPT.md` — kept outside the repository because it goes stale by design.

**Merged today.** Braincrew [#89](https://github.com/DHChe/braincrew-datateam-portfolio/issues/89) as `74ab1772` (PR #90, five review rounds) and [#91](https://github.com/DHChe/braincrew-datateam-portfolio/issues/91) as `43bd404d` (PR #93, two rounds). AX [#58](https://github.com/DHChe/AX_portfolio/issues/58) as `1ead1331` (AX PR #59, five CI jobs green). `develop` is at `43bd404`; the AX checkout is on `develop` at `1ead133`. Both trees clean, AX runtime stopped, volumes unchanged at 114.

**Issue #15 Phase 1 did not run, and should not have.** The authorized runtime start and a single-case probe found three blockers *before* any experiment:

- **A — the capture aborted.** 3 of 15 grounded Verification cases asked as a role AX has never defined, and the check for that compared a value to itself. Fixed by #91.
- **C — the capture cannot tell a broken answer path from a cautious one.** [#92](https://github.com/DHChe/braincrew-datateam-portfolio/issues/92), open.
- **B — the grounded answer path yields no signal**, and this one was diagnosed to root cause.

**Blocker B, measured then diagnosed.** Fifty identical repeats across five cases that all expect `direct_grounded`: **50 abstentions, zero flips**. Not noise — stable at failure. That inverted the plan: pinning sampling (`temperature=0`) had been recommended on the theory that non-determinism was the problem, and the measurement showed the *modal* behaviour is rejection, so pinning would have locked the failure in. **Measuring before changing is what caught that**, and the recommendation was contradicted by the measurement that was run to justify it.

The cause: AX's `_citations_valid` requires the union of cited claim paths to **exactly equal every populated field** of the answer, while the provider request uses a `strict: True` schema that pushes the model to populate every field. The model cites correctly but incompletely — every citation valid, 3–8 fields uncited. `provider_output_unsafe` was `False`; the label `unsafe_provider_output` covers two conditions and nothing unsafe had occurred.

**The product question this raises is the owner's to answer, and the owner owns both tracks.** Whether procedural-advice fields (`review_points`, `additional_checks`) should require citations at all is a design decision, not a defect. A partial fix was tested offline against real model output: narrowing the obligation to claim-bearing fields would have accepted one of the two inspected cases and **not** the other, whose uncited fields were genuine `grounds` and `risk_warning`. So there are **two problems, not one** — contract over-reach, which should be fixed, and model under-citation of real claims, which must not be relaxed. Do not merge them.

**AX #58 is the first evaluation-found defect fixed in the product.** Diagnosing B required temporarily patching AX's source, because `_debug_payload` was attached on the success path only — the answer you most need to inspect was the only one you could not. That is now fixed under three independently load-bearing gates, with the newly exposed content class named rather than folded into "exposure unchanged". The evidence chain is preserved deliberately: the pre-change measurement stands as the evaluation's finding on `SUT@2bcaee3`, the product change is recorded as a product decision, and the changed SUT is a new subject.

**Why #94 is next and is not mechanical.** `PINNED_AX_SHA` means both "the commit under test" (`live_experiment.py:374`) and "the commit the provisioning receipt was produced at" (`live_preflight.py:851`). They diverged today for the first time. The receipt at `2bcaee3` is still valid — a debug attachment does not touch the corpus — but re-pinning naively fails with a message that says the receipt came from an *unreviewed* commit, which is false. The re-pin is unusually safe: `backend/src` was byte-identical between `2bcaee3` and the pre-merge `develop`, so the new SUT differs from the reviewed one by **one file, +22/−2**.

**After #94:** re-pin → re-run the preflight → the 24-case measurement AX #58 exists to make possible, which separates contract over-reach from genuine under-citation and gives the citation-scope decision a basis better than two cases.

**Not claimed.** No experiment has run. No baseline, no candidate, no quality claim. Every quality observation in this repository still comes from `httpx.MockTransport`.

**Evidence outside the repository** (`/Users/astralpig/ax-live-verification-evidence/`): `08` probe and boundary, `09` the three blockers, `10` blocker A root cause, `11` runtime stop, `12`–`13` the variance measurement, `14`–`15` blocker B root cause. Two key-exposure incidents are recorded in `02` and `06`; the second prompted a standing rule that a secret value must never enter a pipeline that a downstream filter is trusted to clean.

### 2026-07-28 — Cycle 111 repairs Issue #91 after the live-path tautology survived review mutation M4

- Independent Cycle 110 review returned `REQUEST CHANGES`: Cycle 109 correctly removed the
  evaluator's double normalization, but the live producer still derived `executed_role` from the
  same case expectation. M4 replaced the recorded value with that derivation and all 505 tests
  passed. The earlier Issue #91 entry below is preserved as history; its claim that the evidence
  boundary was already independent is superseded here.
- Repair: the live capture derives the complete canonical role requirement from both retrieval and
  grounded Verification cases and compares it with AX's complete corpus-identity response map.
  Grounded observations record `answer_observation.request.roles[0]`, the adapter request actually
  constructed, instead of deriving the recorded evidence again from `case.role`.
- Retrieval alignment: retrieval roles now pass through `canonical_ax_role` for both corpus
  identity and retrieval requests, closing the same raw-role gap on both live query paths. This
  capture executes 9 retrieval and 15 grounded Verification requests; the brief's count of 45
  combines all 30 retrieval cases with the 15 grounded Verification cases and is not this capture's
  request count.
- Controlled evidence: a wrong-but-valid `Employee` request for grounded case GA-003 now reaches
  `SYS-GROUNDED-ROLE-MISMATCH`. A copied retrieval case with `hr_manager` reaches the transport as
  `HRPractitioner`. No live AX request, runtime, Docker service, AX change, or dataset edit is
  involved.
- Decision correction: [canonical AX roles and the executed-role evidence boundary](../decisions/2026-07-28-canonical-ax-role-and-executed-role-evidence.md)
  now records the false Cycle 109 claim, the exact strength of corpus versus request evidence, the
  rejected literal `LEGACY_FIXTURE_ROLES` alternative, the six-persona collapse, the 43 preserved
  golden tests, manifest v3 → grounded v2, and the deliberate fail-closed run abort.
- Completion condition: M4 and every repair clause must be killed independently, all ten gates must
  pass, and independent re-review must find no blocking issue before any Git lifecycle proposal.

### 2026-07-28 — Issue #91 fixes the AX role boundary and closes the executed-role tautology

- Phase: Issue #91 implemented on `feat/issue-91-canonical-ax-role` from verified
  `develop` commit `74ab1772`; the change remains uncommitted pending independent review.
- Contract: dataset alias `hr_manager` now maps to AX's provisioned reader identity,
  `HRPractitioner`; every canonical or pass-through role is checked against the local closed set
  `Executive | HRAdmin | HRPractitioner | Employee` before a request can be built.
- Compatibility ripple: the frozen v1 controlled dataset also contains five historical reader
  aliases that are not AX roles. The dataset remains byte-identical; those known aliases map to
  `HRPractitioner`, and only the synthetic observation fixture was corrected to record AX wire
  identities. The mapping preserves fixture replay and does not assert that the persona labels are
  semantically identical.
- Evidence boundary: `GroundedObservation.executed_role` is now compared directly with the
  canonical role expected from the case. The evaluator no longer normalizes both operands through
  the same helper and calls the self-derived result independent evidence.
- Verification: each clause was mutation-tested separately — changing the mapping to `HRAdmin`,
  deleting the unknown-role refusal, restoring double normalization, and replacing the direct
  comparison with `False` each made its named regression test fail before the fixed source was
  restored. The MockTransport acceptance path sends the three `hr_manager` Verification cases as
  `HRPractitioner`. The dataset is unchanged.
- Decision: [canonical AX roles and the executed-role evidence boundary](../decisions/2026-07-28-canonical-ax-role-and-executed-role-evidence.md).
- Explicitly not claimed: no experiment or live AX request ran during implementation. This repairs
  the harness contract; it does not establish that the dataset author's word `hr_manager` meant
  practitioner rather than approver, and it does not produce an answer-quality result.

### 2026-07-28 — Issue #89 in its fourth review round; cycle 106 dispatched, and the orchestrator's own mutation method was corrected by review

- Phase: Issue #89 — Phase 0 of Issue #15 — implemented on `feat/issue-89-run-summary-builder`
  (`HEAD = 46115c0`). Cycles 97–105: implementation → `REQUEST CHANGES` ×4 rounds, repaired between
  each. **Nothing is committed.** Cycle 106, the fourth independent re-review, is dispatched to
  pane 3 as this entry is written.
- Round history, each round changing angle and each new angle finding something the last did not:
  cycle 98 construction (B1–B6, N1–N9) → cycle 100 verdict reachability (F1, F2, M1–M6) → cycle 102
  the storage contract (G1, H1–H8) → cycle 104 the consumer layer and mutation adequacy (J1, J2, J5).
- **The owner's decision inside this ticket:** the release comparison runs on quality and latency;
  cost is excluded and the exclusion is carried in the artifact. Escalated rather than resolved by
  the orchestrator because it changes what a release decision means. Locked in
  [the operational measurement decision](../decisions/2026-07-28-operational-measurement-and-the-cost-exclusion.md).
- **A method the orchestrator got wrong, recorded because it will recur.** To show the G1 remedy was
  load-bearing, the orchestrator restored `NOT NULL` on all four operational columns *together*,
  watched one test go red, and concluded the fix was pinned. Independent review mutated the columns
  *individually*: two of the four **survived**. A collective mutation proves a test exists; it does
  not identify which clause the test protects. Cycle 106's brief carries this as a standing rule.
- **Cycle 106 returned `APPROVE`** — zero blocking findings, eight non-blocking (K1–K8). All three
  cycle-104 blockers are closed and each is pinned by a test that fails when the repair is reverted.
  The mutation measurement that failed in cycle 104 (two of four columns survived) came back
  **six of six killed** this cycle, on six columns rather than the four the orchestrator's brief
  named — the brief was wrong about the count and the reviewer widened rather than followed it.
- **The approval's disclaimer was load-bearing.** The review listed six CI gates it could not run
  (`node_modules` absent, offline by the brief's own constraint) and named the risk precisely: the
  four TypeScript/JSON paths in this diff are in Prettier's scope. Running the frontend job locally
  found **`prettier --check` failing on two files this ticket introduced**, both clean at `HEAD`.
  CI would have rejected the merge. Fixed; the change is two line-wraps and nothing else.
- All seven CI steps now reproduced locally and green: ruff format/check, mypy (70 source files),
  pytest (497), prettier, eslint, `tsc --noEmit`, vitest (6), `next build` (3/3), Playwright (2).
- **The user was given the Git proposal with K1 as an explicit scope choice, and chose to fix K1
  inside this ticket** rather than ship and file a follow-up. Cycle 107 is dispatched to pane 2 as
  this entry is written: regenerate the shipped golden dashboard export from a cost-excluded pair,
  and add the Python test that no existing test covers. The end-to-end path was already proven
  during cycle 106 review, so this is making the shipped artifact use a mechanism that works, not
  building a new one.
- **The choice left to the implementer, deliberately:** flip the four golden comparison fixtures to
  `unmeasured`, or add a cost-excluded pair alongside. The trade-off is real in both directions and
  the reason must be recorded with the rejected option.
- **The trap named in the brief:** the decision requires the cost checks to keep firing when cost
  *is* measured, so that coverage (`tests/unit/test_comparison.py:368-371`) must survive. Deleting a
  check's coverage while making an artifact honest would be the same class of error the ticket is
  about.
- **Cycle 107 closed K1**, choosing option (a). **Cycle 108 verified it and returned
  `REQUEST CHANGES` — on two documentation lines, not on the code.** Both were the orchestrator's
  own: a spliced digest abbreviation in the decision document, and an unscoped "appears nowhere"
  claim contradicted by a stale digest in this file. Both fixed; the historical line is preserved
  with a superseding pointer rather than rewritten.
- **What cycle 108 proved that cycle 107 had not.** Seven Python cost clauses mutated individually,
  seven killed — measured-cost coverage survives the fixture flip because `_mixed_run_payload` builds
  its own cases independently of the four JSON fixtures. The golden chain's PASS/FAIL/INVALID
  decisions are unchanged, because none of them was ever cost-driven. **But one coverage deletion was
  found in TypeScript (K9)**, where cycle 107 had not looked: flipping the shipped export to
  `excluded` made `isOperationalDelta`'s included-warrant path unreachable, so a mutant that was
  detectable before became invisible — *a test that still passes because its inputs no longer reach
  the branch*, the exact shape the brief named. Closed by one added vitest case, verified against the
  reviewer's own mutant list: T1, T2, T3 and T6 all now die. Frontend suite 6 → 7.
- All seven CI gates green after every fix: ruff format/check, mypy (70), pytest (**498**), prettier,
  eslint, tsc, vitest (**7**), next build (3/3), Playwright (2). Tree: 34 uncommitted paths.
- Blocked on: nothing external. Not blocked on the AX runtime — this ticket makes no live call.
- Completion condition for the current step: the authorized Git lifecycle. **No commit, push, PR, or
  merge until the user authorizes it.**
- **Deferred to its own ticket, not forgotten:** the `ParquetDecimal` annotated type that ends the
  five-instance producer/consumer sequence (decision §9), and K2–K8.
- Explicitly not claimed: **no experiment has run.** No baseline, no candidate, no quality claim.
  Every observation still comes from `httpx.MockTransport`. Phase 1 of Issue #15 — the authorized
  runtime start and the two 30-case runs — remains a separate decision.
- **Superseding closeout for Issue #89:** the Git lifecycle above completed. PR
  [#90](https://github.com/DHChe/braincrew-datateam-portfolio/pull/90) merged into `develop` as squash
  commit **`74ab1772`** with both remote jobs, `python` and `frontend`, passing. Issue
  [#89](https://github.com/DHChe/braincrew-datateam-portfolio/issues/89) was then closed manually:
  GitHub closing keywords apply only when a pull request merges into the default branch (`main`), so
  a merge into `develop` does not auto-close the issue.
- **Why the frontend job belongs in the closeout:** independent review approved the code while
  explicitly naming six CI gates it could not run and the four TypeScript/JSON paths at risk. The
  subsequent local frontend run found `prettier --check` failing on two ticket-introduced files
  before the PR was opened. The clean merge therefore depended on treating the review's disclaimer
  as actionable evidence: an approval is only as safe as its statement of what it did not check.

### 2026-07-27 — Issue #85 built Phase 0 of the live experiment, and independent review found the honesty machinery unearned

- Phase: Issue #85 implemented on `feat/issue-85-live-experiment-capture` across cycles 89–93:
  implementation → `REQUEST CHANGES` (four blocking) → repair → **`APPROVE`, no blocking finding** →
  one targeted alignment. **Nothing is committed.**
- **The prerequisite was measured before recommending, this time.** After `READY`, the natural move
  was to request authorization for #15's runtime start. Measuring first showed #15 could not start at
  all. That is the same discipline the previous cycle's error taught, applied deliberately.
- **The trap: attesting to something unobservable.** The comparison gate refuses a dirty SUT, and SUT
  dirtiness cannot be seen over HTTP. The answer was a warrant carrying the method, its subject and
  the check's returned values — not a bare boolean.
- **Review's central finding: the machinery was not earned.** Seven of eleven guards were
  load-bearing; **all four survivors carried the honesty claim.** Neutering the execution-claim
  validator survived all 433 tests. The decisive pair — fabricating the warrant was *caught*; calling
  git, **throwing the answer away**, and recording constants was *not*.
  - **Rule recorded:** a warrant that names a method is not evidence until a test pins that it
    carries *the method's result*. Until then it is worse than a bare boolean, because it reads as
    evidence.
- Three further blocking findings, all closed: every live failure produced a traceback and **exit 1**
  because `AxHttpFailure` subclasses `RuntimeError` (zero of seventeen new tests exercised a
  transport failure, on a run designed to happen once); the `logical_digest` could not be recomputed
  from the file storing it, because `captured_at` was the sole hand-serialized field; and widening
  `execution_mode` without widening `version` made *a fixture parser declaring live execution* the
  only newly-reachable parsing state — asserted by a test as intended.
- **The implementer corrected the orchestrator's ticket again:** live calls are **24, not 30**, since
  6 of the 30 Verification cases are parsing and carry no query. The orchestrator asserted a total
  without measuring its composition — the same error class as earlier in the day.
- **A blocker for the ticket this unblocks was discovered and filed as #86.** The contradiction lives
  in the design specification, which also supplies its own resolution through the per-case metric
  **applicability** concept it already declares. The reviewer verified the orchestrator's addition
  and found it stronger than stated.
- One alignment beyond the review's blocking set: `checkout_path` recorded an absolute host path into
  a citable artifact, conflicting with the standard `live_preflight.py:296` already enforces by
  refusing private paths. Fixed to a basename and pinned by a test. The reviewer had classified it
  non-blocking; the override was to a **stricter** position and is recorded as such.
- Not proven: **no experiment ran, no quality claim exists.** Phase 1 of #15 remains a separate
  decision and is additionally blocked by #86.

### 2026-07-27 — Issue #82 merged as `6ec3abc`; Phase 1 executed once, the first live artifact reported READY, and the readiness flag was earned

- Phase: the five-step runtime plan ran under explicit user authorization. Step 1 verified both
  checkouts clean at their pins, the receipt digest, the volume count (114), and — for the first
  time by direct read-only query rather than inference — the AX #44 principal row (`is_active=t`,
  exactly one user in the target tenant). Step 2 started `backend`/`worker`/`clamav` via
  `docker compose start` deliberately, so Stage 9's containers were **reused, not recreated** — all
  three container IDs byte-identical to the recorded runtime boundary. Step 3 ran the committed
  capture once: exit 0, `READY`, digest `sha256:fe38499e…e128e3`, replayed clean. Step 4 stopped
  the runtime in the Stage 12 order; volumes unchanged. Step 5: AX #43 and AX #37 closed with the
  evidence; independent review of the artifact returned **`APPROVE`, no blocking finding**.
- **An incident, reported before proceeding:** the orchestrator printed the live `OPENAI_API_KEY`
  into the session transcript while inspecting container environment — a BSD-`sed` masking flag
  failed silently and the output was emitted without confirming the mask. Blast radius: transcript
  only (verified absent from both repositories at `HEAD`). The run was **held at the operator's
  choice** until the key was revoked; the capture itself exercises no OpenAI path (six parse +
  three `corpus_identity` reads, verified in source).
- **A deviation, reported rather than absorbed:** the plan said three services; **four ran** — the
  one-shot `migrate` container started as a compose dependency. Evidence it applied nothing: zero
  alembic `Running upgrade` lines, and the schema version extracted read-only from the **pre-B
  archived dump** is byte-identical to the current one. Correction recorded for the next run:
  `docker start <container>` or `--no-deps`.
- **The review corrected the orchestrator twice more.** The evidence set claimed the
  seed-in-all-three-roles fact "had never been observed" — Stage 11 observed it a day earlier; the
  true claim is narrower (first capture through a committed command into a contract-validated
  artifact). And the brief's arithmetic hint for Employee's 130 was wrong in two places; the
  reviewer reconciled it exactly (36 = 12 tenant records + 24 pre-existing Employee-invisible demo
  records) and corroborated it with Stage 11's byte-identical `employee_visibility_invariant`
  digest. Corrections recorded in `05-independent-review.json` without rewriting the reviewed
  files.
- `braincrew_preflight_ready` moved to **`true`** — earned by all five conditions, not by a
  documentation change: the dated `false` measurements above this entry are preserved unchanged.
- Not proven: **no baseline or candidate ran, and no quality claim exists.** Issue #15 remains
  separately authorized. Replay proves integrity, not the corpus numbers; the tenant is bound by
  the capture path; `sut_commit_sha` is an assertion warranted by the Step 1 checkout check.

### 2026-07-27 — Issue #80 merged as `7f3f1bf`; Phase 0 of the runtime capture built, and a worker report disagreed with measurement for the first time

- Phase: Issue #80 merged (PR #81, squash `7f3f1bf`) and closed manually. Issue #82 implemented on
  `feat/issue-82-capture-command` across cycles 83–87: implementation → `REQUEST CHANGES` → repair →
  one extra cycle for a failing test → **`APPROVE` (scoped), no blocking finding**. **Nothing is
  committed** for #82.
- **The prerequisite the orchestrator had not measured.** After #80 merged, the recommendation was to
  request authorization for the AX runtime start. Measuring first showed **there was no way to run
  the capture** — no `src/` caller, no CLI command, v2 absent from the replay dispatch. Running it
  would have meant typing Python into a terminal, and AX PR #53 already repaired a defect of exactly
  that shape. So the plan became two phases, and the runtime start moved behind this ticket.
- **What Phase 0 caught that a typed snippet would have carried into the live run.**
  - `--tenant-id` was an unbound operator keystroke. Review ran two captures identical except for the
    tenant — one on a tenant nobody has ever reviewed — and **both returned `READY` and replayed
    `READY` forever**. The realistic harm was a **false negative** on a once-only run: a
    mistyped-but-valid UUID yields 404s → `NOT_READY`, and the runtime plan forbids repairing
    mid-run, so **an operator typo would have become a preserved artifact that reads exactly like AX
    genuinely failing**, with the single output path burned.
  - The command ran from a **dirty worktree**, stamping a `HEAD` that does not describe the code that
    ran — and replay validates the SHA's *format*, never its relationship to a tree. Every other
    artifact-producing path in this repository records `dirty_worktree`; this one discarded it.
- **First time a worker report disagreed with orchestrator measurement.** The repair reported
  `416 passed`; the orchestrator measured `1 failed, 415 passed` on the same tree. **Neither was
  miscounting** — the test asserted on framework-rendered output that Typer splits into separately
  styled fragments, so it passed where Rich emitted no escapes and failed where it did.
  - **The orchestrator's diagnosis was itself wrong in its mechanism**, and review corrected it:
    colour was blamed, but `NO_COLOR=1` suppresses colour and **not bold**, so the coupling survives
    it. Only `TERM=dumb` yields plain output. The wrong inference would have made `NO_COLOR=1` look
    like a sufficient guard in future work.
  - Rule recorded: this repository's existing CLI tests assert on **application-emitted** strings from
    `typer.echo`, which are plain. This was the first to assert on **framework-generated** output.
    Different classes; only the second needs CSI stripping.
- **Scope discipline in review.** Pane 3's usage window had limited headroom, so cycle 87 was
  deliberately narrowed to four questions and its verdict **states the reduced scope and what it does
  not re-assert**. A review that dies halfway is worth nothing; an approval read more broadly than it
  was earned is worse.
- Documentation: locked in `docs/decisions/2026-07-27-live-verification-capture-command.md`, defended
  as card **D14**. Carried forward there: the repository-internal `--output` path, the wrong-`base-url`
  verdict question, the triple receipt read, provenance the artifact structurally cannot carry, and
  the `PROJECT_ROOT` wheel-install fragility.
- Not proven: **nothing was captured.** `braincrew_preflight_ready` stays `false`. Phase 1 — the
  authorized AX runtime start — remains a separate decision, and AX #37 and AX #43 remain open formal
  blockers of Issue #38.

### 2026-07-27 — Issue #77 merged as `87c0fc4`; Issue #80 gave the verdict a negative value, and a coverage justification was found to have expired

- Phase: Issue #77 merged (PR #79, squash `87c0fc4`) and closed manually. Issue #80 implemented on
  `feat/issue-80-preflight-readiness-verdict` across cycles 79–82: implementation → `REQUEST
  CHANGES` → repair → **`APPROVE`, no blocking finding**. **Nothing is committed** for #80.
- **The ticket existed to prevent a specific mistake.** Issue #38 asks the artifact to report
  `READY`. Measured before starting: a v2 artifact could exist *only* on complete success, so
  `Literal["READY"]` would have been a **constant, not a judgment**. Criteria **4** and **6** were
  therefore one problem — a verdict needs something to say when it is negative, and criterion 4
  already named it: a stable typed blocker. **Option A** was chosen and the same-day rule that v2 may
  not retain blockers was **deliberately reversed**, with its test **renamed and re-scoped rather
  than deleted**.
- **Blocking finding 1 — a verdict on a shared model is not a bound claim.** `readiness` sat on a
  model serving three schemas and was validated only in the v2 branch. A **genuinely blocked** v1
  capture with `"readiness": "READY"` inserted **replayed clean**, reporting
  `{"blocker_count": 1, "readiness": "READY"}` — the exact contradiction v2 refuses by name. The
  exposure was inverted: `cli.py` could print the *unvalidated* verdict and could not print the
  *validated* one. Closed by one clause, following the precedent `capture_contract` already set.
- **Blocking finding 2 — a coverage justification expired.** #77's decision §8 left six clauses
  untested and justified it explicitly: *"the validator's call site is observed."* That was true when
  written. This change added a **second** call site, where detaching turned **zero** tests red. Two
  of the re-opened clauses were the headline findings of the two prior reviews — the
  one-tenant-across-both-halves rule and the privacy clause forbidding a failed request from
  claiming a response correlation id. Disabling the corpus-blocker tenant fold left the suite
  **fully green at 405 passed**, reproduced independently.
  - **The rule now written down:** adding a call site to a validator whose coverage rests on "the
    call site is observed" inherits the obligation to observe the new one. Nobody was wrong; a true
    statement quietly stopped applying.
- **Method note — the orchestrator's brief was wrong and the reviewer said so.** Cycle 80's brief
  listed "`docs/` untouched" as scope discipline to confirm, which conflicts with Issue #80's
  acceptance criterion 4 requiring a decision document. The reviewer reported it **against the
  ticket, not against the brief's author**, and correctly separated "does not block the code" from
  "does block ticket closure." The next brief stated the intended split explicitly. The reviewer also
  re-ran **all thirty** of its own mutations rather than the two the orchestrator had probed —
  a repair closing only those two would have looked identical from the orchestrator's side.
- Documentation: locked in `docs/decisions/2026-07-27-live-verification-readiness-verdict.md`,
  defended as card **D13**. Carried forward there: nine unobserved clauses (#78), the redundant-pair
  prefix checks that must not be "simplified" away, the missing v2 CLI surface, the same
  field-scoping shape on `dataset_identity` for the generic schema, and the fact that the dossier is
  **load-bearing for two test files**.
- Not proven: **nothing was captured.** Everything is `httpx.MockTransport`.
  `braincrew_preflight_ready` stays `false`. A `READY` artifact remains compatible with an empty
  inventory — deliberate, and in force. AX #37 and AX #43 remain open formal blockers of Issue #38.

### 2026-07-27 — Issue #77 implemented, rejected, repaired and approved; three errors in the orchestrator's own ticket and briefs were corrected along the way

- Phase: TDD implementation of Issue #77 on `feat/issue-77-preflight-artifact-v2`, based on
  `d429cb1`. **Nothing is committed**; the next step is a separately authorized Git proposal.
- Cycle 75 implementation → cycle 76 review **`REQUEST CHANGES`** (two blocking defects) → cycle 77
  repair → cycle 78 re-review **`APPROVE`, no blocking defect**.
- **Blocking defect 1 — the composition claim was half unverified.** The v2 artifact exists to say
  *these three things are one observation of one principal boundary*. The corpus half was bound to
  nothing: all three role observations could name a different tenant **and** a different subject and
  the artifact validated and replayed clean; a corpus observation with **zero HTTP attempts** was
  accepted, asserting a role-visible corpus identity with no evidence any request was issued. Fixed
  by mirroring the parse-side request validator and folding corpus tenants into the **same**
  `tenant_ids` set, which can only tighten — the rule is `len(tenant_ids) != 1` and threading only
  ever adds elements.
- **Blocking defect 2 — the load-bearing line had no test above it.** Deleting the five-line
  `_validate_principal_attachment_capture` reuse removed the reviewed-subject binding, the
  single-tenant rule, the frozen timeout, probe-set completeness, and the parse-evidence, span and
  attempt checks from the **entire** v2 contract, and the suite still reported `370 passed`. Seven of
  nine refusals on the new path were unobserved. Now all are, plus 21 more.
- **Three errors of the orchestrator's own, all found by others or by measurement:**
  - the ticket cited the corpus-observation refusal at `:708`; it is `:703`. Corrected before
    dispatch.
  - the ticket claimed that refusal "is currently observed by tests." **It had zero coverage** —
    `git grep` at `d429cb1` returns one hit, in `src/` only. Caught by review, not by me, in a ticket
    whose whole premise is that claims must be measured. The implementation's new test is the first
    that has ever observed it.
  - the cycle-77 brief said Issue #77 had three comments; it has two. Caught by the implementer.
- **Method note.** The orchestrator withheld its own findings from the reviewer again, and again the
  reviewer found something the orchestrator had not — defect 2, the more serious of the two. The
  orchestrator independently reproduced both defects and both repairs rather than accepting the
  reports, and verified the reviewer restored the working tree exactly after 35 mutations
  (`shasum` and `git diff --numstat` both matching).
- Documentation: the contract is locked in
  `docs/decisions/2026-07-27-live-verification-preflight-artifact-v2-contract.md` and defended as
  card **D12**. Known gaps are recorded in §8 of that decision and tracked as a follow-up covering
  **both** halves, because fixing the corpus side alone would leave the asymmetry it was measured
  against.
- Not proven: **nothing was captured.** Every result comes from `httpx.MockTransport`.
  `braincrew_preflight_ready` stays `false`, no AX runtime was started, and AX #37 remains an open
  formal blocker of Issue #38.

### 2026-07-27 — Issue #75 merged and closed; Issue #77 dispatched, with two errors in its own ticket corrected first

- Phase: Issue #75 merged as `d429cb1` (#76) and closed manually — this repository's default branch
  is `main`, so closing keywords never fire on a `develop`-targeted merge. Issue #77 was created,
  labeled `ready-for-agent`, and its implementation cycle dispatched on
  `feat/issue-77-preflight-artifact-v2`.
- **Two defects in the ticket I wrote were found and fixed before the implementer saw it**, both by
  re-measuring claims rather than re-reading them:
  - the corpus-observation refusal was cited as `live_preflight.py:708`; on `d429cb1` it is
    **`:703`**, and `:708` is an unrelated local. The claim was right and only the anchor was wrong,
    but the anchor sits at exactly the point the ticket tells the implementer to be careful.
  - acceptance item 2 said the count of production callers of `AxHttpAdapter.corpus_identity()` must
    stop being zero, without defining "production path". Measured: the precedent capture,
    `capture_principal_attachment_preflight`, has **no CLI command and no `src/` caller either** —
    only tests call it. Left unresolved, an implementer would reasonably have added a CLI command
    this ticket never asked for. Both corrections are a comment on the issue, with the body edited.
- Method note worth keeping: **the checkpoint above was rewritten as part of dispatching this cycle,
  not after reporting it.** PR #72 existed solely to repair a stale checkpoint, and the same
  staleness recurred two cycles later, so the repair is now attached to the action that causes it.
- Completion condition for this cycle: pane 2 writes `DONE` to
  `sentinel-pane2-cycle75.txt`, a harness-tracked watcher observes it, and pane 3 reviews
  independently before any Git proposal. **No Git write is authorized**; the worker is prohibited
  from `commit`, `push`, `add`, branch creation, PR and merge.

### 2026-07-27 — Issue #75 implemented; v3 dataset identity and receipt-bound probes now have separate authorities

- Phase: TDD implementation of Braincrew Issue #75 on
  `feat/issue-75-bind-v3-decouple-probe-set`, based on `a846058`. **Nothing is committed**; cycle 71
  is the independent review and no Git lifecycle action is authorized.
- Authority: the repository owner's locked Option C decision in
  `docs/decisions/2026-07-27-dataset-identity-axis-analysis.md` §18. The preserved §10 remains
  historical recommendation text, not the decision.
- Blast radius was re-measured rather than copied from the ticket. Across the ticket's broad
  v2-reference inventory, `2.0.0|dataset_manifest_v2` matches **32 lines across 8 files** at HEAD,
  not the stated 28 occurrences. Most are intentionally preserved historical v2
  qualification/freeze evidence. The behavior-changing radius was measured by the required
  constants-first run: **19 failed, 346 passed across 3 test modules**.
- RED evidence: changing only the frozen dataset constants to v3 made existing v2
  `dataset_validation` fixtures fail the frozen identity gate. Three acceptance failures, one
  receipt-binding failure, and fifteen principal-attachment contract failures then either returned
  `dataset_identity_mismatch` before HTTP/evidence checks or built the generic artifact shape
  instead of the principal-attachment shape. This demonstrated that the old manifest binding held
  up the whole principal capture suite, not only `_approved_mapping`.
- Probe authority was independently verified before implementation:
  `REVIEWED_PARSING_SOURCE_EVIDENCE` contains exactly six `synthetic-rule-*` entries; all six stored
  digests equal the SHA-256 of their stored canonical text, and all six texts are byte-identical to
  the historical reviewed source documents. `_parse_evidence_failure` consumed only
  `case.document.canonical_text` from its manifest-derived `ParsingCase`.
- Change: the frozen integrated identity now uses `3.0.0`, `DATASET_V3_DIGEST`, and a protected copy
  of `DATASET_V3_COMPONENT_DIGESTS`. The manifest-derived `_verification_cases` function and its
  duplicated `"2.0.0"` literal are removed. Capture member order comes from the reviewed handoff
  receipt after its case set is checked against `REVIEWED_PARSING_SOURCE_EVIDENCE`; strict parse
  comparison receives the frozen reviewed source digest directly.
- Naming: source uses `reviewed_probe_evidence`; tests use `reviewed_probe_cases`. Neither name calls
  the probes a dataset, manifest, version, or parsing component.
- Acceptance evidence: the bound v3 manifest's Verification documents are all `demo-*`, the
  reviewed operational probes are `synthetic-rule-*`, the test asserts the sets are disjoint, and
  the six-probe capture plus replay still succeeds. The complementary receipt test replaces one
  reviewed case and observes refusal before capture.
- Pre-gate evidence: the three affected test modules pass **38 tests**, followed by a full
  **365 passed** run. Final six-gate evidence belongs to the cycle-70 completion report.
- **`braincrew_preflight_ready` remains `false`.** Issue #75 does not add
  `live-verification-preflight-artifact-v2`, role-visible corpus capture, a live runtime start, or
  reconciliation of AX #37/#43.
- Exact next action and entry condition: cycle 71 independent review in the existing pane 3,
  retaining a fresh review context so implementation assumptions are not inherited as evidence.
  Approval requires the v3 identity, disjoint-set success test, receipt mismatch refusal, naming
  boundary, and all six gates to reproduce with zero blocking defect.

### 2026-07-27 — Issue #71 implemented; the re-pin's one real risk turned out to be loud, not silent

- Phase: implementation of Braincrew Issue #71 on `feat/issue-71-repin-evaluation-sut-commit`, based
  on `931d404`. **Nothing is committed**; independent review is cycle 64 and no Git lifecycle action
  is authorized.
- Active skill or workflow: the standing three-pane cycle recorded in `AGENTS.md`. Cycle 63
  implemented; cycle 64 reviews independently; cycle 65 is integration judgment.
- Change: `PINNED_AX_SHA` and the packaged Adapter contract's `sut_commit_sha` both move from
  `72805930…` to `2bcaee34…`, plus seven test files carrying the same assertion. **9 files, 11
  insertions, 11 deletions** — the whole diff is the value, not its shape. Blast radius re-measured
  before starting at 39 matching lines across 9 files, unchanged from the ticket's figure.
- **The ticket's own risk description was wrong, and the correction is worth more than the fix.**
  Issue #71 warned that a find-and-replace would "silently convert" the unreviewed-commit negative
  test into something meaningless. Measured: it fails **loudly**. `test_receipt_from_unreviewed_sut_commit_refuses`
  fed `APPLIED_AX_SHA`, which equals the new pin, so the receipt passes the SUT-commit gate and the
  assertion reports `DID NOT RAISE`. Reproduced independently by pane 1 in the exact intermediate
  state: **1 failed, 363 passed.**
  - So the danger was never detection — it was the **repair decision**. Deleting the test, weakening
    its `match=`, or re-pointing the constant at the new pin would each have removed the general
    protection while turning the suite green.
  - The implementer chose a third SHA, `d7930978…`, which is a **real unreviewed AX commit**
    ("Assert what the bind mount is, not how Docker spells it"), and renamed the constant
    `APPLIED_AX_SHA` → `UNREVIEWED_AX_SHA`. The rename is the better half: the old name described
    what the value *was* at one moment, the new one describes its *role in the test*, which is what
    stops it rotting the same way again.
- **Orchestrator error, corrected.** The cycle-63 brief instructed pane 2 to append this status
  entry, contradicting pane 1's own practice since cycle 54 of owning this file. pane 2 declined,
  citing the SUT decision's §6, and followed the authority over the brief — which is exactly what
  "the brief is direction, not authority" exists for. Its citation slightly over-reads §6, whose
  scope sentence refers to cycle 54 rather than standing policy, but the inconsistency was pane 1's
  and the entry is written here.
- Verification: `ruff format --check`, `ruff check`, `mypy` over 65 source files, **364 passed**,
  clean `git diff --check`, `HEAD` still `931d404`. Run by the implementer and reproduced by pane 1.
- **`braincrew_preflight_ready` remains `false`.** This makes artifacts *constructible*, not
  *captured*; live HTTP parse capture still needs a separately authorized AX runtime start. AX #37
  and #43 also remain open.
- Exact next action and entry condition: cycle 64 independent review — the negative test still
  refuses on a genuinely unreviewed SHA, both pinned points moved atomically, the four historical
  documents are unchanged, and `FROZEN_DATASET_VERSION` and `live_preflight.py:951` are untouched.
  Only after that does a Git proposal follow.

### 2026-07-26 — Cycle 55 returned REQUEST CHANGES; two of the three blocking defects were the orchestrator's own

- Phase: review of the cycle-54 artifacts. Cycle 56 repairs them. Nothing is committed; `HEAD` is
  still `dfc41ff`.
- Review evidence: the independent reviewer **approved the central judgment** — `2bcaee34…` is
  acceptable as the evaluation SUT commit — after confirming the classification criterion, the
  per-commit evidence, the negative-test warning, and the blast-radius figures. It then raised three
  blocking defects, **two of them against the orchestrator's own authored documents.**
- **Orchestrator error 1, corrected.** The interview dossier repeated the claim that
  `FROZEN_DATASET_VERSION = "2.0.0"` beside an AX corpus labelled `3.0.0` is a "name collision, not a
  mismatch". That reasoning is **wrong**: `corpus_qualification.py` declares the AX label as a literal
  alongside Braincrew's **own** `DATASET_ID` and `DATASET_VERSION = "3.0.0"`, pointing at Braincrew's own
  `dataset_manifest_v3.json`. Same namespace, same authority — a real representation defect, not a
  collision. The dossier now records it as a defect and gives the measured reason it stayed out of
  Issue #67's scope: integrated v2's parsing component is `parsing_cases_v1.json`
  (`synthetic-rule-015…020`) and integrated v3's is `parsing_cases_v2.json` (all `demo-*`), sharing
  **no document at all**, so raising one constant changes the case set. The digest comparison blocks
  the mismatch fail-closed, so "silently" was also an overstatement.
- **Orchestrator error 2, corrected.** The dossier reported "2 of 33" principal-path tests running
  against the real pinned digest. Measured: **37 total, 33 override, 4 do not**, and of those 4 only
  **one** reaches a comparison against the real pinned value. The "33" was a pre-repair count;
  the arithmetic is consistent with it going stale when the repair cycle added four tests, but that
  causal step is **inferred rather than verified** — the cycle-level history is not recoverable from
  Git after the squash merge. The error understated the orchestrator's own coverage rather than
  inflating it, but a document that offers numbers as evidence cannot carry wrong ones.
- **Orchestrator error 3, in a brief rather than an artifact.** The cycle-55 brief told the reviewer
  that `datasets/parsing/parsing_cases_v2.json` "carries no version field at all", so the
  implementer's citation was "unsupported by the file". **The file does carry it**, nested under the
  `dataset` object: `"version": "2.0.0"`. The orchestrator had inspected only top-level scalar keys.
  The implementer's citation was accurate.
  - This matters beyond the fact. It was the **one** input that undercut the implementer's side of a
    dispute the orchestrator had an interest in, and it was presented to the adjudicator as a
    verified fact. Recusal alone was not sufficient protection; the inputs a recusing party supplies
    must themselves be independently checked, including the ones that favour the other side. The
    reviewer caught it only because the recusal disclosed the interest and explicitly invited a
    charge of biased framing. **The safeguard worked, and it was needed.**
- **Orchestrator error 4, corrected — inside the correction itself.** The annotation added to the
  locked decision to fix its wrong claims introduced a new wrong claim: it marked the original's
  "canonical text for cases 015–020 is byte-identical to the AX-B bundle" as refuted. **That claim is
  true**, re-measured byte for byte against the six AX-B bundle files, and it is the reason today's
  binding (integrated v2 → parsing v1 → the six `synthetic-rule-*` documents) is coherent at all. The
  supposed refutation compared integrated v2's parsing component against integrated **v3's** — a
  comparison the original never made. The annotation now records the claim as confirmed true and
  names the adjacent false claim it is easily confused with.
  - **The pattern is worth more than the fact.** Twice in this review chain the orchestrator declared
    a true statement refuted after comparing the wrong pair of things — first by reading only
    top-level JSON keys and missing a nested one, then by checking a different pair than the sentence
    named. Both times the error ran in the orchestrator's own favour. The habit that catches it:
    before recording any claim as refuted, copy out the two things the claim itself compares, and
    confirm the refuting evidence compares **those same two things**.
- Non-blocking finding now recorded: **Issue #38's acceptance criteria contradict themselves.** One
  criterion requires nested parsing component `2.0.0` **and** "the six reviewed historical parsing
  Verification cases" in the same sentence, and no repository state satisfies both — the six reviewed
  cases live under integrated v2, whose parsing component is `1.0.0`. This is a **specification
  defect**, not a code defect, and it blocks the follow-up dataset-identity work until resolved.
- Exact next action and entry condition: cycle 56 repairs the implementer's §9 (replace a guess with
  a measurement, strengthen a prescription that breaks if implemented literally, record the Issue #38
  contradiction) while the orchestrator's two document errors are corrected in parallel. Cycle 57
  re-reviews the delta. No implementation and no Git lifecycle action until that review passes and is
  separately authorized.

### 2026-07-26 — Issue #67 merged and closed; the "automatic closure" expectation is corrected, and the SUT-commit review opens

- Phase: Issue #67 complete. Cycle 54 opens two parallel scopes — the AX SUT-commit-for-evaluation
  review, and this record plus the interview defence dossier.
- Merge evidence: PR #69 squash-merged into `develop` as **`dfc41ff`**, parent `c7431f4`. The remote
  and local branches were deleted. Gates re-run on the merged `develop`: `ruff format`, `ruff check`,
  `mypy` over 65 source files, **364 passed**, clean tree. Both pinned values survive the merge
  unchanged.
- **Correction, general and reusable: a `develop`-targeted merge never closes an issue
  automatically.** The prior entry named "automatic closure of Issue #67" as a completion condition;
  it did not fire, and Issue #67 stayed `OPEN` after the merge. GitHub's closing keywords act only
  when a pull request merges into the repository's **default branch**, which here is `main`, not
  `develop`. The `Closes #67` line in PR #69 therefore had no effect. Issue #67 was closed manually
  as `COMPLETED` with the merge commit cited.
  - The same expectation appears in the 2026-07-19 Issue #7 entry. **That entry is left unedited on
    purpose** — it records what was planned at the time, and rewriting past records to match present
    knowledge destroys the audit trail. Checking that issue's timeline shows it too was closed by a
    person, not by a merge event, so the expectation was never satisfied in this repository. Future
    entries should state manual closure, or defer closure to the `develop` to `main` release where
    the keyword does fire.
- Interview defence dossier updated, as `AGENTS.md` requires when a decision locks. Card D10 carried
  the decision but stopped at the decision, so its implementation-stage material was missing: the
  Pydantic validator authority gap and why carrying the derived mapping inside the artifact was
  rejected as self-certifying; the mutation-testing evidence; the fact that the two guard tests are
  load-bearing only through their `match=` strings; and that most principal-path tests necessarily
  override the pinned digest. The count first recorded here was wrong and was corrected the same day —
  measured, 33 of 37 override it, 4 do not, and only one of those four reaches a comparison against
  the real pinned value.
- Measurement correction for the next ticket: the receipt-derived binding decision states the
  `PINNED_AX_SHA` re-pin touches "36 occurrences across 13 files". Measured today it is **50
  occurrences across 15 files** — Issue #67 added references in two test files. The decision
  document's figure is stale, not wrong at the time it was written.
- Exact next action and entry condition: cycle 54 produces a decision document reviewing whether
  `2bcaee3495fd7b3f624398819575cd86a5a15c47` is acceptable as the SUT commit **for evaluation**
  rather than as the **provisioning** execution commit it was already reviewed as. Re-pinning is not
  the assumed outcome. Cycle 55 reviews that decision and this dossier update independently. No
  implementation, and no Git lifecycle action, until the decision is locked and separately
  authorized.

### 2026-07-26 — Issue #67 re-review returned APPROVE; PR #69 published and passed its first remote gate

- Phase: publication of Braincrew Issue #67 from
  `feat/issue-67-receipt-derived-preflight-binding` into a reviewed pull request. The
  implementation and review cycles are complete; merge is not yet authorized.
- Active skill or workflow: the three-pane orchestration cycle recorded in `AGENTS.md`, followed by
  the Git Lifecycle Proposal Gate. Cycle 50 implemented, Cycle 51 reviewed independently, Cycle 52
  repaired, Cycle 53 re-reviewed the delta only.
- Review evidence: Cycle 53 returned **`APPROVE`**. Both Cycle 51 blockers were closed and the
  closure was proved rather than asserted — **mutation testing** disabled each fail-closed guard in
  turn and confirmed its test fails, and an assertion-level comparison against the base found all
  66 existing assertions preserved in order with 3 added, none removed or modified. The reviewer
  recorded the limits of its own method: the mutations reproduced one refactor shape rather than all
  possible ones, and the real-subprocess test could not be mutated because the child process imports
  the installed source.
- Correction carried forward: the implementing pane reported that synthetic fixture identifiers had
  replaced retired operational IDs, but the replacement covered only the new contract file. The
  retired UUID `2c7d525b-…` remains in three other test files as harmless fixture data. The summary
  was not wholesale, and independent verification is what caught it.
- Publication evidence: Lore commit `bc20136` is the head of
  `origin/feat/issue-67-receipt-derived-preflight-binding`, and [PR #69](https://github.com/DHChe/braincrew-datateam-portfolio/pull/69)
  targets `develop` at `c7431f431d92635b53d91595d1cbad96e011a3ca`. Both remote checks passed —
  `python` and `frontend` — and GitHub reports `CLEAN` and `MERGEABLE` with zero requested changes,
  review comments, or unresolved blockers. The pull request was transitioned out of draft only after
  those checks passed.
- Authorization: the user approved the commit, push, and pull request with the ready transition
  conditioned on a passing gate, then approved publishing this status entry before an authorized
  squash merge. Merge itself remains a separate authorization.
- Still not proven by this publication: the pinned digest's own correctness, which no in-repository
  test can establish because copying the receipt in is forbidden — it rests on the Stage 11
  independent review plus manual SHA-256 recomputation by three separate reviewers, and a typo in
  that constant would leave all 364 tests green. Live HTTP parse capture remains unexercised because
  the AX runtime is stopped by Stage 12. `braincrew_preflight_ready` stays **`false`**.
- Exact next action and entry condition: squash merge PR #69 into `develop` and delete the remote
  branch, then verify the merged state, the squash commit's ancestry in a fetched `origin/develop`,
  automatic closure of Issue #67, and remote branch deletion before reporting completion. Do not
  merge if any required check regresses on the new head.

### 2026-07-26 — Issue #67 receipt-derived preflight binding entered review repair verification

- Phase: implementation of Braincrew Issue #67 on
  `feat/issue-67-receipt-derived-preflight-binding`; no Git lifecycle action is authorized in this
  pane.
- Active skill or workflow: `test-driven-development`. Cycle 50 introduced the receipt-derived
  binding; Cycle 52 adds regression observations for two previously uncovered fail-closed guards
  and makes subprocess test execution explicit without redesigning that implementation.
- Expected artifact and completion condition: `live_preflight` must recompute the independently
  reviewed handoff receipt SHA-256, derive the reviewed subject and six case-to-attachment probe
  mapping only from matching bytes, preserve principal-artifact replay validation through Pydantic
  context, and pass the six repository verification commands without changing the pinned AX commit
  or frozen dataset version.
- Review and repair evidence: Cycle 51 pane 3 returned `REQUEST CHANGES`, and pane 1 independently
  reproduced both blockers. Cycle 52 now observes the missing-validation-context and missing-replay-
  receipt refusals directly, replaces 14 subprocess-looking in-process calls with an explicitly named
  `_replay_in_process` helper, and runs one real `uv run braincrew-eval` subprocess that returns exit
  code 2 when a principal artifact omits `--handoff-receipt`. The receipt contract set reports
  `11 passed`, the combined principal contract set reports `34 passed`, and the CLI acceptance set
  reports `3 passed`. Synthetic fixture identifiers no longer reuse retired operational IDs, both
  five- and seven-attachment counts are rejected, and the digest-pin monkeypatch uses its default
  symbol-existence check.
- Completion evidence: the Cycle 52 repository gates report `65 files already formatted`,
  `All checks passed!`, no mypy issues in 65 source files, `364 passed`, and a clean
  `git diff --check`. Correctness of the pinned receipt value is not established by a self-pinned
  test; it rests on the Stage 11 result plus independent receipt-byte SHA-256 recomputation by panes
  1, 2, and 3. `braincrew_preflight_ready` remains **`false`** because the live runtime is stopped
  and the receipt's applied AX commit is not the currently reviewed evaluation SUT commit.
- Exact next action and entry condition: after the Cycle 52 six-command rerun, hand the uncommitted
  diff to panes 1 and 3 for independent re-review; both blockers must be closed and the repository
  gates reproduced before any separately authorized Git proposal.

### 2026-07-26 — the twelve-stage live apply executed end to end; AX-B is applied and verified

- Phase: live operational execution, Stages 1 through 12, each separately authorized by the user.
- Authorization shape: Stage 9 authorization carried the failure-freeze authority the runbook
  requires — the power to stop exactly the Compose `worker` service on a first post-mutation
  failure, because the CLI stopping does not stop the worker. Stage 10 authorization carried the
  acknowledgement that `HRAdmin` approval permission had not been pre-probed and would first be
  verified after durable state existed. Neither was ever exercised as a freeze; both were required
  before starting.
- Completion evidence, measured rather than inferred:
  - handoff receipt `state=COMPLETED`, `completion_confirmed=true`, logical digest
    `sha256:33108cb53fa12c7167bd33af9f2256a420afd7576b535d9debb2b89ffcd20977`;
  - corpus `14/77/77/154` → `20/83/83/166`, with `+6` attachments, extractions and tenant sources
    and `+12` vectors, each delta re-measured in the database rather than taken from the receipt;
  - the six new upload-version rows equal exactly the receipt's six AX-generated approval IDs;
  - blob root holds six files totalling 514 bytes, the exact sum of the six reviewed bundle files;
  - `Employee` sees inventory 130 while `Executive` and `HRPractitioner` see 166 — the `hr_only`
    visibility policy working, not asserted;
  - Stage 11 independent verification returned `PASS`; Stage 12 stopped the worker first and left
    PostgreSQL, Redis and Neo4j untouched at restart count zero with the volume set unchanged.
- Blockers found and cleared mid-flight, in the order they surfaced: the Stage 7 evidence scope did
  not close (AX PR #53); `develop` went permanently red on a wall-clock time bomb unrelated to this
  work (AX PR #54, follow-ups AX #55 and #56); a redis container came up with no network attached
  and reported `healthy` anyway; and Stage 9's bind-mount assertion could not pass on Docker Desktop
  for macOS (AX PR #57). Each was adjudicated independently before any fix, and in two cases the
  adjudication overturned the orchestrator's first reading.
- Corrections the orchestrator applied to its own reporting, recorded because the honest version of
  the record includes them: a JSON census counted intended paths rather than the filesystem and
  missed a seventh file; a baseline query omitted the tenant scope and returned all-tenant totals; a
  content-hash query used a column name that does not exist; a claim that an amended assertion was
  "not more permissive" was false and was replaced with a truth table; and `dead_letter` job dates
  conflated `created_at` with `updated_at`.
- Explicit exclusion: **no quality result is claimed.** A successful apply proves the lifecycle
  executed and produced the exact expected rows. It says nothing about parsing accuracy, retrieval
  quality, or grounded-answer quality, and `braincrew_preflight_ready` has not been re-measured.
- Next action, completed same day: `braincrew_preflight_ready` was re-evaluated against the applied
  corpus and is **`false`** — one of two recorded causes cleared, and a third pin was discovered.
  See the exclusions bullet in the current checkpoint. A scope analysis of what it would take to make
  it true returned **Reconsider Scope**: the flag is a prose claim rather than a computed value,
  three independent pins are stale, the identifier a constants refresh would update is not the
  identifier the version rows use, and the runtime required to validate any option has been stopped.
  The open decision is whether Issue #38's recorded "receipt consumer only" role is a binding
  architectural commitment or merely descriptive; that single answer determines whether the binding
  is re-pinned or derived from the receipt contract.

### 2026-07-25 — AX-B dry-run contract merged, live apply runbook merged, and authorized operational preparation executed

- Scope of this transition: **AX code completion plus authorized operational *preparation*.** No live
  apply was performed. The exclusions at the end of this entry are binding.
- **AX Issue #48 — the no-write dry-run contract.** The scope lock's ordered execution named an
  "AX-B dry-run → independent dry-run review" step that the merged AX-B tool could not perform: its
  CLI had no dry-run mode and its first invocation was destructive. Rather than amend the ordered
  execution, the user chose to add the mode. Independent review authored the contract, which was
  published as a locked ticket.
- **The contract was audited by its own author before implementation.** The audit asked the
  adversarial question — could an implementation satisfy every acceptance checkbox and still be
  wrong? — and found **fourteen items**. **Six were adopted into a published amendment** while
  implementation was still in progress, so the semantics were pinned rather than discovered late:
  ordering-dependent database-read classification; no failure code for a receipt-write failure; an
  `unprovable` list that an empty array would have satisfied; a probe `401` misreported as a
  corpus-identity failure; a `503` classifiable under two codes; and receipt fields specified in
  prose rather than schema. The audit also recorded three attack angles that came back **clean**,
  which is what made it credible rather than performative.
- **Merge results.** The implementation merged as AX PR #49, squash commit
  `2bcaee3495fd7b3f624398819575cd86a5a15c47`; AX Issue #48 is `CLOSED`/`COMPLETED`. The twelve-stage
  live apply runbook merged as AX PR #50, squash commit
  `92681d3cb388eb95b7002e2013344914e035b196`. **AX PR #51 merged as squash commit
  `38a29fae8f90095bf3699bfa8cdab109bd3780fe`**, which records the recovery-procedure defect the
  rehearsal exposed.
- **Authorized operational preparation was executed**, under explicit user authorization, read plus
  external-write only:
  - the **post-import/pre-A database snapshot now exists** at sha256
    `d1b5acb445504f2f22d10c92a19e8ea65967aa543fdc43f4bf3ea59ec296f2b7`;
  - **cluster globals were captured** at sha256
    `74adc2d0ccbfb44b01ae39bd0ead8ec996a867e2978fee5d8aec3c09a4e53625`;
  - the **attachment blob volume was observed with zero entries**;
  - `tenant_provider_transfer_policies` holds **zero rows**, so a non-`fake` embedding adapter fails
    closed rather than transmitting source text externally;
  - the **target-tenant baseline was measured live as exactly `14/77/77/154` with zero attachments**,
    converting a long-standing unverified prose assumption into a measurement;
  - an **isolated restore rehearsal succeeded in one second with zero errors** and reproduced live
    state on nine verification checks.
- **Material finding: `pg_dump` alone is not a recovery point.** The restored `ax_seed_operator`
  role lost `SELECT` on the attachment tables. Its access comes from membership in the cluster-level
  predefined role `pg_read_all_data`, and a database-scoped dump captures neither role memberships
  nor role settings. The recovery point is therefore an **ordered procedure — apply globals first,
  restore, reconcile, verify — not a file pair.** This defect was found *because* the rehearsal was
  performed; a checklist-style checkpoint would have missed it entirely.
- **Independent audit of that evidence returned `EVIDENCE OVERSTATED`.** The grounds were specific:
  the clean restore depended on an undocumented role pre-creation step, so the rehearsal was not
  reproducible from its own evidence; `globals.sql` carried no recorded digest, leaving half the
  declared recovery point unbound; and replaying globals against the live cluster is not the
  operation that was rehearsed. **All five corrections were applied.** The audit also confirmed what
  held: every recorded digest reproduced exactly, all required table definitions and the vector
  extension were present, and the `pg_read_all_data` diagnosis was correct and empirically confirmed.
- **Both blockers behind the earlier `NOT SAFE YET` verdict are now closed** — the missing
  post-import/pre-A recovery point exists and has been rehearsed, and the unperformable dry-run step
  is implemented. All eight section-7 preconditions are resolved. This removes the basis for that
  verdict; it does not by itself declare the operation safe.
- **Exclusions in force.** AX-B has **not** been applied live. No live attachment, extraction,
  approval, materialization, corpus identity, parse observation, or operational receipt exists. The
  corpus is **unchanged at `14/77/77/154`**. `braincrew_preflight_ready` is `false` and Braincrew
  Issue #38 remains blocked. Two items remain explicitly unproven: **restore into the live cluster**,
  including the `CREATE ROLE` conflict when replaying globals there, and **blob recovery**, which no
  archive contains and which becomes permanently non-reconstructable once AX-B runs. No parsing,
  retrieval, grounded-answer, or `READY` claim is made.

### 2026-07-25 — AX-B Issue #45 implemented, reviewed, repaired, and merged; both pull requests closed

- Scope of this transition: **AX code completion only.** It merges reviewed code and documentation.
  It does not apply anything to a live system. See the exclusions at the end of this entry.
- Specification defect and authorized resolution: pre-implementation review found that the locked
  "upload all six files in one multipart request" instruction was **not executable**, because AX
  enforces `MAX_FILES_PER_OPERATION = 5` per upload request
  (`backend/src/ax_engine/attachments/intake.py:12,54`, applied at
  `backend/src/ax_engine/attachments/service.py:64`), with
  `backend/tests/unit/test_attachment_intake.py` pinning the six-file rejection. Acceptance
  checkbox 2 was therefore unsatisfiable and checkboxes 3-7 were transitively blocked. The defect was
  classified as a flaw in the Braincrew-authored ticket and scope lock, not an AX defect. The user
  authorized **two bounded requests of five and one into one target-owned thread**, which conforms to
  the platform contract as written because the cap is per request and `stage_files` imposes no
  per-thread total. Raising the limit and adding an operator-only `stage_files` override were both
  rejected, with reasons recorded in
  [the request-split decision](../decisions/2026-07-25-ax-b-bounded-upload-request-split.md).
- Implementation: AX-B added local/test-only `ax-evaluation-parse-sources` orchestration and the
  `ax-evaluation-parse-source-handoff-v1` create-only sanitized receipt, reusing the existing
  conversation, upload, scan/parse, approval, materialization, strict parse-observation, and corpus
  identity boundaries. Verification confirmed **zero change** to `MAX_FILES_PER_OPERATION`,
  `validate_file_count`, `backend/src/ax_engine/attachments/service.py`, and
  `backend/tests/unit/test_attachment_intake.py`.
- Independent review trail, conducted on two separate axes in a dedicated review context:
  - First review returned **REQUEST CHANGES on both axes** — 1 Standards blocker and 3 Spec
    blockers, plus 4 non-blocking findings, for 8 findings total. The blockers were: production code
    that reported a lost or ambiguous mutation response as a *definite* failure rather than as
    indeterminate; bounded-wait timeout branches that no test executed; a post-materialization
    count-delta path that no test executed; and a "no partial-success receipt" assertion that was
    **vacuous**, because it searched for spaced JSON while the receipt is written with compact
    separators.
  - Pane 2 repaired all eight findings. Re-review confirmed each repair reached the branch it
    claimed rather than asserting around it, and that the added tests were additive, but found **two
    new defects introduced by the first repair**: `N-1`, connect-phase failures such as a stopped API
    server were classified as indeterminate although provably never sent, which also made
    `PARSE_SOURCE_UPLOAD_FAILED` unreachable for the most common conversation-creation failure; and
    `N-2`, the mutating/read-only decision was a path allow-list, so a future mutating route would
    silently default to the unsafe classification.
  - Both were repaired. `URLError` now precedes the timeout arm and inspects `exc.reason`, routing
    `ConnectionRefusedError` and `socket.gaierror` to the definite path; `mutating` became an
    explicit keyword-only parameter with **no default**, so omission is a hard error rather than a
    silent unsafe default. A bounded final check verified the exception ordering end to end against
    the `HTTPError ⊂ URLError ⊂ OSError` and `TimeoutError ⊂ OSError` hierarchies, confirmed all six
    client call sites, and confirmed no previously indeterminate case regressed to definite. Verdict:
    **CLEAR TO PROPOSE**.
- Independent verification at merge time: Braincrew `develop` is
  `f411fae5b5feedd7a3fa4bf49ad4f8aed3e0416f` and clean; AX `origin/develop` contains
  `cf3ae42915833778bc9838780b7d21a5c89327ec`; AX Issue #45 reports `CLOSED`/`COMPLETED`; and the
  published Issue #45 footer resolves the superseding decision at pinned Braincrew commit
  `f411fae5b5feedd7a3fa4bf49ad4f8aed3e0416f` rather than a placeholder branch reference.
- Merge results: Braincrew PR #61 squash-merged into `develop` as
  `f411fae5b5feedd7a3fa4bf49ad4f8aed3e0416f`; AX PR #47 squash-merged into AX `develop` as
  `cf3ae42915833778bc9838780b7d21a5c89327ec`. All required checks passed on both — Braincrew Python
  and frontend, AX Backend Ruff/compile/tests/`uv` lock, the disposable Docker workflow gates,
  frontend typecheck/build/Playwright, the repository command gates, and the routine-rotation
  PostgreSQL required gate. Both merged feature branches and their remotes are deleted.
- Known gaps accepted at merge: the deferred partial-coverage rows are recorded in the AX
  verification document. Every one of the seventeen `PARSE_SOURCE_*` codes is implemented and has at
  least one asserted negative test; the untested items are additional per-code conditions named in
  the ticket text (wrong-SHA, three `PRINCIPAL_INVALID` triggers, `parser_version`, and secondary
  approval/observation/corpus triggers), plus the absence of a test coupling the orchestrator's
  assumed HTTP response shapes to AX's real route projections. These were deliberately deferred, not
  overlooked.
- Exclusions in force: **no live apply occurred.** No live attachment, extraction, approval,
  materialization, corpus identity, parse observation, database or blob checkpoint, snapshot
  recovery, or operational receipt exists. `braincrew_preflight_ready` remains `false`, Braincrew
  Issue #38 remains blocked, and live operational execution requires its own separately authorized
  database and blob checkpoints. No parsing, retrieval, grounded-answer, or other quality result is
  claimed, and no Braincrew `READY` claim is made.

### 2026-07-25 — AX-B upload contract corrected before implementation reached the upload step

- Discovery: independent pre-implementation review of AX Issue #45 against the merged AX-A baseline
  found that the locked instruction "upload all six files in one multipart request" is **not
  executable**. AX enforces `MAX_FILES_PER_OPERATION = 5`
  (`backend/src/ax_engine/attachments/intake.py:12`), validated per call (`intake.py:54`) at the
  single unconditional call site in `stage_files`
  (`backend/src/ax_engine/attachments/service.py:64`), and
  `backend/tests/unit/test_attachment_intake.py:25` pins exactly the six-file rejection. Acceptance
  checkbox 2 of Issue #45 was therefore unsatisfiable, and checkboxes 3 through 7 were transitively
  blocked because no attachment would have been created.
- Classification: a design flaw in the Braincrew-authored ticket and the 2026-07-24 scope lock, not
  an AX defect and not an implementation error. The five-file cap is a deliberate bounded-resource
  control on a tenant-facing multipart endpoint.
- Independent verification: the finding was re-verified before escalation, including the decisive
  fact that the cap is enforced **per request** while `stage_files` (`service.py:51-90`) imposes no
  per-thread total, so `5 + 1` into one thread conforms to the platform contract as written.
- Authorized resolution: **two bounded requests of five and one into one target-owned conversation**,
  through the existing `POST /v1/conversations/{thread_id}/attachments` route, requiring zero AX
  source change and leaving `test_maximum_five_files_per_operation` intact. Raising
  `MAX_FILES_PER_OPERATION` and adding an operator-only override to `stage_files` were both
  rejected; the reasons are recorded in the decision.
- Records produced: superseding decision
  `docs/decisions/2026-07-25-ax-b-bounded-upload-request-split.md`; explicit forward pointers added
  to the 2026-07-24 scope lock at HEAD with its original wording preserved verbatim and its pinned
  commit `fc1302d54ab3f3735800d31a321b6f70e947572e` untouched; interview defense card D8.5b.
- Newly recorded failure mode: the split creates a durable partial-batch state, because the commit
  boundary is per request (`api/routes/attachments.py:191`) and each attachment is enqueued for
  scan/parse immediately (`service.py:105-115`). A failed second request leaves five committed
  attachments and five running jobs with no cross-request rollback. The operation must stop, retain
  evidence, and perform no cleanup or retry. Because `stage_files` de-duplicates by content hash
  within the thread (`service.py:68-76`), a naive retry would return `201` with the existing IDs and
  create nothing, so the rerun must be refused by `PARSE_SOURCE_PREEXISTING_STATE` rather than
  detected after the fact.
- Evidence boundary: this phase changed Braincrew documentation only. It modified no AX source, ran
  no AX test, executed no Git mutation, and accessed no database, service, container, blob store,
  provider, or secret. The AX Issue #45 body amendment was applied separately under its own
  authorization on 2026-07-25 and verified against the refetched published body; only its footer
  pointer to the superseding decision is deferred until this documentation is merged and pinnable by
  commit SHA. AX-B implementation is in progress, unreviewed, and makes no completion, live,
  parse-quality, or `READY` claim.

### 2026-07-24 — AX PR #46 reviewed and squash-merged; AX-B handoff eligible

- GitHub review exposed receipt-destination, exact-replay, concurrent-insert, commit-confirmation,
  and repository-evidence gaps. The demo-label requirement was also repaired.
- AuditEvent creation was rejected because Issue #44 requires exactly one new `User` and no other
  database row.
- Independent final review passed with zero blockers at AX head
  `6499e1b42730f72bf03db769a3f95cb186f1fb07`. Local evidence is `63` targeted tests and
  `1553 passed, 75 skipped` for the full backend suite; no live apply occurred.
- Issue #44 now records `EVALUATION_PRINCIPAL_RECEIPT_UNAVAILABLE`, create-only reservation, and
  indeterminate-commit evidence semantics. All five replacement checks passed, all six review
  threads were resolved with evidence, and PR #46 squash-merged as
  `fe16c0cedc1e64856d9e107e111665d0ba2e444d`; Issue #44 closed.

### 2026-07-24 — PR #59 merge verified; AX-A Issue #44 local TDD and review completed

- The contract/spec axis passed without findings.
- The standards axis found stale workflow-gate wording and cross-repository relative verification
  paths. Both were corrected locally, then independently re-reviewed as PASS.
- The user authorized the corrective commit, push, AX Issue #44/#45 body synchronization, and PR #59
  merge. Remote verification confirms that PR #59 merged into `develop` as
  `95826ee95f0ac9a8bd84eed149dff47dc834aa47`.
- A fresh AX worktree completed Issue #44 `test-driven-development`, including a review-driven
  atomicity repair and independent PASS review. Lore commit
  `99c6300e02498f18763806002c748dd58fe64c04` was pushed and opened as draft AX PR #46; merge
  remains separately gated. Issue #45 remains dependent on the reviewed and merged AX-A result.

### 2026-07-24 — AX principal and parse-restoration scope locked

- Branch/worktree gate: clean Braincrew `develop` and `origin/develop` were both verified at
  `8242003f9ed30a4df4889c1c30abe6a36470bff0` before the isolated
  `docs/ax-evaluation-boundary-scope-lock` worktree was created.
- Cross-review decision: a principal-only issue cannot unblock Braincrew #38 because the six
  reviewed attachment and extraction rows are absent. The selected dependency is AX-A
  tenant-scoped subject provisioning followed by AX-B six-source normal-lifecycle restoration.
  A combined issue and Braincrew-owned repair were rejected.
- Identity lock: AX-A uses deterministic subject
  `26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe`, derived from the reviewed UUIDv5 name, and creates
  exactly one active target-tenant `User`. Local/test roles remain request-scoped through
  `x-ax-roles` and AX's existing static permission mapping; AX-A creates no persisted role or
  membership state and never moves or reactivates the historical subject.
- Dataset lock: the live corpus contribution is
  `braincrew-evaluation-dataset-3.0.0`; the six parse cases retain the historical v2 component
  contract inside the integrated `braincrew-evaluation-dataset@3.0.0` bundle.
- Lifecycle lock: strict non-empty spans require approval and materialization, not extraction
  alone. AX-B therefore expects exact `company_reference` / `hr_only` materialization and bounded
  seed-table additions from `14/77/77/154` to `20/83/83/166`, then freezes actual post-B
  role-visible corpus identities.
- Operational safety: the pre-import Issue #37 dump is not the recovery point for new writes.
  A fresh post-import/pre-A dump and post-A/pre-B database plus blob checkpoints precede later
  operations. Any failure preserves evidence and stops without automatic retry, cleanup, restore,
  deletion, or re-import.
- Evidence boundary: this phase changed documentation only. It did not create GitHub issues, modify
  AX, access a database/service/container/credential, execute HTTP, or publish `READY`.

### 2026-07-24 — AX Issue #37 sealed-pack import applied once into the local AX database

- Scope boundary: this transition records operational work performed against the AX_portfolio
  checkout and its local PostgreSQL. No Braincrew source, dataset, or artifact changed. All
  operational evidence lives outside both repositories in
  `~/ax-seed-issue-37-evidence/` and is not committed.
- Staged gates: role provisioning, filesystem and credential preflight, dry-run, provider lineage,
  snapshot, and apply each ran behind a separate approval, with independent review sessions between
  stages. Two independent reviews returned `REJECT` and were cleared before the destructive step.
- Dry-run evidence: the eligibility receipt reported `state=ELIGIBLE` at file digest
  `sha256:ee114a695f76f4be8f43df94bdfcf0d1a5a6bacd30e8b926859bb537e4906eae`, and the target
  tenant `ae09ec7f-a7bc-5bf8-a645-8b3f1e623850` held zero rows in every seed table and in
  `audit_events`. The no-write claim was confirmed from the database, not from the receipt alone.
- Least-privilege evidence: `ax_seed_import` holds SELECT on seven tables and INSERT on six, with
  no read-only transaction default; `ax_seed_operator` holds `pg_read_all_data` with
  `default_transaction_read_only=on`. The database contains zero `SECURITY DEFINER` functions, so
  retaining PostgreSQL's default `PUBLIC` EXECUTE creates no escalation path.
- Provider lineage evidence: the sealed pack expects `fake-deterministic`, while
  `build_embedding_provider()` returns the OpenAI adapter unless `EMBEDDING_PROVIDER=fake` is set.
  The lineage step caught this before apply; without it the mismatch would have surfaced only as
  `AX_SEED_EMBEDDING_PROVIDER_MISMATCH` at the destructive step. The provider was selected per
  command; `.env` was not modified.
- Snapshot evidence: a full custom-format dump was written outside both repositories at
  `sha256:6d85e86c51e8195d4fce3bed5472e1f87a7ede602f9b2c20c37ddb52c0e61101`, and `pg_restore
  --list` parsed all 812 catalog entries without error, including every seed table definition and
  its ACL. No restore was performed, so post-restore data integrity and ownership compatibility
  remain unproven.
- Apply evidence: the importer ran exactly once and returned `state=LOADED` with
  `commit_confirmation=direct`. Measured row counts match the planned counts exactly: 14 source
  documents, 77 chunks, 77 evidence spans, and 154 vector records, all 154 embedded with non-null
  vectors. The database recorded `provider.embedding.used` with adapter `fake-deterministic` at
  1536 dimensions under the `text-embedding-3-small` label, which is the documented B-prime
  condition rather than a real provider call.
- Exclusions: HTTP boundary verification, the six strict parse observations, and the Braincrew
  preflight handoff did not run. `braincrew_preflight_ready` is `false`. No quality, retrieval, or
  answer claim is made from this import; it establishes corpus presence only.
- Resolved operator action: an `OPENAI_API_KEY` value was exposed in tool output by a
  `docker compose config` invocation during review. The key value was never recorded in evidence,
  and the user confirmed rotation complete on 2026-07-24. Later agents must not inspect the
  replacement secret.
- Next gate: publish and implement the locked AX-A and AX-B contracts before attempting HTTP
  boundary verification. Braincrew Issue #38 remains blocked until both receipts, the live
  observations, and its own approval gate complete.

### 2026-07-23 — Issue #56 AX-canonical publication-byte repair entered TDD

- Repository gate: `origin/develop` was verified at
  `e9a512dbb5ff3de0a0367632f169f91cc8817d81`; all Braincrew branches/worktrees and the AX checkout
  were inspected before the dedicated `feat/issue-56-ax-canonical-pack` worktree was created.
- Clean baseline: formatting, lint, mypy, and all 343 tests passed before the acceptance RED.
- Acceptance RED: a generated import manifest ended in `0a`, while AX's exact canonical bytes ended
  at the closing brace. That single trailing line feed reproduced the consumer rejection boundary.
- Minimal GREEN: only new import publication dropped the line feed. Receipt serialization and all
  qualification identities remain unchanged.
- Replay boundary: receipt-v1, PR #55 receipt-v2/import artifacts, and the new exact import bytes
  remain supported; spaces, pretty printing, multiple line feeds, and newline-free receipts fail
  closed.
- Read-only consumer proof: exact AX SHA
  `e25f333b55fca34118a954a17e5e0cd88dc7ea39` accepted 14 sources and 11,528 source bytes without a
  database or provider. No operational path ran.
- Independent review: Standards found two actionable documentation defects and Spec found one
  operator-gate omission. A new document-contract RED reproduced all three, minimal documentation
  GREEN repaired them, and the independent Standards and Spec re-reviews each reported zero
  actionable findings. The accepted test-setup duplication remains an explicit readability
  judgement, not a required repair.
- Full verification: locked dependencies, Ruff formatting and lint, mypy, all 352 tests, and
  `git diff --check` pass in the Issue #56 worktree.
- Stop condition reached: present the clean uncommitted diff at the Issue #56 Git Lifecycle
  Proposal Gate. Do not commit, push, open or modify a pull request, publish artifacts, or begin
  operational work without the separate required authorization.

### 2026-07-23 — Issue #37 successor corpus qualification succeeded once

- Readiness evidence: PR #54 is merged at
  `e6cfb561349ebcd5f14b2dbe051274b23700557e`; native blockers #33, #36, and #53 are closed; Issue
  #37 is `OPEN/READY` with `ready-for-agent` and publishes the exact frozen input digests.
- TDD evidence: the clean baseline passed all 342 tests. Acceptance RED first exposed private
  absolute paths in qualification and replay stdout; minimal GREEN retained safe file names only.
- Qualification evidence: the actual read-only qualifier ran exactly once and created only
  `corpus-qualification-receipt-v2` plus the
  `seed_version=braincrew-evaluation-dataset-3.0.0` import manifest. The exact logical and file
  digests are recorded in the current checkpoint above.
- Replay evidence: replay reproduced receipt
  `sha256:c564b1442c135fef5d5430b313914951e2b5ab4cc7e0fd0bbbdefb0b928ea6ce`,
  qualification file
  `sha256:8843c87597db779ece932585445bae9dbdf9b5f26f4f81a7b9d069a1699968ed`, and import
  `sha256:9df8dbd212c6e0253b3c58feb392869bffb226d816805ee7ed166072596003bd`.
  Redaction passed and the sealed input tree remained unchanged.
- Scope evidence: no retry, repair, corpus/dataset mutation, AX import, database, service,
  snapshot, preflight, experiment, baseline, candidate, or live quality claim occurred.
- Next gate: stop before commit. AX Issue #37 may begin only after the Braincrew result is
  separately published and its own operator-controlled proposal gate is approved.

### 2026-07-23 — Issue #53 successor dataset candidate published; manual review gate opened

- Candidate evidence: `datasets/dataset_manifest_v3.json`, `datasets/DATASET_CARD_V3.md`, and the
  three v2 component files publish `braincrew-evaluation-dataset@3.0.0` with integrated digest
  `sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d` and component digests
  `sha256:33e17fbb4d3f5485df1482de37e472e1b20fceef922c9b1dda90f8d9dfc25f73` (parsing, 20 cases),
  `sha256:9687ead24590cab1b9d244ef876f226545a1fb1aa2013c50e4be7a63430c8408` (retrieval, 30 cases),
  and `sha256:f76a9a1fa9a6a4b467f76ce7649dc7c15f5ad7c615d6cbb20ed3394e486d94b2` (grounded, 50
  cases covering 40 `grounded_answer` plus 10 `visibility_abstention`).
- Identity-preservation evidence: 100 globally unique case identifiers, the 20/30/40/10 allocation,
  the 70/30 Calibration/Verification split, per-metric minimum Verification denominators, evaluator
  semantics, metric applicability, risk policy, and threshold policy are unchanged from `2.0.0`.
- Rebinding evidence: the manifest `source_corpus` block pins the sealed predecessor
  `braincrew-independent-hr-corpus@1.0.0` by sealed-content digest
  `sha256:5f0c254b3dc64b23470029b1004106dc078a9602062da8fa8041623bf91fb7e4`, provenance digest
  `sha256:eb43fc824cd54bf10e8805b5fdeb1915bcaac368cb458ce8981a481cd7d4fce1`, and receipt digest
  `sha256:bc508b6001facbef67bacd7e0c1d4d5123f04bc1e33d2849b5e7d455183df62b`. Thirteen of the 14
  sealed sources are cited; `demo-lifecycle-checklist-014` remains an uncited distractor.
- Test evidence: `tests/contract/test_successor_dataset_freeze.py` reports 21 passed, covering
  manifest-component-predecessor binding, dataset `2.0.0` byte immutability, preserved evaluator
  and split semantics, complete source-digest and visibility closure, six tampering rejections,
  version-only `3.0.0` substitution rejection, create-only qualification receipt-v2 and seed v3
  with rollback, `receipt-v1` replay support, v1/v2 dispatch separation, wheel packaging of both
  bundles, and exact digest binding in the review checklist.
- Documentation-synchronization evidence: the corpus-provisioning design checkpoint, evaluation
  plane design section 14.4, interview defense card D8.7, and this status file now record the
  successor contract and its review authority.
- Review decision: on 2026-07-23 `DHChe-successor-dataset-reviewer` confirmed all eight checklist
  items and recorded `Decision: APPROVED` against the exact candidate and predecessor digests.
- Reviewer resolution: all 30 retrieval cases carry `role: Executive`. The reviewer accepted this
  as a constraint-induced limitation because `HRManager` maps to `HRPractitioner` and all 14 sealed
  sources are visible to `HRPractitioner`, leaving no valid forbidden source while unchanged
  forbidden-visibility applicability is required. This is not a multi-role retrieval execution
  claim.
- Scope evidence: the exact successor dataset freeze is the only newly approved lifecycle claim.
  No actual qualification receipt publication, seed-pack import, AX/DB/service call, preflight,
  experiment, baseline, candidate run, comparison, or live quality claim occurred. Dataset `2.0.0`
  was not modified.
- Ticket-review evidence: the independent Standards axis approved with zero actionable findings.
  The independent Spec axis found a stale historical `seed_version` in the operative provisioning
  contract and a contradictory pre-approval scope statement. A new contract test first failed, both
  statements were corrected to the successor v2 receipt/seed and approved freeze boundaries, and
  all 22 successor tests then passed. Unresolved findings: zero.
- Verification evidence: frozen dependency sync, Ruff format and lint, strict mypy, all 342
  repository tests, Git whitespace validation, and working-tree inspection pass on
  `feat/issue-53-successor-dataset-freeze`.
- Completion condition: satisfied locally; work is stopped before commit at the Git Lifecycle
  Proposal Gate. Commit, push, pull request, and merge remain separately unauthorized.

### 2026-07-23 — Issue #36 restricted authoring, manual review, sealing, and replay completed

- Entry evidence: `develop`, `origin/develop`, and the new Issue #36 branch all began at clean SHA
  `8e669db46b698b8791739feee910ba1b561a0936`; the full clean baseline passed `320` tests, and Issue
  #36 received `ready-for-agent` only after every content-addressed entry check passed.
- Authorization evidence: create-only `corpus-data-creation-authorization-v1` digest
  `sha256:9eabf4fff6de5bf54065c8d4bd657eda4ebeb06c630ad45f53fe41c36457a1a7`
  binds the clean execution SHA, reviewed tool digest
  `sha256:8ba07d07d35ac359a04f0d2f2e3b30062569b3f883e2d6a16e918aa218af6d3e`,
  four approved input digests, both authorities, and all lifecycle paths.
- Author evidence: one sandboxed run completed without retry and emitted independence receipt
  `sha256:28a22cb6f1c0d35ced80d43dc727699cecae388a8012f6a292d618719371cf7f`.
  The staged pack contains 14 sources totaling 11,528 bytes; retained evidence exposes only
  identities, counts, and digests rather than source text.
- Manual review evidence: `DHChe-corpus-provenance-reviewer`, distinct from authoring owner
  `codex-issue-36-authoring-agent`, approved every exact source digest, newly authored synthetic
  origin, and `CC0-1.0` assignment on `2026-07-23` in `Asia/Seoul`.
- Seal and replay evidence: `braincrew-independent-hr-corpus@1.0.0` sealed once and replayed once.
  Sealed content digest is
  `sha256:5f0c254b3dc64b23470029b1004106dc078a9602062da8fa8041623bf91fb7e4`,
  provenance digest is
  `sha256:eb43fc824cd54bf10e8805b5fdeb1915bcaac368cb458ce8981a481cd7d4fce1`,
  and receipt digest is
  `sha256:bc508b6001facbef67bacd7e0c1d4d5123f04bc1e33d2849b5e7d455183df62b`.
- Scope evidence: no qualification, successor dataset freeze, AX/DB/service call, preflight,
  experiment, PR #29 change, retry, repair, overwrite, or feedback-driven second pass occurred.
- Completion condition: canonical documents and repository gates pass, then stop at the Git
  Lifecycle Proposal Gate before commit, push, pull request, or merge.

### 2026-07-23 — Issue #36 data-creation policy approved for a new session

- User decision: all six proposed lifecycle conditions are approved, and selection of the dynamic
  clean execution SHA plus external authoring-tool digest is delegated to the next agent under the
  fail-closed rules recorded above.
- Authority decision: `codex-issue-36-authoring-agent` owns restricted authoring;
  `DHChe-corpus-provenance-reviewer` is the distinct human manual provenance-review authority.
- Input and path decision: the four authoring inputs and the exact external lifecycle root are
  fixed. Source bytes, receipts, review evidence, and sealed output remain create-only and outside
  the repository.
- Order and failure decision: Author, then review, then seal, then replay. Every entry, sandbox,
  authoring, review, sealing, or replay failure stops without retry, repair, overwrite, or feedback.
- Scope evidence: no #36 label transition, source-byte authoring, sealing, qualification,
  AX/DB/service call, preflight, experiment, branch/worktree creation, commit, push, pull request,
  or merge occurred in this decision step.
- Completion condition: the documentation contract passes and this approval record is merged into
  `develop`; #36 then starts in a fresh session and first pins the exact clean execution SHA and
  authoring-tool digest through RED entry contracts.

### 2026-07-23 — PR #49 merge verification and Issue #47 closure completed

- Merge evidence: PR #49 is `MERGED` into `develop` as `4d80b9b8950f4d7356a9aa9806f492ae79126dab`; the required Python and frontend checks completed successfully, and `develop` resolves to that exact merge commit.
- Tracker evidence: Issue #47 is `CLOSED`; #35, #46, and #47 no longer block #36 through unfinished-ticket state.
- Remaining blocker: Issue #36 remains `BLOCKED`, has no `ready-for-agent` label, and cannot start until the separate data-creation proposal gate approves the source-first execution inputs and manual provenance-review authority.
- Scope evidence: no #36 readiness transition, source-byte authoring, sealing, qualification, dataset freeze, AX/DB/service operation, preflight, experiment, branch/worktree creation, commit, push, pull request, or merge occurred.
- Next action: verify this documentation-only diff, then stop at the Git Lifecycle Proposal Gate before any publication action.

### 2026-07-23 — Issue #47 restricted-input and provenance-sidecar TDD reached GREEN

- Entry evidence: PR #48 is merged into `develop` as `49a8c2a6228418757c34d8f4bfa0f384d3f0ff52`; Issue #46 is `CLOSED`; Issue #35 is `CLOSED`; Issue #47 has `ready-for-agent`; and the dedicated worktree starts clean from that exact `origin/develop` commit.
- RED/GREEN evidence: the restricted-input acceptance test failed on the wrong pack schema before the content-schema pin passed. Six sidecar tests failed on the absent required evidence and missing CLI/replay path before v2 sealing passed for canonical immutable sidecars and failed closed for missing, pending, mismatched, mutable, tampered, and staging-contained evidence.
- Compatibility boundary: new seals require `--provenance-sidecar` and emit `corpus-sealing-receipt-v2`; replay still accepts historical `corpus-sealing-receipt-v1` evidence. The sealed receipt and sidecar retain digests and review metadata only, never source text, credentials, private paths, or evaluation content.
- Scope evidence: no actual corpus source bytes or operator sealing, qualification, dataset inspection, preflight, experiment, AX/DB/service call, dependency, PR #29, or Issue #15 branch modification occurred.
- Review repair: reviewers found that the new sealed sidecar had to be accepted during initial qualification revalidation as well as replay. The qualification acceptance test failed first, then passed with the six provenance-sidecar contracts after the controlled extra-file allowlist was shared. Independent re-review found no remaining ticket blocker.
- Next action: run `verification-before-completion`, then use the authorized `commit -> push` sequence. Issue #36 remains `BLOCKED` until this ticket is merged and verified plus the separate data-creation proposal gate.

### 2026-07-23 — PR #49 review P1 repairs reached local verification

- Review findings: PR #49 identified three P1 gaps: self-review was accepted, replay depended on preserved read-only filesystem bits, and the canonical evaluation-plane design still described v1 sealing and pack-schema authoring inputs.
- RED/GREEN evidence: each behavior failed before repair. The sidecar contract now rejects equal authoring and reviewer identities; external sealing input remains read-only while replay validates canonical bytes and digest independent of normalized filesystem write bits; the canonical design now describes the v2 sidecar and content-schema-only authoring boundary.
- Verification evidence: focused sealing, qualification, and workflow contracts passed `43`; frozen sync, Ruff format/lint, strict mypy, and the full repository suite passed (`320 passed`).
- Lifecycle gate: the fixes are local and uncommitted. A new explicit proposal is required before commit/push; PR #49 must receive fresh review and CI before merge. Issue #36 remains `BLOCKED` until #47 is merged and verified plus the separate data-creation proposal gate.

### 2026-07-23 — Issue #46 locks source-first evaluation freeze

- Entry evidence: `origin/develop` is `828524f6a85b9083b72400279987830b12b07a67`; Issue #35 is `CLOSED/COMPLETED`; Issue #36 is `BLOCKED`; Issue #46 is the ready source-order decision frontier; and Issue #47 remains the separate restricted-input and provenance-sidecar repair.
- Decision: Source-first evaluation freeze is selected. A new independently sealed corpus version must precede a successor evaluation dataset version greater than `2.0.0`; dataset v2 remains immutable and cannot be an authoring or qualification target in this lane.
- Qualification boundary: the later receipt must bind the successor dataset version and digest to the unchanged sealed corpus digest. Qualification stays read-only and cannot feed any identifier, digest, or correction back to authoring.
- Failure response: Issue #36 remains `BLOCKED`, has no `ready-for-agent` label, and cannot start until Issue #47 is closed and a separate data-creation proposal gate authorizes the selected order. No source byte, sealing, dataset freeze, qualification, preflight, experiment, AX operation, or PR #29 change is authorized here.
- Completion condition: the Issue #46 contract test, ticket-scoped code review, and full repository verification pass; then stop at the Git Lifecycle Proposal Gate before commit, push, pull request, or merge.

### 2026-07-23 — PR #45 review converted Issue #36 into an explicit blocked frontier

- Entry evidence: PR #45's Codex review produced four actionable findings against published head `2013da04509f2f23c340467fbe4f8f770b17be69`. The schema-phase, status, provenance-evidence, and source-order claims were all independently reproduced before repair.
- Scope correction: a proposed production launcher change was removed because Issue #35 owns the brief contract, not the closed Issue #32 runtime. Issue #47 now owns content-schema sandbox input plus create-only provenance-sidecar sealing/replay support.
- Architecture correction: Issue #46 owns the reviewed source-first or pre-existing evaluation-independent source contract. Qualification feedback, hidden evaluation identifiers, and hidden digests remain forbidden authoring inputs.
- Tracker evidence: #46 and #47 are native sub-issues of #30 and native blockers of #36. Issue #36's body says `BLOCKED`, links #35/#46/#47, and carries no `ready-for-agent` label.
- Exact-byte evidence: a new evaluation-blind authoring context removed time-dependent approval wording. A different blind reviewer approved the final 10,680-byte brief at `sha256:121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3` with zero material findings.
- Publication evidence: Lore repair commit `0d4c0ae8876ad13d37acaa3bca81e2870c1d85d9` is pushed to PR #45, and its committed brief bytes reproduce the approved digest. Replacement CI and final merge-readiness checks remain required after the status-only commit.
- Completion condition: PR #45 may merge only after the latest head passes all required CI and no unresolved review blocker remains. Issue #36 remains blocked after that merge; #46 and #47 define the next dependency frontier.

### 2026-07-22 — Issue #35 evaluation-blind authoring brief approved for exact bytes

- Entry evidence: PR #44 is `MERGED` into `develop` as `67d7c104757f60194e59df20240ac47f8be9c027`; Issue #34 is `CLOSED/COMPLETED` and cleaned up; Issue #35's blocker #32 is `CLOSED/COMPLETED`; and #35 alone received the child-ticket `ready-for-agent` transition. The dedicated branch/worktree starts at the exact merge commit.
- Independence boundary: fresh authoring/review contexts read only the Issue #35 body, vendored pack schema and digest, Python execution settings, authored brief/test, and the explicitly authorized canonical AX role contract. They did not read datasets, fixtures, evaluation cases/queries/answers/evidence, scores/splits, prior results, PR #29, or `feat/issue-15-live-verification`.
- RED/GREEN evidence: `2 failed -> 2 passed` for the absent brief; review-driven `4 failed, 1 passed -> 5 passed` for role authority and byte binding; `2 failed, 5 passed -> 7 passed` for CC0-only and canonical byte/path policy; `2 failed, 7 passed -> 9 passed` for the first digest/review evidence; then state and exclusion consistency each failed before separate fresh evaluation-blind repairs and exact-byte reapproval cycles restored `10 passed`. The final synthetic-only provenance assertion also failed before its fresh blind repair, followed by `2 failed, 8 passed -> 10 passed` for the final approval lock. The workflow-order contract separately reports `1 failed -> 1 passed`.
- Approval evidence: the final independent `code-reviewer` reported `APPROVE` with zero material findings for exact 8,531-byte brief digest `sha256:f21f5df1950ec0872e45c956f9c689b09c59362d2cae53dbd2f86635bbb690ae`. The adjacent digest declaration and durable leakage-review file record that decision.
- Active boundary: the brief is frozen and may not be modified after opening the synchronized design/draft/interview/status documents. Any required brief change must restart in a fresh evaluation-blind authoring context and receive a new independent review/digest.
- Completion condition: ticket-scoped Standards/Spec review and every required repository gate pass with the frozen digest unchanged; both are now satisfied locally. Work is stopped at the Git Lifecycle Proposal Gate. Issue #36 remains blocked until a clean committed SHA passes post-commit byte equality.

### 2026-07-22 — PR #44 Codex review remediation entered TDD

- Entry evidence: local and remote PR head both equaled `713d09017dcc5b1fde0a6297b0f9782ff9a7b613`; GitHub reported both Python and frontend checks successful; the worktree was clean; and all four current Codex threads were unresolved and not outdated.
- Clean review baseline: frozen sync, Ruff format/lint, strict mypy, all `280` pre-review tests, `git diff --check`, and clean status passed before the first review RED.
- RED/GREEN evidence: separate tests reproduced empty-span overblocking, available-response failure-code acceptance, exhausted-retry evidence loss, frozen integrated-digest substitution, component-digest substitution, rehashed artifact identity substitution/removal, legacy-v1 omitted-field digest drift, and correlation-header credential retention. Minimal repairs preserve evaluator-bound empty spans, fail closed on inconsistent responses, retain sanitized blocker attempts, digest untrusted correlation values, preserve legacy replay, and bind successful six-probe capture/replay to exact dataset identity. The four preflight files report `32 passed`.
- Active boundary: no actual AX preflight, READY publication, quality score, corpus mutation, experiment execution, or PR #29 modification occurred.
- Completion condition: full local gates and independent review pass; the Lore fix commit is pushed; all four threads are answered and resolved; required CI remains green at the new head; PR #44 then merges into `develop` under the authorization recorded above.

### 2026-07-22 — PR #44 second Codex review remediation entered TDD

- Entry evidence: the first repair Lore commit `cbbdfe58f4c708f390288fb9252f7c4274a4ce1f` matched local, remote, and PR heads; Python and frontend CI passed; GitHub reported `CLEAN`; and the original four threads were resolved before a fresh `@codex review` request.
- New review findings: one P2 showed that two retryable failures followed by a successful but invalid parse response lost all attempt evidence; a second P2 showed that a blocked post-dataset capture could lose `dataset_identity`, be rehashed, and replay because only successful six-probe artifacts required identity.
- RED/GREEN evidence: a controlled `503`, `503`, invalid-parser sequence first produced an empty blocker attempt list, while a first-case exhausted-retry artifact replayed after identity removal and rehash. Minimal GREEN retains all three attempts and adds the optional `principal-attachment-preflight-v1` discriminator, under which frozen identity is mandatory for complete, partial, and blocked captures. Legacy generic Issue #42 v1 artifacts remain compatible.
- Independent review repair: both Standards and Spec axes reproduced a downgrade when discriminator and identity were deleted together. The complete and blocked CLI acceptance paths first replayed successfully after that double removal and rehash. A semantic fingerprint then rejected the downgrade but collided with valid generic v1 evidence.
- Schema-boundary repair: confirmatory review showed that even a narrowed fingerprint could not preserve the complete unauthenticated generic v1 shape while proving Issue #34 identity. Fingerprinting was removed. Generic artifacts remain `live-preflight-evidence-v1`; every post-dataset Issue #34 artifact is `principal-attachment-preflight-evidence-v1`, which requires its capture contract and frozen dataset identity. Both collision-shaped legacy replays pass, both new-schema double-removal replays fail, and replay reports the schema so downstream Issue #34 qualification can reject generic evidence.
- Final local review result: Standards and Spec axes both report PASS with zero actionable finding. Fresh frozen sync, Ruff format/lint, strict mypy, focused `35 passed`, full `288 passed`, and Git diff validation support publication. The only non-blocking residual risk is unauthenticated artifact origin; downstream Issue #34 consumers must require the new schema, and actual READY consumption remains Issue #38.
- Active boundary: no actual AX preflight, READY publication, quality score, corpus mutation, experiment execution, or PR #29 modification occurred.
- Completion condition: fresh full verification and both review axes pass; the second Lore repair is pushed; both new threads are answered and resolved; replacement CI and Codex review are green with no unresolved blocker; PR #44 then merges under the recorded authorization.

### 2026-07-22 — PR #44 third Codex review remediation entered TDD

- Entry evidence: the second Lore repair `621b5c84778144a3b616a24dbcd27bf3dcaedf50` matched local, remote, and PR heads; Python and frontend CI passed; GitHub reported `CLEAN`; and the first six threads were resolved before the fresh Codex review completed.
- New review findings: one P1 showed that a successful Issue #34 artifact still replayed after deleting one of the six parse observations and recomputing its logical digest; one P2 showed that a non-timeout connection failure produced `LIVE_PARSE_OBSERVATION_UNREACHABLE` without retaining the attempted operation.
- RED/GREEN evidence: the five-probe rehash replay first exited successfully and a synthetic `ConnectError` first produced an empty blocker attempt list. Minimal GREEN makes the Issue #34 schema revalidate the ordered reviewed probe map, owner, sole role, and complete-or-terminal-blocker shape, while the Adapter records one non-retryable `request_error` attempt and preserves the existing LIVE blocker taxonomy.
- Independent review repair: Standards reproduced `LIVE_PARSE_OBSERVATION_UNAVAILABLE` being rejected by the new validator, a rehashed parser/source-policy mutation replaying, and removal of all blocker attempts replaying. Each path was observed RED; the validator now preserves the unavailable blocker, rechecks strict response/source/span and canonical attempt evidence, and requires coherent nonempty attempts on an operation blocker. A second pass reproduced span text-digest substitution, different canonical tenants across observations, and `LIVE_PARSE_OBSERVATION_UNREACHABLE` paired with a forged success attempt. A final pass shortened a three-503 blocker to one renumbered terminal attempt. All paths were RED before frozen substring, single-tenant, blocker-terminal taxonomy, and exact retry-exhaustion checks reached GREEN. Generic Issue #42 replay remains compatible. The five focused files report `50 passed`; full pytest reports `289 passed`.
- Final local review result: Standards and Spec both report PASS with zero actionable finding. Frozen sync, Ruff format/lint, strict mypy, full pytest (`289 passed`), and Git whitespace validation pass.
- Active boundary: no actual AX preflight, READY publication, quality score, corpus mutation, experiment execution, or PR #29 modification occurred.
- Completion condition: both independent review axes and every repository gate pass; the third Lore repair is pushed; both latest threads are answered and resolved; replacement CI and Codex review are green with no unresolved blocker; PR #44 then merges under the recorded authorization.

### 2026-07-22 — PR #44 fourth Codex review remediation entered TDD

- Entry evidence: the third Lore repair `2ac5be9b10fa0a938f2d24e8600297e728f1c292` matched local, remote, and PR heads; Python and frontend CI passed; GitHub reported `CLEAN`; and the first eight threads were resolved before the fresh Codex review completed.
- New review findings: five P2 findings showed that a first-probe blocker lacked principal request evidence; blocker code could be relabeled without changing its detail and terminal attempt; a parse request could carry unrelated query/corpus fields; a response-less request failure could claim a response correlation; and an unsafe server-controlled span ID could be retained.
- RED/GREEN evidence: six focused tests first failed on those five contracts. Minimal GREEN retains and revalidates the exact canonical request on every operation blocker; freezes the capture-v1 run/case/correlation, tenant, owner, role, timeout, attachment, and parse-only request shape; binds blocker code/detail/outcome and fixed statuses; forbids response correlations without a response; and rejects unsafe span IDs before retention. Independent Standards/Spec review then reproduced generic legacy span-ID rejection, and Standards also reproduced raw query retention through a generic blocker request. Both paths became RED before shared span compatibility was restored, generic blocker requests were rejected, and principal replay alone retained the safe-ID rule. The five focused files report `54 passed`.
- Final local review result: Standards and Spec both report PASS with zero actionable finding after confirming generic-v1 raw-query and legacy span compatibility, principal-only span-ID enforcement, exact blocker request/taxonomy/correlation semantics, retry exhaustion, and all scope exclusions.
- Final local verification: frozen sync, Ruff format/lint, strict mypy, focused `54 passed`, full `293 passed`, and Git whitespace validation pass.
- Active boundary: no actual AX preflight, READY publication, quality score, corpus mutation, experiment execution, or PR #29 modification occurred.
- Completion condition: both independent review axes and every repository gate pass; the fourth Lore repair is pushed; all five latest threads are answered and resolved; replacement CI and Codex review are green with no unresolved blocker; PR #44 then merges under the recorded authorization.

### 2026-07-22 — Issue #34 principal and attachment preflight entered TDD

- Entry evidence: fetched `origin/develop` and the worktree head both equal Issue #42 merge `93c8e8dabab855b7f2f700df73cd04ce38995f29`; Issue #42 is `CLOSED/COMPLETED`; Issue #34 is `OPEN` with `ready-for-agent` and no open blocker; AX #34/#40 are complete at the pinned SUT SHA; and draft PR #29 remains untouched at `b14653c7f2b6e7aad9a36c41c7141a9ccb3ce674`.
- Cleanup evidence: Issue #42's worktree and local/remote branch still exist cleanly, so predecessor cleanup is pending and is not claimed complete.
- Clean baseline: frozen sync, Ruff format/lint, strict mypy, all `264` pre-change tests, `git diff --check`, and clean branch status passed before the first RED.
- RED/GREEN evidence: the first 15 new contract/acceptance tests failed on the intentionally absent canonical-principal and attachment-policy implementation. Minimal GREEN validated pre-HTTP UUIDs, active-owner policy, exact role/mapping, typed blocker classification, six strict parse observations, retained retry attempts, sanitized evidence, create-only publication, and replay. Ticket review then exposed non-matching parser acceptance before the pinned parser repair; the affected set reports `52 passed` with zero unresolved Standards or Spec finding.
- Active boundary: Issue #34 does not execute the real Issue #38 preflight, publish READY, score parsing quality, apply/import corpus data, call providers, change AX services, run experiments, repair data, or modify PR #29.
- Verification evidence: frozen sync, Ruff format/lint, strict mypy, all `280` repository tests, and Git whitespace validation pass; status contains only the expected Issue #34 implementation, tests, and documentation changes.
- Active gate: one Lore commit, same-branch push, and review-ready PR creation are authorized; merge remains unperformed and separately gated.

### 2026-07-22 — Issue #42 minimum live-preflight substrate extraction entered TDD

- Entry evidence: fetched `origin/develop` equals Issue #33 merge `fdbb732ee05a9de5270c91a82f0930da0413107b`; PR #41 is merged; Issue #33 is `CLOSED/COMPLETED` with cleanup complete; AX #34/#40 are complete at the required merge SHA; and draft PR #29 remains untouched at `b14653c7f2b6e7aad9a36c41c7141a9ccb3ce674`.
- Boundary evidence: current `develop` has only the original Issue #7 Adapter contract, where parse is unavailable and corpus identity is unverified. The create-only live-preflight/replay implementation and authorization-aware dataset-v2 types exist only on unmerged PR #29, while merged dataset v2 intentionally reuses the exact v1 component files.
- Scope decision: the user authorized a separate minimum prerequisite. Issue #42 was created under #30, marked `ready-for-agent`, and made a native blocker of #34; #34's `ready-for-agent` label was removed until this substrate merges.
- Clean baseline: frozen sync, Ruff format/lint, strict mypy, all `254` pre-change tests, `git diff --check`, and clean branch status passed before the first RED.
- RED/GREEN evidence: collection first failed on the absent strict AX response and live artifact modules, and the packaged contract failed on the old AX pin. Minimal GREEN passed 24 focused tests. Review tests then exposed a nested-digest rehash bypass, private-path retention, stale corpus capability reason, ambiguous attachment naming, mixed run identity, and the old grounded Adapter pin before repair.
- Contract evidence: the packaged Adapter pins AX `72805930d9addd8ea41743d1922acf8de621c3f8`, exact corpus/parse paths and response-schema digests, safe attachment encoding, canonical identities, complete attempts, bounded permanent details, and the unchanged timeout/429/5xx retry ceiling.
- Artifact evidence: create-only `live-preflight-evidence-v1` stores sanitized transport evidence and only `captured`; installed CLI replay revalidates strict schema, nested response digests, top-level logical digest, run identity, and private-path exclusion. It creates no parsing result or READY claim.
- Review and verification evidence: Standards and Spec have zero unresolved finding; focused coverage including the grounded Adapter regression is `26 passed`; full pytest is `264 passed`; Ruff format/lint, strict mypy, and Git whitespace checks pass.
- Active boundary: Issue #34 remains responsible for principal validation, typed blocker mapping, real attachment ownership/role policy, six-probe evidence qualification, and actual live-preflight orchestration. Issue #38 remains responsible for READY renewal.
- Active gate: Git Lifecycle Proposal Gate; no commit, push, pull request, or merge has been performed.

### 2026-07-22 — Issue #33 sealed-corpus qualification reached the Git Lifecycle Proposal Gate

- Entry evidence: fetched `origin/develop` equals Issue #32 merge `9502f21e10ece832cd2c1bc369d2b5d0f9f1fb94`; PR #40 is merged; Issues #31 and #32 are `CLOSED/COMPLETED`; #32 has no `ready-for-agent`; #33 received it only after native blocker verification; and draft PR #29 remains untouched at `b14653c7f2b6e7aad9a36c41c7141a9ccb3ce674`.
- Clean baseline: frozen sync, Ruff format/lint, strict mypy, all `239` pre-change tests, `git diff --check`, and clean branch status passed before the first RED.
- RED/GREEN evidence: the initial 13 tests failed on the absent v2 manifest and qualification CLI. Minimal implementation passed them. Review-driven tests then failed on a stale v1 card reference, missing wheel replay resources, and non-atomic output-pair failure before all three repairs reached GREEN.
- Contract evidence: qualification replays Issue #31 schema, manifest, per-source and sealed digests; validates the exact 100-case dataset v2 digest; projects required/frozen/forbidden identities and roles; requires synthetic reviewed CC0 provenance and a distractor; and emits only the approved `CORPUS_*` blocker family.
- Artifact evidence: success alone publishes canonical create-only receipt/import bytes through create-only links. The receipt contains bounded identities, expected/observed digests, and roles but no raw content or private path. The import manifest binds tenant/demo target, sealed digest, qualification receipt, and AX normalization/chunking contracts.
- Review evidence: Standards and Spec axes have zero unresolved finding after the dedicated v2 card, packaged replay bundle, and rollback-safe pair publication fixes.
- Verification evidence: all `254` repository tests and all `15` focused qualification tests pass; Ruff format/lint, strict mypy, wheel-content validation, replay, tamper rejection, and Git whitespace checks pass.
- Scope fence: Issues #34-#38 execution, repair, AX apply or service changes, experiments, PR #29, dependencies, and trajectory evaluation remain excluded.
- Completion condition: satisfied locally; work is stopped at the Git Lifecycle Proposal Gate.

### 2026-07-22 — Issue #32 authoring-boundary implementation and review reached GREEN

- Entry evidence: fetched `origin/develop` equals Issue #31 merge `df5891378732a653511e7fa37aae53ac56883672`; PR #39 is merged; Issue #31 is `CLOSED/COMPLETED`; Issue #32's native blocker is closed; #32 alone carries `ready-for-agent`; and draft PR #29 remains untouched at `b14653c7f2b6e7aad9a36c41c7141a9ccb3ce674`.
- Clean baseline: frozen sync, Ruff format/lint, strict mypy, all `232` pre-change tests, `git diff --check`, and clean branch status passed before the first RED.
- RED/GREEN evidence: all five initial tests first failed on the missing `launch-authoring` command. Minimal implementation passed them. Review added or strengthened denial probes for repository identity, file metadata, tool-label error handling, and the system keychain; each defect was observed failing before repair, and all seven authoring tests now pass.
- Boundary evidence: only the committed brief, exact pack schema, digest declaration, and generated digest inventory are readable; staging alone is writable; inherited environment secrets and all repository/evaluation/network/post-seal inputs are denied.
- Receipt evidence: `corpus-authoring-independence-receipt-v1` is create-only, binds the clean SHA, tool/input identities, capability classes, timing, exit, and path-redacted output digests, and retains no process transcript or raw/private material.
- Scope fence: qualification, mapping, real brief/content authoring, sealing execution, dataset comparison, AX operation, preflight, experiments, PR #29, new dependencies, and trajectory evaluation remain excluded.
- Review evidence: Standards and Spec axes have zero unresolved finding. The launcher rejects non-Braincrew remotes, allows only ancestor metadata needed to traverse declared/runtime paths, returns a typed invalid-label error without traceback, denies system-keychain data and metadata, and discards child transcripts without buffering them.
- Verification evidence: frozen sync, Ruff format/lint, strict mypy, all `239` repository tests, all `32` combined authoring/sealing tests, installed CLI help, and Git whitespace validation pass freshly.
- Completion condition: satisfied locally; work is stopped at the Git Lifecycle Proposal Gate.

### 2026-07-22 — Issue #31 schema sealing reached the Git Lifecycle Proposal Gate

- Entry evidence: fetched `origin/develop` and the branch base equal `e33de765dc54ac76159f249525456d5ab4e63667`; draft PR #29 is open at `b14653c7f2b6e7aad9a36c41c7141a9ccb3ce674`; AX Issue #33 is closed; AX PR #39 is merged as `47673b83a9fb431f2bad550781db18c7bee8b67e`; and Issue #31 carries `ready-for-agent` after the label moved from parent #30.
- Clean baseline: `uv sync --frozen --all-groups`, Ruff format/lint, strict mypy, full pytest (`207 passed`), `git diff --check`, and clean status succeeded before the first RED.
- RED/GREEN evidence: the missing vendored schemas and `seal-corpus` command produced the intended feature RED; 25 focused tests now pass. Review reproduced one unsafe backslash-path acceptance defect RED before its minimal rejection fix passed GREEN.
- Contract evidence: the four vendored AX schema and digest files match the merge commit byte-for-byte; source and manifest bytes fail closed on schema, path, UTF-8, BOM, line-ending, NFC, float, provenance/license, digest, unknown-field, evaluation-derived-field, and mutation violations.
- Artifact evidence: `corpus-sealing-receipt-v1` is create-only, omits raw or private material, and binds fixed schema identity plus ordered source identities/digests. Installed CLI replay reproduces the receipt and sealed-content digest and rejects tampered source bytes.
- Review evidence: Standards and Spec axes have zero unresolved finding after the test-helper simplification and path repair.
- Final verification: frozen sync, Ruff format/lint, strict mypy, `232 passed`, `git diff --check`, installed CLI seal/replay, sanitized receipt scan, and wheel schema inclusion all pass.
- Scope fence: no #32 authoring launcher, #33 qualification, #34 principal mapping, corpus authoring, AX operation, Issue #15 preflight change, experiment execution, dependency, or Agent trajectory work entered the diff.
- Active gate: commit, push, pull-request creation/modification, and merge require separate explicit authorization.

### 2026-07-20 — Issue #13 completed; Issue #14 static-dashboard implementation activated

- Upstream evidence: [PR #27](https://github.com/DHChe/braincrew-datateam-portfolio/pull/27) is `MERGED` at `2026-07-20T01:32:43Z` with squash merge commit `52e85ecc303291e0145ac0867c807e9579b04800`; its required `Python quality gates` check passed. [Issue #13](https://github.com/DHChe/braincrew-datateam-portfolio/issues/13) is `CLOSED/COMPLETED` at `2026-07-20T01:40:13Z`.
- Remote and cleanup evidence: after `git fetch --prune origin`, `origin/develop` points exactly to `52e85ecc303291e0145ac0867c807e9579b04800`. No local `*issue-13*` branch, remote `origin/*issue-13*` branch, registered Issue #13 worktree, or Issue #13 directory under the Braincrew worktree root remains.
- Dependency evidence: Issue #14's only declared blocker, Issue #13, is closed; Issue #14 is open and now carries `ready-for-agent`.
- Branch evidence: `/Users/astralpig/.config/superpowers/worktrees/braincrew/issue-14-static-dashboard` was created on `feat/issue-14-static-dashboard` from exact `origin/develop@52e85ecc303291e0145ac0867c807e9579b04800`.
- Clean baseline: `uv sync --frozen --all-groups`, Ruff format and lint, strict mypy, full pytest (`200 passed in 10.57s`), `git diff --check`, and clean branch status succeeded before the first RED.
- Locked frontend decision: root `npm@11.12.1` and `package-lock.json` lockfile v3; Node.js `>=20.19.0`; Next.js `16.2.10`; React `19.2.7`; TypeScript `5.9.3`; Prettier `3.9.5`; ESLint `9.39.5` with `eslint-config-next@16.2.10`; Vitest `4.1.10`; Playwright `1.61.1` Chromium smoke against `dashboard/out`; and transitive PostCSS `8.5.10` with zero npm-audit findings. ESLint 10 was rejected after clean-install peer conflicts with Next.js lint plugins.
- Command contract: `npm ci`, `npm run format:check`, `npm run lint`, `npm run typecheck`, `npm test -- --run`, `npm run build`, and `npm run test:e2e`.
- Rationale and rejection: npm is already shipped with Node and the repository had no frontend manager or lockfile evidence. pnpm, Yarn, and Bun add an unjustified bootstrap dependency; Jest and Cypress duplicate the selected test responsibilities. The accepted cost is a larger lockfile and a first-run Chromium download.
- Active skill: `test-driven-development`.
- Expected artifact: replay-validated and publish-safe Python `dashboard-export-v1`, readonly static Next.js comparison UI, ordered three-gate trace, metric and failure drill-down, publishable case evidence, golden total/decision equality, static production output, and browser smoke evidence.
- Scope exclusions: dashboard experiment execution, browser PostgreSQL/DuckDB access, live AX Verification, Agent trajectory evaluation, any Issue #13 threshold/digest/compatibility/gate change, and frontend recomputation of canonical evidence.
- Completion condition: all export/UI behaviors have observed RED/GREEN evidence, all required Python/frontend commands pass, separate Standards and Spec review report zero unresolved finding, and `verification-before-completion` passes before the Git Lifecycle Proposal Gate.

### 2026-07-20 — Issue #14 TDD implementation and two-axis review completed

- Python export RED/GREEN: missing `braincrew.dashboard_export`, missing `export-dashboard`, accepted email-like and sensitive slug identifiers, and missing execution provenance were each observed failing before the minimum exporter/CLI contract passed.
- Frontend RED/GREEN: the first contract test failed on missing `dashboard/lib/dashboard-data`; the first UI build failed on missing `app`/`pages`; taxonomy row projection and fixture/live provenance validation each failed before their readonly implementations passed.
- Golden evidence: `dashboard/data/dashboard-export-v1.json` retains canonical decision `PASS`, logical digest `sha256:f8630e70892f976ee120ac497ef63ce6cc64add8aa1d71989a576891b5ae7bbe`, 15 cases, 6 metrics, three ordered `PASS` gates, fixture mode, Evaluation Plane SHA, and SUT SHA. Frontend unit and Playwright assertions compare the rendered decision, digest, totals, gate count, evidence drill-down, and fixture-not-live label with that artifact.
  - **Superseded 2026-07-28 by Issue #89; the text above is deliberately unchanged as the record of what was true then.** The digest `sha256:f8630e70…5ae7bbe` is no longer the artifact's identity. Issue #89 closed finding K1 — the shipped export declared a **measured** cost that no producer in this repository can emit, inverting the cost-exclusion decision the ticket implements — by flipping the four golden fixtures to `cost_measurement_status: "unmeasured"` and regenerating the export. The current digest is `sha256:d426e04c0c2b960d8c8c17efc216688891b2078faaaa51ff226c137c2f8694ae`, pinned at `tests/frontend/dashboard-data.test.ts:120` and `tests/frontend/e2e/dashboard.spec.ts:18`; the artifact now renders **"Not measured — both runs declare cost unmeasured"**. Decision recorded in [the operational-measurement decision](../decisions/2026-07-28-operational-measurement-and-the-cost-exclusion.md) §11. Everything else in the bullet above — decision `PASS`, 15 cases, 6 metrics, three ordered gates, fixture mode — still holds. This pointer exists because independent review found the stale digest **in the commit**, not after it.
- Toolchain repair: clean npm installation exposed ESLint 10 peer incompatibilities with the Next 16 lint plugins, so the final lock uses ESLint `9.39.5`; transitive PostCSS is overridden to patched `8.5.10`, and `npm audit --audit-level=moderate` reports zero vulnerability.
- Static evidence: Next.js `output: "export"` generates `dashboard/out`; Playwright serves only that directory. A 1440×1000 full-page browser inspection showed the comparison, gates, metrics, operational deltas, and drill-down layout without an external runtime dependency.
- Standards review: PASS, zero unresolved finding. The exporter reuses the existing strict manifest contract and comparison replay/result-store boundaries, dependencies are pinned without a new package manager, imports and write behavior follow repository patterns, and no speculative service or database access was added.
- Spec review: PASS, zero unresolved finding. Publishability is fail closed, frontend values are readonly and copied, fixture evidence cannot masquerade as live AX evidence, golden totals/decision match the screen, and every explicit exclusion remains outside the diff.
- Verification evidence: `uv sync --frozen --all-groups`; `uv run ruff format --check .`; `uv run ruff check .`; `uv run mypy`; full `uv run pytest -q` with `207 passed`; both pre- and post-frontend `git diff --check`; `npm ci` with 472 audited packages and zero vulnerability; `npm run format:check`; warning-free `npm run lint`; `npm run typecheck`; `npm test -- --run` with 4 tests; `npm run build` with `/` statically prerendered into `dashboard/out`; and `npm run test:e2e` with 2 Chromium tests all pass.
- Final local state: the dedicated branch contains only Issue #14 changes in the working tree; no commit, push, PR creation/modification, or merge has occurred.
- Active next stage: Git Lifecycle Proposal Gate.
- Completion condition: explicit user authorization names the allowed Git action; otherwise the worktree remains uncommitted and unpublished.

### 2026-07-20 — Expanded PR #27 review repair published and cleared

- Authorization executed: one seven-file Lore repair commit, a force-free push to `origin/feat/issue-13-experiment-comparison`, and evidence-backed replies and resolution for all six review threads.
- Commit evidence: `f802bf815b758557d84fbcc240af21b6ab38ed0d`; its committed state passed frozen sync, Ruff format and lint, strict mypy, `200 passed in 9.89s`, `git diff --check`, and a clean Git status before push.
- Installed-CLI evidence: `/tmp/braincrew-issue13-commit.rduK6X` contains six comparisons and six successful replays; every DuckDB cache contains 90 rows, one decision, and one distinct digest; PASS, FAIL, and INVALID repeat digests match the locked values.
- Remote evidence: local, remote, and PR heads match `f802bf815b758557d84fbcc240af21b6ab38ed0d`; the replacement Python quality gate passed in 41 seconds; all six review threads contain a response and report resolved; GitHub reports `CLEAN`.
- Ticket evidence: Issue #13 remains open with `ready-for-agent`, as required before the separate merge decision.
- Active action: synchronize this completed transition in one status-only commit, then verify its replacement PR head before the squash-merge proposal.
- Completion condition: obtain explicit authorization for one Lore status commit and force-free push; merge remains a separate approval after the new head is verified.

### 2026-07-20 — Full six-thread audit expanded PR #27 repair scope

- Discovery: after `0bd3dc1dd067aa162342a65641a14341db237228` passed its replacement Python gate, a GraphQL review-thread query showed six unresolved inline threads. The earlier REST response had been truncated, so the prior two-thread assumption was an unverified workflow error rather than a code result.
- Previously handled threads: non-finite metric decimals already fail with controlled Pydantic `ValidationError`; recursive nested mapping mutation was reproduced RED and repaired by commit `0bd3dc1`.
- Additional confirmed defects: one zero-baseline case discarded computable run-level operational aggregates; accepted decimals could be rounded or overflowed by Parquet `DECIMAL(38, 28)`; a JSON publication failure could leave a blocking Parquet orphan; and library callers could use traversal comparison IDs outside the CLI guard.
- RED evidence: six focused tests failed for the expected missing contracts: failure-safe pair rollback, model-level safe ID, two exact Decimal constraints, zero-case aggregate preservation, and replayable derived-overflow invalidation.
- Minimal GREEN: `RunId` now guards comparison IDs; source decimals must fit Parquet exactly; case-relative deltas are nullable and independent from aggregate calculations; unrepresentable derived case deltas fail closed; Parquet relative columns accept null; JSON and Parquet stage in one temporary directory and publish via create-only links with synchronous rollback.
- Focused evidence: Ruff format/lint, strict mypy, `git diff --check`, and the comparison unit suite pass; the focused suite reports `40 passed`.
- Full repository evidence: `uv sync --frozen --all-groups`, Ruff format and lint, strict mypy, `git diff --check`, and the full suite pass; the suite reports `200 passed in 9.36s`.
- Installed-CLI evidence: from `/tmp/braincrew-issue13-expanded-review.hshjTh`, PASS, FAIL, and INVALID were each compared twice and replayed twice; all six JSON artifacts replayed, all six DuckDB caches contained 90 rows with one decision and one distinct digest, and repeated decisions retained identical digests: PASS `sha256:8a14166be831f330630580f3934803fcfa11d86763723bdbcebdfdee8bee1cf4`, FAIL `sha256:400507a8ffd1b6b289cf0f8b3d69e57dc97e8fbc90eb390969fbf18192c9d9b4`, INVALID `sha256:9e2bbc7e413318e9792939eeab5e77aae2040f9324a4132f8a28369a5ffea9a4`.
- Standards re-review: PASS with zero finding. The repair uses only standard-library temporary-directory and hard-link primitives, preserves create-only/no-overwrite behavior, reuses `RunId`, keeps changes ticket-local, and introduces no dependency or speculative service.
- Spec re-review: PASS with zero finding. Zero-case evidence no longer suppresses computable aggregates, canonical Parquet never silently rounds accepted source values, derived overflow fails closed and remains replayable, publication races preserve competing bytes, and all entry points enforce the safe identifier boundary without changing gate policy or fixture meaning.
- Scope boundary: no threshold, compatibility dimension, ordinary fixture decision/digest meaning, dashboard, live AX Verification, or Agent trajectory evaluation is added or changed.
- Active action: present the exact expanded repair publication proposal and stop before another commit, push, review reply, thread resolution, or merge.
- Completion condition: explicit authorization covers one Lore repair commit, a force-free push to the existing PR branch, and evidence-backed replies and resolution for all six review threads; merge remains a later, fresh decision after the replacement head and review state are verified.

### 2026-07-20 — PR #27 review-repair publication authorized

- Authorization: the user approved one Lore commit for the reviewed repair diff, a force-free push to `origin/feat/issue-13-experiment-comparison`, and evidence-backed reply and resolution for both automated inline review threads.
- Included scope: recursive sealing for accepted and derived comparison mappings, controlled non-finite-decimal regression coverage, TDD and re-review evidence, and synchronized decision, canonical design, interview defense, and delivery workflow documents.
- Required publication evidence: frozen sync, Ruff format and lint, strict mypy, full pytest, `git diff --check`, exact six-file staging, and clean Lore commit must pass before push.
- Required remote evidence: local, remote, and PR heads match; the replacement Python quality gate passes; both review threads are answered and resolved; GitHub reports merge state `CLEAN` with no unresolved blocker.
- Scope boundary: no gate threshold, fixture decision, logical digest, dashboard, live AX Verification, Agent trajectory evaluation, or unrelated file is included.
- Active exclusion: merge, Issue #13 closure, branch deletion, and worktree cleanup remain separate decisions.
- Next action: publish and verify the repair, then stop at a fresh squash-merge Git Lifecycle Proposal Gate.

### 2026-07-20 — PR #27 merge paused for review-driven TDD repair

- Merge preflight: frozen sync, Ruff format and lint, strict mypy, full pytest, `git diff --check`, local/remote head equality, and the required Python quality gate passed for PR head `e9ee64ac21a492b989ad609aad68487fe8818148`; GitHub reported merge state `CLEAN`.
- Review evidence: the later automated review attached two P2 suggestions to implementation commit `2ac9508fd3ec39b94ecbecd6c9f03adb41e64ac1`. API inspection found both inline comments before merge, so the no-unresolved-review-blocker condition was not satisfied and no merge occurred.
- Non-finite-decimal finding: not reproduced as a product defect. Under the locked Pydantic version, `NaN`, positive infinity, and negative infinity for primary or retrieval metrics already raise controlled `finite_number` `ValidationError` results before `ExperimentCaseResult.validate_metrics()` or CLI comparison arithmetic.
- Recursive-mutation finding: confirmed code defect. A frozen Pydantic model still permitted mutation of nested metric, model-parameter, and derived-delta dicts after the digest was computed. The RED regression failed because no `TypeError` was raised.
- Minimal GREEN: comparison contracts recursively freeze every accepted and derived mapping and nested list-like value. The focused comparison suite reports `34 passed`; Ruff format/lint and strict mypy pass after the repair.
- Standards re-review: PASS with zero finding. The repair follows the repository's TDD, no-new-dependency, immutable-evidence, documentation, and scope-fence rules; the ticket-local immutable mapping boundary is required to preserve Pydantic's canonical dictionary serialization while preventing ordinary mutation.
- Spec re-review: PASS with zero finding. The repair strengthens Issue #13's immutable artifact and replay contract without changing compatibility fields, gate order or thresholds, fixture meanings, deterministic digest payload, or explicit exclusions.
- Scope boundary: the repair changes only comparison artifact sealing and regression evidence. Gate thresholds, deterministic fixture digests, dashboard, live AX Verification, and Agent trajectory evaluation remain unchanged.
- Repository verification: frozen sync, Ruff format and lint, strict mypy, `git diff --check`, and full pytest pass; the repair suite contains 194 passing tests.
- Installed-CLI verification: PASS, FAIL, and INVALID fixtures each produce the same decision and logical digest across two independent comparison IDs; all six JSON artifacts replay, and all six disposable DuckDB caches contain 90 rows with one decision and one logical digest. The digests remain `sha256:8a14166be831f330630580f3934803fcfa11d86763723bdbcebdfdee8bee1cf4`, `sha256:400507a8ffd1b6b289cf0f8b3d69e57dc97e8fbc90eb390969fbf18192c9d9b4`, and `sha256:9e2bbc7e413318e9792939eeab5e77aae2040f9324a4132f8a28369a5ffea9a4` respectively.
- Verification artifacts: ephemeral comparison outputs are under `/tmp/braincrew-issue13-review.s7aBBF`, outside the repository and excluded from publication.
- Active action: present the exact repair diff, evidence, Lore commit and push strategy, replacement PR check requirement, and risk for explicit authorization.
- Completion condition: user explicitly authorizes the review-repair commit and push; no merge occurs until the replacement PR head passes remote verification and receives a fresh merge decision.

### 2026-07-20 — PR #27 published and first remote gate passed

- Authorization: the user approved a status-only durable workflow sync, one Lore commit, and a normal push to the existing Issue #13 branch; merge, Issue #13 closure, branch deletion, and worktree cleanup remain excluded.
- Publication evidence: implementation commit `2ac9508fd3ec39b94ecbecd6c9f03adb41e64ac1` is present on `origin/feat/issue-13-experiment-comparison`; review-ready [PR #27](https://github.com/DHChe/braincrew-datateam-portfolio/pull/27) is `OPEN` against `develop` and carries `Closes #13`.
- Remote evidence: the Python quality gate for the implementation commit completed successfully, GitHub reported merge state `CLEAN`, and the PR had no review or comment at the checkpoint.
- Claim boundary: published evidence covers deterministic fixture comparison and replay only. Dashboard, live AX Verification execution, and Agent trajectory evaluation remain unimplemented and unclaimed.
- Active action: commit only this workflow-state correction, push it without force to the existing PR branch, and verify the replacement PR head plus its required Python gate.
- Completion condition: local `HEAD`, the remote branch, and PR #27 head are identical; the new Python quality gate succeeds; the worktree is clean; Issue #13 remains open until an independently authorized merge.
- Next action: present a squash-merge proposal for PR #27 with current remote evidence and wait for explicit authorization.

### 2026-07-20 — Issue #13 local Lore commit verified; push and PR gate activated

- Commit result: branch `feat/issue-13-experiment-comparison` contains one ticket-scoped Lore commit above `origin/develop@eb252e4c32d1ea2167f0cc31371423541dc3b315`; the dedicated worktree was clean when committed-state verification began.
- Repository evidence: `uv sync --frozen --all-groups`, Ruff format check, Ruff lint, strict mypy, full pytest, and `git diff --check` pass from the committed tree; pytest reports `187 passed in 9.04s`.
- Installed-CLI evidence: PASS, FAIL, and INVALID fixtures each produce the same decision and logical digest across two independent comparison IDs, and all six canonical JSON/Parquet pairs replay successfully.
- Rebuilt-cache evidence: rebuilding DuckDB independently from each Parquet artifact produces 90 rows, one decision, and one logical digest for every PASS, FAIL, and INVALID run.
- Deterministic digests: PASS is `sha256:8a14166be831f330630580f3934803fcfa11d86763723bdbcebdfdee8bee1cf4`; FAIL is `sha256:400507a8ffd1b6b289cf0f8b3d69e57dc97e8fbc90eb390969fbf18192c9d9b4`; INVALID is `sha256:9e2bbc7e413318e9792939eeab5e77aae2040f9324a4132f8a28369a5ffea9a4`.
- Verification artifacts: committed-state outputs are under `/tmp/braincrew-issue13-committed.DIvmwx`, outside the repository and excluded from publication.
- Scope evidence: dashboard, live AX Verification execution, and Agent trajectory evaluation remain unimplemented and unclaimed.
- Active gate: push and pull-request creation remain unauthorized. Merge, Issue #13 closure, and worktree cleanup remain later independent decisions.
- Next action: present the push and review-ready pull-request proposal, then wait for explicit authorization before any remote write.

### 2026-07-20 — Issue #13 local Lore commit authorized

- Authorization: the user approved the proposed local Issue #13 Lore commit and clean committed-state verification.
- Included scope: the reviewed comparison and release-gate contracts, compatibility and confound enforcement, case/macro and failure-taxonomy aggregation, canonical JSON/Parquet result-store path, disposable DuckDB cache, deterministic replay, PASS/FAIL/INVALID Verification fixtures, regression tests, dependency lock, canonical design lock, interview defense, and workflow evidence.
- Required pre-commit evidence: frozen dependency sync, Ruff format and lint, strict mypy, full pytest, `git diff --check`, branch/base verification, and ticket-scoped status inspection must pass immediately before commit.
- Required post-commit evidence: the committed worktree is clean; the same repository gates pass; the installed CLI reproduces PASS, FAIL, and INVALID decisions and deterministic digests from committed fixtures; every JSON/Parquet pair replays successfully; DuckDB remains rebuildable from Parquet.
- Active exclusion: push, pull-request creation or modification, merge, Issue #13 closure, and worktree cleanup remain separate Git lifecycle decisions and are not authorized by this approval.
- Next action: create one verified Lore commit, complete committed-state verification, then stop at the next Git Lifecycle Proposal Gate.

### 2026-07-19 — Issue #13 final verification completed; Git proposal gate activated

- Completed skill: `verification-before-completion`.
- Repository evidence: `uv sync --frozen --all-groups`, Ruff format check, Ruff lint, strict mypy, full pytest, and `git diff --check` all pass; the fresh full suite reports `187 passed in 8.88s`.
- Installed-CLI decisions: `.venv/bin/braincrew-eval compare` produced PASS, FAIL, and INVALID twice each from the 15-case Verification fixtures. The repeated logical digests are respectively `sha256:8a14166be831f330630580f3934803fcfa11d86763723bdbcebdfdee8bee1cf4`, `sha256:400507a8ffd1b6b289cf0f8b3d69e57dc97e8fbc90eb390969fbf18192c9d9b4`, and `sha256:9e2bbc7e413318e9792939eeab5e77aae2040f9324a4132f8a28369a5ffea9a4`.
- Replay and cache evidence: all six installed-CLI JSON/Parquet pairs replay to the stored decision and digest. Each disposable DuckDB cache and source Parquet contains the same 90 analytical rows with one decision and one logical digest.
- Base and upstream evidence: after a fresh fetch, both branch `HEAD` and `origin/develop` remain exactly `eb252e4c32d1ea2167f0cc31371423541dc3b315`; PR #26 remains merged with its Python quality check successful, Issue #12 remains closed, and Issue #13 remains open with `ready-for-agent`.
- Artifact location: ephemeral verification evidence is under `/tmp/braincrew-issue13-verification.zJxX3L`; it is outside the repository and is not proposed for commit.
- Git state: all Issue #13 changes remain uncommitted in the dedicated worktree. No commit, push, pull request, or merge has been performed.
- Active gate: Git Lifecycle Proposal Gate.
- Completion condition: present the target branch and remote, exact included scope, fresh verification evidence, PR/merge strategy, and known risks; wait for explicit authorization before the first Git lifecycle action.

### 2026-07-19 — Issue #13 ticket review completed; final verification started

- Completed skill: ticket-scoped `code-review` against fixed point `origin/develop@eb252e4c32d1ea2167f0cc31371423541dc3b315`.
- Standards result: PASS with zero unresolved finding. Comparison logic no longer owns artifact storage or DuckDB; the Immutable Result Store owns create-only JSON/Parquet, replay, and cache rebuild. The retrieval configuration field now names only the fixed digest, mutable model defaults use a factory, and required provenance digests are strict canonical SHA-256 values.
- Spec result: PASS with zero unresolved finding. Review-driven RED/GREEN repairs reject per-case applicability movement, corpus or dirty-state drift, missing retrieval confound evidence, under-covered Verification denominators, missing operational evaluator provenance, severity drift in frozen critical failures, and failure identities that do not reference run evaluator provenance. Failure taxonomy now carries baseline, candidate, and signed delta counts by code and family.
- Fixture boundary: all PASS/FAIL/INVALID summaries are explicit 15-case Verification inputs that meet the frozen 6/9/10/10/15/5 denominator minima and carry present, unchanged Recall@5, MRR@10, and authority-priority confound evidence.
- Focused evidence: Ruff format/lint, strict mypy, `git diff --check`, and the comparison unit plus CLI acceptance suite pass; the focused suite reports `28 passed`.
- Documentation evidence: the canonical design, interview defense, and workflow status now record the same split, minimum-coverage, provenance, taxonomy, storage, replay, gate, and exclusion contracts.
- Active skill: `verification-before-completion`.
- Completion condition: every required repository command and installed CLI PASS/FAIL/INVALID compare/replay/digest/cache check passes with fresh evidence; no commit, push, pull request, or merge occurs.
- Next action: run final verification from the dedicated Issue #13 worktree and record the exact evidence before proposing the Git lifecycle sequence.

### 2026-07-19 — Issue #13 TDD implementation completed; code review started

- Completed skill: `test-driven-development`.
- RED/GREEN evidence: the missing comparison surface, immutable JSON/Parquet writer, DuckDB cache rebuild, installed CLI compare/replay path, missing required provenance, retrieval confound drift, metric-denominator drift, unordered Gate 3 execution, Parquet tampering, repeating-decimal truncation, and missing taxonomy aggregation were each observed failing for the expected missing behavior or actual defect before minimal GREEN.
- Fixture decisions: the installed CLI produces PASS for a 3-point claim-support improvement, FAIL for a 16-percent p95 latency regression, and INVALID for model-identity drift.
- Artifact contract: `experiment-comparison-artifact-v1` stores complete baseline/candidate summaries, case and macro deltas, operational changes, code/family taxonomy, ordered gate traces, decision and reasons, plus a logical digest independent of comparison and input run IDs. JSON and Parquet are create-only canonical evidence; DuckDB is rebuildable cache only.
- Focused and regression evidence: Ruff format/lint, strict mypy, `git diff --check`, and full pytest all pass; the fresh suite reports `177 passed`.
- Documentation evidence: the canonical design, interview defense, and workflow status record the same compatibility, confound, gate, storage, replay, validation, and exclusion boundaries.
- Active skill: ticket-scoped `code-review` against fixed point `origin/develop@eb252e4c32d1ea2167f0cc31371423541dc3b315`.
- Completion condition: separate Standards and Spec axes report zero unresolved blocker after any review-driven RED/GREEN repair.
- Next action: review all tracked and untracked Issue #13 changes without committing, pushing, opening a pull request, or merging.

### 2026-07-19 — PR #26 and Issue #12 completed; Issue #13 implementation activated

- Upstream evidence: [PR #26](https://github.com/DHChe/braincrew-datateam-portfolio/pull/26) is `MERGED` into `develop` at `2026-07-19T14:52:55Z`; its squash merge commit is `eb252e4c32d1ea2167f0cc31371423541dc3b315`, fetched `origin/develop` points to that exact commit, and the required `Python quality gates` check completed successfully.
- Dependency evidence: blocker [Issue #12](https://github.com/DHChe/braincrew-datateam-portfolio/issues/12) is `CLOSED` at `2026-07-19T14:53:22Z`; [Issue #13](https://github.com/DHChe/braincrew-datateam-portfolio/issues/13) is open and now carries `ready-for-agent`.
- Branch evidence: dedicated worktree `/Users/astralpig/.config/superpowers/worktrees/braincrew/issue-13-experiment-comparison` was created on `feat/issue-13-experiment-comparison` from `origin/develop@eb252e4c32d1ea2167f0cc31371423541dc3b315`.
- Baseline evidence: `uv sync --frozen --all-groups` completed and the unchanged branch baseline reported `159 passed in 7.79s`.
- Active skill: `test-driven-development`.
- Expected artifact: compatible fixture baseline/candidate comparison with immutable canonical JSON and Parquet, disposable DuckDB query cache, complete version compatibility and confound evidence, exact case/macro aggregation and failure taxonomy, three ordered release gates, deterministic replay, and fixture PASS/FAIL/INVALID paths.
- Explicit exclusions: dashboard, live verification experiment, and Agent trajectory evaluation.
- Completion condition: every new contract and defect is observed RED before minimal GREEN; the canonical design, interview defense, and workflow status agree; Standards and Spec reviews have zero unresolved blocker; every required repository and installed-CLI verification passes before the Git Lifecycle Proposal Gate.
- Next action: map the frozen gate and compatibility contracts to focused RED tests, then implement the smallest comparison boundary that satisfies them.

### 2026-07-19 — Issue #12 Git publication authorized

- Authorization: the user approved one ticket-scoped Lore commit, committed-state verification, push to `origin/feat/issue-12-dataset-freeze`, and a review-ready pull request targeting `develop` with `Closes #12`.
- Included scope: the reviewed 100-case dataset registry and card, allocation/split/identity/schema/provenance/license/risk/applicability/leakage validation, scoring-content digests, immutable fixture artifact and deterministic replay, parsing replay repair, regression tests, canonical design lock, interview defense, and delivery-workflow evidence.
- Required pre-push evidence: the committed worktree is clean; frozen sync, Ruff format and lint, strict mypy, all tests, and diff checks pass; two installed 100-case create/replay runs share one logical digest and record the new Evaluation Plane commit SHA with `dirty_worktree=false`.
- Active exclusion: merge remains a later Git lifecycle decision after required remote checks and review evidence. Issue #13 comparison/release gates, live baseline/candidate execution, dashboard, LLM judge, AX product changes, and Agent trajectory evaluation remain out of scope.
- Next action: create the approved Lore commit, verify the clean committed state, then push and open the review-ready pull request only if every gate passes.

### 2026-07-19 — Issue #12 final verification completed; lifecycle proposal gate reached

- Completed skills: `test-driven-development`, ticket-scoped `code-review`, and `verification-before-completion`.
- Repository evidence: `uv sync --frozen --all-groups`, Ruff format and lint, strict mypy, full pytest (`159 passed`), and `git diff --check` all exited successfully from the complete reviewed worktree.
- Installed CLI evidence: two independent `.venv/bin/braincrew-eval run-dataset` executions created `dataset-run-artifact-v1` artifacts with different run IDs; both stored and replayed `COMPLETED`, 100 total/scored cases, component states `COMPLETED`, and identical logical digest `sha256:6eb713bf0707f8c4baf3f6afe8446af3b306cea472020494c72b1587029b4896`.
- Dataset evidence: the artifacts reproduce 20 parsing / 30 retrieval / 40 grounded-answer / 10 visibility-abstention, 70 Calibration / 30 Verification, minimum Verification denominators 6/9/10/10/15/5, and dataset digest `sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b`.
- Replay evidence: snapshot, provenance, component evaluations, and logical digest were recomputed successfully for both artifacts. Existing 20/30/50-case create/replay compatibility remains covered by the fresh full regression suite and final dual-axis review.
- Provenance evidence: pre-commit artifacts correctly record Evaluation Plane base commit `c6cd5920ed7b46798618734c7c55977b89c9d9af` with `dirty_worktree=true`; the declared non-executed AX SUT remains `c318b2192006bdb36a5bd5b3a2bc403425b45701` with unknown dirty state.
- Committed-state gate: the required Issue #12 commit SHA and `dirty_worktree=false` artifact cannot exist before commit authorization. It is a mandatory post-commit, pre-push verification, not a passed pre-commit claim.
- Scope evidence: no Issue #13 comparison/release gate, live baseline/candidate run, dashboard, LLM judge, AX product change, or Agent trajectory evaluation was implemented or claimed.
- Active gate: Git Lifecycle Proposal Gate. No Issue #12 commit, push, pull request, or merge has been performed.
- Next action: present the exact Lore commit intent, target branch/remote, included changes, verification evidence, PR/merge strategy, known risks, and post-commit clean-state check for explicit authorization.

### 2026-07-19 — Issue #12 code review completed; final verification started

- Standards result: PASS with zero remaining finding. Bundle path escape, duplicate canonical-digest implementations, duplicated bundle/snapshot invariants, and misleading focus-applicability naming/detail were repaired; digest logic is shared and bundle load delegates semantic invariants to the replay validator.
- Spec result: PASS with zero remaining finding and no scope creep. Review-driven RED/GREEN repairs cover expected grounded-answer literals embedded in queries, zero and focus-specific applicability drift, unreviewed provenance, rehashed dataset-level license drift, rehashed snapshot path escape, and manifest/component/case source-type disagreement.
- Replay boundary: rehashed adversarial snapshots now fail closed for answer leakage, applicability, provenance review state, focus applicability, dataset-level license, component path, and source-type drift even when component, integrated, and top-level logical digests are recomputed.
- Focused evidence after review: the Issue #12 contract/unit/acceptance suites plus existing fixture, parsing, retrieval, and grounded acceptance regressions report `64 passed`; Ruff lint and strict mypy pass.
- Documentation evidence: the canonical design, interview defense dossier, and workflow status now state the same bundle/replay path, license, provenance-source, answer-leakage, and focus-specific applicability contracts.
- Active skill: `verification-before-completion`.
- Completion condition: frozen sync, Ruff format/lint, mypy, full pytest, `git diff --check`, installed 100-case fixture create/replay twice, logical-digest comparison, artifact/provenance inspection, and final Git state checks all pass with fresh evidence.
- Next action: execute the full verification sequence, then stop before any commit, push, pull request, or merge at the Git Lifecycle Proposal Gate.

### 2026-07-19 — Issue #12 TDD implementation completed; code review started

- Completed skill: `test-driven-development`.
- Frozen contract: `braincrew-evaluation-dataset@1.0.0` composes exactly 100 cases at 20 parsing / 30 retrieval / 40 grounded-answer / 10 visibility-abstention and 70 Calibration / 30 Verification. The integrated scoring-content digest is `sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b`.
- RED/GREEN evidence: missing registry/card/CLI surfaces; allocation and split contracts; stable and duplicate identity/content checks; component schema declaration and payload validation; provenance, license, risk, metric applicability, cross-split leakage, answer leakage, component and integrated digest invalidation; full 100-case aggregation; replay tamper rejection; and parsing replay compatibility were each observed failing for the expected missing contract or actual defect before minimal GREEN.
- Defect classification: parsing artifacts were not supported by the shared replay dispatcher; a false manifest component schema declaration produced only a digest mismatch; and a missing declared dataset card was accepted. These actual contract defects were reproduced as RED and repaired. Missing/duplicate observation, append-only collision, and selected invalid-run tests passed on first addition and are recorded as coverage gaps, not newly discovered production defects.
- Execution contract: `run-dataset` combines the existing parsing, retrieval, and grounded fixtures into immutable case-level and aggregate results. Independent run envelopes share a logical digest, while replay revalidates dataset snapshots and recomputes component evaluations. Existing 20/30/50-case commands and replays remain compatible.
- Focused evidence before review: the new contract, unit, and acceptance suites plus existing fixture, parsing, retrieval, and grounded acceptance regressions report `55 passed`; mypy passes across 33 source files.
- Documentation evidence: rationale, rejected alternatives, trade-offs, failure modes, validation evidence, exclusions, and likely interview follow-ups are synchronized in the canonical design, interview defense dossier, and this workflow checkpoint.
- Active skill: ticket-scoped `code-review` against fixed point `origin/develop@c6cd5920ed7b46798618734c7c55977b89c9d9af`.
- Completion condition: separate Standards and Spec reviewers return PASS with zero unresolved blocker; every behavioral finding must enter a new RED/GREEN cycle before re-review.
- Next action: review all tracked and untracked Issue #12 changes without committing, pushing, opening a pull request, or merging.

### 2026-07-19 — PR #25 and Issue #11 completed; Issue #12 implementation activated

- Upstream evidence: [PR #25](https://github.com/DHChe/braincrew-datateam-portfolio/pull/25) is `MERGED` into `develop` at `2026-07-19T10:05:39Z`; its squash merge commit is `c6cd5920ed7b46798618734c7c55977b89c9d9af`, fetched `origin/develop` points to that exact commit, and the commit is an ancestor of the Issue #12 branch. The required `Python quality gates` check completed successfully.
- Dependency evidence: blocker Issues [#8](https://github.com/DHChe/braincrew-datateam-portfolio/issues/8), [#9](https://github.com/DHChe/braincrew-datateam-portfolio/issues/9), and [#11](https://github.com/DHChe/braincrew-datateam-portfolio/issues/11) are all `CLOSED`; [Issue #12](https://github.com/DHChe/braincrew-datateam-portfolio/issues/12) is open and now carries `ready-for-agent`.
- Branch evidence: dedicated worktree `/Users/astralpig/.config/superpowers/worktrees/braincrew/issue-12-dataset-freeze` was created on `feat/issue-12-dataset-freeze` from current `origin/develop@c6cd5920ed7b46798618734c7c55977b89c9d9af`.
- Active skill: `test-driven-development`.
- Expected artifact: one strict, versioned 100-case dataset registry that composes the frozen parsing, retrieval, grounded-answer, and visibility/abstention cases; validates identity, allocation, split, provenance, license, risk, applicability, and leakage invariants; records a scoring-content digest and dataset card; and executes all fixture observations into immutable case-level and aggregate results with deterministic replay.
- Completion condition: every new validation and mutation is observed RED for the expected missing contract or actual defect before minimal GREEN; the existing 20/30/50-case fixture and replay paths remain compatible; the installed full 100-case fixture create/replay path, independent logical-digest comparison, repository gates, ticket-scoped Standards and Spec review, and `verification-before-completion` all pass before the Git Lifecycle Proposal Gate.
- Clean baseline: `uv sync --frozen --all-groups`, Ruff format and lint, mypy, full pytest (`122 passed`), `git diff --check`, and clean status succeeded before the first RED.
- Scope exclusions: Issue #13 baseline/candidate comparison and release gates, live baseline/candidate execution, dashboard implementation, LLM-as-judge scoring, AX product changes, and Agent trajectory evaluation.
- Next action: add and run the first failing integrated dataset-contract test before production implementation.

### 2026-07-19 — Issue #11 Git publication authorized

- Authorization: the user approved one ticket-scoped Lore commit, committed-state verification, push to `origin/feat/issue-11-answer-mode-abstention`, and a review-ready pull request targeting `develop` with `Closes #11`.
- Included scope: the reviewed 50-case answer-quality dataset and observations, deterministic Answer Mode, abstention, visibility and role contracts, invalid and hard-failure preservation, create-only artifact and replay-integrity repairs, regression tests, canonical design lock, interview defense, and workflow evidence.
- Required pre-push evidence: the committed worktree is clean; frozen sync, Ruff format and lint, mypy, all tests, diff checks, and installed 50-case grounded CLI create/replay pass with the new Evaluation Plane commit SHA and `dirty_worktree=false`.
- Active exclusion: merge remains a later Git lifecycle decision after required remote checks and review evidence.
- Next action: create the approved Lore commit, verify the clean committed state, then push and open the review-ready pull request only if every gate passes.

### 2026-07-19 — Issue #11 final verification completed; lifecycle proposal gate reached

- Completed skills: `test-driven-development`, ticket-scoped `code-review`, and `verification-before-completion`.
- Repository evidence: `uv sync --frozen --all-groups`, Ruff format and lint, mypy, full pytest (`122 passed`), and `git diff --check` all exited successfully from the complete reviewed worktree.
- Installed CLI evidence: `.venv/bin/braincrew-eval run-grounded` created `grounded-run-artifact-v1`; installed CLI replay reproduced `COMPLETED` and logical digest `sha256:7e2f5e00bedebe5022158febb1a6b5b76b4a5c1fbbbace88799c62658780a351`.
- Artifact evidence: all 50 case evaluations are stored; Verification coverage is 15 cases with Answer Mode denominator 15 and abstention denominator 5. Exact macros are claim support `13/16`, citation precision `69/80`, citation coverage `73/80`, Answer Mode `49/50`, and abstention `4/5`; hard-failure cases are `GA-003`, `GA-008`, `VA-003`, `VA-005`, `VA-008`, and `VA-009`.
- Provenance evidence: dataset `braincrew-answer-quality@1.0.0` has digest `sha256:f3a6f6848cccb4c5bddea8f5f9df9151b08b61b8537054c46afb7855957d3fbe`; declared non-executed AX SUT is `c318b2192006bdb36a5bd5b3a2bc403425b45701`; fixture Adapter and all Answer Mode, abstention, visibility, claim, traversal, normalizer, matcher, source-resolution, and guard versions or digests are recorded.
- Pre-commit state: Evaluation Plane provenance correctly records base commit `c4ae62f1d1dfa905f34a02dbb5fa647affe8076c` with `dirty_worktree=true`. The required committed-state SHA and `dirty_worktree=false` artifact cannot exist before the Git Lifecycle Proposal Gate authorizes a commit; it remains a mandatory post-commit, pre-push check.
- Scope evidence: the run is fixture-authoritative only. No full 100-case freeze, live comparison, release gate, dashboard, LLM judge, AX product change, or Agent trajectory evaluation was implemented or claimed.
- Active gate: Git Lifecycle Proposal Gate. No Issue #11 commit, push, pull request, or merge has been performed.
- Next action: present the exact Lore commit, target branch/remote, included changes, verification evidence, PR/merge strategy, known risks, and post-commit clean-state check for explicit authorization.

### 2026-07-19 — Issue #11 code review completed; final verification started

- Standards result: PASS with zero remaining finding. Ruff format/lint, mypy, and `git diff --check` pass after the review repairs; no new dependency, AX product change, release-gate logic, or out-of-scope feature was introduced.
- Spec findings repaired through RED/GREEN: punctuation inside a protected identifier could bypass atom-level leakage scanning; unavailable observations erased hard-failure evidence during `INVALID` return; an ambiguous atom could hide a forbidden conclusive proposition; replay trusted stored dataset digest and SUT identity after a top-level rehash.
- Repair evidence: visibility now scans full normalized generated fields before atomization and preserves leakage beside `INVALID`; forbidden abstention checks inspect every matched proposition; invalid runs retain available case diagnostics and hard-failure identities; replay recomputes dataset provenance and SUT identity from stored snapshots.
- Focused re-review evidence: grounded evaluator, run, and CLI acceptance suites report `37 passed`; Ruff format and lint pass, mypy succeeds across 28 source files, and `git diff --check` passes.
- Active skill: `verification-before-completion`.
- Completion condition: frozen sync, all quality gates, full pytest, installed `braincrew-eval` 50-case create/replay, artifact/provenance inspection, and final Git state checks all pass with fresh evidence.
- Next action: execute the full verification sequence from the complete reviewed worktree, then stop at the Git Lifecycle Proposal Gate.

### 2026-07-19 — Issue #11 TDD implementation completed; code review started

- Completed skill: `test-driven-development`.
- RED/GREEN evidence: frozen 40/10 allocation, split drift, Answer Mode and abstention applicability, exact mode equality, forbidden conclusive abstention, `out_of_scope`, protected-identifier leakage, forbidden-role propositions, observation role mismatch, 50-case macro aggregation, snapshot compatibility versions/digests, and conclusive-proposition identity integrity were each observed failing for the expected missing contract or real defect before minimal repair.
- Defect evidence: runtime split drift initially remained `COMPLETED` and cross-role observations lacked execution-role provenance; both were reproduced as RED, then repaired to fail closed as `INVALID`. The unavailable and 15/5 minimum-applicability regressions passed on first addition and are recorded as coverage gaps, not production-code defects.
- Fixture evidence: `braincrew-answer-quality@1.0.0` contains 40 grounded-answer cases at 30/10 and 10 visibility/abstention cases at 5/5. Exact macro goldens are claim support `13/16`, citation precision `69/80`, citation coverage `73/80`, Answer Mode `49/50`, and abstention `4/5`; Verification denominators are 15 and 5.
- Hard-failure evidence: `GA-003`, `GA-008`, `VA-003`, `VA-005`, `VA-008`, and `VA-009` preserve unsupported-confidence, failed-abstention, protected-identifier, forbidden-conclusion, and forbidden-role identities without mislabeling successful execution as infrastructure failure.
- Compatibility evidence: the artifact adds snapshot-derived `answer-mode-v1`, `abstention-v1`, and `answer-visibility-v1` digests, stores `executed_role`, and rejects rehashed contract-digest tampering during replay.
- Documentation evidence: the implementation lock, rationale, rejected alternatives, trade-offs, failure modes, validation boundary, and interview follow-ups are synchronized in the canonical design, interview defense dossier, and this workflow checkpoint.
- Active skill: ticket-scoped `code-review` with separate Standards and Spec axes against fixed point `origin/develop@c4ae62f1d1dfa905f34a02dbb5fa647affe8076c`.
- Completion condition: both axes return PASS with zero unresolved blocker; any behavioral finding must enter a new RED/GREEN cycle before re-review.
- Next action: review all tracked and untracked Issue #11 changes without committing, pushing, opening a pull request, or merging.

### 2026-07-19 — PR #24 and Issue #10 completed; Issue #11 implementation activated

- Upstream evidence: [PR #24](https://github.com/DHChe/braincrew-datateam-portfolio/pull/24) is `MERGED` into `develop` at `2026-07-19T08:59:32Z`; its squash merge commit is `c4ae62f1d1dfa905f34a02dbb5fa647affe8076c`, fetched `origin/develop` points to that exact commit, and the commit is an ancestor of the Issue #11 branch.
- Dependency evidence: blocker [Issue #10](https://github.com/DHChe/braincrew-datateam-portfolio/issues/10) is `CLOSED` at `2026-07-19T09:00:09Z`; [Issue #11](https://github.com/DHChe/braincrew-datateam-portfolio/issues/11) is open and now carries `ready-for-agent`.
- Branch evidence: dedicated worktree `/Users/astralpig/.config/superpowers/worktrees/braincrew/issue-11-answer-mode-abstention` was created on `feat/issue-11-answer-mode-abstention` from current `origin/develop@c4ae62f1d1dfa905f34a02dbb5fa647affe8076c`.
- Active skill: `test-driven-development`.
- Expected artifact: a deterministic 40-case grounded-answer plus 10-case visibility/abstention benchmark with exact Answer Mode and abstention metrics, zero-tolerance unsupported-confidence and forbidden-role leakage evidence, immutable case and aggregate results, and snapshot-derived replay tamper rejection.
- Completion condition: every new behavior is observed failing for the expected missing-contract or real-defect reason before minimal implementation; the installed 50-case fixture create/replay path, repository gates, ticket-scoped Standards and Spec review, and `verification-before-completion` all pass before the Git Lifecycle Proposal Gate.
- Clean baseline: `uv sync --frozen --all-groups`, Ruff format and lint, mypy, and full pytest (`101 passed`) succeeded with a clean worktree before the first RED.
- Scope exclusions: Issue #12's full 100-case freeze, live baseline/candidate comparison, release gates and threshold comparison, dashboard implementation, LLM-as-judge scoring, AX product changes, and Agent trajectory evaluation.
- Next action: inspect the locked answer-mode, abstention, visibility, artifact, and Adapter contracts, then add and run the first failing Issue #11 contract test before production implementation.

### 2026-07-19 — Issue #10 TDD implementation completed; code review started

- Completed skill: `test-driven-development`.
- RED/GREEN evidence: claim normalization and traversal, proposition and observation contracts, source-text resolution, claim/citation metrics, mixed contradiction, unmapped and ambiguous atoms, required-path placeholders, high-risk fail-closed behavior, zero-applicability invalidation, exact metric validation, ten-case macro aggregation, create-only CLI storage, and replay tamper detection were each observed failing for the expected missing or defective behavior before passing.
- Fixture evidence: ten Verification cases at `braincrew-grounded-answer-initial@1.0.0` produce hand-calculated macro goldens of claim-support precision `1/4`, citation precision `9/20`, and citation coverage `13/20`; `GA-003` and `GA-008` preserve high-risk hard-failure evidence.
- Compatibility evidence: `grounded-run-artifact-v1` records evaluator `grounded-answer-v1`, adapter `fixture-grounded-sut-v1`, declared AX SUT SHA `c318b2192006bdb36a5bd5b3a2bc403425b45701`, and proposition, traversal, normalizer, source-resolution, and guard versions.
- Pre-review verification: Issue #10 focused pytest reports `25 passed`; full pytest reports `94 passed`; Ruff format and lint, mypy, and `git diff --check` pass after the final GREEN refactor.
- Documentation evidence: the implementation lock, rationale, rejected alternatives, trade-offs, failure modes, validation boundary, and likely interview follow-ups are synchronized in the canonical design and interview defense dossier.
- Active skill: ticket-scoped `code-review` with separate Standards and Spec axes against fixed point `origin/develop@b67929a0546d32d6ffafc7b801028c9c53fc2d6a`.
- Completion condition: every blocking finding is repaired through a new RED/GREEN cycle and both review axes pass with zero unresolved blocker.
- Next action: review all tracked and untracked Issue #10 changes without committing, pushing, opening a pull request, or merging.

### 2026-07-19 — Issue #10 code review requested fixes; review-driven TDD repairs completed

- Standards finding: the CLI accepted an SUT SHA that could disagree with the observation batch, allowing contradictory experiment provenance. A failing acceptance test reproduced artifact creation with mismatched SHAs; the command now fails closed before repository capture or artifact creation.
- Spec findings: the initial proposition schema used non-canonical modality names, required `object`, omitted forbidden Answer Modes and matcher identity; release failure IDs were reversed; source resolution lacked an executable `AxHttpAdapter.source_text()` integration seam; missing-output placeholders could receive citation-coverage credit; and compatibility plus hand-calculated case evidence was incomplete.
- RED/GREEN repair evidence: focused failures reproduced every behavioral defect before repair. The schema now uses `must`, `may`, `must_not`, `unknown`, and `review_required`; keeps `object` optional; records forbidden modes and matcher digests; emits the exact locked `A-*` identities; resolves unique cited sources through the Issue #7 Adapter seam; excludes placeholders from the coverage numerator; records atomizer/normalizer/matcher/proposition/case digests; and freezes all case fractions plus a zero replay delta.
- Current focused evidence: Ruff format and lint pass, mypy succeeds across 28 source files, and the Issue #10 contract/unit/acceptance selection reports `30 passed`.
- Active skill: ticket-scoped `code-review` re-review with separate Standards and Spec axes.
- Completion condition: both reviewers confirm zero unresolved blocking finding against the repaired complete diff.
- Next action: run both re-review axes, then transition to `verification-before-completion` only if both pass.

### 2026-07-19 — Issue #10 second specification review repairs completed

- Remaining Spec integrity finding: replay recomputed evaluation and the top-level digest but trusted stored derived compatibility digests. A RED acceptance test proved that an attacker could rewrite a matcher-set digest and then rehash the artifact. Compatibility derivation is now shared by build and replay, and replay rejects any snapshot-derived mismatch.
- Remaining Spec coverage gap: the existing source-resolution mismatch test was standard-risk only. A focused high-risk characterization test now proves that a conclusive claim with citation identity but unresolved supporting text retains both `A-UNSUPPORTED-CLAIM` and `A-UNSUPPORTED-HIGH-RISK-CONCLUSION` plus its hard-failure atom identity. The implementation already behaved fail-closed; this was a missing regression proof, not a production-code defect.
- Active skill: ticket-scoped `code-review` final re-review.
- Completion condition: Standards remains PASS and Spec confirms both remaining MEDIUM findings are closed.
- Next action: request the final Spec re-review, then start `verification-before-completion` if it returns zero blocker.

### 2026-07-19 — Issue #10 code review completed; final verification started

- Standards result: PASS with zero blocker. The SUT SHA provenance repair and its no-artifact-on-mismatch regression passed; the earlier LOW duplication concern was withdrawn because a shared factory would be speculative beyond the repository's current domain-specific artifact pattern.
- Spec result: PASS with zero blocker. Final re-review confirmed snapshot-derived compatibility recomputation during replay and the high-risk source-resolution critical identity regression.
- Active skill: `verification-before-completion`.
- Completion condition: every required repository gate and an installed `braincrew-eval run-grounded` plus `replay` execution pass from the complete repaired worktree, followed by exact branch/base/status inspection.
- Next action: run the full verification sequence and record its fresh evidence before presenting the Git lifecycle proposal.

### 2026-07-19 — Issue #10 final verification completed; lifecycle proposal gate reached

- Completed skills: `test-driven-development`, ticket-scoped `code-review`, and `verification-before-completion`.
- Fresh repository evidence: `uv sync --frozen --all-groups`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, `uv run pytest -q`, and `git diff --check` passed; pytest reported `101 passed`.
- Installed CLI evidence: `braincrew-eval run-grounded` created `grounded-run-artifact-v1` and `braincrew-eval replay` reproduced logical digest `sha256:12950b2c6180eec6e928f3565a98f634bc9d239ef75842be8775960d112c8b1f` with `COMPLETED`. Coverage is ten total and ten Verification cases; claim-support precision is `1/4`, citation precision `9/20`, citation coverage `13/20`, and high-risk cases remain `GA-003` and `GA-008`.
- Provenance evidence: the artifact records declared non-executed AX SUT SHA `c318b2192006bdb36a5bd5b3a2bc403425b45701`, fixture Adapter `fixture-grounded-sut-v1`, and all locked compatibility versions and digests. This remains fixture evidence, not a live AX answer-quality claim.
- Branch evidence: after `git fetch --prune origin`, branch HEAD, `origin/develop`, and merge base all equal `b67929a0546d32d6ffafc7b801028c9c53fc2d6a`; Issue #10 remains open with `ready-for-agent`.
- Active gate: Git Lifecycle Proposal Gate. No commit, push, pull request, or merge has been performed.
- Next action: present the ticket-scoped Lore commit, committed-state verification, branch push, and review-ready PR proposal; merge remains excluded pending remote checks, review, and separate authorization.

### 2026-07-19 — Issue #10 Git publication authorized

- Authorization: the user approved one ticket-scoped Lore commit, committed-state verification, push to `origin/feat/issue-10-grounded-claims`, and a review-ready pull request targeting `develop` with `Closes #10`.
- Included scope: grounded proposition/traversal contracts, deterministic evaluator and metrics, bounded dataset and observations, Adapter source-text seam, create-only CLI/result-store/replay path, review-driven regressions, canonical design lock, interview defense, and workflow evidence.
- Required pre-push evidence: the committed worktree is clean; frozen sync, Ruff format and lint, mypy, all tests, diff checks, and installed grounded CLI create/replay pass with `dirty_worktree=false` and the new Evaluation Plane commit SHA.
- Active exclusion: merge remains a later Git lifecycle decision after required remote checks and review evidence.
- Next action: create the Lore commit, verify the clean committed state, then push and open the review-ready pull request only if every gate passes.

### 2026-07-19 — Issue #9 merged; Issue #10 implementation activated

- Upstream evidence: [PR #23](https://github.com/DHChe/braincrew-datateam-portfolio/pull/23) is `MERGED` into `develop` at `2026-07-19T08:09:08Z`; its merge commit is `b67929a0546d32d6ffafc7b801028c9c53fc2d6a`, and fetched `origin/develop` points to that exact commit.
- Ticket evidence: [Issue #9](https://github.com/DHChe/braincrew-datateam-portfolio/issues/9) is `CLOSED` at `2026-07-19T08:09:41Z`.
- Dependency evidence: blocker Issues [#6](https://github.com/DHChe/braincrew-datateam-portfolio/issues/6) and [#7](https://github.com/DHChe/braincrew-datateam-portfolio/issues/7) are both `CLOSED`; Issue [#10](https://github.com/DHChe/braincrew-datateam-portfolio/issues/10) now carries `ready-for-agent`.
- Branch evidence: dedicated worktree `/Users/astralpig/.config/superpowers/worktrees/braincrew/issue-10-grounded-claims` was created on `feat/issue-10-grounded-claims` from current `origin/develop` at `b67929a0546d32d6ffafc7b801028c9c53fc2d6a`.
- Active skill: `test-driven-development`.
- Expected artifact: versioned `claim-proposition-v1` and `claim-traversal-v1` contracts, deterministic grounded-claim metrics, fail-closed high-risk behavior, bounded golden cases, and fixture CLI/result-store/replay evidence.
- Completion condition: clean baseline passes before the first RED; then every new behavior is observed failing for the expected missing-contract reason before minimal implementation, followed by ticket-scoped code review and `verification-before-completion`.
- Clean baseline: `uv sync --frozen --all-groups`, Ruff format and lint, mypy, full pytest (`69 passed`), and `git diff --check` succeeded before the first RED.
- Scope exclusions: the complete 40-case grounded-answer set, Issue #11 Answer Mode and abstention scope, the full 100-case benchmark, LLM-as-judge scoring, AX product changes, and Agent trajectory evaluation.
- Next action: inspect the locked Issue #10 contracts and existing evaluator seams, then add and run the first failing claim-proposition contract test before production implementation.

### 2026-07-19 — Issue #9 Git publication authorized

- Authorization: the user approved the proposed single Lore commit, committed-state verification, push to `origin/feat/issue-9-retrieval-quality`, and review-ready pull request targeting `develop`; merge was not authorized.
- Included scope: the reviewed Issue #9 retrieval dataset, strict contracts, deterministic evaluator, CLI/result-store/replay path, tests, pinned-AX synthetic smoke evidence, locked design decision, interview defense, and delivery-workflow status.
- Required pre-push evidence: the committed worktree is clean; frozen sync, Ruff, mypy, full pytest, diff checks, and an installed-console-script retrieval run and replay pass with the new committed Evaluation Plane SHA and `dirty_worktree=false`.
- Pull-request strategy: use `Closes #9`, expose the 30-case fixture coverage and exact metrics, and state that the pinned live smoke returned zero candidates and therefore makes no positive live retrieval-quality claim.
- Active exclusion: merge remains a later Git lifecycle decision after required checks and review evidence.
- Next action: create the Lore commit, run committed-state verification, push the verified branch, and open the review-ready pull request.

### 2026-07-19 — Issue #9 final verification completed; lifecycle proposal gate reached

- Completed skill: `verification-before-completion`.
- Repository evidence: `uv sync --frozen --all-groups`, Ruff format and lint, mypy, full pytest (`69 passed`), and `git diff --check` all exited successfully from a fresh run.
- Fixture artifact evidence: installed `braincrew-eval run-retrieval` created and `braincrew-eval replay` recomputed `retrieval-run-artifact-v1` as `COMPLETED` with the same logical digest `sha256:9f00231e8adfbc87230e9391635b26d09de3cf438929138af96cdc81f875afcc`.
- Coverage and metric evidence: 30 scored cases, 21 Calibration, 9 Verification, Verification Recall@5 denominator 9, 28 authority cases, 30 forbidden-visibility cases, Recall@5 `14/15`, MRR@10 `14/15`, authority `1/1`, forbidden visibility `0/1`, and zero hard-failure case in the fixture.
- Provenance evidence: dataset `braincrew-retrieval-quality@1.0.0` with digest `sha256:5364cb7d7919304f5ebe78e4b7bd9bf2ed073c5e9f1e84c36f48697c2759fca8`, adapter `fixture-retrieval-sut-v1`, evaluator `retrieval-quality-v1`, and declared non-executed AX SUT `c318b2192006bdb36a5bd5b3a2bc403425b45701` were recorded exactly; the uncommitted Evaluation Plane provenance correctly records `origin/develop@c549c255c55e97639b6261d9414fb0abfa64026e` with `dirty_worktree=true`.
- GitHub and branch evidence: PR #22 remains merged at `c549c255c55e97639b6261d9414fb0abfa64026e`, Issue #8 remains closed, Issue #9 remains open with `ready-for-agent`, and branch `feat/issue-9-retrieval-quality`, `HEAD`, `origin/develop`, and their merge base all point to that merge commit.
- Review evidence: independent Spec and Standards reviews report `PASS` with zero remaining finding after all review-driven RED/GREEN repairs.
- Scope evidence: AX retrieval implementation, grounded-answer scoring, the full 100-case benchmark, and Agent trajectory evaluation were not added or claimed. The pinned live smoke returned zero candidates and therefore proves only the HTTP/Adapter/evaluator boundary, not positive live retrieval quality.
- Active gate: Git Lifecycle Proposal Gate; no commit, push, pull request, or merge has been performed for Issue #9.
- Next action: propose one Lore commit on `feat/issue-9-retrieval-quality`, committed-state verification, push to the matching origin branch, and a reviewed pull request targeting `develop`; wait for explicit authorization before executing.

### 2026-07-19 — Issue #9 code review completed; final verification started

- Review result: the independent Spec and Standards axes both report `PASS` with zero remaining finding against fixed point `c549c255c55e97639b6261d9414fb0abfa64026e`.
- Final review-driven RED evidence: an unavailable observation carrying a forbidden identity lost `R-FORBIDDEN-VISIBILITY` and the run-level `hard_failure_cases` entry; the new regression test failed against that behavior.
- Final repair evidence: `INVALID` remains the evidence state, while forbidden-source identity is scanned before invalid-return paths and preserves the zero-tolerance failure code and hard-failure entry; the focused evaluator suite reports `14 passed`, with Ruff and mypy clean.
- Active skill: `verification-before-completion`.
- Completion condition: frozen sync, Ruff format/lint, mypy, full pytest, `git diff --check`, installed fixture CLI execution, create-only artifact inspection, and artifact replay all succeed with fresh evidence.
- Next action: run the complete local gate set and installed 30-case retrieval CLI/replay path, then record the exact evidence and stop at the Git Lifecycle Proposal Gate.

### 2026-07-19 — Issue #9 code review requested fixes; TDD repairs completed

- Review findings: Standards reported one HIGH replay gap and two MEDIUM fail-closed contract gaps; Spec reported one HIGH Recall@5 deduplication-boundary error.
- RED evidence: four focused tests failed for retrieval replay, the fifth unique identity at original rank 6, zero-applicability aggregate handling, and impossible or display-mismatched exact metric values.
- Repair evidence: retrieval replay now recomputes stored case and aggregate evidence and rejects tampering; Recall@5 slices the deduplicated sequence; a zero aggregate denominator produces explicit `INVALID`; metric contracts validate both fraction bounds and display consistency.
- Focused GREEN evidence: legacy fixture replay plus Issue #9 unit and acceptance tests reported `28 passed`; Ruff format/lint, mypy, and `git diff --check` passed after the repairs.
- Active skill: ticket-scoped `code-review` re-review on the unchanged fixed point `c549c255c55e97639b6261d9414fb0abfa64026e`.
- Completion condition: both Standards and Spec axes clear the repaired worktree with zero unresolved finding before final verification begins.
- Next action: repeat both independent read-only review axes across all tracked and untracked changes.

### 2026-07-19 — Issue #9 re-review aligned hard failures with canonical run states

- Re-review result: Spec passed with zero finding; Standards cleared the four prior repairs and reported one new HIGH state-semantics conflict.
- Conflict: the retrieval evaluator used `FAILED` for a fully scored forbidden-source result, while the locked global contract reserves `FAILED` for runtime or infrastructure execution failure.
- RED evidence: the unit and CLI acceptance tests were changed to require `COMPLETED` plus preserved hard-failure evidence, and both failed against the old state assignment.
- Repair: a fully scored retrieval run now remains `COMPLETED`; `R-FORBIDDEN-VISIBILITY` and `hard_failure_cases` remain zero-tolerance evidence that a later release gate must reject.
- Active skill: ticket-scoped Standards re-review.
- Completion condition: Standards clears the state repair with zero unresolved finding, then final verification begins.
- Next action: rerun the focused tests and the Standards review axis before changing workflow phase.

### 2026-07-19 — Issue #9 implementation completed; code review started

- Completed skill: `test-driven-development`.
- Fixture evidence: all 30 cases executed through the installed CLI and create-only result store; the artifact reported `COMPLETED`, a 21/9 split, Verification Recall@5 denominator 9, Recall@5 `14/15`, MRR@10 `14/15`, authority `1/1`, and forbidden visibility `0/1` with exact dataset, evaluator, adapter, and SUT identities.
- Live boundary evidence: the pinned AX service at `c318b2192006bdb36a5bd5b3a2bc403425b45701` completed the synthetic retrieval request through `ax-sut-http-v1`; it returned zero candidates, so the smoke proves transport and provenance only and explicitly does not claim positive retrieval quality.
- Implementation evidence: Ruff lint, mypy, full pytest (`63 passed`), and `git diff --check` passed before review.
- Active skill: ticket-scoped `code-review` with independent Standards and Spec axes against `origin/develop@c549c255c55e97639b6261d9414fb0abfa64026e`.
- Completion condition: every blocking finding is reproduced with a failing regression test, repaired, and cleared by re-review before final verification starts.
- Next action: inspect all tracked and untracked Issue #9 changes without committing, pushing, opening a pull request, or merging.

### 2026-07-19 — PR #22 and Issue #8 completed; Issue #9 implementation started

- Merge evidence: PR #22 reports `MERGED` into `develop` with merge commit `c549c255c55e97639b6261d9414fb0abfa64026e`, and Issue #8 reports `CLOSED`.
- Frontier evidence: Issue #9 is open, its blockers Issues #6 and #7 are closed, and `ready-for-agent` is applied.
- Active skill: `test-driven-development` in the dedicated `feat/issue-9-retrieval-quality` worktree based exactly on fetched `origin/develop@c549c255c55e97639b6261d9414fb0abfa64026e`.
- Expected artifact: 30 versioned retrieval cases with a frozen 21/9 split, deterministic Recall@5 and MRR@10, authority and applicability evaluation, zero-tolerance forbidden visibility, explicit unresolved-identity policy, fixture CLI/result-store evidence, and a synthetic live retrieval smoke against the pinned AX service.
- Clean baseline: frozen dependency sync, Ruff format and lint, mypy, full pytest (`43 passed`), and `git diff --check` succeeded before the first RED.
- Scope exclusions: AX retrieval implementation changes, grounded-answer scoring, the complete 100-case benchmark, and Agent trajectory evaluation.
- Next action: add and run the first failing retrieval dataset-contract test before production implementation.

### 2026-07-19 — Issue #8 lifecycle proposal approved

- Authorization: the user approved one Lore commit, clean committed-state verification, push to `origin/feat/issue-8-parsing-quality`, and pull-request creation against `develop`; merge was not authorized.
- Included scope: the reviewed Issue #8 dataset, contracts, deterministic parsing evaluator, fixture CLI/result store, tests, design decision, interview defense card, and workflow evidence.
- Required pre-push evidence: the committed worktree is clean; Ruff, mypy, full pytest, diff checks, and an installed-console-script parsing run pass with the committed Evaluation Plane provenance.
- Pull-request strategy: use `Closes #8`, require the Python quality check and no unresolved review blocker, and keep squash merge as a separately proposed action.
- Known risk: live AX parsing remains unobservable, so fixture completion cannot be presented as live AX parsing quality or a release `PASS`.
- Next action: create the Lore commit and run the committed-state verification before any push.

### 2026-07-19 — Issue #8 final verification completed; lifecycle proposal gate reached

- Completed skill: `verification-before-completion`.
- Quality evidence: `uv sync --frozen --all-groups`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, `uv run pytest -q`, and `git diff --check` all exited successfully; pytest reported `43 passed`.
- CLI evidence: installed `braincrew-eval run-parsing` executed `datasets/parsing/parsing_cases_v1.json` with `tests/fixtures/parsing_observations_v1.json` and stored `parsing-run-artifact-v1` outside the repository.
- Artifact evidence: run state `COMPLETED`; 20 total and scored cases; 14 Calibration and 6 Verification cases; Verification EvidenceSpan denominator 6; five applicable table and five list cases; dataset digest `sha256:a4ce3d2381853288e92cc2fd21df5cfcd9629db39ea134d8314594e146b48127`; logical digest `sha256:3e612b659ad662ce666c74e9b9bff523b43729efbdd3bb1266302ab402a906fc`.
- Provenance evidence: dataset `braincrew-parsing-quality@1.0.0`, adapter `fixture-parsing-sut-v1`, parser `fixture-parser-v1`, evaluator `parsing-quality-v1`, and declared non-executed AX SUT commit `c318b2192006bdb36a5bd5b3a2bc403425b45701` were recorded exactly.
- Review evidence: post-refactor Standards and Spec axes both returned `PASS` with zero remaining finding.
- Scope evidence: no AX parsing implementation, retrieval/answer scoring, full benchmark, or Agent trajectory evaluation was added or claimed; live AX parse observability remains explicitly unavailable and therefore invalid for a live parsing benchmark.
- Active gate: Git Lifecycle Proposal Gate; no commit, push, pull request, or merge has been performed.
- Next action: propose one Lore commit on `feat/issue-8-parsing-quality`, push to `origin`, and open a reviewed PR targeting `develop`; wait for explicit authorization before executing.

### 2026-07-19 — Issue #8 code review completed; final verification started

- Completed skill: `code-review`.
- Review evidence: the Spec axis passed with no missing, partial, incorrect, or out-of-scope behavior; the Standards axis initially reported two LOW duplicated-code smells, then passed with zero remaining finding after common CLI validation/provenance and create-only writer helpers were extracted and re-reviewed.
- Refactor evidence: fixture and parsing acceptance tests reported `13 passed`; Ruff and mypy passed before re-review.
- Active skill: `verification-before-completion`.
- Completion condition: fresh `uv sync --frozen --all-groups`, Ruff format/lint, mypy, full pytest, `git diff --check`, and the versioned 20-case fixture CLI execution all exit successfully and the stored artifact reports `COMPLETED`, 20 scored cases, Verification denominator 6, and exact provenance.
- Next action: execute the full required gate set, inspect Git status and artifact evidence, then stop at the Git Lifecycle Proposal Gate.

### 2026-07-19 — Issue #8 implementation completed; code review started

- Completed skill: `test-driven-development`.
- Completion evidence: dataset, EvidenceSpan integrity, strict schema, exact metric golden, 20-case macro aggregation, parser-version/case-set integrity, fixture CLI artifact, append-only collision, and unobservable-parse `INVALID` tests all passed; full pytest reported `43 passed` before review.
- Active skill: `code-review` with separate Standards and Spec axes.
- Expected artifact: findings with severity and exact file references against the complete uncommitted Issue #8 worktree diff.
- Completion condition: every blocking finding is repaired through a new RED/GREEN cycle and both axes pass on re-review.
- Next action: pin `origin/develop@0d137a64b86158e33a14d435caaabf5d42ea20c1`, enumerate tracked and untracked worktree changes, and run the two review axes without committing.

### 2026-07-19 — Issue #8 implementation started

- Active skill: `test-driven-development`.
- Expected artifact: a versioned 20-case parsing dataset with a frozen 14 Calibration / 6 Verification split, fixture parsing observations, deterministic EvidenceSpan/structure/metadata/table/list metrics, hand-calculated goldens, and an append-only CLI result artifact.
- Completion condition: each new behavior is observed failing before implementation, all 20 cases execute through the CLI and result store, unavailable parsing produces `INVALID` rather than `PASS`, exact dataset/evaluator/adapter/SUT identities are recorded, and Ruff, mypy, full pytest, and diff checks pass.
- Entry evidence: `origin/develop`, branch HEAD, and merge base all equal `0d137a64b86158e33a14d435caaabf5d42ea20c1`; Issues #6 and #7 are closed through merged PRs #20 and #21 with successful required checks; Issue #8 has `ready-for-agent`.
- Clean baseline: `uv sync --frozen --all-groups`, Ruff format and lint, mypy, full pytest (`25 passed`), and `git diff --check` succeeded before the first RED.
- Scope exclusions: AX parsing implementation changes, retrieval or answer scoring, the complete 100-case/live benchmark, and Agent trajectory evaluation.
- Next action: add and run the first failing parsing dataset-contract and hand-calculated metric tests before production implementation.

### 2026-07-19 — Issue #6 implementation started

- Active skill: `test-driven-development`.
- Expected artifact: one versioned fixture case that runs from the Typer CLI through a fixture SUT adapter and deterministic evaluator into an append-only JSON result with a gate decision, plus deterministic artifact replay.
- Completion condition: the acceptance test is observed failing before implementation, then passes with Ruff, mypy, full pytest, and repeated-run logical digest equality evidence.
- Entry evidence: `feat/issue-6-cli-immutable-gate` and fetched `origin/develop` both point to `ffb56a86ca6a83b4c081cfd5571e4bc4aaf2d06d`; Issue #6 is open, labeled `ready-for-agent`, and has no blocker.
- Scope exclusions: live AX HTTP, the full metric suite, the 100-case dataset, dashboard work, and Agent trajectory evaluation.
- Next action: write and run the failing Issue #6 CLI acceptance test before production implementation.

### 2026-07-19 — Issue #6 implementation completed; code review started

- Completed skill: `test-driven-development`.
- Completion evidence: `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, `uv run pytest -q`, and `git diff --check` passed; two console-script fixture runs and artifact replay produced the same logical digest `sha256:d11ba8fc170c5b2be94688d73b4db707aeeefe00bcdea0a73854a0555b83759e` and `PASS` decision.
- Active skill: `code-review`.
- Expected artifact: ticket-scoped review findings with severity and exact file references.
- Completion condition: all blocking findings are fixed through TDD and fresh verification passes.
- Next action: review the full Issue #6 diff before proposing commit, push, pull request, or merge actions.

### 2026-07-19 — Issue #6 code review requested fixes

- Standards axis: four findings; worst findings were the advanced `origin/develop` base and non-UTF-8 fixture traceback instead of an explicit invalid-input failure.
- Spec axis: four findings; worst finding was accepting a caller-supplied Evaluation Plane SHA as executed provenance without recording dirty state.
- Shared findings: dataset digest incorrectly covered fixture response and prompt/model configuration; replay did not require the complete `run-artifact-v1` envelope; runner, evaluator, adapter, and store responsibilities were mixed.
- Scope review: no live AX, full metric suite, 100-case dataset, dashboard, or Agent trajectory scope creep found.
- Active skill: `test-driven-development` for review-driven repairs.
- Completion condition: each behavior defect is observed RED before its fix, module boundaries are repaired without behavior change, the branch is moved onto current `origin/develop`, and fresh review plus verification passes.

### 2026-07-19 — Issue #6 code review and verification completed

- Completed skills: `test-driven-development`, `code-review`, and `verification-before-completion`.
- Review evidence: the independent standards and specification review axes both returned `PASS` with zero blockers after confirming the provenance, invalid-input, full artifact-envelope, dataset-digest, module-boundary, and latest-`develop` repairs.
- Branch evidence: `feat/issue-6-cli-immutable-gate`, fetched `origin/develop`, and their merge base all point to `2c3540ed37afeb865bde1466ef992af278799700`; the ancestor check returned zero.
- Verification evidence: `uv lock --check`, `uv sync --frozen --all-groups`, `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, `uv run pytest -q`, and `git diff --check` passed; pytest reported ten passing acceptance tests.
- Replay evidence: two console-script fixture runs and artifact replay returned `PASS` with the same logical digest `sha256:ed3a600bf7bcf75d8c5664a71fec6efbaeac78e8e59d9cdacdd04870ff140155`.
- Scope evidence: no live AX HTTP connection, full metric suite, 100-case dataset, dashboard, or Agent trajectory evaluation was added or claimed.
- Active gate: Git Lifecycle Proposal Gate; no commit, push, pull request, or merge has been performed.
- Next action: present the verified ticket-scoped lifecycle proposal and wait for explicit authorization before executing its first write action.

### 2026-07-19 — Issue #6 lifecycle proposal approved; PR opened

- Authorization: the user approved the proposed commit, push, and pull-request sequence; merge remains a separate evidence-gated action.
- Commit evidence: Lore commit `b63b2f926e17c549afbfc9037eb3e8e2f92a5df4` contains the reviewed Issue #6 implementation and documentation.
- Remote evidence: `origin/feat/issue-6-cli-immutable-gate` was created and [PR #20](https://github.com/DHChe/braincrew-datateam-portfolio/pull/20) targets `develop` with `Closes #6`.
- Pre-push verification: the committed branch remained based on `origin/develop` at `2c3540ed37afeb865bde1466ef992af278799700`; Ruff, mypy, ten pytest cases, and diff checks passed.
- Replay evidence: two clean committed-state CLI runs and replay returned `PASS` with logical digest `sha256:b033d931313f3ae2462ed0068712f900b7cf9f8b8dd1433c961fdc10c6e063dc`.
- Active gate: wait for the latest PR checks and review evidence, then request explicit merge authorization.

### 2026-07-19 — Issue #6 merged; Issue #7 implementation started

- Merge evidence: PR #20 reports `MERGED` with successful `Python quality gates`; fetched `origin/develop` points to merge commit `230f90fb53df950173896bd6824792e3a70945ae`, and Issue #6 is closed.
- Frontier evidence: Issue #7 has only Issue #6 as a native blocker; #6 is closed. Issue #7 now carries `ready-for-agent`, while the label was removed from completed Issue #6.
- Active skill: `test-driven-development`.
- Expected artifact: a versioned `ax-sut-http-v1` Adapter contract and capability manifest that preserve the pinned AX identity, operation availability, every HTTP attempt, response provenance, timing, and permanent or retryable failure classification without importing AX internals.
- Completion condition: controlled HTTP tests cover success, timeout, `429`, `5xx`, schema mismatch, and permanent failure; preflight makes missing parsing observations explicit; any available live smoke uses synthetic or publicly releasable input; all repository quality gates and ticket-scoped review pass.
- Branch evidence: local `develop`, `origin/develop`, and `feat/issue-7-ax-http-contract` started at `230f90fb53df950173896bd6824792e3a70945ae`; `uv sync --frozen --all-groups`, Ruff format and lint, mypy, the full ten-test suite, and the Issue #6 acceptance gate passed before Issue #7 edits.
- Scope exclusions: AX product implementation, the full parsing/retrieval/answer metric suites, the 100-case dataset, dashboard work, and Agent trajectory evaluation.
- Next action: add and run the first failing controlled HTTP contract test before implementing the live Adapter.

### 2026-07-19 — Issue #7 implementation completed; code review started

- Completed skill: `test-driven-development`.
- Controlled evidence: fifteen Issue #7 contract tests cover capability preflight, frozen field mappings and schema digests, create-only manifest persistence, retrieve, answer, source text, explicit parse unavailability, timeout, `429`, `5xx`, permanent `401`, response schema mismatch, invalid tenant configuration, and bearer-credential exclusion.
- Live evidence: the pinned AX stack reported ready; preflight confirmed four supported operations and explicit parse/corpus-identity gaps. A synthetic retrieval returned zero candidates, and answer generation failed closed as `insufficient_evidence` with zero citations and no generated natural-language answer.
- Verification evidence: `uv lock --check`, frozen sync, Ruff formatting and lint, mypy, all 23 tests, the ten-case Issue #6 acceptance gate, wheel build, packaged `ax-http-v1.yaml`, and `git diff --check` passed after implementation repairs.
- Active skill: `code-review`.
- Expected artifact: separate repository-standards and Issue #7 specification findings with exact file references and no unresolved blocker.
- Completion condition: blocking findings are repaired through TDD and the full verification sequence passes again.
- Next action: review the full worktree diff from `origin/develop@230f90fb53df950173896bd6824792e3a70945ae`.

### 2026-07-19 — Issue #7 code review requested fixes; verification started

- Review findings: repository-standards review found that `bearer_token` could enter a serialized configuration; specification review found that failure/preflight evidence lacked the canonical request identity and that `ax-http-v1.yaml` lacked exact field mappings plus literal response-schema digests.
- Repair evidence: each behavior was first captured by a failing test. `bearer_token` is now excluded from representation and serialization; all HTTP requests send evaluation run, case, and correlation headers; success, failure, and preflight evidence preserve the same canonical request; the packaged contract locks field mappings and validates literal digests against the complete Pydantic response schemas.
- Review result: separate repository-standards and Issue #7 specification passes report zero unresolved blocker. No AX internal import, copied implementation, expanded benchmark scope, or quality claim was found.
- Active skill: `verification-before-completion`.
- Completion condition: the full repository gates, wheel-content check, latest pinned live synthetic smoke, and diff hygiene all pass after the review-driven repairs.

### 2026-07-19 — Issue #7 code review and verification completed

- Completed skills: `test-driven-development`, `code-review`, and `verification-before-completion`.
- Review evidence: repository-standards and Issue #7 specification reviews both returned `PASS` with zero unresolved blocker after the credential, canonical-request, field-mapping, and schema-digest repairs.
- Fresh repository evidence: frozen sync, Ruff format and lint, mypy, all 25 tests, the ten-case Issue #6 acceptance gate, wheel build, packaged Adapter code and `ax-http-v1.yaml`, and `git diff --check` passed.
- Fresh live evidence: the post-review run `issue-7-live-review` against AX commit `c318b2192006bdb36a5bd5b3a2bc403425b45701` reported ready; preserved preflight, retrieval, and answer case identities; confirmed four available operations plus the explicit parse and corpus-identity gaps; and repeated the zero-candidate, `insufficient_evidence`, zero-citation, no-generated-answer result without making a quality claim.
- Environment cleanup: the temporary alternate-port AX Compose containers and network were removed after the smoke; named data volumes were preserved.
- Active gate: Git Lifecycle Proposal Gate. No commit, push, pull request, or merge has been performed for Issue #7.

### 2026-07-19 — Issue #7 Git publication authorized

- Authorization: the user approved the proposed single Lore commit, push to `origin/feat/issue-7-ax-http-contract`, and draft pull request to `develop`; merge remains explicitly excluded.
- Included scope: the reviewed AX HTTP Adapter, packaged contract and dependency lock, controlled tests, live-smoke evidence, locked design decision, interview defense, and delivery-workflow state.
- Publication completion condition: the remote branch and draft pull request point to the verified Lore commit, after which required checks and review evidence become the active gate.

### 2026-07-19 — Issue #7 draft pull request passed its first remote gate

- Publication evidence: Lore commit `3aa72646c134c13ad261542fd25f9a3c79879cd3` is the head of `origin/feat/issue-7-ax-http-contract`, and draft PR #21 targets `develop` at `230f90fb53df950173896bd6824792e3a70945ae`.
- Remote evidence: `Python quality gates` completed successfully; GitHub reported `CLEAN`, with zero PR review, issue comment, inline comment, or requested change.
- Authorization: the user instructed the next step after publication, authorizing the ready-for-review transition but not merge.
- Active gate: publish this status update, require the new head's Python gate to pass, then mark PR #21 ready for review and stop before merge.

### 2026-07-19 — Issue #7 squash merge authorized

- Ready evidence: PR #21 is not a draft, its latest Python quality gate passed, GitHub reports `CLEAN`, and no review comment, requested change, or unresolved blocker exists.
- Authorization: the user approved the proposed squash merge into `develop` and removal of the remote `feat/issue-7-ax-http-contract` branch.
- Exclusion: local worktree cleanup and any Issue #8 implementation remain outside this merge transaction.
- Completion condition: verify the merged PR state, returned squash commit ancestry in fetched `origin/develop`, automatic Issue #7 closure, and remote branch deletion before reporting completion.
  - Forward reference added 2026-07-26, text above deliberately unchanged: the "automatic closure" expectation is **wrong in this repository** and was never satisfied — closing keywords fire only on merges into the default branch, which is `main`, not `develop`. Issue #7 was in fact closed by a person. See the 2026-07-26 entry "Issue #67 merged and closed; the 'automatic closure' expectation is corrected" at the top of this history. This bullet is preserved as the record of what was planned at the time; only this pointer is new.

## Transition record format

For each transition, record:

- date and phase;
- active skill or workflow;
- expected artifact and completion condition;
- completion evidence or blocker;
- exact next skill or action and its entry condition.

Do not mark a phase complete merely because a document exists. Record the review, test, benchmark, or merge evidence required by that phase.
