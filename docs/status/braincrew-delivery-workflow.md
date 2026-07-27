# Braincrew Portfolio Delivery Workflow Status

Last updated: 2026-07-25

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

- Active phase: **none. [Issue #71](https://github.com/DHChe/braincrew-datateam-portfolio/issues/71)
  is the next implementable ticket** — re-pin `PINNED_AX_SHA` to the reviewed AX commit. It is
  labelled `ready-for-agent`, needs no runtime, and is the only fully unblocked item on the critical
  path.
- **What the last two merges changed, and what they deliberately did not.** `origin/develop` is
  `354d5b3`.
  - `dfc41ff` (#69, Issue #67) — the live preflight now derives the evaluation principal and the
    six-case attachment mapping from the AX handoff receipt, pinning **one** digest that is
    recomputed and refused on mismatch at run time, instead of seven literals that were wrong by
    construction and never checked.
  - `354d5b3` (#70) — `2bcaee3495fd7b3f624398819575cd86a5a15c47` is **reviewed and accepted as the
    SUT commit for evaluation**, which is a different assertion from the provisioning review it
    already had. The re-pin itself is **not** implemented, so `PINNED_AX_SHA` is still the
    superseded ancestor `72805930…` and **no artifact captured against today's substrate can be
    constructed yet.**
- **`braincrew_preflight_ready` remains `false`, and Issue #71 will not change that.** The re-pin
  makes artifacts *constructible*, not *captured*. Live HTTP parse capture still requires a
  separately authorized AX runtime start, stopped since Stage 12.
- **Blocked, and blocked on a human decision:** the dataset-identity work. Braincrew
  [Issue #38](https://github.com/DHChe/braincrew-datateam-portfolio/issues/38)'s acceptance criteria
  contradict themselves — one clause requires nested parsing component `2.0.0` *and* the six reviewed
  historical Verification cases, and no repository state satisfies both, because the six live under
  integrated v2 whose parsing component is `1.0.0`. Recorded as a comment on that issue; its body is
  unchanged. Three questions must be settled before that work starts: which case set the evaluation
  runs against, which integrated manifest version that implies, and how integrated and nested
  versions are represented so they cannot be conflated again.
  - **The human decision is not the only blocker.** Issue #38 formally lists
    [AX #37](https://github.com/DHChe/AX_portfolio/issues/37) — the operator-controlled snapshot
    gate — among its blocking issues, and it is still **`OPEN`**, as is the linked
    [AX #43](https://github.com/DHChe/AX_portfolio/issues/43). That issue topology has to be
    reconciled alongside the decision, not after it. The SUT-commit decision's §10 already directed
    this and it has now been omitted from the record twice; it is written here so a third omission
    is harder.
- Deferred and tracked, not forgotten: the duplicated literal `"2.0.0"` at `live_preflight.py:951`
  belongs to the dataset-identity work rather than to Issue #71, and the blast-radius figures in the
  SUT decision's §6 and §14 were measured at `dfc41ff` and need re-measuring when Issue #71 starts.
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
