# Agent autonomy envelope: constraint inventory, red-team assessment, and a proposed design

Date: 2026-08-01
Status: **proposal — not locked, not adopted, no rule changed.** `AGENTS.md` is unmodified.
Origin: the owner asked whether the rule-level constraints that gate agent autonomy could be removed
so orchestrator and workers could run to a stated goal without per-action approval, and asked for a
review including a red-team opinion before any change.

This document exists so that decision can be resumed later without reconstructing it from
conversation memory. **Nothing here is authoritative.** If any of it is adopted, the adopted part
belongs in `AGENTS.md` and in a `docs/decisions/` file, and this document becomes its background.

## 1. What the owner proposed

Replace per-action human approval with goal-level delegation: the owner states an objective, and the
orchestrator and workers carry it to completion — including the Git lifecycle — without stopping for
approval at each step. The stated motivation is that implementation feels slow and accumulates side
branches.

## 2. Constraint inventory

Everything currently gating autonomy, grouped by what it actually is. The grouping matters more than
the list: the three groups have different costs and different value, and treating them as one thing
is how a useful constraint gets removed alongside a useless one.

### A. Approval gates — work stops until a human answers

| Constraint | Source |
| --- | --- |
| Propose and wait for explicit authorization before `commit`, `push`, pull request, or merge | Git Lifecycle Proposal Gate |
| No direct commits to `main` or `develop`; feature branch and reviewed pull request required | Branching Strategy |
| Never merge with failing required checks, unresolved review blockers, or unverifiable benchmark claims | Git Lifecycle Proposal Gate |

The third is not really an approval gate — it is a hard invariant that happens to live in the same
section. It should not move with the other two.

### B. Process obligations — no human needed, but a cost every cycle

| Constraint | Source |
| --- | --- |
| Announce the active skill or workflow, its artifact, and its completion condition before acting | Skill Workflow Navigation Contract |
| Update `docs/status/braincrew-delivery-workflow.md` whenever a phase starts, completes, blocks, or changes | Skill Workflow Navigation Contract |
| Provide a copy-ready fresh-session prompt plus a plain-Korean explanation of its instructions | Skill Workflow Navigation Contract |
| Operate the project as a guided Matt Pocock skill-learning environment; supply reusable mental models | Skill Workflow Navigation Contract |
| Korean responses; `Korean (English term, plain meaning)` on first use; six-element explanation per material defect | User Communication Contract |
| Lore-format commit messages | Git Lifecycle Proposal Gate |

### C. Hard invariants — what makes this project's central claim true

| Constraint | Verified working on 2026-08-01 |
| --- | --- |
| Claim only what was executed and reproducibly verified | yes |
| Do not accept a worker's report as evidence; reproduce load-bearing claims independently | yes — the blocking defect was reproduced against the real capture, not taken from the report |
| The same rule binds the orchestrator toward workers; mark each claim measured or inferred and name the measurer | yes — an inherited claim about two AX issues was measured before being asserted |
| The orchestrator does not review its own writing | **yes — this caught four of the five blocking defects** |
| Never let two panes edit the same file | yes |
| Never run two test suites concurrently in the shared tree; verify `git status` afterwards | yes, enforced by serialising every run |
| Stage explicitly named paths; never `git add -A`, never `git commit -a` | yes |
| Durable records are append-only | yes |
| Every published experiment records the SUT commit SHA and the dataset, evaluator, prompt and model versions | yes |
| AX runtime: `docker start` only, never `up`; stage-by-stage authorization | not exercised — no runtime was started |

## 3. Measured cost, from the 2026-08-01 session

The session delivered Issue #106 across cycles 138 to 146.

- **Human approval interactions: 5** — scope selection, commit/push/PR, merge, branch deletion plus
  status record, and a final push/merge.
- **Agent-internal cycles: 9**, of which **zero** required a human.
- **Blocking defects found: 5.** One in code. **Four in the orchestrator's own prose**, one of which
  had reached the recruiter-facing dossier card.

**The approval gates did not lengthen this session; the review and audit loop did, and that loop is
already fully autonomous.** The gates themselves produced zero corrections — every proposal was
approved as written.

That finding cuts both ways, and the second edge is the stronger one: the gates cost nothing *while
the owner is present*, and cost an unbounded stall while the owner is away. Asynchronous operation is
the real case for removing them.

## 4. Red-team assessment

### R1. Acceleration raises the output rate of the thing that fails most

Four of five blocking defects this session were false statements in the orchestrator's own writing,
not code. The pattern is not new: a 2026-07-31 audit found three overclaims in the orchestrator's
status entry, and Issue #101's audit returned `NOT SAFE TO COMMIT` on four records-level findings
**after two code reviews had already passed**.

This project's product is evidentiary integrity. Its characteristic failure is not a broken build but
a published false claim, and the orchestrator is its most reliable source. Speeding the loop increases
production on exactly the defect-dense surface.

**Implication: autonomy must strengthen the audit, not relax it.**

