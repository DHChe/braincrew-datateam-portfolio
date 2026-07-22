# Issue #15 Live Verification Preflight

Date: 2026-07-20

## Scope and current result

This document records fail-closed evidence for the pinned 30-case live Verification experiment.
The baseline and candidate have not started. The current state is a provenance and workflow block,
not a product-quality failure and not a live quality claim.

## Frozen identities

- Evaluation Plane branch: `feat/issue-15-live-verification`
- last committed and pushed producer SHA: `f2c60b91623563ce7dd223b36fbd9bba41c0bac7`
- current Evaluation Plane state: dirty with uncommitted dataset-v2 and preflight-v2 changes
- AX repository: `/Users/astralpig/portfolio/AX_portfolio`
- pinned AX SHA: `a5391ae8aa2b0d1342809f3599283b7759d6e4e3`
- dataset: `braincrew-evaluation-dataset@2.0.0`
- dataset digest: `sha256:bf29c2c18c66afb24bba546b8f7f32471dc744ba640f64a9d7901117c28c3448`
- Verification cases: exactly `30`
- required AX authorization roles: `Employee`, `Executive`, `HRPractitioner`
- candidate plan: `candidate-plan-v1`
- baseline: `top_k=5`, `evidence_limit=3`
- candidate: `top_k=5`, `evidence_limit=5`

The original `braincrew-evaluation-dataset@1.0.0` files remain unchanged and still validate at
digest `sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b`.
They cannot authorize the new live run because their generic `role` field does not distinguish AX
permission from scenario persona.

## Authorization role and persona decision

The earlier proposal required `AX_ROLE_MAPPING_JSON` to translate six generic dataset labels into
AX roles. Red-team review rejected that design because an external table would decide visibility
authority and could be changed independently of the frozen cases.

Dataset v2 instead stores two independent fields in every parsing, retrieval, and
grounded/visibility case:

- `authorization_role`: the exact AX role used for permission checks;
- `persona`: the job or scenario label used to explain who is asking.

Persona does not grant, imply, or derive authority. The contract does not contain a persona-to-role
mapping rule. Current reviewed case assignments happen to use three AX roles, but every case owns
its explicit authorization value and a future reviewed case may reuse a persona with another role.

## Dataset-v2 evidence

The new bundle preserves all 100 case identities, expected evidence, risk/applicability policy,
20/30/40/10 primary-focus allocation, and 70 Calibration / 30 Verification split. It adds:

- `datasets/dataset_manifest_v2.json` (`dataset-manifest-v2`);
- `datasets/parsing/parsing_cases_v2.json` (`parsing-dataset-v2`);
- `datasets/retrieval/retrieval_cases_v2.json` (`retrieval-dataset-v2`);
- `datasets/grounded/grounded_cases_v2.json` (`grounded-dataset-v2`);
- `datasets/DATASET_CARD_V2.md`.

All three components use strict v2 models. They reject the old generic `role`, missing persona,
unsupported AX roles, extra fields, wrong schema versions, and a dataset version other than
`2.0.0`. Component and integrated digests cover both new fields.

## Preflight-v2 contract

`live-verification-preflight-artifact-v2` derives required authority only from Verification-case
`authorization_role` values. It requires:

1. `AX_ROLES` to equal the dataset role set exactly;
2. one strict ID/version/digest corpus identity per role in `AX_CORPUS_IDENTITIES_JSON`;
3. one AX capability discovery request per role with no combined-role request;
4. the AX response to report the same single principal role;
5. every role-visible corpus to match its frozen identity and name
   `braincrew-evaluation-dataset@2.0.0` as a contributing version;
6. exact attachment UUIDs for all six parsing Verification documents and one successful strict
   parse-observation probe through each case's own `authorization_role`;
7. clean, pinned Evaluation Plane and AX repositories plus frozen prompt, model, evaluator, Adapter,
   `top_k`, and evidence-limit identities.

The artifact stores role-keyed capability evidence and a raw-text-free parse-probe digest for each
parsing document. Missing discovery evidence produces
`LIVE_CAPABILITY_EVIDENCE_MISSING`; mismatched role coverage, request/response authority, corpus
identity, or dataset provenance produces a typed blocker. Direct artifact construction therefore
cannot report `READY` before AX discovery. Missing, unavailable, contradictory, or failed parse
observations also block `READY`. Replay supports only the v2 preflight schema and recomputes its
logical digest. Credentials, bearer tokens, and extracted document text do not enter the artifact.

## Current AX evidence and unresolved provenance

