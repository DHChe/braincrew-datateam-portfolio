# Locked: live experiment capture, and what to do when the thing you must attest is not observable

Date: 2026-07-27
Status: locked
Implements: [Issue #85](https://github.com/DHChe/braincrew-datateam-portfolio/issues/85) — Phase 0 of [Issue #15](https://github.com/DHChe/braincrew-datateam-portfolio/issues/15)
Discovered en route: [Issue #86](https://github.com/DHChe/braincrew-datateam-portfolio/issues/86), which blocks Phase 1 of #15

## 1. Why Phase 0 existed at all

`READY` was reached on 2026-07-27, and #15 — the pinned 30-case baseline/candidate experiment — became
the only step it licenses. Measured before starting, #15 could not start:

| layer | state |
| --- | --- |
| `AxHttpAdapter.retrieve()` / `.answer()` | existed since #7 |
| evaluators, 30 Verification cases, minimum denominators | existed (#12) |
| comparison gate, dashboard | existed (#13, #14) |
| **live observation capture** | **zero production callers of `retrieve`/`answer`** |
| **run-artifact contracts** | **`execution_mode: Literal["fixture"]` — a live run was unrepresentable** |

`ExperimentProvenance` in `comparison.py` **already** permitted `Literal["fixture", "live"]`. Someone
anticipated live runs at the comparison layer and it was never propagated down. This is the same
shape #38 had that morning — the model existed, nothing produced it — one layer up.

The lesson that produced this ticket is the one that produced #82: **the authorized runtime start is
manual and expensive, so it happens once, after the entry point exists.** Recommending a runtime
start without measuring whether anything could run was an error made once already; this is the
correction applied a second time.

## 2. The trap: attesting to something you cannot observe

`ExperimentProvenance` carries `sut_dirty: bool`, and the comparison gate refuses when either side is
dirty. Braincrew can check its own worktree — #82 enforces that. **The SUT's dirtiness is not
observable over HTTP.** The adapter sends only tenant, user and role headers; no response reports the
server's worktree.

Emitting `sut_dirty=False` would manufacture a clean-state claim from nothing.

**Decided:** the artifact carries a `SutStateWarrant` — not a bare boolean, but the **method**
(`read-only-git-check`), its **subject** (repository, checkout name, timestamp), and the values the
check returned. A live manifest cannot exist without saying, in its own bytes, where its belief comes
from.

**Rejected:** defaulting to `false`. **Rejected:** omitting the field, which would silently fail the
gate's dirty refusal. **Rejected** for this ticket: probing the server for its own identity — that is
a real gap (below), not something to invent under time pressure.

## 3. What independent review caught, and why it mattered more than the design

The design was sound; **the honesty machinery was not earned.** Review ran eleven mutations. Seven
guards were load-bearing. **Four survivors were, without exception, the ones carrying the honesty
claim:**

| mutation | before repair |
| --- | --- |
| **M11** — CLI calls git, then records constants and **discards the result** | survived |
| M6 — drop `provenance` ↔ `sut_state_warrant` agreement | survived |
| M5 — drop manifest partition coverage | survived |
| M1 — neuter the execution-claim validator entirely | **survived all 433 tests** |

The M10/M11 pair is the exact answer to the question that was asked. M10 (fabricate the warrant
instead of calling git) was **caught**. M11 (call git, throw the answer away, record constants) was
**not**. A test pinned that the check *is invoked*; nothing pinned that the warrant **reports what
the check returned**.

**The general rule this establishes:** a warrant that names a method is not evidence until a test
pins that it carries *the method's result*. Otherwise the sentence is a string a caller types — and
that is worse than a bare boolean, because it reads as evidence.

Three further blocking findings, all now closed:

- **Every live failure produced a traceback and exit 1.** `AxHttpFailure` subclasses `RuntimeError`,
  which the CLI's `except` tuple did not cover. Every realistic failure — 5xx/429 after retries,
  timeout, `RequestError`, schema mismatch — bypassed the locked exit-code table, where `1` is
  reserved for uncaught exceptions and `2` means *no artifact produced*. Zero of the seventeen new
  tests exercised a transport failure. On a run designed to happen once, the most likely failure
  produced the least legible output.
- **The `logical_digest` could not be recomputed from the file it was stored in.** `captured_at` was
  the sole hand-serialized field (`isoformat()` → `+00:00`) while Pydantic wrote `Z`. A reader doing
  the obvious thing would conclude the artifact had been **altered**. For a create-only artifact
  whose purpose is citability, an integrity field that fails its own check is worse than no field.
  Fixed by **deriving** the pre-image — the same principle as §3 of the capture-command decision.
- **The `execution_mode` widening made only a false state reachable on the parsing axis.**
  `ParsingAdapterProvenance.version` was not widened, so the sole newly-representable state was a
  *fixture parser declaring live execution* — and a test asserted it as intended. Reverted; parsing
  stays fixture, which is correct, since 6 of the 30 Verification cases are parsing.

## 4. A correction to the ticket, made by the implementer

The ticket said the command should issue live `retrieve`/`answer` "across the **30** Verification
cases." That is impossible by the data contract: the 30 are **6 parsing + 9 retrieval + 15
grounded**, and parsing cases carry no query. Live calls are **24**. The manifest now encodes the
partition explicitly through `live_case_ids` / `fixture_case_ids`, which is the better outcome. The
orchestrator asserted a total without measuring its composition.

## 5. Issue #86 — found here, blocks #15 Phase 1, and the specification contains both sides

`_confound_violations()` iterates every case pair and demands `recall_at_5`, `mrr_at_10` and
`authority_priority` from each. The 21 non-retrieval Verification cases structurally cannot supply
them, so a real 30-case comparison is `INVALID` by construction.

The contradiction is in the **design specification**, not only the function — line 258 declares those
metrics "mandatory confound evidence" per case. But the same document supplies the resolution:

- line **181** — every retrieval case records **"evaluator applicability"** as a first-class field;
- line **183** — authority priority is "**applicable only** with reviewed resolved ground truth", and
  an aggregate with "**zero applicable cases**" invalidates the run with an explicit denominator
  reason;
- line **240** — "minimum **applicable** Verification denominators … **9 for Recall@5**".

Nine, not thirty. **Scoping the confound check to applicable cases is the specification being
applied, not relaxed.** Filed as #86 with that framing; the fix must amend the design document, not
just the function.

## 6. Carried forward deliberately

- **`--sut-checkout` is not bound to `--base-url`.** A pristine clone at the pinned SHA plus a server
  running a dirty tree yields a true statement about a directory presented as a warrant about the SUT
  that answered. This limit is **pre-existing and already locked** (§6 of the capture-command
  decision: *"`sut_commit_sha` is an assertion, never an observation"*); #85 improves on it by moving
  the check from a human runbook step into the command. Closing it needs the server to attest its own
  identity — an AX-side change.
- **`checkout_path` records a basename, and the contract still permits any string.** The production
  path was aligned with the standard `live_preflight.py:296` already enforces by refusing private
  paths in artifacts, and a test pins it. The *contract* is not constrained — the third instance of a
  binding living at the call site rather than in the contract, after the tenant (#82) and the SUT
  commit.
- **`SutStateSubject.checked_at` is not independent corroboration.** One `datetime.now(UTC)` binds
  both the warrant subject and `captured_at`, so the artifact cannot show whether the checkout was
  inspected before or after the live calls — which is the question a reader asks of a worktree
  warrant.
- **`SutStateSubject.repository` is a typed `Literal`, not derived** from the checkout's remote.
- **`model_copy(update=…)` bypasses validation** for the returned manifest; the object returned was
  never validated in its final form. Benign today, and one line to remove the reasoning step.
- **The run layer has no way to say "mixed."** This capture is genuinely 24 live / 6 fixture, and
  `RunEnvelope.execution_mode` is a single flag, so #15 must choose between an over-claim and an
  under-claim. The capture manifest handles it well; nothing carries it forward.

## 7. What this does not prove

**No experiment ran.** No baseline, no candidate, **no quality claim**. Every result comes from
`httpx.MockTransport`; no AX runtime was started, no live network call was made, no `docker` command
was run.

`braincrew_preflight_ready` stays `true` on the strength of the preflight alone and gains nothing
here. **Phase 1 of #15 — the authorized runtime start and the two 30-case runs — remains a separate
decision, and is additionally blocked by #86.**