### R2. Removing the gate removes the hook the audit hangs on

The pre-commit audit runs because the Git gate creates a natural checkpoint before the irreversible
action. Remove the gate and the audit becomes a habit; habits are rationalised under time pressure,
and the orchestrator's self-assessment is the specific faculty that fails here.

**Implication: the audit must become a machine precondition, not a practice.**

### R3. Reviewer independence is currently the orchestrator's discretion

The orchestrator writes the reviewer's brief. On 2026-08-01 it deliberately withheld its own findings,
and the reviewer recorded that this is why it found the blocking defect. **That was a choice, not a
rule.** Nothing prevents a future orchestrator from writing a leading brief, and under autonomy
nobody would notice.

### R4. Reviewer budget exhaustion produces silent non-review

The reviewing pane reached 96 percent of its weekly budget earlier the same day. In an unattended
loop, exhaustion yields either unreviewed work or a silent stall. Neither is currently handled by any
rule.

### R5. Issue #97 is a precondition for more parallelism, not a follow-up

`tests/contract/test_corpus_pack_sealing.py` writes drift into the tracked `schemas/` directory, and
concurrent runs can leave it durably corrupted with a self-consistent `(schema, digest)` pair that
only `git status` detects. Today the orchestrator prevents this by serialising every suite by hand.
Faster, less supervised work raises the violation probability against an unfixed hazard.

### R6. The loop has no convergence criterion of its own

The "mutually consistent" claim generated a fresh finding every review round. What ended it was a
judgement — enumerate the claim as a closed list — and that judgement came from the reviewer, not the
orchestrator. An unattended loop needs an explicit definition of done and a circuit breaker, or it
will keep finding true defects forever.

### R7. Scope selection is the one decision that should not be delegated

The owner chose one of five recorded gaps. The orchestrator's recommendation matched, but the
orchestrator does not hold the context that makes that choice correct — interview timing, what a
recruiter will actually open, which claim matters most. Delegating scope risks building the wrong
thing efficiently.

## 5. Proposed design — an envelope, not a gate removal

### Hard stops that remain

1. Spending provider money, including any candidate capture.
2. Starting the AX runtime or changing any container state.
3. Merging to `main`, the recruiter-facing release surface.
4. Force push, history rewrite, deletion of an unmerged branch, any change to Git configuration.
5. Final publication of anything outward-facing as finished.

### Delegated, with machine preconditions replacing the human gate

Commit, push, pull request and merge **into `develop`**; filing, commenting on and closing issues;
deleting merged branches; and writing status, decision and dossier documents — **only when all of the
following hold**:

- every CI job green;
- independent review returned `APPROVE`;
- pre-commit audit returned `SAFE TO COMMIT`;
- `git status --short schemas/` empty;
- staging was by explicitly named path.

### Invariants that hold in every mode

All of section 2C, without exception. In particular *the orchestrator does not review its own
writing* and *a worker's report is not evidence* — together these accounted for every blocking defect
found on 2026-08-01.

### New rules autonomy would require

| Rule | Answers |
| --- | --- |
| A reviewer's brief must not contain the orchestrator's own conclusions — a rule, not a discretion — and the reviewer's verdict is recorded verbatim in the durable record | R3 |
| An autonomy ledger: every decision that replaced a human gate is logged with the evidence for each precondition, so the owner audits after the fact instead of before | converts synchronous approval into asynchronous review, which is the actual acceleration |
| A circuit breaker: two consecutive `NOT SAFE TO COMMIT` verdicts, or more than N cycles on one ticket, stops the loop and surfaces it | R6 |
| A reviewer-budget precondition checked before dispatch, with an explicit stall-and-report path | R4 |

### The cheapest real saving, which is not a gate

The largest pure overhead in section 2B is the **pedagogical** clause — operating the project as a
guided skill-learning environment, supplying reusable mental models, and writing copy-ready handoff
prompts with plain-language explanations. It is explicitly a teaching goal, not an integrity control.
If the objective has shifted to delivery speed, this is the first thing to cut and nothing of the
project's claim is lost.

The User Communication Contract should be **kept**. Under greater autonomy the owner controls the work
only through after-the-fact reading, so report quality matters more, not less.

## 6. Expected effect

Applying the envelope to the 2026-08-01 session would have reduced five human interactions to one or
two — scope selection, and a release decision. While the owner is away, blocking stalls approach zero.

## 7. Open decisions

1. Does scope selection stay with the owner? (Recommended: yes.)
2. Are the five hard stops agreed, and is anything missing or over-included?
3. Is Issue #97 fixed before parallelism increases? (Recommended: yes.)
4. Is the pedagogical clause removed?
5. Is autonomy a standing `AGENTS.md` clause or a per-session opt-in?

Adopting any of this requires editing `AGENTS.md`, which is a rules file and needs the owner's
explicit instruction. Adding a pointer to this document from `AGENTS.md` § Standards & References
would make it findable, and also touches that file, so it is likewise not done here.
