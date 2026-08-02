# Locked: publish the reviewed stored-live evidence as an immutable replay boundary

Date: 2026-08-02
Status: locked
Implements: the published-live-artifact replay portion of [Issue #16](https://github.com/DHChe/braincrew-datateam-portfolio/issues/16)

## 0. Supersedes

This reverses one rejected alternative in
[the clean fixture container decision](./2026-08-02-issue-16-clean-fixture-container-and-live-replay-boundary.md),
locked earlier the same day, which listed *"Copy or commit the owner-held live artifacts"* among its
rejections. **The ground it gave was that publication was the owner's decision and had not been
made** — not that publishing was unsafe. The owner made it, a publishability review returned
`PUBLISHABLE` with no redaction for all four files, and that ground was discharged. That document is
marked superseded in part and its text is deliberately left unchanged, as is this repository's
practice. Card **D30** is superseded by **D31** on the same grounds.

The three occurrences in `docs/status/braincrew-delivery-workflow.md` that now read as stale sit under
`## Transition history` and are **not** corrected: that section is append-only, and editing a dated
entry to match a later state would falsify the record.

## 1. Decision

The owner authorised publication, with no redaction, of exactly four reviewed files from the
2026-07-31 baseline. They are placed under `evidence/` without reformatting, reserializing, or
reindenting:

```text
evidence/capture-baseline-2026-07-31/
  issue-15-phase1-baseline-2026-07-31.capture-manifest.json
  issue-15-phase1-baseline-2026-07-31.grounded-observations.json
  issue-15-phase1-baseline-2026-07-31.retrieval-observations.json
evidence/eval-baseline-2026-07-31/
  issue-15-phase1-baseline-2026-07-31.json
```

The three capture files remain siblings because the manifest stores each observation reference as a
bare file name and pins its content digest. Moving either observation into a nested directory would
break the committed replay contract.

The publishing test uses the existing `replay` CLI path and pins these values as test literals:

| Stored artifact | Reproduced logical result |
| --- | --- |
| capture manifest | `sha256:775a85295fb5db2f9cfb6e1aa5504206ea3b629a032452932ca685a7ab1a5049`; 15 grounded and 9 retrieval cases |
| evaluation artifact | `sha256:9435c9daaa21e4e3129dad997a9dff79717452a2c1f112acfd7a95ba3e80f6fb`; `run_state` `INVALID` |

## 2. Byte-identity evidence

The destination bytes were compared directly against the read-only source with SHA-256:

| File | SHA-256 |
| --- | --- |
| capture manifest | `5dd771e89fc39a5d05ac3f6b9f9af6100d5cbc0fcff5293c0409d743b340f340` |
| grounded observations | `98f1c97d102f6a759dc37512e3881df9292d636965f01f3cd8610e6269d3faf9` |
| retrieval observations | `c20308468b36c8040bae8c454bed9a9ab06d7684a110feb8a44ba5490f120cc2` |
| evaluation artifact | `e708483faa1207cdfe27c3f49cd3852931c2eb5ca96b6e53ca80e40f7aff9811` |

## 3. What this permanently fixes

Publication fixes one inspectable historical boundary: the stored evaluation logical digest
`sha256:9435c9da…`, the 242 recorded corpus digests, AX commit `1ead133`, and dataset `3.0.0`.
That irreversibility is intentional. If a later corpus changes, its digest no longer matches this
published historical artifact; the record must not be silently rewritten to follow it.

Three further consequences, none covered by the digest pinning above:

- **The bytes cannot be withdrawn.** A public Git history is forked, cloned and archived. Removing
  these files later requires rewriting history and still does not reach copies. This is the property
  that made the decision worth its own review, and it is recorded here so it is not confused with the
  digest pinning.
- **The four files are now effectively immutable.** The acceptance test pins their logical digests as
  literals, so any reformat, `jq` re-serialisation, editor newline normalisation, or pre-commit hook
  touching `evidence/` turns the suite red. Treat that directory as sealed bytes, not as JSON.
- **A gate decision of `INVALID` is now permanently public.** That is the honest result of the run and
  the README leads with it, but from here it is fixed rather than provisional.

The owner-approved publishability review covers these four candidates only. Its authorization
records a `PUBLISHABLE` result with no redaction. The other 33 files in the source directory were
outside that review and are not publication candidates; no copy or quotation of them belongs in this
repository. In particular, the review scope did not extend to the source directory's incident records.

## 4. Issue #16 criterion accounting

| Criterion | State after this decision | Evidence and remaining limit |
| --- | --- | --- |
| Clean, network-isolated validation | met | The Braincrew-only image replays the repository-resident files with `--network none`; no host mount, Docker Compose, or AX container is involved. |
| One-command deterministic replay of stored published-live artifacts | met | The committed CLI replays both artifacts and the literal-digest regression test passes. |
| Replay-versus-rerun claim boundary | met as documentation and replay behavior | Replay validates fixed stored bytes and recomputed logical results. It does not make a current live-quality or release claim. |
| No sensitive-data publication | met for the four reviewed candidates | The owner-approved review authorizes exactly these files with no redaction; its scope excludes the remaining 33 files. |
| Named CI validation | implemented locally, externally unverified | The fixture-container job uses the same image, but a pull-request run is still the evidence for hosted CI. |
| A fresh live rerun is not presented as byte-identical | remains open as live-execution evidence | Issue #15 remains open and no new AX/provider run occurred here. The required distinction remains an enforced documentation boundary, not a newly demonstrated live run. |

## 5. Rejected alternatives

- **Reformat or reserialize the JSON while copying.** Stored sibling digests and the purpose of
  publication both require identical bytes.
- **Move the capture observations into separate directories.** The manifest's bare-file-name
  references intentionally require sibling placement.
- **Treat replay as a fresh live rerun.** A replay checks immutable stored evidence; a fresh SUT or
  provider invocation is a new measurement at a new time.
- **Broaden publication to the remaining source files.** Their review status is deliberately unknown
  in this decision, so the safe boundary is the four explicitly authorized candidates.

## 6. Validation evidence

The new acceptance test first failed because the capture manifest was absent, then passed after the
four byte-identical copies were placed. Changing one digit in its pinned capture digest made that named
test fail; restoring the literal reproduced SHA-256
`b76f896bb5d7b6d21c863d5fec034bf2e89902c4c0d76f18b5e56dd9c429ad19` for the test file. Changing
one byte in a temporary copy of the evaluation artifact made `replay` refuse it with `Invalid artifact:
artifact logical content does not reproduce its stored digest`.

Host gates reported Ruff format/check clean, mypy clean, `599 passed`, and `11 passed` for the Issue #6
fixture file. The clean container reported `596 passed, 3 skipped` followed by `11 passed`; the three
skips are the documented unsupported OS-sandbox cases. The complete command output and all source/
destination hashes are retained in the Cycle 184 report.