The pinned AX local/test health endpoint is currently ready and the AX checkout is clean at the
pinned SHA. Role-isolated corpus discovery returned different visible inventories, proving why one
shared corpus identity would be incorrect:

| Authorization role | Visible records | Corpus digest |
| --- | ---: | --- |
| `Employee` | 10 | `sha256:ccc37f7d85306e13d6e18d725b9afd2c60f2a9504fd4168d888b45b49d8d4647` |
| `Executive` | 134 | `sha256:9ecffe846c41a6edd674bc791869c7eb147892d66897d165c467e2e72b4a3d68` |
| `HRPractitioner` | 119 | `sha256:e1d2c986edb048a8afd893fea7bc5eb31bdd9f56257cc36e3bd2e60be66fde9b` |

All three responses reported the requested single principal role and contributing version
`bprime-2026-07-04`. A prospective clean-producer preflight completed capability discovery for all
three roles and returned three `LIVE_CORPUS_DATASET_PROVENANCE_MISMATCH` blockers, one per role,
because none names `braincrew-evaluation-dataset@2.0.0`. The same strict preflight then attempted
the first frozen parsing attachment through `HRPractitioner` and added
`LIVE_PARSE_OBSERVATION_FAILED` after the Adapter exhausted its three transient retries.

The local/test parse-observation endpoint and six synthetic attachment identities had previously
returned strict valid responses. A fresh read-only check in this resumed state returned HTTP `503`
with `audit_persistence_failed` for all six and the Adapter exhausted its three transient retries.
This is current operational failure evidence, not parsing-quality evidence. It must be resolved and
reverified before a live run even after corpus provenance becomes valid.

The current create-only dirty-producer artifact
`issue-15-v2-strict-parse-precommit-20260720` returned `BLOCKED`, replayed successfully, and froze
logical digest `sha256:e93ad82698f2c5098730af010e974825d4282d51e327af591374de68928132c7`.
It records `LIVE_CAPABILITY_EVIDENCE_MISSING` and `LIVE_EVALUATION_PLANE_DIRTY` because the formal
path stops before HTTP discovery and parse probes when its producer is dirty. The separate
prospective check above shows the three corpus-provenance blockers and current parse failure that
will remain after a clean commit unless external AX data or operational state changes.

### Clean-producer external blocker reproduction

After commit `1185ba8a9e6bab038743531a56f8f2c5ce2b44eb`, a separate clean-producer preflight was created
outside the repository at
`/private/tmp/braincrew-issue15-clean-preflight.Dy9AW6/issue-15-v2-clean-producer-1185ba8.json`.
Replay reproduced state `BLOCKED`, logical digest
`sha256:06bcb74747000c0aedb825f14eac0bb45d12ba37e50394a527fad3d33b7caecf`, and exactly four
external blockers: one `LIVE_CORPUS_DATASET_PROVENANCE_MISMATCH` for each of `Employee`,
`Executive`, and `HRPractitioner`, plus `LIVE_PARSE_OBSERVATION_FAILED` for the first strict
parsing probe. Neither baseline nor candidate started.

Read-only AX database and endpoint inspection then isolated the parsing failure. The configured
mapping used nonexistent placeholder attachment UUIDs, so AX entered the denied-access audit
path. The configured user ID `evaluation-plane` was not a UUID; denied-audit persistence called
`uuid.UUID(principal.user_id)`, raised `ValueError: badly formed hexadecimal UUID string`, and
was surfaced as HTTP `503 audit_persistence_failed`. PostgreSQL, `audit_events`, the parser, and
all six stored attachments were healthy.

The current synthetic attachment mapping is:

| Parsing document | AX attachment UUID | Required role |
| --- | --- | --- |
| `synthetic-rule-015` | `2c7d525b-7463-463e-8893-0d37009775de` | `HRPractitioner` |
| `synthetic-rule-016` | `e2d16eeb-c86e-45be-994f-fe3aecfc3f8d` | `HRPractitioner` |
| `synthetic-rule-017` | `87dcebfe-f3cf-47cd-8e0c-c03a6a28270f` | `HRPractitioner` |
| `synthetic-rule-018` | `816b01c3-a571-4f02-9f14-32e71d7fb2ee` | `HRPractitioner` |
| `synthetic-rule-019` | `07b849ea-5e0a-44f7-87c9-600f539d7d9a` | `HRPractitioner` |
| `synthetic-rule-020` | `569dc67a-5ba8-4a00-a0d8-e03a8ac43449` | `HRPractitioner` |

