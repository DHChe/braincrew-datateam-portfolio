# Braincrew Data Team Portfolio Agent Guide

## Operational Commands

Install the locked Python 3.12 environment with:

```bash
uv sync --frozen --all-groups
```

Run the Python quality gates with:

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest -q
```

Run the Issue #6 tracer-bullet benchmark and deterministic replay check with:

```bash
uv run pytest tests/acceptance/test_cli_fixture_gate.py -q
```

Before committing any change, also run:

```bash
git diff --check
git status --short
```

The complete 100-case and live AX benchmarks are not introduced by Issue #6 and must not be claimed by these commands.

## Golden Rules

- Treat AX_portfolio as an evolving Subject Under Test (SUT); do not present it as a finished or fully evaluated product.
- Evaluate and claim only capabilities that were actually executed and reproducibly verified.
- Do not add or claim Agent evaluation merely to match job-posting terminology.
- Evaluator and experiment contracts may reserve extension points for future Agent trajectory evaluation, but those extension points must be labeled `planned` or `not evaluated` until implemented and verified.
- Every published experiment must record the exact SUT commit SHA and dataset, evaluator, prompt, and model versions.
- Do not commit private customer, employee, or company documents. Use synthetic or publicly releasable evidence only.
- Keep AX product development and the Braincrew Evaluation Plane in separate repositories with separate histories. Connect them through the documented SUT Adapter contract; do not copy or import unmerged AX product internals into evaluation work.
- Do not commit `.omx/`, credentials, local environment files, generated caches, or unreviewed benchmark outputs containing sensitive data.
- Whenever a design decision becomes locked, update both its canonical design or decision document and the interview defense dossier. Record the rationale, rejected alternative, trade-offs, failure modes, validation evidence, and likely follow-up questions; do not leave interview preparation to retrospective reconstruction.

## User Communication Contract

These rules apply only inside this repository. They govern the final answer regardless of which skill, workflow, or subagent produced the underlying work.

- Respond in clear Korean when the user writes in Korean.
- Lead with the result and current state, then explain the reason and next action.
- On first use, write specialized terms as `Korean explanation (English term, plain meaning)`. Expand abbreviations such as SUT or PR immediately.
- Do not paste raw specialist or subagent language without translating it to this level. The lead agent owns the final plain-language explanation.
- For every material technical defect, explain: what is wrong, why it matters, one concrete example, what is currently blocked or affected, the available choices, and the recommended choice.
- Distinguish clearly between a code failure, a design flaw, an unverified assumption, and a workflow gate. Do not call all of them “bugs.”
- Preserve exact file names, commands, schema fields, and code identifiers when needed, but explain their role in ordinary language beside them.
- Prefer short sections, concrete examples, and simple sentences over dense jargon. Do not hide uncertainty or weaken technical accuracy merely to simplify wording.

## Skill Workflow Navigation Contract

The canonical delivery route is the locked Ask Matt flow documented in `docs/decisions/2026-07-18-evaluation-scope-and-skill-flow-lock.md`: setup or verify the Matt Pocock skills, run `to-spec`, run `to-tickets`, then execute each ready ticket in fresh context with TDD and code review before the full benchmark and submission verification.

- Before taking task actions with a skill or workflow, tell the user the active skill or workflow, why it applies now, the artifact it should produce, and the condition that will make the step complete.
- If the active skill or workflow changes, announce the transition before acting. Never silently replace the locked Ask Matt route with a parallel planning workflow such as `to-prd`, `writing-plans`, or `ralplan`.
- Use a parallel or supporting skill only when it fills a concrete gap inside the current canonical step. Explain its limited role and return explicitly to the locked route afterward.
- When one skill or workflow step finishes, report its completion evidence and name the exact next skill or action, why it follows, and what must be true before it starts.
- Update `docs/status/braincrew-delivery-workflow.md` whenever the canonical delivery phase starts, completes, becomes blocked, or changes. Keep completed phases and their evidence visible so both the user and future agents can recover the route without relying on conversation memory.
- Treat this project as a guided Matt Pocock skill-learning environment as well as a delivery project. At the moment a Matt Pocock skill becomes appropriate, proactively explain when that skill is generally useful, why it fits the current situation, what the user must decide, what the agent will execute, and which durable artifact it will leave behind.
- Teach skills in context rather than as a detached tutorial. Do not invoke extra skills merely for practice; propose them only when they advance the portfolio or remove a concrete uncertainty, and explicitly distinguish required canonical steps from optional supporting skills.
- After completing a Matt Pocock skill for the first time, give the user a short reusable mental model for recognizing the same situation in future work.
- At every implementation or review handoff, state explicitly whether the next step should continue in the current session or start in a fresh session, and explain why that context choice reduces risk or improves focus.
- When a fresh session is recommended, provide one copy-ready prompt that includes the exact skill invocation, issue or artifact link, repository and branch, required source documents, in-scope work, explicit exclusions, verification commands, documentation duties, and the Git lifecycle stop condition.
- After the copy-ready prompt, explain the purpose of its major instructions in plain Korean so the user learns how to construct a similar request instead of treating the prompt as unexplained boilerplate.
- Distinguish what the user must do manually, such as opening a fresh session or approving a Git action, from the safe work the next agent should execute automatically.
- Do not require the user to paste the full conversation into a fresh session when durable repository documents and GitHub Issues contain the necessary decisions. Name the minimum sources the next agent must inspect instead.
- End every handoff with the next step's completion condition and the skill or review stage that follows it, so the user can recognize when to advance the workflow.
- A Git lifecycle action is not a workflow phase transition. Continue to follow the separate Git Lifecycle Proposal Gate for commits, pushes, pull requests, and merges.

## Multi-Agent Orchestration Topology

This project runs as a persistent three-pane cmux team, not as a single agent. The topology is a standing configuration and survives session boundaries; it is not re-decided per task.

- pane 1 is the orchestrator: requirement analysis, work decomposition, conflict prevention, and final integration judgment. It owns the user-facing answer.
- pane 2 implements. pane 3 reviews and performs QA, and is read-only unless a contract explicitly requires it to write one named artifact.
- The cycle is: orchestrator brief, implementation, independent review, integration judgment, next cycle design. Record which files changed in each cycle.

Rules that apply to every cycle:

- Never let two panes edit the same file. Separate the scopes in the brief, before dispatch.
- Write each brief to be self-sufficient. Name the authoritative source documents and state that the brief is direction, not authority, because a worker may have lost prior context.
- Do not accept a worker's report as evidence. Independently reproduce its load-bearing claims before acting on them.
- Pair every dispatch with a harness-tracked completion watcher. A human must never have to notice that a pane finished and re-prompt the orchestrator.
- Do not silently resolve a contested judgment the orchestrator has an interest in. When the question is whether a check is wrong rather than the thing it checks, route it to independent adjudication first.
- Never run two full test suites concurrently in one shared working tree, and verify `git status` after any concurrent or interrupted run before trusting the tree or reporting a gate result. Some tests in this repository write to tracked files: `tests/contract/test_corpus_pack_sealing.py` drifts the tracked `schemas/` directory and restores captured bytes in a `finally`, so a second run that captures its "original" inside the first run's drift window writes the drifted bytes back as pristine. Both runs complete normally and the tree is left durably corrupted with a self-consistent `(schema, digest)` pair — one that every recompute-and-compare check accepts, leaving the pinned `EXPECTED_SCHEMA_DIGESTS` constant and `git status` as the only detectors. Measured 2026-07-30; tracked as [#97](https://github.com/DHChe/braincrew-datateam-portfolio/issues/97).
- Confirm `git status --short` names only the intended paths immediately before committing, and stage explicitly named paths — never `git add -A` and never `git commit -a`. In a repository whose value is evidentiary integrity, a silent tracked-file corruption committed beside real work is worse than any defect review is likely to find.

Every handoff prompt written under the Skill Workflow Navigation Contract must address the incoming orchestrator and instruct it to adopt the existing panes rather than work alone. A handoff that omits the topology silently discards this configuration, and that omission has already happened once.

## Git Lifecycle Proposal Gate

For this repository, agents must actively propose the next Git lifecycle action whenever it is warranted; they must not silently leave completed work uncommitted or remotely unintegrated.

Before a new `commit`, `push`, pull request, or merge that has not already been explicitly authorized in the current request, present a concise proposal containing:

- intended action and why it is now appropriate;
- target branch and remote;
- changes or commits included;
- verification evidence available or still required;
- pull-request and merge strategy, including known risks.

Wait for explicit user authorization before performing an unapproved `push`, opening or modifying a pull request, or merging remote changes. Local read-only Git inspection is always allowed. A commit explicitly authorized by the user may proceed after verification without asking again.

Use Lore-style commit messages:

```text
<intent line: why the change was made>

