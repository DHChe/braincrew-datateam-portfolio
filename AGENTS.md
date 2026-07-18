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

## Standards & References

- [Locked evaluation scope and workflow](./docs/decisions/2026-07-18-evaluation-scope-and-skill-flow-lock.md)
- [Braincrew Data role and hackathon benchmark](./docs/research/braincrew-data-role-and-hackathon-benchmark.md)
- [Data Team growth red-team assessment](./docs/research/braincrew-data-team-growth-red-team-2026-07-18.md)
- [AX-adjacent open-role comparison](./docs/research/braincrew-open-roles-ax-closeness.md)

Keep accepted design decisions in durable documents. Use production-grade language and distinguish measured facts, inferences, plans, and exclusions.