All six return strict `ax-parse-observation-v1` when called with owner principal UUID
`22222222-2222-2222-2222-222222222222` and `HRPractitioner`. This proves the recovery requires
principal/mapping correction and typed UUID validation, not service restart or database repair.
The attachment UUIDs are local synthetic identifiers, not private document evidence.

### Prerequisite implementation checkpoint — 2026-07-22

AX #33, #34, and #35 are closed through AX `develop` merge
`6bfc27a7bf170172a20dd470d6fd877858c9fb80`. They provide the reviewed generic schema and
no-write dry-run, typed evaluation-principal failures, and the atomic apply path. This is
prerequisite implementation evidence only: no independently authored Braincrew pack, operator
snapshot, target-database apply, renewed role-visible corpus identity, or renewed strict parse
observation was produced. The clean preflight artifact and its four blockers therefore remain the
latest experiment evidence.

Braincrew #31 and #34 now have their external AX prerequisites closed, and AX #36 has AX #35
closed. Braincrew #31 is the selected next ticket because it unlocks the longest remaining corpus
path. None of these implementation-frontier facts authorizes baseline/candidate execution or
changes the recorded `BLOCKED` result.

The old create-only v1 artifacts and their replay digests remain historical evidence of earlier
fail-closed checks. Because their dataset, generic-role, single-corpus, and schema contracts were
superseded, they cannot authorize either v2 run.

## No-claim boundary and resume conditions

No latency, token, cost, score, failure, comparison, or candidate-superiority claim exists. No AX
behavior, Calibration result, dashboard behavior, Issue #13 gate meaning, or Agent trajectory
evaluation changed.

Resume only after all of the following are true:

1. the approved Braincrew #31-#37 and AX #36 tickets satisfy their own implementation, review,
   evidence, repository-gate, and Git Lifecycle Proposal contracts, including clean-baseline and
   RED/GREEN proof where their ticket type requires code changes;
2. Braincrew #34 freezes valid evaluation principals and the exact six-attachment mapping against
   the merged AX typed-principal contract;
3. reviewed public or synthetic AX data proves the exact role-visible corpus identity and
   `braincrew-evaluation-dataset@2.0.0` provenance for `Employee`, `Executive`, and
   `HRPractitioner`;
4. AX #37 completes its separately approved snapshot, dry-run, atomic load, and sanitized handoff
   without automatic repair or cleanup;
5. the six parsing attachment UUIDs and all prompt/model/evaluator/Adapter identities are frozen;
6. Braincrew #38 creates a new clean, create-only v2 preflight that replays and reports `READY`;
7. only then may the 30-case baseline and candidate run, replay, compare, and receive manual
   critical-failure and provenance review.

Issue #15 remains open until the full live evidence path is complete.

## Verification status

Fresh local verification after implementation and documentation synchronization:

- `uv sync --frozen --all-groups`: passed, 29 locked packages checked;
- `uv run ruff format --check .`: passed, 44 files already formatted;
- `uv run ruff check .`: passed;
- `uv run mypy`: passed, 44 source files;
- `uv run pytest -q`: passed, 241 tests;
- `git diff --check`: passed;
- v1 dataset replay: `VALID`, 100 cases, 30 Verification cases, original digest unchanged;
- v2 dataset replay: `VALID`, 100 cases, 30 Verification cases, digest reproduced;
- current create-only preflight replay: `BLOCKED`, digest reproduced, no credential or extracted-text
  field stored.

Ticket-level Standards review found no remaining code or repository-rule blocker. The versioned v1/v2
contract duplication is intentional because changing the frozen v1 schema in place would invalidate
historical artifacts. Ticket-level Spec review confirms the requested authority/persona separation,
role-isolated corpus discovery, strict parse probing, and fail-closed execution gate are implemented.

Manual critical-failure review found no baseline or candidate failures because neither run exists.
Manual provenance review instead confirms the current blockers: every visible AX corpus proves only
`bprime-2026-07-04`, not dataset v2, and the first exact parse probe currently exhausts its retries on
HTTP 503. Therefore baseline/candidate artifact replay, comparison gates, and result-level critical
failure review are correctly not run; treating them as passed would be a false quality claim.

On 2026-07-22 the user authorized one documentation-only Lore commit and force-free push of the
four synchronized canonical documents plus the two approved provisioning documents to the
existing draft PR #29. That authorization does not cover code, corpus, database, service, labels,
ready transition, merge, Issue #15 closure, or baseline/candidate execution.
