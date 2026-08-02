# Locked: AX pin `5b0f5f2` has a newly argued continuity warrant, not a transplanted conclusion

Date: 2026-08-02

Status: locked

Implements: [Issue #134](https://github.com/DHChe/braincrew-datateam-portfolio/issues/134)

## 1. The decision

The under-test AX commit moves from `3bb27f8` to
`5b0f5f2ae2cfb4c4870a2228f9aa226e009241f5`. `PINNED_AX_SHA` and the packaged
`ax-http-v1.yaml` `sut_commit_sha` move together. The reviewed provisioning receipt remains bound to
`2bcaee3495fd7b3f624398819575cd86a5a15c47`; it is not regenerated and no AX runtime state is changed.

The continuity warrant is re-derived from the complete production-source range
`d7930978d7b0cb41668a86acd9fe77c16068801d` to `5b0f5f2`, rather than carrying forward the prior
two-path conclusion.

## 2. Re-measured source identity and scope

| Field | Measured value | Derivation |
| --- | --- | --- |
| provisioned source tree | `846c06ba9461c97a75b16caf7b85570e0c0f14fd` | `git rev-parse 2bcaee3…:backend/src` |
| last-equivalent source tree | `846c06ba9461c97a75b16caf7b85570e0c0f14fd` | `git rev-parse d7930978…:backend/src` |
| under-test source tree | `3dbd5b8bdec742f29ec1e6e5550c3f0b320ea899` | `git rev-parse 5b0f5f2…:backend/src` |
| changed production paths | `answers/contracts.py`, `answers/service.py`, `attachments/jobs.py` | `git diff --name-only d7930978… 5b0f5f2 -- backend/src` |

The full range also changes three AX test paths: `backend/tests/integration/test_evaluation_api.py`,
`backend/tests/unit/test_answer_runtime.py`, and `backend/tests/unit/test_attachment_jobs.py`. They are
excluded from `changed_paths`, which is a statement about the changed production source rather than a
claim that no tests were changed.

## 3. The `jobs.py` argument, made from the new diff

The new production path is close to attachment provisioning, so the old warrant cannot answer for it.
The complete `jobs.py` diff adds only this extraction function and one field in the creation branch:

```python
def _headings_from_text(text: str) -> list[str]:
    headings: list[str] = []
    for line in text.splitlines():
        first_non_whitespace = line.lstrip()
        if not first_non_whitespace.startswith("#"):
            continue
        if first_non_whitespace.startswith("##"):
            headings.append(line)
            continue
        headings.append(first_non_whitespace[1:].strip())
    return headings

if extraction is None:
    extraction = AttachmentExtraction(
        # existing identity, parser, text, and hash fields omitted here
        page_or_section_map={
            "text_truncated": parsed.text_truncated,
            "headings": _headings_from_text(parsed.text),
        },
    )
    session.add(extraction)
```

The function is a pure projection of `parsed.text`. The state write is guarded by `if extraction is
None`; the adjacent code does not update a present extraction. The range has no migration, seed,
approval, materialization, corpus, principal, or receipt-production change, and the changed AX unit test
confirms that the new value is a parse-time `AttachmentExtraction` fact.

This earns a deliberately narrow conclusion: `provisioning_state_affected=False` means this range does
not alter the receipt-backed provisioning state that already exists. It does **not** mean a new attachment
parsed at `5b0f5f2` has the same map as one parsed before it; it intentionally gains headings. AX's own
commit rejects a backfill or re-extract of existing rows, and the creation guard makes that boundary
concrete.

## 4. The resulting warrant and binding contract

`REVIEWED_PROVISIONING_CONTINUITY_WARRANT` retains the matched provisioned and last-equivalent tree
hashes, binds the new full under-test SHA, and names these paths in diff order:

```text
backend/src/ax_engine/answers/contracts.py
backend/src/ax_engine/answers/service.py
backend/src/ax_engine/attachments/jobs.py
```

The packaged contract moves with `PINNED_AX_SHA`; the production `AxHttpAdapter` constructor rejects a
different configured and packaged SHA. The five independent test witnesses remain literals and are updated
by hand. They must not import `PINNED_AX_SHA`, because then a wrong pin can move both the code under test
and its asserted value together.

## 5. Answer-path census re-enumeration

`backend/src/ax_engine/answers/service.py` has SHA-256
`972f15c9d68da856c163d830fdef849d915d05bb08f83dd642bade37a20cd47d` at both `3bb27f8` and `5b0f5f2`.
It was nevertheless re-read at `5b0f5f2`: metadata construction remains at lines 235, 561, 617, and 698;
template-result calls remain at 75, 91, 115, 161, and 203. The census fixture therefore preserves its
shapes and source SHA-256, but records the new commit and `enumerated_at: 2026-08-02`.

This is a hand control. The repository's tests compare the census hash to a committed constant; they do
not read the AX checkout, so identical bytes cannot substitute for a fresh commit-identity enumeration.

## 6. Historical boundaries

The 2026-08-01 decision, its four-witness statement, dossier D28, and every existing Transition-history
entry remain records of their dates. The fifth literal witness was added by #131 after the previous
decision; it is counted in this move without rewriting the earlier record. No `evidence/` file, AX
checkout file, attachment, provider result, live capture, comparison, or container state is changed.

## 7. Rejected alternatives

| Rejected | Reason |
| --- | --- |
| Change only `under_test_sha` | It would claim a two-path diff where the new diff has three production paths. |
| Treat attachment proximity as automatic refusal | The actual diff shows a new fact for only new extractions, with no backfill or provisioning-state rewrite; refusal would discard a supported bounded conclusion. |
| Treat the new map as proof all future or past extractions are equivalent | Future new extractions intentionally differ, and existing ones remain untouched. The warrant makes neither wider claim. |
| Include AX test paths in `changed_paths` | That weakens a production-source attestation by mixing it with its tests. |
| Convert literal witnesses to imports | It removes independent detection of a bad pin move. |
| Rewrite historical documents to say five witnesses | It falsifies records that were accurate on 2026-08-01. |

## 8. Validation evidence

- `uv run ruff format --check .`: `72 files already formatted`.
- `uv run ruff check .`: `All checks passed!`.
- `uv run mypy`: `Success: no issues found in 72 source files`.
- `uv run pytest -q`: `608 passed in 40.57s`.
- `uv run pytest tests/acceptance/test_cli_fixture_gate.py -q`: `11 passed in 3.04s`.
- Mutating only `PINNED_AX_SHA` to the old commit while YAML remained at `5b0f5f2` made the full suite
  `171 failed, 437 passed`. A direct `AxHttpAdapter` construction then raised the production error
  `configured AX SHA does not match ax-http-v1 contract`. Restoring `live_preflight.py` reproduced
  SHA-256 `d0af2fd177b71990a837c23bd7c334276bcf33496176f10cf02fbcd6478fb4e5`.
- Mutating only `changed_paths` back to the old two-path tuple while keeping the new `under_test_sha`
  made `test_reviewed_provisioning_receipt_is_accepted_for_newer_sut_for_warranted_reason` fail with the
  missing `attachments/jobs.py` difference: `1 failed, 607 passed`. Restoration reproduced the same
  SHA-256. This is stronger than the brief's conditional no-failure branch, but it is a test of the
  committed expected warrant payload, not an automatic AX-git-diff validator.

## 9. Remaining limits

The warrant is a source-diff attestation, not proof that a running server corresponds to the AX checkout.
It does not create the six required v3 attachments, capture parser observations, or turn an existing
`INVALID` evaluation into a quality claim. The census re-enumeration cannot prove a future AX commit was
reviewed; every subsequent re-pin needs a new diff inspection and hand check.

## 10. A failed continuity warrant is represented by its absence

`ReceiptSutContinuityWarrant.provisioning_state_affected` is deliberately
`Literal[False]`, not a Boolean status field. Reconstructing the current warrant with
`provisioning_state_affected=True` fails Pydantic validation with
`literal_error: Input should be False`. The model can express only a measured positive attestation:
that the reviewed range does not affect the receipt-backed provisioning state.

If a future re-pin cannot establish that argument, it must report the failed argument outside this
attestation and omit the warrant entirely. For divergent receipt and under-test commits,
`ReceiptSutCommitBinding` accepts no such absence: it requires a reviewed continuity warrant. An
attestation that says “no” is therefore an absent attestation, not an attestation widened to carry an
unreviewed negative value. The warrant is constructed at module import; attempting to encode the
unsupported `True` value stops collection with the validation error rather than letting an unreviewed
divergence proceed.

This is deliberate fail-closed design, not a missing reporting channel. Commit `3822daf` directs future
modifiers never to widen the warrant to accept a divergence shape it has not reviewed and to keep
import-time validator failures. Widening `Literal[False]` to `bool` “to allow reporting” would make a
negative claim look structurally accepted by the same warrant that is supposed to be absent; it is the
forbidden relaxation. A failed review belongs in the ticket/report and leaves no usable continuity
warrant in the data model.

## 11. The two answer paths carry forward identical reviewed bytes

This distinction was re-measured against the immediately previous reviewed pin:

```text
$ git diff --name-only 3bb27f8 5b0f5f2
backend/src/ax_engine/attachments/jobs.py
backend/tests/integration/test_evaluation_api.py
backend/tests/unit/test_attachment_jobs.py
```

The range has one production delta, `attachments/jobs.py`. In addition,
`git diff --exit-code 3bb27f8 5b0f5f2 -- backend/src/ax_engine/answers/contracts.py
backend/src/ax_engine/answers/service.py` exits zero: both answer paths are byte-identical at the two
commits. Their inclusion in `changed_paths` therefore carries forward a review of the same bytes; it
does not transplant a conclusion across an unreviewed source change. The `jobs.py` conclusion is
different: it is newly argued from its newly introduced production diff.
