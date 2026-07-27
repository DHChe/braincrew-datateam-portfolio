# Locked: the live verification capture command, its exit codes, and where the tenant binding lives

Date: 2026-07-27
Status: locked
Implements: [Issue #82](https://github.com/DHChe/braincrew-datateam-portfolio/issues/82)
Discharges: §8 of [`2026-07-27-live-verification-readiness-verdict.md`](./2026-07-27-live-verification-readiness-verdict.md), which deferred the CLI exit-code question to "whoever wires the live capture path"

## 1. Why a command, rather than running the capture directly

Two merges earlier the same day built the v2 artifact (`87c0fc4`) and gave it a readiness verdict
(`7f3f1bf`). **Neither made it possible to run.** Measured before this work: no `src/` caller of
`capture_live_verification_preflight`, no CLI command, and v2 absent from the `replay` dispatch. The
only way to capture was to type Python into a terminal.

That is not acceptable **here specifically**, and the project has already ruled on it. AX PR #53
repaired a defect of exactly this shape: a blob inventory "had been produced by *reimplementing* the
runbook's generator instead of running it," and its regeneration check passed only because it
compared that script against itself.

The artifact this command produces is meant to be cited as **the evidence that Issue #38 reached
`READY`**. An artifact whose provenance is "someone typed this at the time" cannot carry that weight,
and Issue #16 will additionally require one-command deterministic replay.

**So the authorized AX runtime start happens once, after this exists — not twice.**

## 2. Exit codes

| code | meaning | what the operator does |
| --- | --- | --- |
| `0` | `READY` | replay and record the evidence |
| `3` | `NOT_READY`; **the artifact was written** | stop, replay, inspect its typed blocker — do **not** repair inputs and re-run |
| `2` | no artifact was produced | investigate the capture failure, then retry |

**Why `NOT_READY` is not `2`.** Every other failure path in `cli.py` exits `2` — 23 call sites at
`7f3f1bf`, uniformly, all meaning *we produced nothing*. `NOT_READY` is not that: the artifact is
written, valid, and replayable, and it is precisely the evidence the negative verdict was built to
produce. Collapsing the two destroys the distinction between **"we captured a refusal"** and
**"we failed to capture"** — the distinction an operator needs most at the moment the runtime is live
and something looks wrong.

**Why not `0`.** A preflight that cannot fail a script is not a gate.

**Why `3` is safe.** Click reserves `1` (`Abort`, uncaught exception) and `2` (`UsageError`). `3` is
free, and using it does not collide with the framework's own semantics.

## 3. Derive, do not type — and the input that proved it

An operator retyping an identity is a way to run against the wrong thing, on a run that happens once.
Derived rather than accepted as options: `captured_at`, the Evaluation Plane SHA, `sut_commit_sha`
(from `PINNED_AX_SHA`), the frozen v3 dataset validation, and — via
`capture_reviewed_live_verification_preflight` — the **subject and the six attachment mappings** from
the receipt.

The first implementation still took `--tenant-id` as a bare string. Review measured the cost: two
full captures identical except for the tenant, one on a tenant nobody had ever reviewed, **both
returned `READY` and both replayed `READY` forever.**

The realistic harm was a **false negative**, and it was specific to a once-only run. The reviewed
tenant is `ae09ec7f-…`; the demo tenant that has already caused one wrong-tenant incident in this
project is `11111111-…`. A mistyped-but-valid UUID yields 404s → `attachment_not_found` →
`NOT_READY`, and the runtime plan requires that a blocker be *preserved and analyzed, not repaired
mid-run*. **An operator typo would have become a preserved, create-only, replayable artifact that
reads exactly like AX genuinely failing** — with the single output path already burned.

**Decided: derive the tenant from the receipt.** `tenant_id` joins `_ReceiptTarget` and
`_ReviewedHandoffBinding`; `--tenant-id` is gone.

**Rejected: pin a reviewed-tenant constant and compare.** `REVIEWED_HANDOFF_RECEIPT_SHA256` already
pins the exact receipt **bytes**, so a tenant read from it cannot vary — a constant would be
redundant with a check that already exists. This is also why §5 of the receipt-binding decision does
not forbid deriving here: that section refuses to derive `PINNED_AX_SHA` because the SHA is a
*committed Braincrew review decision* and comparing the two is a real check. **The tenant had no such
counterpart** — it was an operator keystroke with no committed authority, so deriving it deleted no
check.

## 4. Where the tenant binding lives, and what Issue #38 may therefore claim

**This is the most important sentence in this document.** The tenant is bound at the **entry point**,
not in the **artifact contract**.

Three barriers close the operator hazard: the tenant is not a wrapper parameter at all (passing it is
a `TypeError`, not a rejected value); `--tenant-id` is absent from the CLI and a **signature-level**
test asserts it cannot return; and altering the receipt's tenant changes its bytes, which the pinned
digest refuses.

But the **subject** enjoys a validator-level binding the tenant does not:
`_validate_principal_parse_request` and `_validate_live_verification_corpus_request` both compare
`request.user_id` against `reviewed_binding.subject_id`, so an unreviewed subject cannot survive
validation **or replay**, no matter who calls what. The validators check the tenant only for
canonical-UUID form and single-tenant consistency. Calling the inner
`capture_live_verification_preflight` directly with an arbitrary tenant still produces an artifact
that validates and **replays `READY`**.

**Consequence, and it must be honoured:** Issue #38's AC1 clause *"binds the exact … tenant …
identit[y]"* is satisfied **by the capture path**, not by the artifact in isolation. A reviewer handed
only the artifact and the receipt cannot verify the tenant. A reviewer handed the artifact **and the
fact that it came from `capture-live-verification`** can. Do not cite the artifact alone for that
clause.

This was deliberately **not** fixed here: #82 puts "changing what any validator accepts or refuses"
out of scope, and demanding a validator-level tenant comparison would have pushed the implementer to
violate the ticket.

## 5. A test can be coupled to the terminal, and `NO_COLOR` is not the control

The repair's first attempt reported `416 passed`; the orchestrator measured **`1 failed`** on the
same tree. Neither was miscounting — the test was coupled to the environment.

Typer renders an option name as **two separately styled fragments**, so the literal substring
`Invalid value for '--output'` does not appear in `CliRunner` stderr. The orchestrator's account
attributed this to colour, and **that was wrong**. Measured:

| environment | raw stderr fragment | plain substring present? |
| --- | --- | --- |
| `NO_COLOR=1` | `'\x1b[1m-\x1b[0m\x1b[1m-output\x1b[0m'` | **no** |
| `FORCE_COLOR=1` | `'\x1b[1;36m-\x1b[0m\x1b[1;36m-output\x1b[0m'` | **no** |
| `TERM=dumb` | `'--output'` | yes |

`NO_COLOR=1` suppresses colour but **not bold**, so the fragments stay separately styled. The trigger
is **Rich styling being active at all**, not colour. Recording this because the wrong inference would
make `NO_COLOR=1` look like a sufficient guard in future work, and it is not.

**Fixed by stripping CSI sequences in the test helper**, which removes a dependency `NO_COLOR` would
not have removed. The specific assertions were **kept, not weakened** — a return-code-only assertion
would have been worthless, because `2` is now the busiest code in the CLI.

**The transferable rule:** this repository's existing CLI tests assert on **application-emitted**
fixed strings (`typer.echo(..., err=True)`), which are plain and stable. This was the first test to
assert on **framework-generated** output. Those are different classes, and the second needs the
strip.

## 6. Carried forward deliberately

- **`--output` may point inside the repository.** The runtime plan requires the artifact be written
  outside it, and the repository is meant to record the artifact's digest, not its bytes. A
  create-only artifact landing in a tracked directory becomes accidentally committable. Not a leak —
  the artifact is sanitized and refuses private paths.
- **A well-formed but wrong `--base-url`** (wrong port, `https` against a loopback `http` listener)
  produces a create-only `NOT_READY` at the output path rather than "no artifact produced". Whether a
  transport failure on the **first** request — before any observation exists — should be a verdict
  about AX at all is a design question, not a defect. The runtime plan mitigates it by verifying
  `health/ready` first.
- **The receipt is read and digest-verified three times per capture.** Fails closed; tidiness only.
- **Provenance the artifact structurally cannot carry:** no adapter contract identity, no
  provider/model, no runtime configuration. And `sut_commit_sha` is an **assertion, never an
  observation** — the adapter sends only tenant, user and role headers, so nothing verifies the
  running AX is at `PINNED_AX_SHA`. The runtime plan covers the AX checkout read-only instead. **The
  #38 assessment must not over-claim these.**
- **`PROJECT_ROOT = Path(__file__).resolve().parents[2]`** assumes a source checkout; the frozen
  manifest would not resolve from a wheel install. Deriving the path is the right call; only the
  resolution strategy is fragile.
- **The new receipt-model refusal and its sibling are unobserved by tests.** Recorded with
  [#78](https://github.com/DHChe/braincrew-datateam-portfolio/issues/78).

## 7. What this does not prove

**Nothing has been captured.** Every observation in this repository still comes from
`httpx.MockTransport`. No AX runtime was started, no live network call was made, no `docker` command
was run. `braincrew_preflight_ready` stays **`false`**.

This makes the capture *runnable and reproducible*. It does not run it. The authorized AX runtime
start is Phase 1 of `plan-live-runtime-capture.md` and remains a separate decision.
[AX #37](https://github.com/DHChe/AX_portfolio/issues/37) and
[AX #43](https://github.com/DHChe/AX_portfolio/issues/43) remain open formal blockers of Issue #38.
