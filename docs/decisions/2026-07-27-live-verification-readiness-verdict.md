# Locked: the v2 preflight readiness verdict, and why it required reversing a decision made the same day

Date: 2026-07-27
Status: locked
Implements: [Issue #80](https://github.com/DHChe/braincrew-datateam-portfolio/issues/80)
Reverses, deliberately: §3/§4 of [`2026-07-27-live-verification-preflight-artifact-v2-contract.md`](./2026-07-27-live-verification-preflight-artifact-v2-contract.md) — specifically its rule that a v2 artifact may not retain blockers

## 1. What was decided — Option A

`live-verification-preflight-artifact-v2` carries
`readiness: Literal["READY", "NOT_READY"] | None`, and **may retain one typed
`LivePreflightBlocker` when the verdict is `NOT_READY`**. Corpus fetch failures become a typed
`LIVE_CORPUS_IDENTITY_FAILED` blocker instead of an escaping `AxTransientFailure`.

The field is **scoped to v2**: any other schema declaring it is refused with
`only live verification schema may declare readiness`.

This closes Issue #38 criteria **4** and **6** *in code*. It does not meet them *in evidence* — see
§7.

## 2. Why a verdict could not simply be added

Issue #38 criterion 6 asks that the artifact "reports `READY`". The obvious implementation —
`readiness: Literal["READY"]` — would have been **a constant, not a judgment.**

Measured before the work started: a v2 artifact could exist **only** on complete success. Every
failure path produced no artifact at all.

| input | before |
| --- | --- |
| unreviewed attachment mapping | no artifact — `ValueError` |
| subject is not the reviewed owner | no artifact — `ValueError` |
| corpus endpoint 503 after all six probes succeeded | no artifact — `AxTransientFailure` |

A `READY` literal on that schema would have been true in every artifact that could ever exist, and
no test could have observed it being false. That is the tautology shape this repository has now
recorded **five** times, every one found by mutation rather than by reading — and the most recent
one was in this same contract, two cycles earlier. Shipping a sixth on purpose was the one outcome
the ticket existed to prevent.

**So criteria 4 and 6 turned out to be one problem.** Criterion 4 wants principal, mapping,
transport, provenance, identity and receipt mismatches to remain *stable typed blockers*; on the v1
contract they were, on the v2 path they were exceptions. A verdict needs something to say when it is
negative, and criterion 4 already named what that something is.

## 3. Rejected alternatives

**B — a separate report layer computing readiness from the artifact.** Rejected: with no artifact
there is nothing to compute from. It leaves "the corpus endpoint was down" surfacing as a bare
traceback at exactly the moment this contract is first pointed at a live runtime.

**C — keep v2 success-only and record that readiness is implicit.** Rejected: it fails criterion 4
outright, and it makes the *absence* of evidence the carrier of meaning. An evidence-first plane
should emit evidence of failure.

**A was chosen** because the machinery already existed — `LivePreflightBlocker`, `_blocked_capture`,
`_classify_parse_failure`, and the partial/pre-probe blocker taxonomy the v1 contract already
validates. The reversal is a **strict narrowing**, not a loosening:

| #77 rule | #80 rule | equivalent when `READY`? |
| --- | --- | --- |
| `if artifact.blockers: raise` | `if readiness == "READY" and artifact.blockers: raise` | yes |
| `if dataset_identity is None: raise` | `if readiness == "READY" and dataset_identity is None: raise` | yes |

A `READY` artifact is still validated by exactly the path #77 locked.

## 4. The reversal was handled as a reversal, not as a bug fix

#77's refusal of retained blockers was **correct for a success-only schema**, was reviewed, and was
observed by a test. Changing it is a decision, not a repair.

The test was **renamed and re-scoped, not deleted** —
`test_live_verification_v2_replay_refuses_retained_blocker` → `..._when_ready`. Deleting a test
whose rule has changed is how a repository loses a protection while its suite stays green; updating
it keeps the protection and records that the rule moved.

The relaxation of `dataset_identity` on the negative side is **compensated, not dropped**. A
`NOT_READY` artifact may omit it because pre-probe blockers fire before dataset identity is
established. Three branches close the gap: the corpus-blocker branch re-requires it; the
principal-blocked-with-identity branch routes to the sibling validator; and the pre-probe branch pins
the blocker to a three-element allow-list of `(code, detail)` pairs. Each is observed by a test.

## 5. A verdict is a claim, so the field must be bound — not just one branch of it

The first implementation put `readiness` on `LivePreflightArtifact`, which serves **three** schema
versions, and validated it only in the v2 branch. Independent review found the consequence: a
**genuinely blocked** `principal-attachment-preflight-evidence-v1` capture — real 404 blocker, zero
probes — with `"readiness": "READY"` inserted and the digest recomputed **replayed clean** and
reported `{"blocker_count": 1, "readiness": "READY"}`.

That is the exact contradiction v2 refuses by name, accepted on its sibling.

The objection "it is only reachable by tampering" does not survive contact with what
`replay_live_preflight_artifact` is *for*. Every refusal in that file is unreachable from a capture
path — that is the point. Replay's job is to refuse an artifact that contradicts itself **regardless
of where it came from**. A new field that escapes that job on two of three schemas is a hole in the
same wall the other twenty-odd clauses make up.

The repository already had the pattern: `capture_contract` is refused on the generic schema with
`generic live preflight schema cannot declare a capture contract`. `readiness` simply had not been
given the same treatment. It has now.

The exposure was also **inverted**, which is worth recording: `cli.py` dispatches only the two v1
schemas into `replay_live_preflight_artifact` and prints the summary wholesale. So the CLI could
print an *unvalidated* verdict and could not print the *validated* one at all. The leak is closed;
the missing v2 CLI surface is carried forward in §8.

## 6. The transferable lesson: a coverage justification can expire

§8 of the #77 decision left six clauses of `_validate_live_verification_corpus_attempts` untested,
and justified it explicitly: *"the validator's **call site** is observed: detaching it turns three
tests red."* That reasoning was sound when written.

This change added a **second** call site — the corpus-blocker path. At that call site, detaching the
validator turned **zero** tests red. The justification did not become wrong through anyone's error;
it silently stopped applying the moment a second caller existed.

Two of the three clauses this re-opened are the ones prior reviews named as headline findings: §4's
rule that a v2 artifact's two halves must sit on one tenant, and §8's privacy clause that a failed
request must not claim a response correlation id. Disabling the corpus-blocker tenant fold left the
suite **fully green at 405 passed**, reproduced independently.

**The rule to carry forward:** when you add a call site to a validator whose test coverage rests on
"the call site is observed," you inherit the obligation to observe the new one. A justification that
names a specific structural fact is only as durable as that fact.

## 7. What this does not prove

**Nothing was captured.** Every result behind this decision — implementer's, reviewer's and
orchestrator's — comes from `httpx.MockTransport`. No AX runtime was started and no live network
call was made.

`braincrew_preflight_ready` stays **`false`**. The preflight can now *report* a verdict; that is not
the same as the verdict having ever been `READY` against a live runtime.

Per §4 of the #77 decision, still in force: a `READY` artifact asserts nothing about `corpus_id`,
`corpus_digest`, `inventory_count` or `counts`. **A `READY` artifact is compatible with an empty
inventory.** That exclusion is deliberate — no frozen expectation exists for runtime-observed values,
and inventing one would convert a measurement into a tautology.

[AX #37](https://github.com/DHChe/AX_portfolio/issues/37) and
[AX #43](https://github.com/DHChe/AX_portfolio/issues/43) remain open formal blockers of Issue #38.
AX #37's own unmet sixth criterion is carried by AX #43, whose blocker list is empty — so the
remaining work there is **operational**, not implementable.

## 8. Carried forward deliberately

- **Nine further clauses on the blocked paths are unobserved** — a pre-probe blocker may not carry
  parse observations, a `case_id`, a `request`, or `attempts`; and the corpus blocker's `operation`,
  single-role and not-after-a-complete-role-set checks. All fire correctly at runtime. Lower severity
  than the three that were fixed, because none is a defence a prior review established. Tracked with
  [#78](https://github.com/DHChe/braincrew-datateam-portfolio/issues/78).
- **The completed-role prefix checks are individually redundant but jointly observed.** Neither
  disjunct is killed alone; the duplicate-role test kills them together. **Not a gap — do not
  "simplify" them away.**
- **v2 has no CLI replay surface.** `cli.py` dispatches only the two v1 schemas. Pre-existing from
  #77. Scoping `readiness` to v2 changed what this costs: the CLI can no longer print an
  *unvalidated* verdict, so what remains is only that the *validated* one is unreachable from the
  CLI. Deciding what the CLI prints for a `NOT_READY` artifact, and whether the exit code differs,
  is a design question that belongs with whoever wires the live capture path.
- **`dataset_identity` has the same shape the readiness leak had, at lower stakes.** It is
  constrained on the principal-attachment schema (must be non-`None`) and on v2 (must be non-`None`
  when `READY`), but is **unconstrained on the generic `live-preflight-evidence-v1` schema** — a
  generic artifact carrying a real frozen dataset identity replays clean. Found by review checking
  the neighbours rather than leaving the question open once the readiness leak was closed. Lower
  stakes because `DatasetIdentityEvidence` self-validates against the frozen digests, so it cannot
  assert an arbitrary dataset, and because it is *evidence* rather than a *verdict* — it claims
  nothing about readiness. Present at `87c0fc4` and before. Recorded so it is a **known** choice
  rather than an unexamined one.
- **Canonical documents are load-bearing for two test files.**
  `tests/contract/test_successor_dataset_freeze.py` and
  `tests/acceptance/test_corpus_provisioning_workflow_order.py` assert that the canonical design,
  issue-draft, review, and status documents contain specific strings. Additive edits are
  safe; a future **rewrite** of one of them can turn the suite red from a documentation change
  alone. Worth knowing before anyone reorganizes them.
