# Locked: the `live-verification-preflight-artifact-v2` contract

Date: 2026-07-27
Status: locked
Implements: [Issue #77](https://github.com/DHChe/braincrew-datateam-portfolio/issues/77)
Follows: [`2026-07-27-dataset-identity-axis-analysis.md`](./2026-07-27-dataset-identity-axis-analysis.md) §18 (Option C), implemented by Issue #75 as `d429cb1`

## 1. What was decided

`live-verification-preflight-artifact-v2` is a **third schema** alongside
`live-preflight-evidence-v1` and `principal-attachment-preflight-evidence-v1`. It carries, in one
create-only artifact:

- the frozen integrated **v3** dataset identity,
- **three** role-visible corpus identity observations — `Employee`, `Executive`, `HRPractitioner`,
- the **six** reviewed parsing probe observations,

and cross-checks that every role's `contributing_versions` contains the qualified base contribution
named by `corpus_qualification.SEED_VERSION`.

This satisfies the sixth acceptance criterion of
[Issue #38](https://github.com/DHChe/braincrew-datateam-portfolio/issues/38) **in shape**. It
satisfies nothing about readiness — see §7.

## 2. The problem was not the model

`LivePreflightArtifact` already carried `dataset_identity`, `corpus_observations` and
`parse_observations` on one shared model, and the generic schema branch forbade neither. It could
structurally hold all three before this change.

What did not exist was anything that **produced** the combination. Measured on `d429cb1`:

| Fact | Value |
| --- | --- |
| `grep -rn "live-verification-preflight-artifact-v2" src/ tests/` | 0 matches |
| callers of `AxHttpAdapter.corpus_identity()` in `src/` | **0** — three test files only |
| the principal-attachment contract | rejected corpus observations at `live_preflight.py:703` |

So the work was a **capture path and an artifact contract**, and only then the cross-check. Framing
it as "add a cross-check" understates it by an order of magnitude, and that framing was rejected in
the ticket before implementation started.

## 3. Third schema, not subsumption

**Decided:** v2 is a third schema. The principal-attachment contract is **not** subsumed and its
refusal of corpus observations is preserved verbatim.

**Rejected — subsume the principal-attachment contract into v2.** Its narrowness is itself
load-bearing evidence: it exists to say *this capture is only the six probes, by the reviewed
subject, and nothing else*. Folding it into a contract that legitimately carries corpus observations
would put every one of its thirteen refusals up for re-derivation inside a single change, which is
the shape of change that loses a protection without anyone noticing.

**How the strictness is reused without relaxing it.** The v2 validator hands a corpus-stripped copy
to the sibling:

```python
principal_evidence = artifact.model_copy(update={"corpus_observations": ()})
_validate_principal_attachment_capture(principal_evidence, reviewed_binding=..., tenant_ids=...)
```

`model_copy` does not re-run validators, so there is no recursion, and the sibling's refusal is
untouched on its own contract. Independent review verified all thirteen pre-existing refusals still
fire **on the v2 path**.

## 4. One artifact means one principal, across both halves

The first implementation bound the six parse probes to one tenant and one reviewed subject and left
the three corpus observations bound to **nothing**. Reproduced: mutating a parse observation's
tenant was refused; moving **all three** corpus observations to a different tenant *and* a different
subject was **accepted**, and replayed clean. A corpus observation with **zero HTTP attempts** was
also accepted — asserting a role-visible corpus identity with no evidence any request was issued.

**Decided:** the corpus half is validated by `_validate_live_verification_corpus_request` mirroring
`_validate_principal_parse_request`, and the corpus tenants are folded into the **same**
`tenant_ids` set the parse half already builds, so the single-tenant rule spans both halves.

The threading is safe in one direction only, which is why it was chosen: the rule is
`len(tenant_ids) != 1` and threading can only **add** elements, so a shared set can raise the count
but never lower it. Sharing can tighten; it cannot mask.

**Deliberately not added:** any expected value for `response.corpus_id`, `corpus_digest`,
`inventory_count` or `counts`. No frozen expectation for them exists in this repository — they are
genuinely runtime-observed. Two canary mutations confirm the line held: a response naming a
different tenant's corpus and a response reporting an empty inventory are both still **accepted**.
Pinning them would have been an invented expectation, not a check.

Consequence, recorded because it will look like a gap later: a v2 artifact whose **both** halves sit
consistently on some other canonical tenant validates. That is correct. The rule is *agreement
between the halves*; there is no frozen tenant value to pin against.

## 5. The timeout is pinned to a neutral constant, not to a coincidence

The corpus adapter originally omitted `timeout_seconds` and inherited `AxHttpAdapterConfig`'s
default of `10.0`, which happened to equal `PRINCIPAL_PARSE_TIMEOUT_SECONDS`. Two halves agreeing by
coincidence is not a contract: the day that default changes, the corpus half drifts silently while
the parse half stays pinned.

**Decided:** `LIVE_PREFLIGHT_REQUEST_TIMEOUT_SECONDS = 10.0` is the neutral authority;
`PRINCIPAL_PARSE_TIMEOUT_SECONDS` is defined as it; **both** call sites pass it explicitly. The old
name survives as an alias so the parse validator's error text needs no rename churn.

## 6. What the review process itself established

Two findings are worth keeping because they are about method, not about this contract.

**A load-bearing line with no test above it is invisible to a green suite.** The five-line reuse in
§3 held the reviewed-subject binding, the single-tenant rule, the frozen timeout, probe-set
completeness, and the parse-evidence, span and attempt checks for the **entire** v2 contract.
Deleting it left the suite at `370 passed`. It was found by disabling the line, not by reading it —
the fifth time this repository has recorded that shape. It is now observed by
`test_live_verification_v2_replay_keeps_principal_parse_validation`, a v2 artifact whose parse
observation carries a foreign `user_id`.

**A claim in our own ticket was false and was caught by review.** The ticket asserted the
corpus-observation refusal "is currently observed by tests." It had **zero** coverage at `d429cb1` —
one `git grep` hit, in `src/` only. The instruction it supported was right and was followed; only
the supporting claim was wrong. The correction is a comment on Issue #77 and the body is preserved,
so the error stays visible. The implementation's new test is the first that has ever observed that
refusal.

## 7. What this does not prove

`braincrew_preflight_ready` stays **`false`**, and completing this work does not earn it.

Every result behind this contract comes from `httpx.MockTransport`. **Nothing was captured.** No AX
runtime was started and no live network call was made. This builds an artifact *shape* and proves it
against controlled transports; a live AX runtime answering real parse probes remains unmet and needs
a **separately authorized runtime start**, stopped since Stage 12.

[AX #37](https://github.com/DHChe/AX_portfolio/issues/37) remains an open formal blocker of Issue
#38, as does the linked [AX #43](https://github.com/DHChe/AX_portfolio/issues/43). Issue #38 cannot
close on code alone.

## 8. Known gaps, carried forward deliberately

Six reachable clauses inside `_validate_live_verification_corpus_attempts` have no test. **Five of
the six mirror an identical pre-existing gap in the parse-side sibling** — measured, not assumed —
so the repair matched the standard the sibling already sets rather than falling below it. **One does
fall below it:** the corpus half omits the only attempt-level clause the parse half demonstrably
tests, and that clause is the privacy one — a failed request must not claim a response correlation
id. The parse side has `test_request_error_attempt_cannot_claim_a_response_correlation` for exactly
that threat.

These do not block, because the validator's **call site** is observed: detaching it turns three
tests red. It can be weakened from inside, which is narrower and more visible than the §6 failure,
where the whole reuse could vanish silently.

Also carried forward: the principal partial-capture single-tenant rule has no test — pre-existing,
but this change altered where its variable comes from, so it is now worth one it never had. And a
corpus fetch failure escapes as an untyped adapter exception rather than a typed blocker; this is
fail-closed today, but when this contract is pointed at a live runtime, "the corpus endpoint was
down" will surface as a bare traceback rather than a typed operational outcome.

Tracked as a follow-up ticket covering **both halves**, because fixing the corpus side alone would
leave the asymmetry it was measured against.
