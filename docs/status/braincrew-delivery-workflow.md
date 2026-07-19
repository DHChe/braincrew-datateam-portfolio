# Braincrew Portfolio Delivery Workflow Status

Last updated: 2026-07-19

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

- Completed phase: research, role comparison, and Data Team red-team assessment.
- Completed phase: portfolio direction and evaluation boundaries locked.
- Completed phase: `brainstorming` design loop, independent specification review, and PR #1 merge into `develop`.
- Completed phase: `setup-matt-pocock-skills`; GitHub Issues was selected, the five canonical triage labels were configured, and the single-context domain-document rules were recorded.
- Completed phase: `to-spec`; the user approved the CLI-to-gate, AX Adapter, and dashboard-export test seams, and implementation specification Issue #4 was published with the `ready-for-agent` label.
- Completed phase: `to-tickets`; the user approved 12 vertical implementation slices, GitHub Issues #6 through #17 were published as sub-issues of #4, and 22 native dependency edges were recorded.
- Completed phase: Issue #6 implementation with `test-driven-development`; ten acceptance cases cover CLI execution, deterministic rerun and replay, append-only collision handling, invalid and tampered input, complete artifact-envelope validation, dataset-digest boundaries, path traversal, and commit identity validation.
- Completed phase: Issue #6 ticket-scoped code review; both the standards and specification axes passed with zero unresolved blockers after review-driven TDD repairs.
- Active canonical phase: Git Lifecycle Proposal Gate.
- Active artifact: a commit, push, pull-request, and merge proposal for the verified Issue #6 diff; no Git write or remote lifecycle action has been performed.
- Active completion condition: the user explicitly authorizes the proposed lifecycle action before the corresponding commit, push, pull request, or merge occurs.
- Next canonical phase: after authorization, create the local Lore commit, refresh and reverify the remote base, push the ticket branch, open a reviewed pull request to `develop`, and merge only after required checks and approval pass.
- Entry condition: Issue #6 is the only unblocked implementation ticket and carries `ready-for-agent`; Issues #7 through #17 remain blocked by their recorded dependency edges.
- Entry condition status: satisfied on 2026-07-19; implementation must start from the latest verified `develop` on a ticket-bounded feature branch.
- Following phase: after Issue #6 is reviewed and merged into `develop`, remove its frontier role and activate the next dependency-unblocked ticket in a fresh context.
- Blocker: none.

## Transition history

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

## Transition record format

For each transition, record:

- date and phase;
- active skill or workflow;
- expected artifact and completion condition;
- completion evidence or blocker;
- exact next skill or action and its entry condition.

Do not mark a phase complete merely because a document exists. Record the review, test, benchmark, or merge evidence required by that phase.
