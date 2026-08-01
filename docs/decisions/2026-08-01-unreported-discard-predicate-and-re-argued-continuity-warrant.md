# Locked: an unreported discard predicate is unknown, not false — and a continuity warrant is re-argued, never carried forward

Date: 2026-08-01
Status: locked
Implements: [Issue #121](https://github.com/DHChe/braincrew-datateam-portfolio/issues/121),
[Issue #122](https://github.com/DHChe/braincrew-datateam-portfolio/issues/122)
Owner decision recorded here: the under-test AX pin moves to the commit that split the two discard
causes, and Braincrew records that split without asserting anything about the runs that predate it

## 1. What changed upstream, and why it reaches this repository

AX commit `3bb27f8` (`#60`, `#61`) separated two failures that had shared one label. Before it, a
provider answer was discarded with `failure_reason = "unsafe_provider_output"` whether the cause was a
**citation-contract violation** (the answer cited evidence it was not given) or **unsafe provider
output** (the safety guardrail fired). One name, two meanings. AX now emits both causes as separate
booleans while deliberately leaving the historical `failure_reason` label unchanged on the wire.

Braincrew is the measuring instrument. When the instrument's subject grows a distinction, the
instrument must record it — or every future measurement silently collapses the two causes again.

## 2. The decision that carries the weight

**An absent predicate is `None`, and `None` means *unknown*. It is a third state, not a synonym for
`False`.**

The already-published 2026-07-31 capture contains 15 grounded observations, and its discarded cases
were produced by pre-split AX. For those records we do not know which cause fired, and no amount of
re-reading the artifact can tell us. Only a new run against `3bb27f8` can.

Had these fields defaulted to `False`, every rebuild of that published capture would assert that **not
one** of those discards was a citation-contract violation. That is a claim with zero evidence behind
it, manufactured by a default value, in a repository whose entire proposition is that its claims are
measured. It is the same one-code-two-causes defect the upstream ticket existed to remove, re-created
one layer down.

## 3. Why `exclude_if`, and not merely `default=None`

`default=None` gets the semantics right in Python and wrong on the wire. `model_dump(mode="json")`
would emit `"citation_contract_violation": null` into every serialized `AnswerPathHealth`, changing
the bytes of records that are **already published**.

The capture manifest pins content digests over its sibling observation files, and the artifact is
create-only. Changing the dump leaves two outcomes, both unacceptable: the published capture stops
replaying, or we rewrite published evidence to make it replay again.

```python
citation_contract_violation: StrictBool | None = Field(
    default=None,
    exclude_if=lambda value: value is None,
)
```

`exclude_if` omits the key entirely when the value is `None`, so a stored record dumps byte-identically
to the day it was written, while a record captured against `3bb27f8` carries both predicates.

**Measured:** all 15 stored `AnswerPathHealth` objects round-trip through the new model with zero byte
differences; each dumps exactly `failure_reason`, `llm_call_performed`, `llm_call_succeeded`; none
acquires either new key. `canonical_digest` over the rebuilt set is
`sha256:e3ff09642c8df51ffebba488573dd817c9af338e7e45d819c334f648c46e35a3`.

## 4. Why the warrant was re-argued rather than carried forward

`ReceiptSutContinuityWarrant` is **an argument, not a fact**. It states: the SUT source tree changed in
exactly these paths between the provisioned commit and the commit under test, and none of them touch
provisioning state — therefore a receipt taken at the older commit still binds.

When the under-test commit moves, that argument must be re-made from the new diff. Its *conclusion*
must never be transplanted.

Concretely, this mattered. The previous warrant named one changed path. The new diff changes two,
because `backend/src/ax_engine/answers/contracts.py` is new to it. Bumping `under_test_sha` alone
would have left a warrant asserting a one-file change for a two-file change — a statement that reads
as true, passes every existing check, and is wrong.

**Measured, re-derived from the AX checkout rather than from the previous warrant:**

| Field | Value | Command |
| --- | --- | --- |
| provisioned tree | `846c06ba…` | `git rev-parse 2bcaee34…:backend/src` |
| last-equivalent tree | `846c06ba…` | `git rev-parse d7930978…:backend/src` |
| under-test tree | `627fcdff…` | `git rev-parse 3bb27f87…:backend/src` |
| changed production paths | `answers/service.py`, `answers/contracts.py` | `git diff --name-only d7930978… 3bb27f87… -- backend/src` |

The full commit also touches `backend/tests/unit/test_answer_runtime.py`. It is excluded because
`changed_paths` is a claim about **production** source; including a test path would weaken the
warrant's meaning while appearing to strengthen its thoroughness.

`provisioning_state_affected=False` is therefore a bounded conclusion from a two-file diff containing
no corpus import, seed, migration, attachment, principal, or role operation — not an inference from
absence of evidence.

## 5. Both repositories independently express the same convention

Independent review traced the `None` state across all four segments and found the two repositories
implement the same rule by different mechanisms, without either having been written to match the other:

| Segment | Behaviour | Mechanism |
| --- | --- | --- |
| AX emission | non-split paths pass no predicate → `None` | `_provider_metadata` defaults |
| HTTP wire | a `None` field is **not transmitted at all** | `response_model_exclude_none=True` on the answers route |
| Braincrew mapper | absent key → `None`; `StrictBool \| None` refuses a coerced `1` | `.get()` with no default |
| Stored artifact | `None` → key omitted | `exclude_if` |

That the wire already drops `None` fields means Braincrew's `exclude_if` is not a local convenience but
the consumer-side half of a convention the subject already keeps. `False` survives explicitly at every
one of the four segments.

## 6. The pin and the packaged contract cannot drift apart

Production code binds `PINNED_AX_SHA` to the packaged `ax-http-v1.yaml` contract. **Measured** by
mutating the pin alone: 164 tests fail, including
`ValueError: configured AX SHA does not match ax-http-v1 contract`. The guard lives in production
source, not in a test, so it holds for any consumer and not merely for the suite.

## 7. A deliberate reduction in independent witnesses, recorded so it is not rediscovered

Five test files that had each carried their own hardcoded SHA literal now import `PINNED_AX_SHA`. This
removes a real property, and the removal is accepted rather than unnoticed.

**Measured by independent review:** moving the pin constant *and* the packaged YAML together to a fake
SHA — the axis a single-constant mutation cannot reach — fails 87 tests, and **none of the five
converted files is among them**. Their literals had been independent witnesses; a value derived from
the code under test cannot contradict it.

What still catches a pin divergence: `test_cli_live_experiment_capture.py` (71 failures),
`test_ax_http_adapter.py` (12), `test_preflight_receipt_binding.py` (3) — all three keeping literals —
and the census `commit_sha` (1). Four witnesses, not seven, and the four cover the widest surface.

The trade bought something real: this re-pin updated five consumers automatically, so a partial re-pin
that leaves some files behind is now structurally impossible. **The next person to move this pin must
know that the four remaining witnesses are load-bearing, and that converting any one of them to a
derived value deletes a witness rather than tidying a duplicate.**

This does not violate Issue #94's `Directive:`, which forbids comparing `PINNED_AX_SHA` and
`REVIEWED_PROVISIONED_AX_SHA` **to each other** to establish validity. No such comparison exists here.
The warrant's import-time construction property that the same `Directive:` requires is preserved —
measured: a warrant with a path outside `backend/src/` takes the suite down at collection with 9 errors.

## 8. Rejected alternatives

| Rejected | Reason |
| --- | --- |
| Default both predicates to `False` | Manufactures a measurement. Asserts of every pre-split discard that it was not a citation-contract violation, which is exactly what is unknown. |
| Make the predicates required | Invalidates every stored record; the published capture stops loading at all. |
| `default=None` without `exclude_if` | Correct in Python, wrong on the wire — emits `null` keys and changes the bytes of published evidence. |
| Bump `under_test_sha` and keep the existing `changed_paths` | Produces a warrant that under-reports the diff it warrants. True-looking and wrong. |
| Re-capture immediately to fill in the unknowns | Costs a provider run, and answers a different question — it reports a *new* run's predicates, not the published run's. The published record stays unknown by construction. |
| Drop the historical `failure_reason` label now that the booleans carry the cause | AX deliberately kept it; changing it here would diverge the instrument from the subject and break stored records. |

## 9. Validation evidence produced

- `ruff format`, `ruff check`, `mypy` clean; **598 tests pass** (baseline 592).
- Published capture manifest replays to
  `sha256:775a85295fb5db2f9cfb6e1aa5504206ea3b629a032452932ca685a7ab1a5049`, 15 grounded / 9 retrieval.
- Published evaluation artifact replays to
  `sha256:9435c9daaa21e4e3129dad997a9dff79717452a2c1f112acfd7a95ba3e80f6fb`, state `INVALID`.
- 15/15 stored `AnswerPathHealth` objects dump byte-identically through the new model.
- `None` / `False` are distinguishable at every layer; `StrictBool` rejects `1`; `extra="forbid"` holds.
- The source-derived emission census pins `service.py` at `972f15c9…`, matching the real AX file at
  `3bb27f8`, and enumerates seven distinct shapes including the three new split states.
- Per-clause mutation: removing the citation mapper line turns the named capture test RED; mutating
  the pin turns 164 tests RED. Both restorations proven byte-identical by SHA-256.
- Independent review reproduced the gates, the three warrant tree SHAs, the `changed_paths` derivation,
  the census source hash and the `schemas/` non-drift to the exact value, ran four further mutations
  (joint pin+YAML move, emptied census shapes, a removed census coordinate, an out-of-tree warrant
  path), and searched every JSON file in the repository for the two new keys — **17 hits, all in the
  census fixture**, none in any published capture or observation fixture.
- One review finding was applied: the new capture test looped over its observations with no count
  assertion and would have passed while asserting nothing had the collection been empty. It now pins
  15, the measured count for that capture, matching the file's own convention — which pins counts in
  nine other places, not the two the review brief claimed.

## 10. Validation evidence still required

**The published capture's twelve unknown discards stay unknown.** This change stops new measurements
from collapsing the two causes; it does not recover which cause fired in a run taken before the split
existed.

Answering that requires a diagnostic re-capture against `3bb27f8` — a live provider run, with cost,
and a hard stop pending explicit owner authorization. Until then, the honest statement is that the
predicates for those records are absent because they were never observed.

**The replay evidence rests on one pane, not two.** The published capture and evaluation artifacts are
deliberately not committed — they are benchmark output under `.gitignore` — and independent review
could not locate them, so it verified the *substance* of the requirement by other means (the
repository-wide JSON search and `exclude_if` round-trip stability) rather than by re-running the
replay. The two digests in the section above were each produced once.

**The census `sha256` is checked against a constant, not against AX.** `AGENTS.md` keeps the two
repositories separate, so no test reads the AX working tree. The census's source hash is therefore only
as accurate as the human re-enumeration that produced it. It was cross-checked by hand this cycle —
`git show 3bb27f8:backend/src/ax_engine/answers/service.py | shasum -a 256` returns `972f15c9…`,
matching — and that check must be repeated by hand at every future re-pin.
