# Braincrew Evaluation Dataset Card

Dataset ID: `braincrew-evaluation-dataset`

Dataset version: `2.0.0`

Frozen content digest: `sha256:bf29c2c18c66afb24bba546b8f7f32471dc744ba640f64a9d7901117c28c3448`

## Intended use

This public, synthetic engineering benchmark is the authorization-safe input for pinned live
evaluation of the evolving AX subject under test. It preserves the 100 case identities, expected
evidence, 70 Calibration / 30 Verification split, metric applicability, and risk policy from
`1.0.0`. It changes the scoring-relevant authorization contract, so it is a new dataset version
rather than an in-place correction of the frozen `1.0.0` bundle. Existing deterministic fixture
observations and fixture artifacts remain bound to `1.0.0`; attempting to score them against this
version returns `DATASET_FIXTURE_SCHEMA_UNSUPPORTED` instead of translating their old role labels.

| Primary focus | Calibration | Verification | Total |
| --- | ---: | ---: | ---: |
| Parsing | 14 | 6 | 20 |
| Retrieval | 21 | 9 | 30 |
| Grounded answer | 30 | 10 | 40 |
| Visibility and abstention | 5 | 5 | 10 |
| Total | 70 | 30 | 100 |

## Authorization role and persona

All parsing, retrieval, grounded-answer, and visibility/abstention cases separate:

- `authorization_role`: the exact AX role used to authorize retrieval and answer requests;
- `persona`: the job or scenario label used to explain who is asking.

The current reviewed case assignments are summarized below for auditability only:

| Persona | AX authorization role |
| --- | --- |
| `executive` | `Executive` |
| `hr_manager`, `recruiter`, `investigator` | `HRPractitioner` |
| `employee`, `manager`, `interviewer`, `it_admin` | `Employee` |

A persona does not grant, imply, or derive AX permissions. The table is not a reusable mapping
rule: every case carries its own independently reviewed `authorization_role`. `manager` and
`interviewer`, for example, remain visible in the current case evidence while those specific cases
execute with `Employee` authorization. A future case may use the same persona with another reviewed
authorization role without changing the persona definition. The removed generic `role` field must
not be reconstructed through an external crosswalk.

## Provenance and license

- Provenance status: complete
- License status: approved
- Source type: synthetic
- License: CC0-1.0
- Parsing, retrieval, and grounded components use strict v2 schemas and preserve their reviewed synthetic
  evidence and proposition content.
- No private customer, employee, or company document is included.

## Risk, leakage, and identity controls

- The risk classification, stable case identities, duplicate-content rejection, answer-leakage
  checks, and minimum Verification denominators remain unchanged from `1.0.0`.
- `authorization_role` and `persona` are scoring-relevant and covered by the component and
  integrated dataset digests.
- Live evidence must record the requested AX authorization role and the role AX actually applied.
- Each role-visible corpus identity must be verified separately before a live run.
- Every parsing Verification attachment must return one strict, available parse observation through
  its case's own `authorization_role`; the preflight artifact stores only its digest and execution
  metadata, not extracted document text.

## Minimum Verification denominators

EvidenceSpan recovery: 6; Recall@5: 9; claim-support precision: 10; citation precision: 10;
Answer Mode accuracy: 15; abstention accuracy: 5. A run below any minimum is `INVALID` and has no
integrated aggregate claim.

## Explicit exclusions

This version does not add AX product roles, grant manager or interviewer privileges, change
expected answers, retune Calibration after viewing Verification results, change comparison gates,
or add Agent trajectory evaluation.
