# Locked: parsing refuses a drifted observation, and the evaluator is versioned so existing evidence still replays

Date: 2026-08-01
Status: locked
Implements: [Issue #118](https://github.com/DHChe/braincrew-datateam-portfolio/issues/118)
Owner decision recorded here: parsing must refuse an observation made against a different document
rather than scoring it zero; and the refusal is introduced as a new evaluator version so that
already-published artifacts continue to replay

## 1. Measured defect

Parsing was the only one of three evaluator families with **no version-drift detector**.

| Family | Detector | Behaviour on drifted input |
| --- | --- | --- |
| retrieval | `observation.query != case.query` → `RETRIEVAL_QUERY_MISMATCH` | `INVALID` |
| grounded | `SYS-GROUNDED-ROLE-MISMATCH` | `INVALID` |
| **parsing** | **none** | **`COMPLETED`, cases `SCORED 0.0000`, `invalid_reasons: []`** |

`evaluate_parsing_case` had exactly one `INVALID` path — `parse_available` being false, a refusal the
**SUT self-reports**. There was no evaluator-side integrity check at all.

**This was not theoretical. It is in a published artifact.** The 2026-07-31 live evaluation reports a
parsing aggregate of `0.0000` on all three metrics with every case `SCORED`. The number reads as a
measurement and is not one.

**The control that settles causation.** Running the v1 manifest against the v1 observations — the same
observations, the same evaluator, the correct dataset version — produces `1.0000` on all five parsing
metrics with 20 × `SCORED`. The zeros come from version mismatch and nothing else. That control was
proposed and run by independent review; pane 1 had not thought to run it.

## 2. Why this is an evaluator defect and not a dataset problem

The shared precondition is the `v1 → v2` rewrite, which preserved case identifiers while replacing
documents and queries: `parsing-015`'s document is `synthetic-rule-015` in v1 and
`demo-terms-guide-002` in v2; **30 of 30** retrieval queries and **50 of 50** grounded queries differ.

**That rewrite is deliberate, reviewed and locked** — v2 rebinds evidence to an independently authored
corpus — and it was **already documented** on 2026-07-27 in
[the dataset identity axis analysis](2026-07-27-dataset-identity-axis-analysis.md), which records that
the two parsing files reuse `parsing-015`–`parsing-020` with different `document.id` values and states
that *"the document IDs, source text, and digests are the load-bearing identity, not the outer case
IDs."*

So: **one shared precondition, three behaviours, one defect.** Two families already refuse. The fix
belongs in the third, not in the dataset. pane 1's first framing called the rewrite "the root cause",
which would have pointed the ticket at the dataset; independent review corrected it.

## 3. Decision

- **`parsing-quality-v2`** is the evaluator version for every **fresh** evaluation.
- Under v2, an available parsing observation that **claims at least one evidence span** and whose
  span `source_text_digest` values have **no overlap** with the case's expected spans is refused with
  `PARSE_OBSERVATION_DOCUMENT_IDENTITY_MISMATCH`, and no metric is computed.
- **`parsing-quality-v1` is reachable only from stored provenance**, on the replay paths in
  `replay_dataset_run_artifact` and `replay_run_artifact`. No fresh route can select it.

## 4. Why the predicate is document digest, and not span identity

The first implementation keyed on the tuple `(span.id, span.source_text_digest)`. Two review rounds
removed two distinct misdiagnoses from it, and the second changed the predicate's basis.

**`source_text_digest` is a document-level value.** Every expected span of a case carries the same
digest — `parsing-006`'s two spans both carry `sha256:1132d6c8…`. It *is* the document identity.
Keying it as half a tuple with the span `id` discarded that identity and substituted something that
was never a document signal.

Measured consequence, before the change: an observation carrying the **correct** document digest with
a SUT-assigned span id was refused as a document-identity mismatch — a cause its own evidence
contradicts. That shape is not hypothetical for long: `live_preflight.py:789` copies `id=span.id`
straight from AX's parse response, so span ids are SUT-assigned on the live path. When the live
parsing-observation bridge is built, AX-assigned ids would have collided with dataset-authored
expected ids and **every case would have been refused even when AX read the correct document.**

Digest-only overlap was measured to refuse all six published drift cases identically — zero overlap
under both predicates — so no detection was traded away.

## 5. What this does NOT do

**The published 2026-07-31 artifact still recomputes six `SCORED 0.0000` parsing cases**, under its
stored `parsing-quality-v1` dispatch. That is correct and deliberate: it is what preserving
replayability means. This work stops **new** evaluations from producing a false zero; it does **not**
remove the false zero from published evidence.

Any later record that says the published zero was fixed is wrong.

## 6. The bound that remains

**One overlapping document digest is sufficient to pass.** A document partially rewritten while
retaining one expected span's source text is not detected. The guard detects total document-identity
drift, not partial rewriting. Recorded rather than chased: widening the predicate to catch it would
reintroduce the class of misdiagnosis this decision spent two review rounds removing.

A second bound of the same family, measured by review: **7 digests are shared across cases** in the v2
parsing bundle, so a document-level predicate cannot distinguish two cases drawing on the same
document. Not reachable through the run path, which matches observations to cases by `case_id`, but
real, and stated here rather than discovered later.

## 7. Rejected alternatives

**Accept supersession — fix the evaluator and let the published artifact stop replaying.** Rejected by
the owner: in a repository whose value is evidentiary integrity, losing the verifiability of existing
evidence in order to fix a defect is the wrong trade.

**Keep a dataset-version-keyed selector so fresh runs on older manifests use v1.** Rejected. The
justification for keeping v1 reachable was replay, and replay is served independently by the
stored-version dispatch — proved by mutation, since hard-coding v2 there breaks the published
artifact. The selector therefore served only fresh runs, and independent review demonstrated it by
emitting a **fresh** `COMPLETED` artifact with 20 × `SCORED` and aggregate `0.0000` — the defect,
still producible. It was deleted, not bypassed.

**Refuse whenever no expected span is recovered.** Rejected: an observation that claims no spans has
recovered nothing *and that is a measurement* — `evidence_span_recovery = 0/N` is what the metric is
for. Review found the first implementation refused exactly that case, and named the same defect class
this project filed against its own SUT as [AX#60](https://github.com/DHChe/AX_portfolio/issues/60):
one reason code covering two unrelated causes.

**Author v2-consistent observations so the current dataset has an offline run.** Rejected as out of
scope, and separately shown unreachable: `build_dataset_run_artifact`'s live-provenance check
(`dataset_run.py:317`) requires a live run's `evaluation_plane_sha` to equal the current commit, and the only live capture pins `f9d9cfd`, so the
v3 Verification artifact cannot be rebuilt at `HEAD` by anyone.

## 8. Validation evidence produced

Implemented across cycles 152, 154 and 156, with independent review at 153 and a scoped re-review at
155. Review returned **REQUEST CHANGES** once, on two findings, and **APPROVE** after the repair.

**What review found that implementation and orchestration had not:** that the guard refused a
legitimate zero-recovery observation of the correct document; that fresh runs on two of the three
committed manifests had no guard at all, demonstrated by producing a fresh false-zero artifact; and
that the predicate misdiagnosed a correct document carrying a SUT-assigned span id.

**Measured by pane 1 directly, on the final tree:** an observation with the correct document digest
and a SUT-assigned span id **scores** `0.0000` with structure and metadata retained; a zero-recovery
observation of the correct document **scores**; an observation with a different document digest is
**refused**; the v3 × v1 probe refuses all cases with aggregate `None`; the legitimate v1 path is
`COMPLETED` with all five metrics `1.0000`; and both real artifacts still replay —
`sha256:9435c9da…` for the evaluation artifact and `sha256:775a8529…` for the capture manifest,
Issue #106's acceptance criterion, which must not regress and did not.

Gates reproduced solo by pane 1: Ruff format and check, mypy, **589 pytest tests**, `git diff --check`,
`git status --short schemas/` empty.

Mutation verification ran one clause at a time with each restore proved by SHA-256; review checked
every label against `d6b98ec` byte-identity and found each correct.

## 9. Validation evidence still required

No AX runtime was started and none was needed. No live parsing observation exists anywhere in this
repository, so the guard has never run against a real AX parse response — the shape §4 protects
against is anticipated, not observed. Nothing here bears on the AX answer path or the twelve
unscoreable grounded cases, and no candidate run exists, so there is still no comparison, no gate
decision and no answer-quality claim.
