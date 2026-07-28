# Locked: operational measurement, and what to do when a dimension cannot be measured

Date: 2026-07-28
Status: locked
Implements: [Issue #89](https://github.com/DHChe/braincrew-datateam-portfolio/issues/89) — Phase 0 of [Issue #15](https://github.com/DHChe/braincrew-datateam-portfolio/issues/15)
Owner decision recorded here: the release comparison runs on quality and latency; cost is excluded, and the exclusion is carried in the artifact

## 1. Why this ticket existed

`compare` consumed a file **no code in this repository produced**:

```
$ grep -rn "ExperimentRunSummary(" src/ | grep -v "class \|: Experiment"
(no matches — only model_validate_json at cli.py:403,406)
```

Two further gaps in the same layer: per-case `latency_ms` and `cost_usd` existed **nowhere** below
`ExperimentCaseResult`, which requires both; and there was **no operational evaluator**, though the
gate requires that key. This is the fourth instance of the shape #38, #82 and #85 each had — the
consumer exists, the producer does not — and #15's own *Delivers* list names latency, token and cost
analysis, so it was always this ticket's work.

## 2. The trap: two required fields with `ge=0`

`latency_ms` and `cost_usd` were **required**. The cheapest way to satisfy that contract is `0`.

Those values do not stop at the case. `comparison.py` computes `baseline_p95_latency_ms`,
`candidate_p95_latency_ms` and `baseline_mean_cost_usd` from them, and those figures land in a
**published comparison artifact**. A zero written to satisfy a validator becomes a measured-looking
latency and cost in recruiter-facing output.

This repository had already answered this shape three times — `sut_dirty`, `sut_commit_sha`, the
readiness verdict — and the answer was never to default. **Carry the warrant, or refuse to emit.**

## 3. Latency — the definition is the type

```python
type LatencyDefinition = Literal[
    "client wall-clock from adapter call start through terminal response validation, "
    "including retries; excludes corpus identity and evaluator time"
]
```

The definition cannot drift from the number, because it *is* a type. A latency whose definition is
unstated cannot be compared across runs, which is the whole point of the field.

**Corrected during review:** the first version said "including retries **and retry backoff**".
`ax_http_adapter._request_json` has **no backoff** — it retries immediately, with no `sleep` anywhere
in the module. The measurement was right; the sentence described a mechanism that does not exist.
**A typed contract asserting a false fact is worse than an untyped one**, because the type lends it
credibility.

**Rejected:** using `HttpAttempt.elapsed_ms`, which already existed. Per-attempt elapsed time does
not give per-case, all-retries latency, so measurement at the capture boundary was still required.
(The orchestrator's brief wrongly claimed no latency field existed at all — it searched for the word,
not the concept. The implementer caught it, and the conclusion survived the corrected premise.)

## 4. Cost — the contract expresses absence

`cost_usd: Decimal | None`, with a `cost_status` bound to it by a validator and a run-level
`cost_measurement_status` validated **bidirectionally** against the case values: `unmeasured` means
no case may carry a cost; `measured` means at least one must. The status is **derived** from the
observations, not asserted and then checked.

**Rejected: writing `0`.** The only plausible cost source is
`AnswerResponse.provider_metadata: dict[str, object]`, which is free-form and unvalidated — reaching
into it and inventing a schema would assert a structure AX has not promised.

A test pins the trap directly: `test_run_summary_refuses_zero_cost_under_an_unmeasured_warrant`.

## 5. The owner's decision — the comparison runs without cost, and says so

The first implementation added `SYS-COMPARISON-COST-UNMEASURED` to `invalid_reasons`. Because the
builder declares cost unmeasured, **every summary it could produce came out `INVALID`** — the
three-gate release decision could never reach `PASS` or `FAIL`. Suppressing that one line reached the
gates, so unmeasured cost was the **only** thing blocking a verdict; compatibility, confounds and
denominators were all clean.

This was escalated rather than resolved by the orchestrator: it changes what a release decision
*means*.

**Decided by the owner:** the comparison runs on **quality and latency**; cost is **excluded**, and
the exclusion is recorded.

Implemented as a `CostDecisionWarrant` with `status: "included" | "excluded"` and a validator
requiring a reason when excluded, carried into the artifact and consulted by the gates.

**The point of the decision, and the thing that must not erode:** skipping a check must never read as
the check having passed. A reader holding only the artifact must not be able to conclude that cost
was evaluated and found acceptable. And the checks **still fire when cost is measured** — the skip is
conditional on the declared status, not a removal.

**Rejected: keeping `INVALID` on unmeasured cost.** It converts *"we could not measure cost"* into
*"the comparison is invalid"*, which overstates the problem: the quality comparison is perfectly
valid. Under that rule #15 could never produce a release decision until AX exposed token and usage
data, which is outside this project's scope.

## 6. F1 — the release verdict was still unreachable, for a different reason

Resolving the cost blocker did not deliver a reachable verdict. Independent review found that with
**real** measured latency, every pair was still `INVALID`:

```
trial 0: INVALID  ('SYS-COMPARISON-DECIMAL-RANGE',)   3/24 per-case deltas overflow
trial 1: INVALID  10/24
...
-> 0/8 real-latency pairs reached a release verdict.
```

`Decimal` division yields 28 **significant** digits, so a ratio whose magnitude is below 1 lands at
exponent −29 or smaller, and the Parquet contract requires `exponent >= -28`. Reproduced:
`0.164083 ms → 0.15525 ms` gives `-0.05383251159474168561033135669`, exponent **−29**, rejected.

**The acceptance test passed only because it injected a synthetic clock** giving baseline and
candidate the identical tick sequence, so all 24 latencies were exactly 1 ms and every per-case delta
was exactly `0`.

> **An injected clock that makes every value identical removes the exact variation the code must
> handle.** That is how a broken pipeline looked green. This is a testing-methodology rule, not a
> one-off: a deterministic test is fine, but at least one test must carry values that genuinely
> differ across cases and runs.

**Decided:** quantise to the contract's scale before the fit check —
`PARQUET_DECIMAL_QUANTUM = Decimal(1).scaleb(-28)` with `ROUND_HALF_EVEN` under a local context whose
precision is sized from the value's own exponent. The range check itself was correct; **producing a
value it must reject was the bug.**

**F2, the mirror image:** every *per-case* delta was range-checked, but the *aggregate the gates
actually read* was not — `_required_relative_delta` called the raw helper, and a published value at
exponent −30 was observed. **Per-case failed closed; the aggregate failed open.** Fixed at the
producer, so both now route through the same quantise-then-check helper.

## 7. Carried forward deliberately

- **One of gate 2's six primary metrics cannot move.** `evidence_span_recovery` is computed from
  **fixture** parsing observations inside a run labelled `execution_mode: "live"`, because
  `evidence_limit` cannot affect parsing. The warrant is carried — `adapter_versions.parsing` is
  `"fixture-parsing-sut-v1"` in the compared provenance — but the macro delta is identically `0` in
  every pair. **This must be stated wherever the comparison is presented.**
- Retrieval and grounded switch to Verification-only on a **magic string** in the input data, while
  parsing uses an explicit keyword. Same intent, two mechanisms.
- Replay **echoes** `prompt`, `model` and `sut.dirty_worktree` for live artifacts rather than
  re-deriving them, so those three compare equal by construction.
- `canonical_ax_role` now normalises both sides of the evaluator's role check, narrowing what
  `SYS-GROUNDED-ROLE-MISMATCH` can detect.
- Every comparison denominator sits **exactly at its locked minimum**. Zero margin.

## 8. Why the Parquet fit check exists at all — DuckDB rounds silently

The `exponent >= -28` half of `_fits_parquet_decimal` looked like belt-and-braces next to a
`DECIMAL(38, 28)` column that would surely reject a bad value. It does not. Probing the sink
directly:

```
scale 28 (in range)  in=0.0909090909090909090909090909    out=0.0909090909090909090909090909    equal=True
scale 29 (exp -29)   in=0.09090909090909090909090909091   out=0.0909090909090909090909090909    equal=FALSE
scale 31 (exp -31)   in=0.0009090909090909090909090909091 out=0.0009090909090909090909090909    equal=FALSE
adjusted 10 (1e10)   in=10000000000                       -> ConversionException
```

**An over-scale value is silently truncated; only an over-magnitude value raises.** So the two halves
of the fit check defend against different things: `adjusted <= 9` against a loud failure, and
`exponent >= -28` against **silent corruption of published evidence**. `replay_comparison_artifact`
re-reads every Parquet row and compares numerically against the recomputed Python rows, and it is the
*only* thing that would notice. That is why bypassing the check at any producer is a correctness
defect rather than a style nit — and it is the reason the same shape being missed five times (§9)
matters.

## 9. The shape that appeared five times, and the type that would end it

Independent review found this shape in five distinct places across four review rounds: **a producer
emitting a `Decimal` its consumer contract refuses.**

| # | site | found in |
| --- | --- | --- |
| 1 | per-case relative delta | F1 |
| 2 | the aggregate the gates actually read | F2 |
| 3 | `_score` (parsing, retrieval) | H8 |
| 4 | the grounded metric value | J1 |
| 5 | `run_summary.py:211-212, 241-242` — `operational.latency_ms`, `operational.cost_usd` | cycle 106, open |

Instance 5 is **not reachable today**, and the reason is worth stating because it is an accident
rather than a guarantee: the only in-repo producer computes
`Decimal(clock_ns() - started_ns) / Decimal(1_000_000)`, and division by a power of ten is exact, so
the result carries at most 6 decimal places. `cost_usd` is hardcoded `None`. The two contracts agree
**because the divisor happens to be 10⁶ and because cost happens to be absent** — nothing enforces
the relationship, and nothing pins it. `OperationalMeasurement` accepts exponent −29 and −30, which
`ExperimentCaseResult` refuses:

```
1/3    exp=-28  fits_parquet=True   OperationalMeasurement=ACCEPTED
1/30   exp=-29  fits_parquet=False  OperationalMeasurement=ACCEPTED
1/300  exp=-30  fits_parquet=False  OperationalMeasurement=ACCEPTED
```

**The root cause is nameable, and it is not carelessness.** The fit check lives on the *consumer*,
and the type at every *producer* boundary is a bare `Decimal`. There is no type in this codebase
meaning "a Decimal that fits the published scale". Correctness at five-and-counting sites therefore
depends on a person remembering to call `_quantize_parquet_decimal`, while mypy, the contracts and
the linters are all silent when they do not. **Every new producer is a fresh draw.**

**Decided: the sequence ends with a type, not a sixth point fix.** A `ParquetDecimal` —
`Annotated[Decimal, BeforeValidator(quantise), AfterValidator(assert_fits)]` — applied at
`ExperimentCaseResult`, `OperationalMeasurement`, `CaseDelta` and `OperationalDelta` alike. Then
producer 6 cannot exist, and instance 5 closes as a side effect. **Deliberately deferred to its own
ticket**, because it is a contract change across four models and does not belong in a ticket already
at five review rounds.

**Rejected: quantising at instance 5 now.** It closes one site and leaves the generator running.

## 10. Carried forward as known-unpinned

- **`_p95` is unpinned from above.** Mutating it to return the **maximum** instead of the 95th
  percentile leaves all 497 tests green; mutating it to the minimum is caught. Two independent
  causes hide it at once: the unit fixtures use `n = 15`, where `ceil(0.95 × 15) - 1 = 14` **is** the
  last index so the two are arithmetically identical, and the 24-case acceptance test — where they
  genuinely differ — never asserts the p95 value. `baseline_p95_latency_ms` and
  `candidate_p95_latency_ms` are the operational headline numbers on the dashboard. Fix is one
  assertion in the 24-case test.
- **The gates' cost-warrant consultation cannot be killed by any test, and no one should try.**
  `operational.mean_cost_relative_delta if warrant.status == "included" else None` is a tautology
  within `compare_runs`: `excluded` implies both mean costs are `None`, which implies the delta is
  `None`. It is correct defensive code, but §5's phrase "consulted by the gates" should be read
  precisely — it *is* consulted, and the consultation is not what does the work. The exclusion
  happens because the delta is `None`.
- **One measurement is now stored in two representations.** The grounded artifact holds the
  full-precision ratio (exp −29); the summary and Parquet hold the quantised one (exp −28), differing
  by `1E-29`. This is forced, not sloppy: `GroundedMetricScore` re-derives the value from its counts
  and **refuses** the quantised value, while the storage contract refuses the full-precision one.
  Rounding at the boundary is the only point satisfying both. Nothing in the codebase reads the two
  together.
- **`OperationalDelta.*_cost_case_count` can only hold `0` or `N`,** since partial cost coverage is
  refused by design and pinned by a named test. It carries one bit, not a count.

## 11. What this does not prove

**No experiment has run.** No baseline, no candidate, **no quality claim.** Every observation still
comes from `httpx.MockTransport`; no AX runtime was started, no live network call was made, no
`docker` command was run. `braincrew_preflight_ready` stays `true` on the preflight alone.

Phase 1 of #15 — the authorized runtime start and the two 30-case runs — remains a separate decision.
Whether the live answer path requires a generation provider is an **AX-side fact not observable from
this repository**, and is to be settled by a single-case probe at that time rather than guessed at.

**The dashboard now demonstrates the cost-exclusion decision.** The four existing golden run-summary
fixtures were changed to `cost_measurement_status: "unmeasured"` with null case costs, and
`dashboard/data/dashboard-export-v1.json` was regenerated from the baseline/pass pair. The shipped
artifact therefore carries an `excluded` cost warrant and renders **"Not measured — both runs
declare cost unmeasured"**, matching the only shape the repository's live producer can emit.

**Chosen: update the existing golden fixture family.** One canonical fixture chain now represents
the producer contract used by the public dashboard, while the independent `_mixed_run_payload`
comparison tests retain measured-cost gate coverage. **Rejected: add a second cost-excluded fixture
family.** That narrower immediate diff would leave measured and unmeasured golden families to keep in
sync even though only the unmeasured family can represent repository-produced run summaries.

**The surviving coverage was proved by mutation, not by observing that a test passes.** §5 requires
the cost checks to keep firing when cost *is* measured, and flipping the golden fixtures to
`unmeasured` is exactly the change that could silently remove that. Deleting the
`GATE-2-COST-REGRESSION` clause from `comparison.py:788-793` turns
`test_measured_cost_regression_still_fails_gate_2` red and nothing else — `1 failed, 497 passed`. A
passing test would only have shown the property is not contradicted; the mutation shows it is
enforced.

**The regenerated artifact was verified by re-deriving it, not by trusting a comparison.** Rebuilding
from `comparison_baseline_v1.json` + `comparison_candidate_pass_v1.json` with
`provenance.dataset_digest` set to the manifest's `content_digest` — the same single transformation
`test_dashboard_export.py::_comparison_artifact` applies — reproduces
`sha256:d426e04c0c2b960d8c8c17efc216688891b2078faaaa51ff226c137c2f8694ae` and a **byte-identical**
`dashboard-export-v1.json`. That digest is the one pinned in both
`tests/frontend/dashboard-data.test.ts:120` and `tests/frontend/e2e/dashboard.spec.ts:18`. All 15
published cases carry `cost_relative_delta: null`.

> **Two corrections to this section, kept rather than quietly overwritten, because both are the
> failure mode this document exists to warn about.** It first quoted the digest as
> `sha256:d426e04c…4670b`. The tail `4670b` came from a **different digest** —
> `sha256:2c16cdd4…4670b`, produced by a first regeneration attempt that used the raw fixtures
> without the `dataset_digest` substitution and was rejected by the exporter. The head of the correct
> digest was spliced onto the tail of the wrong one. **An abbreviated digest is not a digest**; it
> reads as verification while carrying none, and this is a provenance document. It also claimed *"the
> superseded digest appears nowhere in the tree"* — the search that justified it covered `tests`,
> `dashboard` and `src`, but the claim was written unscoped, and `f8630e70…` was in fact still in
> `docs/status/braincrew-delivery-workflow.md`. **A search's scope is part of its result.** Both were
> caught by independent review before the commit.