Constraint: <external constraint>
Rejected: <alternative> | <reason>
Confidence: <low|medium|high>
Scope-risk: <narrow|moderate|broad>
Directive: <warning for future modifiers>
Tested: <verification performed>
Not-tested: <known gaps>
```

Never merge with failing required checks, unresolved review blockers, or unverifiable benchmark claims.

## Branching Strategy

- `main` is the stable, recruiter-facing release branch.
- `develop` is the integration branch and the source for design and feature branches.
- Start design work on `docs/evaluation-plane-design` from a verified `develop`.
- Start each implementation branch from the latest verified `develop`; keep it bounded to one ticket or cohesive capability.
- Merge feature branches into `develop` through reviewed pull requests, then release through a `develop` to `main` pull request after the full benchmark passes.
- Do not create speculative feature branches before their dependencies and ticket contracts are ready.
- Never commit product work directly to `main` or `develop` after bootstrap.

## Project Context

This repository contains the application portfolio for Braincrew's Data Team: an Evidence-First HR/Labor RAG Evaluation Plane built around AX_portfolio as the SUT. The first production release focuses on parsing, retrieval, grounded-answer, operational, experiment-comparison, and release-gate evaluation.

The ten-day delivery structure is asymmetric: the Evaluation Plane is the primary track, while AX product work is limited to completing already-started work or making narrowly scoped changes that unblock evaluation.

The locked first-release stack is Python 3.12 with `uv`, Pydantic v2, Typer, `httpx`, DuckDB, Parquet and JSON artifacts, pytest, Ruff, and mypy; the recruiter-facing dashboard is a statically exported Next.js TypeScript application. PostgreSQL and pgvector remain in AX_portfolio and are not duplicated here.

## Standards & References

- [Locked evaluation scope and workflow](./docs/decisions/2026-07-18-evaluation-scope-and-skill-flow-lock.md)
- [Braincrew Data role and hackathon benchmark](./docs/research/braincrew-data-role-and-hackathon-benchmark.md)
- [Data Team growth red-team assessment](./docs/research/braincrew-data-team-growth-red-team-2026-07-18.md)
- [AX-adjacent open-role comparison](./docs/research/braincrew-open-roles-ax-closeness.md)
- [Living interview defense dossier](./docs/interview/braincrew-data-portfolio-defense.md)
- [Evaluation Plane design and review status](./docs/superpowers/specs/2026-07-18-evidence-first-evaluation-plane-design.md)

Keep accepted design decisions in durable documents. Use production-grade language and distinguish measured facts, inferences, plans, and exclusions.
