# Braincrew Evaluation Portfolio — Scope and Skill Flow Lock

Date: 2026-07-18  
Status: LOCKED

## 1. Submission claim boundary

The portfolio evaluates only capabilities that are implemented and reproducibly verified during the ten-day build window.

- Do not add Agent evaluation merely to match job-posting terminology.
- Do not claim Agent or multi-step trajectory quality unless a real Agent execution path, trace contract, dataset, evaluator, and repeatable result all exist.
- Mark unavailable or unfinished capabilities as `planned` or `not evaluated`.
- Treat AX_portfolio as the evolving Subject Under Test (SUT), not as a finished system whose quality is assumed.
- Record the exact SUT commit SHA together with dataset, evaluator, prompt, and model versions for every published experiment.

## 2. Forward-compatible evaluation contract

The first production release validates document parsing, retrieval, grounded answering, operational measurements, experiment comparison, and release gates. Its contracts must remain extensible to later Agent trajectory evaluation without pretending that this later scope has already been built.

The evaluator and experiment schemas therefore reserve stable extension points for:

- evaluation target type, such as `parsing`, `retrieval`, `answer`, and future `trajectory`;
- ordered execution steps and tool-call observations;
- step-level inputs, outputs, evidence references, latency, token usage, and cost;
- trajectory-level expected outcomes, constraints, and failure labels;
- evaluator provenance and versioning;
- baseline-versus-candidate comparison across the same dataset revision.

These are schema and interface extension points only. The submission UI, README, resume, and demo must report only evaluators and experiments that were actually executed and verified.

## 3. Explicitly excluded claims

- No fabricated Agent benchmark.
- No LLM-judge-only proof of quality.
- No claim that the entire AX_portfolio has been evaluated.
- No claim that planned trajectory fields constitute an implemented Agent evaluator.
- No use of private customer or employee documents as portfolio evidence.

## 4. Skill and workflow ownership

### Current question-and-design loop: `brainstorming`

The current questions come from the `brainstorming` skill. Its job is to turn the chosen portfolio direction into an approved design by:

1. inspecting the project context;
2. clarifying one decision at a time;
3. comparing alternative approaches;
4. presenting and approving the design section by section;
5. writing and reviewing the final design specification;
6. handing off only to implementation planning after design approval.

Therefore, a question asking whether an evaluation scope, architecture, schema, metric, or test boundary is correct belongs to `brainstorming`, not to Ask Matt.

### Ask Matt blueprint: workflow router and execution architecture

Ask Matt previously defined the higher-level route used after the direction was selected:

```text
existing Braincrew research and AX_portfolio context
  -> setup/verify Matt Pocock workflow skills
  -> grill-with-docs for adversarial requirements interrogation
  -> optional time-boxed prototype only for a concrete runnable uncertainty
  -> handoff
  -> to-spec
  -> to-tickets with dependency edges
  -> fresh-context implementation per ticket with TDD
  -> code review per ticket
  -> full benchmark and submission verification
```

Ask Matt determines how the work moves from evidence and clarified requirements into specification, tickets, implementation, and review. It is not the source of each incremental design-approval question.

## 5. Non-negotiable wording for the final submission

Preferred claim:

> While an HR/labor AX product was evolving, I introduced measurable quality criteria, a versioned evaluation dataset, failure taxonomy, experiment comparison, and release gates for the capabilities that were actually available and tested. The evaluation contracts are designed to extend to Agent trajectories, but Agent evaluation is not claimed in this submission.

## 6. Repository and SUT boundary

The Evaluation Plane and AX_portfolio are separate repositories with separate histories and responsibilities.

```text
braincrew-datateam-portfolio
  ├─ versioned evaluation datasets
  ├─ experiment runner and result store
  ├─ parsing, retrieval, answer, and operational evaluators
  ├─ comparison and release-gate logic
  ├─ dashboard and submission material
  └─ SUT Adapter ──HTTP──> AX_portfolio
```

- `braincrew-datateam-portfolio` owns the Evaluation Plane and submission evidence.
- `AX_portfolio` remains the evolving product and Subject Under Test.
- The live adapter calls AX through a documented HTTP contract and normalizes responses into evaluation observations.
- AX internals are not copied or imported into the Evaluation Plane.
- If required evaluation observations are unavailable, AX may receive a narrowly scoped observability endpoint through its own product branch and review process.
- Recorded fixtures may support deterministic development and replay, but they do not replace at least one reproducible live-SUT benchmark for submission claims.

## 7. Branching strategy

Use a lightweight integration-branch workflow for the ten-day delivery window:

```text
main
  └─ develop
       ├─ docs/evaluation-plane-design
       ├─ feat/evaluation-contracts
       ├─ feat/dataset-registry
       ├─ feat/ax-sut-adapter
       ├─ feat/evaluator-runner
       ├─ feat/experiment-comparison
       └─ feat/dashboard-release-gates
```

- `main` is the stable, recruiter-facing release branch. It receives release pull requests from `develop` only.
- `develop` is the integration baseline for the approved design and verified feature work.
- Design work starts on `docs/evaluation-plane-design` from `develop`; implementation does not start before the written design and implementation plan pass their gates.
- Each feature branch starts from the latest verified `develop`, owns one bounded capability, and returns through a pull request with tests and review evidence.
- Do not create all feature branches in advance. Create a branch only when its dependency is ready and its ticket is executable.
- After integration and full benchmark verification, open a release pull request from `develop` to `main` and tag the frozen submission commit.
- AX_portfolio keeps its own branch and worktree lifecycle. No branch crosses repository boundaries.
