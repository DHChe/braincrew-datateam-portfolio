# Locked: the confound check was under-implementing a contract it already had

Date: 2026-07-27
Status: locked
Implements: [Issue #86](https://github.com/DHChe/braincrew-datateam-portfolio/issues/86)
Unblocks: Phase 1 of [Issue #15](https://github.com/DHChe/braincrew-datateam-portfolio/issues/15) — the last code blocker on it

## 1. The defect, stated precisely

`_confound_violations()` demanded `recall_at_5`, `mrr_at_10` and `authority_priority` from **every**
case pair. The 21 non-retrieval Verification cases — 6 parsing with no query, 15 grounded — cannot
supply them, so a real 30-case comparison was `INVALID` by construction and #15 could not produce a
decision.

**The sharp part: the evaluator's *correct* behaviour was what triggered the violation.**
`evaluator.py` computes each metric only when the case declares it applicable (`:169`, `:173`,
`:180`, `:192`). The comparison layer then read that deliberate omission as `-MISSING`. Two layers
disagreed about what an absent metric *means*, and the layer that knew never told the layer that
asked — `comparison.py` referenced applicability **zero** times.

Found while building #85, reported by the implementer without touching `comparison.py` because that
file was scoped out, and confirmed independently before being filed.

## 2. This was conformance, not a contract change

The first framing — mine — was that adding a required field to `ExperimentCaseResult` while leaving
`schema_version` at `"experiment-run-summary-v1"` is a contract change made tolerable because no
stored artifact breaks. **Independent review rejected that reasoning**, and was right to:

> *"'No stored artifact breaks' is a migration fact — it shows the change is cheap now. It would not
> justify keeping a version name if the contract's meaning had changed."*

The correct reason is stronger. The design document's **unchanged** description of
`experiment-run-summary-v1` already stated that comparison "fails closed when either run is not
`COMPLETED`, either repository state is dirty, case coverage, **per-case applicability**, or metric
denominators differ."

**Per-case applicability was already part of what v1 means.** The code was under-implementing a
contract it already had. Adding the field brings the code into conformance; it does not redefine the
version, so the version name stands. Had the meaning genuinely changed, this repository's own
practice would have demanded a bump — the precedent is `live-verification-preflight-v2`, created at
comparable maturity for exactly that reason.

## 3. The fix is plumbing, because applicability already existed

```python
class RetrievalApplicability(StrictContract):   # contracts.py:197
    recall_at_5: bool
    mrr_at_10: bool
    authority_ordering: bool
    forbidden_visibility: bool
```

Present on `RetrievalCase`, validated there, and carried in all three v2 dataset files.
`ExperimentCaseResult` simply dropped it. It is now carried — **required, with no default**, so a
summary omitting it is rejected rather than silently defaulting to "everything applicable," which
would have restored the original behaviour under a new name.

Three states remain distinguishable, each established by mutation:

| declared | value | outcome |
| --- | --- | --- |
| applicable | absent | `SYS-CONFOUND-*-MISSING` |
| **inapplicable, both sides** | absent | skipped — not a confound candidate |
| applicable | differs | `SYS-CONFOUND-*` |

**Rejected: inferring applicability from the absence of a metric.** That would let a genuinely
missing metric masquerade as a non-retrieval case — destroying the control while looking like a fix.
The entire reason this ticket was tractable is that inference was unnecessary.

## 4. The two traps

**The name mismatch.** The confound metric is `authority_priority`; the applicability field is
`authority_ordering`. A silent key miss would make that metric **permanently inapplicable** — a
disabled control that looks like a fix. Resolved by an explicit map whose keys and values are both
`Literal` types, so a rename fails type-checking rather than silently skipping.

**Inapplicable but present.** A metric declared inapplicable could still carry a value, and the skip
meant a difference in that value was never compared. Closed by a validator: declared inapplicable
implies the value is absent. Neutering it turns three tests red.

Also tightened, deliberately: applicability drift between baseline and candidate now raises
`SYS-COMPARISON-METRIC-APPLICABILITY-MISMATCH`. The skip requires **both** sides to declare
inapplicable; that `and` is redundant with the mismatch error and is commented as such, so a future
reader does not mistake the redundancy for the control.

## 5. The specification was amended, because the code was not the origin

Line 258 declared those metrics "mandatory confound evidence" per case — the sentence that produced
the defect. A code fix alone would recreate it the next time someone implemented from the spec.

The same document supplied its own resolution: line **181** records `evaluator applicability` as a
first-class per-case field; line **183** treats a metric with zero applicable cases as a denominator
problem rather than a division; line **240** fixes the applicable Verification denominator for
Recall@5 at **9** — the number the capture manifest carries and the number the old check
contradicted.

Three amendments, all small:

- line 258 now scopes confound evidence to metrics **declared applicable**, and states that a
  declared-inapplicable metric is not a confound candidate;
- the same sentence says "declared **applicable**", not merely "declared" — every case declares all
  four booleans, including declaring them `false`;
- the enumeration of what `experiment-run-summary-v1` stores now names **per-case evaluator
  applicability**, which the next clause already required to be compared. That omission is the
  ambiguity that made this defect possible.

## 6. What this establishes

**A real mixed-category 30-case comparison can now reach a decision** — not merely be un-refused.
Verified by construction on a 6 parsing + 9 retrieval + 15 grounded pair with the 21 non-retrieval
cases declaring the retrieval metrics inapplicable: the comparison produces `FAIL`, a gate outcome
computed from evidence, **with the confound control still armed on all 9 retrieval cases.**

## 7. What this does not prove

That `FAIL` is arithmetic over synthetic fixture values, not a measurement of any system. **No
experiment has run**; every observation in this repository still comes from `httpx.MockTransport`. No
AX runtime was started, no live network call made, no `docker` command run.

**No quality claim exists.** `braincrew_preflight_ready` stays `true` on the preflight alone.

This removes the last **code** blocker from Issue #15. Phase 1 of #15 — the authorized runtime start
and the two 30-case runs — remains a separate decision.
