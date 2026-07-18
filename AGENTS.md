# Braincrew Data Team Portfolio Agent Guide

## Operational Commands

This repository is currently documentation-first. Before committing documentation changes, run:

```bash
git diff --check
git status --short
```

When executable evaluation code is introduced, add its exact install, lint, typecheck, test, benchmark, and reproducibility commands here before calling that work complete.

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
- A Git lifecycle action is not a workflow phase transition. Continue to follow the separate Git Lifecycle Proposal Gate for commits, pushes, pull requests, and merges.

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
