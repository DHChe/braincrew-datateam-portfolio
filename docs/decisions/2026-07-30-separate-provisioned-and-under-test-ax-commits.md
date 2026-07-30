# Separate the AX commit under test from the commit that produced the reviewed receipt

Date: 2026-07-30  
Status: IMPLEMENTED; INDEPENDENT REVIEW PENDING  
Implements: [Issue #94](https://github.com/DHChe/braincrew-datateam-portfolio/issues/94)  
Supersedes in part:
[the receipt-derived binding decision](./2026-07-26-preflight-receipt-derived-binding.md)
and
[the AX SUT review](./2026-07-26-ax-sut-commit-for-evaluation-review.md)

This record supersedes exactly two operative values while preserving the historical records:

- `REVIEWED_PROVISIONED_AX_SHA` remains
  `2bcaee3495fd7b3f624398819575cd86a5a15c47`, the AX commit that produced the
  byte-digest-pinned handoff receipt;
- `PINNED_AX_SHA` becomes
  `1ead1331166538e417027a7064179f15c5cfbf61`, the AX commit under test.

`REVIEWED_HANDOFF_RECEIPT_SHA256`, the receipt bytes, and the frozen dataset do not change.

## 1. Decision

The two commit meanings are separate code contracts. A reviewed receipt is accepted against the
current SUT only under one of two explicit reasons:

1. the receipt's reviewed provisioning commit and the under-test commit are identical; or
2. a code-pinned `ReceiptSutContinuityWarrant` binds the exact divergent commits and carries the
   measured result of the review that established provisioning continuity.

The current warrant records:

- method: `reviewed-ax-source-diff`;
- provisioned-at commit: `2bcaee3495fd7b3f624398819575cd86a5a15c47`;
- last commit with an identical `backend/src` tree:
  `d7930978d7b0cb41668a86acd9fe77c16068801d`;
- identical tree hash at those two commits:
  `846c06ba9461c97a75b16caf7b85570e0c0f14fd`;
- under-test commit: `1ead1331166538e417027a7064179f15c5cfbf61`;
- the only changed AX source path after the last equivalent commit:
  `backend/src/ax_engine/answers/service.py`;
- reviewed conclusion: the change does not affect the provisioned corpus, principal, attachment
  mapping, or other receipt-bound state.

The relation is enforced, not documented only. If either code constant moves without a new warrant
that names the exact new pair, preflight refuses with
`reviewed provisioning continuity warrant does not bind the current AX commits`.

## 2. Why this is a warrant

The live preflight can verify the receipt bytes and the receipt's recorded commit. It cannot inspect
the AX Git history or reconstruct whether a later code change affected the state described by an
already-produced receipt. Treating that conclusion as observable at preflight time would manufacture
evidence.

The established `SutStateWarrant` rule therefore applies: when a required fact cannot be observed at
check time, carry the method, subject, and returned values, then test that those values are what the
check returned. Here the warrant is code-pinned rather than operator-supplied because it represents a
review decision that must change only with a reviewed re-pin.

The acceptance contract asserts the complete warrant payload, not only a success path. That prevents
the method name from becoming decorative while its measured outputs drift.

## 3. Why the receipt remains valid

Three measurements establish the narrow continuity claim:

1. `git rev-parse 2bcaee3:backend/src` and
   `git rev-parse d793097:backend/src` both return
   `846c06ba9461c97a75b16caf7b85570e0c0f14fd`;
2. `git diff --stat 2bcaee3..1ead133 -- backend/src` reports one file, `+22/-2`;
3. the only path is `backend/src/ax_engine/answers/service.py`, and the diff adds abstention debug
   evidence without changing provisioning, receipt production, corpus rows, principals, or
   attachments.

This is a bounded statement about the existing receipt's continued applicability. It is not a
general rule that answer-service changes never affect evaluation behaviour; the answer-service
change is precisely why `1ead133` is the new commit under test.

## 4. Distinct refusal conditions

The former message, `reviewed handoff receipt was produced from an unreviewed AX commit`, conflated
two conditions and became false when the commits legitimately diverged. The implementation now
distinguishes:

| Condition | Refusal |
| --- | --- |
| receipt commit is not `REVIEWED_PROVISIONED_AX_SHA` | `reviewed handoff receipt commit does not match the reviewed provisioning commit` |
| preflight artifact SUT SHA is not `PINNED_AX_SHA` | `live preflight artifact SUT commit does not match the under-test AX commit` |
| live capture SUT warrant SHA is not `PINNED_AX_SHA` | `live capture SUT commit does not match the under-test AX commit` |
| the two reviewed commits differ without an exact current warrant | `reviewed provisioning continuity warrant does not bind the current AX commits` |

Every condition remains fail-closed. None degrades to a warning or a fallback.

## 5. Rejected alternatives

**Accept `{2bcaee3, 1ead133}` as a set.** Rejected. A set says which values pass but not why the old
receipt remains valid. It would make the next re-pin a mechanical append and convert a reviewed
relation into a growing allow-list.

**Rename two constants and leave their relation unenforced.** Rejected. That removes the misleading
name while preserving the defect: a future pin change would not require anyone to establish receipt
continuity.

**Derive validity from receipt-carried corpus and attachment digests.** Rejected for the current
receipt contract. Issue #94 says the receipt already carries those digests, but
`_ReviewedHandoffReceipt` parses only repository commit, target identity, completion state, and the
case-to-attachment mapping with `extra="ignore"`. The real receipt is an external runtime input and
was not inspected for this implementation. Depending on unparsed, unverified fields would replace a
known conflation with an unverified assumption. The byte-digest pin remains untouched.
The 2026-07-26 receipt-derived-binding decision §8 does record documentary support for part of the
premise: the reviewed receipt carried `bundle.manifest_digest` and its own `logical_digest`. It does
not record the ticket's claimed attachment digests, and neither recorded digest is parsed or
validated as continuity evidence by the current consumer.

**Require ancestry only.** Rejected. An ancestor relation is checkable but says nothing about
whether descendant commits changed provisioning or the receipt-bound state.

**Regenerate provisioning or the receipt at `1ead133`.** Rejected. The existing receipt remains
valid; regeneration is outside Issue #94, would discard useful provenance, and conflicts with the
create-only receipt and prior rerun-trap decisions.

## 6. Trade-offs

The Evaluation Plane now carries one more reviewed AX identity and a fixed evidence record in code.
Every future SUT re-pin that diverges from the provisioning commit must re-measure the relation and
replace the warrant. This maintenance cost is intentional: a re-pin should not silently inherit a
receipt-validity conclusion.

The warrant is an attestation, not runtime proof. Its strength comes from exact recorded outputs,
independent review, fail-closed binding to both constants, and mutation-tested guards. It does not
bind an arbitrary `--sut-checkout` directory to the server that answers; that existing
`SutStateWarrant` limit remains separate.

## 7. Failure modes

- A fabricated receipt from an unrelated commit must fail before HTTP.
- Changing only `PINNED_AX_SHA` must fail until a new exact continuity warrant is reviewed.
- Changing only `REVIEWED_PROVISIONED_AX_SHA` must fail until the receipt and warrant agree.
- Deleting the receipt byte-digest check would recreate the prior tautology; this change does not
  touch that check or its tests.
- Recording only `provisioning_state_affected=False` would be an unsupported boolean. The warrant
  therefore also records the comparison method, subject commits, tree outputs, and changed path.
- The Issue #94 digest premise may become true in a future receipt schema. That would justify a new
  decision and migration; it does not retroactively make ignored fields an authority here.

## 8. Validation evidence

The cycle 115 implementer reported observing these TDD-red states before implementation. No durable
raw output was preserved, so this is process history rather than independently reproducible
evidence:

- the reviewed `2bcaee3` receipt had no acceptance-reason binding;
- the unrelated-receipt test saw the former misleading message;
- changing the under-test pin did not make live capture refuse the old commit.

After implementation, six isolated mutations each made its named test fail and returned green after
restoration:

- neutralizing the reviewed provisioning-commit condition;
- neutralizing the exact warrant-to-current-pin condition;
- neutralizing the preflight artifact's under-test pin condition;
- neutralizing the live-capture under-test pin condition;
- replacing the required continuity acceptance reason with the same-commit reason;
- replacing the measured changed path carried by the warrant.

Cycle 117 then added direct invalid-construction tests for all six clauses in
`ReceiptSutCommitBinding.require_reason_for_divergence` and
`ReceiptSutContinuityWarrant.require_measured_continuity`. Nine isolated branch mutations made
their exact parameter cases red and restored green, including separate mutations for both sides of
each disjunction.

Cycle 119 added loader-level acceptance coverage for the future same-reviewed-commit path. The
test re-pins the under-test constant to the reviewed provisioning commit and asserts both the
`same-reviewed-commit` reason and the absence of a continuity warrant. Isolated production-branch
mutations made each half red separately and restored the source byte-identically.

The full gates passed: Ruff format and lint over 70 files, mypy over 70 source files,
`521 passed` in pytest, Prettier, ESLint, TypeScript, 7 Vitest tests, the static Next.js build,
2 Playwright tests, and `git diff --check`. Independent pane 3 review remains required before
integration.

No AX runtime, Docker service, or live endpoint was used. No experiment ran and no answer-quality
claim is made.

## 9. Likely follow-up questions

**"Why not store the warrant in the artifact?"** The artifact cannot independently observe or
recompute the Git review. The warrant is a code-side acceptance decision used before the artifact can
exist. Persisting another copy in every artifact would add bytes without adding corroboration; the
exact Evaluation Plane commit already identifies the code-side warrant applied.

**"Is `provisioning_state_affected=False` just another typed assertion?"** By itself, yes. It is
accepted only together with the method and exact measured outputs, and the test pins the complete
payload. This follows D16's lesson that naming a method without pinning its result is worse than a
bare boolean.

**"Why does `backend/src` equality stop at `d793097` rather than the new pin?"** Because AX #58
intentionally changes `answers/service.py`. The equality proves the receipt baseline stayed
source-identical through the last pre-observability commit; the single subsequent path is then
reviewed for provisioning impact rather than falsely claimed byte-identical.

**"Does accepting the receipt prove the new SUT behaves the same?"** No. It proves only that the
receipt-bound provisioning state remains applicable. `1ead133` is deliberately a different SUT
commit and must be evaluated as such.

**"Can this warrant schema express every legitimate future re-pin?"** No, deliberately.
`receipt-sut-continuity-warrant-v1` requires at least one changed path, requires every path to be
under `backend/src/`, and permits only `reviewed-ax-source-diff` as its method. A future legitimate
re-pin with a byte-identical `backend/src`, or with a differently shaped review method, cannot be
represented and therefore fails closed. That new divergence shape should receive a reviewed schema
version rather than speculative widening now.
