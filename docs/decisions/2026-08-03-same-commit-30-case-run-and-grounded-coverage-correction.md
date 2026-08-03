# A same-commit 30-case assembly removes one barrier but cannot create comparison evidence

**Status:** owner-authorized external run measured; documentation-only Cycle 200

## Decision

Record the owner-authorized same-commit re-capture as a real but bounded result:
the six parsing and nine retrieval Verification cases now reach `COMPLETED` at AX
`5b0f5f2ae2cfb4c4870a2228f9aa226e009241f5`. It does not create an
answer-quality verdict, comparison artifact, or release decision, because the
grounded partition remains `INVALID` with zero answer-quality coverage in both
the baseline and candidate runs.

The 2026-08-02 Issue #15 closing comment remains unedited. Its same-day
correction is the current issue record: the earlier comment attributed the
`INVALID` result to the parsing partition alone, although the stored baseline
artifact already recorded the same grounded failure. This document records that
misattribution as an error rather than presenting it as a newly discovered fact.

## Measured external run

The checked files are outside this repository at
`/Users/astralpig/ax-live-verification-evidence/run-2026-08-03-30case/` and have
not had a public-suitability review or an `evidence/` publication.

| Measurement | Result |
| --- | --- |
| Preflight | `READY`, zero blockers, logical digest `sha256:a13074e116c9664f04a1881dc2598d1ce4a02983b3e0279c1b6f19b5c7b0a532` |
| Baseline evaluation | `INVALID`, logical digest `sha256:86f2563a714f711f2c1c6dcf3a2b0a80bfec087d26446e09f6785b9d3f2bd6b7` |
| Candidate evaluation | `INVALID`, logical digest `sha256:dd03f4c4d198173d5cb8d6b9b1cffc8c3ec9785d365b2b606ed51faab4fd3365` |
| Parsing | `COMPLETED`; 6 of 6 Verification cases scored |
| Retrieval | `COMPLETED`; 9 of 9 Verification cases scored |
| Grounded | `INVALID`; `verification_citation_precision_cases: 0` and `verification_claim_support_cases: 0` |
| Run invalid reasons | `grounded:SYS-GROUNDED-COVERAGE-INVALID`, `DATASET_CASE_COVERAGE_INVALID` |
| Baseline grounded answer path | 13 provider answers discarded, 1 provider answer succeeded, and 1 path made no LLM call; all 13 discards have `citation_contract_violation=True` and `unsafe_provider_output=False` |

The preflight and capture-manifest logical digests were recomputed directly from
their external JSON. The two evaluation logical digests were independently
reconstructed in memory from those exact capture inputs using the committed
dataset evaluator; no evaluation output was written.

## Recorded misattribution

The pane 1 closing-comment attribution was wrong. The 2026-08-02 baseline
artifact at
`/Users/astralpig/ax-live-verification-evidence/run-2026-08-02/issue-15-baseline-2026-08-02.json`
already reports `state: INVALID`, `grounded.state: INVALID`,
`verification_citation_precision_cases: 0`, and
`verification_claim_support_cases: 0`. That evidence was available before the
decision to re-capture but was not read.

The parsing partition was a real assembly barrier, and the same-commit run
removed it. It was not the cause of the grounded result. The deeper, independent
barrier is AX answer-path behavior: thirteen of fifteen grounded cases return
HTTP 200 after their provider output is discarded for a citation-contract
violation; the two remaining answer paths still supply no usable grounded
answer-quality evidence. Re-pinning or re-capturing does not change that SUT
behavior, which is why the identical zero coverage reproduced at the new commit.

## Why no comparison artifact exists

`src/braincrew/comparison.py:427` requires both baseline and candidate runs to
be `COMPLETED`. Both reconstructed same-commit evaluations are `INVALID` for the
grounded coverage and whole-dataset coverage reasons above. The project can
therefore honestly record the first one-commit 30-case assembly with two
completed partitions, but no comparison artifact exists or can exist against the
current SUT state.

## Dashboard decision and rejected alternatives

The recruiter-facing dashboard keeps its golden fixture. A frontend cycle
labelled that fixture **“Fixture evidence — not a live AX verification,”** on the
page itself; it receives no live data from this run because there is no comparison
artifact to display.
This is the Issue #15 input to Issue #17's claim-to-evidence package.

- **Rejected: manufacture a comparison from live inputs or partial results.** It
  would make the dashboard appear to show an evaluated result that the evaluator
  refuses to produce, violating the rule to claim only what was executed and
  verified.
- **Rejected: call the two completed partitions an answer-quality or release
  result.** Parsing structure and retrieval completed, but grounded coverage is
  zero and neither proves AX answer quality.
- **Rejected: rewrite the earlier issue comment or dated partition record.** The
  correction is meaningful only if the record still shows that the evidence was
  available and was not read.

## Boundaries retained

This documentation cycle changes no source, test, fixture, dashboard, runtime,
container, attachment, provider, `evidence/`, or Git lifecycle state. The prior
2026-08-02 decision's rejection of a re-capture was scoped to that cycle; the
later owner authorization is recorded as a new result rather than a relaxation
of any evidence or adapter boundary.
