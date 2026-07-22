# Independent Evaluation Corpus Provisioning Design

Date: 2026-07-20
Status: independent spec review passed; user written-spec approved 2026-07-21; tracker graph published and implementation progress reconciled 2026-07-22
Braincrew fixed point: `1185ba8a9e6bab038743531a56f8f2c5ce2b44eb`
AX fixed base: `a5391ae8aa2b0d1342809f3599283b7759d6e4e3`
Latest merged AX importer prerequisite: `6bfc27a7bf170172a20dd470d6fd877858c9fb80`
Pinned AX schema merge: `47673b83a9fb431f2bad550781db18c7bee8b67e`
Dataset: `braincrew-evaluation-dataset@2.0.0`
Issues: Braincrew #15 and prerequisite #30

## 1. Purpose

Issue #15 cannot start its live 30-case baseline/candidate pair until AX proves that each
required authorization role sees a reviewed public or synthetic corpus derived from the
intended dataset version and all six parsing probes return strict AX observations.

This design creates that prerequisite without letting evaluation expectations generate their
own evidence. Braincrew owns an independently authored corpus pack and a fail-closed
cross-validator. AX owns a generic local/test importer described in repository
`DHChe/AX_portfolio`, parent Issue #32, historical fixed base
`a5391ae8aa2b0d1342809f3599283b7759d6e4e3`, and canonical file
`docs/superpowers/specs/2026-07-20-generic-synthetic-seed-pack-importer-design.md`.
The repositories exchange files and JSON receipts only. Braincrew never imports AX internals
or writes to the AX database.

This is a provisioning and preflight design. It does not execute the baseline, candidate,
comparison, Calibration retuning, or any quality claim.

## 2. Confirmed external blockers

The clean producer artifact is
`sha256:06bcb74747000c0aedb825f14eac0bb45d12ba37e50394a527fad3d33b7caecf`
and replays as `BLOCKED`. Its four material blockers are:

| Blocker | Confirmed evidence | Meaning |
| --- | --- | --- |
| Employee corpus provenance | 10 visible records; `sha256:ccc37f7d85306e13d6e18d725b9afd2c60f2a9504fd4168d888b45b49d8d4647`; contributing version `bprime-2026-07-04` only | The visible corpus is real but does not prove dataset v2 contribution. |
| Executive corpus provenance | 134 visible records; `sha256:9ecffe846c41a6edd674bc791869c7eb147892d66897d165c467e2e72b4a3d68`; contributing version `bprime-2026-07-04` only | The visible corpus is real but does not prove dataset v2 contribution. |
| HRPractitioner corpus provenance | 119 visible records; `sha256:e1d2c986edb048a8afd893fea7bc5eb31bdd9f56257cc36e3bd2e60be66fde9b`; contributing version `bprime-2026-07-04` only | The visible corpus is real but does not prove dataset v2 contribution. |
| Parsing probe | `synthetic-rule-015` exhausts retries on HTTP 503 `audit_persistence_failed` | The configured attachment and principal do not currently reach a strict observation. |

The parsing 503 is not a PostgreSQL outage or missing audit privilege. The configured map uses
placeholder attachment UUIDs that do not exist, so AX enters the denied-access audit path. The
configured user ID `evaluation-plane` is not a UUID. AX then attempts
`uuid.UUID(principal.user_id)` while recording the denial, raises
`ValueError: badly formed hexadecimal UUID string`, and maps that audit-path exception to
`503 audit_persistence_failed`.

The six real synthetic attachments still exist and return strict
`ax-parse-observation-v1` responses when called with their owner principal and the frozen
`HRPractitioner` authorization role. The parser itself and the database contents do not need
repair for this blocker.

## 3. Locked decisions

1. Braincrew owns the independent corpus pack; AX owns only a generic importer.
2. Corpus documents are authored without access to evaluation queries, expected answers,
   expected evidence, scores, split labels, or fixture observations.
3. The pack is sealed before it is compared with the evaluation dataset.
4. A mismatch produces a typed blocker. It never triggers corpus edits, dataset edits, automatic
   deletion, or a second authoring pass informed by expected results.
5. The pack covers the complete 100-case source identity surface and includes distractors. It is
   not required to contain one document per case.
6. Only public or synthetic data is allowed. Private company or employee documents, credentials,
   and raw secrets are forbidden.
7. AX database access remains behind the AX importer. Braincrew receives only sanitized
   dry-run, load, corpus-identity, parse-probe, and preflight receipts.
8. A `READY` preflight freezes the corpus. No corpus, AX code, model/provider, prompt, role,
   dataset, or configuration mutation is allowed between baseline and candidate.

## 4. Ownership and component boundary

```text
independent authoring brief
        |
        v
isolated corpus staging directory
        |
        v
schema, license, secret and digest validation
        |
        v
sealed Braincrew corpus pack
        |
        +----> Braincrew cross-validator <---- dataset v2, read only
        |
        v
AX generic dry-run importer
        |
        v
approved snapshot and atomic AX load
        |
        v
role corpus identities + six parse probes
        |
        v
create-only Braincrew preflight and replay
```

Braincrew owns:

- `datasets/corpus/braincrew-evaluation-corpus-v2/` after the pack is sealed;
- source files, an independently sealed `corpus-manifest.json`, license/provenance review,
  role-visibility declarations, and file digests;
- a cross-validator that compares only a sealed pack with dataset v2;
- a post-validation `import-manifest.json` that binds the unchanged corpus digest to the dataset
  version and successful cross-validation receipt;
- sanitized cross-validation and preflight receipts;
- the decision to stop on any mismatch.

AX owns:

- the generic `ax-synthetic-seed-pack-v1` input contract;
- dry-run validation, provider verification, embedding, transactionality, idempotency, and audit;
- server-side tenant and visibility enforcement;
- the authoritative role-visible corpus identity returned by AX.

Neither repository imports source code, ORM models, migrations, fixtures, or runtime objects from
the other. The boundary is a versioned pack plus strict JSON receipts.

## 5. Independent authoring and sealing

The authoring session starts in fresh context. Its readable inputs are limited to an approved
domain brief, synthetic-content/CC0 requirements, synthetic-company labels, the allowed AX role
names, and the generic pack schema. It must not read:

- `datasets/**` from the Braincrew repository;
- `tests/fixtures/**`;
- case queries, expected answers, expected evidence, scores, or split assignments;
- existing observed baseline/candidate output;
- private documents or credentials.

The exact future authoring inputs are:

- Braincrew `docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md`;
- Braincrew `schemas/ax-synthetic-seed-pack-v1.schema.json`, whose bytes and SHA-256 must match
  the reviewed schema published by the pinned AX implementation at
  `docs/contracts/ax-synthetic-seed-pack-v1.schema.json`;
- an empty isolated staging directory outside the Braincrew repository.

The authoring brief does not exist at this design-review fixed point and must not be written by a
session that has inspected evaluation cases or fixtures. Its creation is a separate fresh-context
step. It may define domain families, synthetic-content and CC0 policy, source-authority policy,
allowed AX roles, language/format bounds, and distractor policy. It may not contain dataset case
IDs, case queries, expected answers/evidence, expected source IDs/digests, scores, or split labels.
Authoring cannot start until that brief and the vendored schema are reviewed and committed at a
clean Braincrew SHA.

Independence is enforced by filesystem capability, not only by prompt wording. The authoring
process receives a read-only input directory containing only the committed brief, the exact
vendored schema, and a file of their SHA-256 values; it receives one empty writable staging
directory and no Braincrew repository mount, dataset mount, fixture mount, AX database access, or
network access. The launcher records the clean Braincrew SHA, command/tool version, allowed input
paths and digests, denied path classes, an opaque staging run ID, start/end time, exit state, and
resulting source/manifest digests in a sanitized independence receipt. It records no prompt transcript,
source text, credential, or private path.

Because the final pack path is under `datasets/`, the authoring session writes to an isolated
staging directory outside that tree. A separate sealing step validates the staged bytes, creates
the manifest digest, and copies those exact bytes to
`datasets/corpus/braincrew-evaluation-corpus-v2/`. After sealing, content bytes are immutable.
A correction requires a new corpus version and a fresh independent authoring process, not an
in-place edit.

The independently authored `corpus-manifest.json` contains at least:

- `schema_version`, `corpus_id`, `corpus_version`, and `sealed_content_digest`;
- `synthetic=true`, `demo_company=true`, `corpus_mode=demo`;
- ordered source descriptors with stable `source_id`, relative file path, source class,
  authority level, document version, visibility roles, content SHA-256, provenance status, and
  license;
- exact per-source byte digests and a canonical sealed-content digest that binds them;
- a manual provenance-review decision and reviewer-safe timestamp/identity fields.

The manifest and source files must not contain query text, answer keys, expected-answer fields,
expected evidence, metric values, case-to-answer mappings, Calibration/Verification labels, or
fixture observations. The schema rejects those names recursively rather than relying only on a
review convention.

Version 2.0.0 provisioning chooses the synthetic branch of the allowed public-or-synthetic
boundary: every source is newly authored synthetic content, labeled synthetic/demo at both pack
and source level, and licensed `CC0-1.0`. Public-source ingestion is not mixed into this v1 AX
pack contract because a pack-wide `synthetic=true` label must remain truthful. Every source must
be explicitly `reviewed`; `pending` or missing provenance blocks sealing.

`seed_version` is deliberately absent from the independently authored content manifest. After a
successful post-seal cross-validation, Braincrew creates `import-manifest.json` under the strict
generic `ax-synthetic-seed-pack-v1` contract. That non-content envelope references the sealed
corpus ID, version, `sealed_content_digest`, source manifest, tenant/demo-company target, and
cross-validation receipt digest, and sets
`seed_version = braincrew-evaluation-dataset@2.0.0`. AX therefore receives the dataset version
only after actual content alignment is proven. A failed cross-validation cannot produce an
import manifest, which prevents an arbitrary version string from masquerading as provenance.

## 6. Canonical identity and tamper behavior

Braincrew and AX use one byte contract. Source files must already be UTF-8 without BOM, NFC, and
LF-only; CRLF, bare CR, invalid UTF-8, and non-NFC input are rejected instead of normalized.
Each source `content_sha256` is over the exact accepted file bytes. Manifest strings must already
be NFC and contain no CR. Canonical manifest JSON is UTF-8, sorted by object key, preserves array
order, uses compact separators, contains no floating-point values, and materializes all schema
defaults. `sealed_content_digest` hashes canonical `corpus-manifest.json` with that digest field
omitted. `import_digest` hashes canonical `import-manifest.json` with its own digest field omitted.

The import manifest binds `sealed_content_digest`, `seed_version`, tenant/demo-company target,
`qualification_receipt_digest`, and normalization/chunking contract versions. Braincrew calls
that `import_digest` the `pack_digest` in receipts; source, sealed-content, and import digests are
never treated as interchangeable. The pack identity therefore covers every field that affects
source identity, visibility, provenance/license, normalization, and AX materialization.

The following are identity changes and require a new pack version and digest:

- source text, source ID, title, document version, class, authority, or visibility change;
- source addition or removal, including distractors;
- provenance/license review change;
- normalization or chunking contract change;
- content schema version, corpus ID, or corpus version change.

Timestamps, filesystem location, local operator name, and receipt path are excluded from the
sealed-content and import digests but remain outside them as operational envelope fields.

## 7. Post-seal cross-validation

Only after sealing may the Braincrew cross-validator read both the pack and dataset v2. It is
read-only and must never emit repaired corpus or dataset bytes. It proves:

1. strict schema and forbidden-field compliance;
2. manifest and per-file digest reproduction;
3. complete 100-case required source-identity closure;
4. exact source-text digest equality wherever dataset v2 freezes source text;
5. required visibility for `Employee`, `Executive`, and `HRPractitioner`;
6. absence of every forbidden visibility exposure;
7. provenance and license review completion;
8. non-empty distractor coverage independent of expected answer sources.

On success, the validator creates a sanitized cross-validation receipt and the separate import
manifest described above. These files bind the sealed corpus digest to dataset v2 but do not
change corpus source bytes or the content digest. On failure, neither file is emitted.

Any failure ends the provisioning attempt with one or more of:

- `CORPUS_PACK_SCHEMA_INVALID`;
- `CORPUS_PACK_DIGEST_MISMATCH`;
- `CORPUS_REQUIRED_SOURCE_MISSING`;
- `CORPUS_SOURCE_TEXT_DIGEST_MISMATCH`;
- `CORPUS_REQUIRED_VISIBILITY_MISMATCH`;
- `CORPUS_FORBIDDEN_VISIBILITY_MISMATCH`;
- `CORPUS_PROVENANCE_REVIEW_REQUIRED`.

The receipt stores source IDs, expected/observed digests, role labels, and blocker identities only.
It excludes raw source text, query text, expected answers, vectors, credentials, database URLs,
and HTTP authorization material.

## 8. Parsing mapping and principal recovery

The strict parse preflight must replace the placeholder map with the current local synthetic
attachments:

| Document | Attachment UUID |
| --- | --- |
| `synthetic-rule-015` | `2c7d525b-7463-463e-8893-0d37009775de` |
| `synthetic-rule-016` | `e2d16eeb-c86e-45be-994f-fe3aecfc3f8d` |
| `synthetic-rule-017` | `87dcebfe-f3cf-47cd-8e0c-c03a6a28270f` |
| `synthetic-rule-018` | `816b01c3-a571-4f02-9f14-32e71d7fb2ee` |
| `synthetic-rule-019` | `07b849ea-5e0a-44f7-87c9-600f539d7d9a` |
| `synthetic-rule-020` | `569dc67a-5ba8-4a00-a0d8-e03a8ac43449` |

All six dataset-v2 parsing cases require `HRPractitioner`. The request principal must use the
owning local synthetic user UUID `22222222-2222-2222-2222-222222222222`, not the non-UUID
label `evaluation-plane`. Tenant and user IDs are validated as UUIDs before the first HTTP call.
Malformed configuration becomes `EVALUATION_PRINCIPAL_ID_INVALID`. A well-formed but nonexistent
or inactive tenant-user subject becomes `EVALUATION_PRINCIPAL_SUBJECT_INVALID` and is not
retried. For the validated active owner subject, a nonexistent or unreadable attachment becomes
`PARSE_ATTACHMENT_MAPPING_INVALID` or the existing `LIVE_*` operation blocker. No result is
inferred from attachment status or earlier fixtures.

`READY` still requires six fresh strict responses with `parse_available=true`, matching
attachment IDs, expected parser/source-text digests, valid span coordinates, exact applied
principal role, and raw-text-free response digests. A successful transport does not turn missing
headings, metadata, tables, lists, or spans into a quality pass; those remain later evaluator
observations.

## 9. Credentials, permissions, and operational authority

Braincrew corpus creation and validation require:

- read/write access only to the isolated staging area and the new corpus-pack path;
- read-only access to dataset v2 during post-seal cross-validation;
- no AX database access;
- no model credential;
- manual authority to approve provenance and license review.

AX dry-run and loading require, through the AX-owned command:

- local/test environment authority and the existing demo tenant identity;
- read access to the sealed pack;
- `EMBEDDING_PROVIDER=fake` for the confirmed current corpus lineage, yielding adapter identity
  `fake-deterministic`; no model credential is required for this approved path;
- database `CONNECT` and schema `USAGE`;
- database `SELECT` on `tenants`, `demo_seed_runs`, `seed_source_documents`,
  `seed_source_chunks`, `seed_evidence_spans`, `seed_vector_records`, and `audit_events`;
- an operator with database snapshot authority before apply;
- additive `INSERT` on `demo_seed_runs`, `seed_source_documents`, `seed_source_chunks`,
  `seed_evidence_spans`, `seed_vector_records`, and `audit_events`;
- execution of PostgreSQL session advisory-lock functions if revoked from `PUBLIC`;
- no `UPDATE`, `DELETE`, `TRUNCATE`, schema migration, sequence, or
  `synthetic_operational_records` privilege.

The AX command holds a tenant-wide PostgreSQL session advisory lock, but no open database
transaction, while it rechecks identity, verifies provider lineage, and completes embeddings.
It then inserts the prepared completed vectors, exact digest manifest, and one
`provider.embedding.used` audit event in a single transaction. This makes concurrent identical
apply attempts call the provider only once and preserves all-or-nothing database state.

Braincrew preflight requires:

- the local/test AX evaluation router;
- valid tenant, user UUID, and one exact role per request;
- the six attachment mapping and three expected role corpus identities;
- model credential only for the later live answer runs, not for corpus validation or parse probes.

Credentials remain environment-only. Receipts store provider and model identity, never secret
values.

## 10. TDD and independence proof

Braincrew implementation begins only after a fresh clean baseline. Tests are added and observed
failing before production code for:

1. strict pack schema and recursive forbidden fields;
2. canonical digest and single-byte tampering;
3. source identity closure and duplicates;
4. required and forbidden visibility;
5. source-text digest equality;
6. provenance/license review;
7. sealed-pack behavior with no automatic repair output;
8. typed blockers and raw/secret-free receipts;
9. malformed and unknown evaluation principals plus attachment mapping;
10. import-manifest digest binding and exact AX receipt/audit digest agreement;
11. existing dataset v1/v2, fixture, preflight, replay, and all current regression behavior.

The independence test records the authoring input allowlist, denylist, opaque staging identity, output
digest, seal time, lack of repository/dataset/network mounts, and clean source SHA. A contract
test attempts reads of dataset, fixture, repository, and network resources and must observe
denial before authoring is accepted. The post-seal validator runs in a different process/context.
Its only
allowed outputs are a success receipt or typed blockers. A mismatch cannot feed a new prompt or
mutation command back into the authoring lane.

## 11. Execution and stop order

The required sequence is:

1. approve and review the Braincrew and AX design documents;
2. publish `to-spec` parents and the dependency-reviewed `to-tickets` graph;
3. implement and merge AX #33 schema/dry-run, AX #34 principal validation, and AX #35 atomic apply;
4. vendor and digest-check the reviewed AX JSON schema in Braincrew #31, then stop at its Git gate;
5. implement Braincrew #32 authoring isolation, #33 qualification, and #34 principal/mapping repair
   from separate clean baselines with RED/GREEN and independent review;
6. implement AX #36 disposable-PostgreSQL idempotency/concurrency proof before any operator load;
7. in a fresh restricted context, approve the Braincrew #35 authoring brief and run Braincrew #36
   independent authoring/sealing without evaluation data access;
8. use Braincrew #37 to cross-validate the unchanged sealed pack against dataset v2;
9. at the separate AX #37 operational gate, run the exact importer dry-run;
10. create and verify a restricted PostgreSQL snapshot outside both repositories;
11. perform the approved atomic AX load once and preserve sanitized evidence;
12. query and freeze all three role-visible corpus identities;
13. re-run all six strict parse observations through the reviewed principals and mappings;
14. create and replay the Braincrew #38 preflight artifact;
15. stop at `READY`.

Baseline and candidate execution is a separate, later authorization. Stop immediately on a
schema, digest, source, visibility, private-data, license, provider, snapshot, dry-run, embedding,
transaction, corpus-identity, or parse-probe failure. Do not auto-edit, retry with changed data,
delete, restore, commit, push, modify a pull request, mark ready, or merge.

### Issue #31 schema-sealing implementation lock

Issue #31 vendors all four reviewed AX contract files from merge
`47673b83a9fb431f2bad550781db18c7bee8b67e`. The content schema is exactly 3,699 bytes with
SHA-256 `372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb`; the import schema is
exactly 2,241 bytes with SHA-256
`4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa`. Runtime sealing checks
both fixed digests and their committed declaration files, so changing schema bytes and rewriting
the adjacent digest together still fails closed as `AX_SCHEMA_DRIFT`.

`braincrew-eval seal-corpus` accepts one isolated staging directory and one output root. It reads
only canonical `corpus-manifest.json` plus the ordered declared source files, rejects undeclared
files and unsafe/symlink/non-POSIX paths, and copies the exact validated bytes into
`<output-root>/<corpus-id>/<corpus-version>/`. An existing destination returns
`SEALED_CORPUS_VERSION_EXISTS`; no existing byte is opened for write.

The validator mirrors the shared v1 byte contract: strict frozen Pydantic models, recursive
evaluation-derived-field rejection, no floats, UTF-8 without BOM, NFC, LF-only text, exact
per-source SHA-256, and a canonical ordered `sealed_content_digest`. Pack and source labels must
remain synthetic/demo, `CC0-1.0`, and reviewed. The generated `corpus-sealing-receipt-v1` stores
only corpus identity, fixed AX schema identity, ordered source IDs/digests, counts, byte total,
and its own digest. It stores no dataset version, query/answer, raw text, credential, database
location, or private path. Existing `braincrew-eval replay` revalidates the receipt, schema pin,
manifest, and current sealed source bytes and rejects any mutation.

Rejected alternatives were normalizing invalid input, generating missing digests, overwriting a
version in place, embedding source text or staging paths in the receipt, reading dataset v2 during
sealing, or importing AX implementation code. Those alternatives weaken provenance or cross the
Issue #31 boundary into #32/#33 or AX-owned operations.

Verification on `feat/issue-31-schema-sealing` reproduced all four AX contract files byte-for-byte,
observed the missing schema/CLI contracts RED before GREEN, and passes 25 focused sealing tests plus
the full 232-test repository suite. Ruff format/lint, strict mypy, `git diff --check`, installed CLI
seal/replay, sanitized-receipt scanning, and wheel schema inclusion also pass. Separate Standards
and Spec review axes have zero unresolved finding. Publication remains stopped at the repository
Git Lifecycle Proposal Gate.

## 12. Rejected alternatives and consequences

- Reverse-generating the corpus from expected evidence was rejected because the evaluator would
  manufacture the facts it later claims to retrieve.
- Hard-coding Braincrew data or dataset semantics in AX was rejected because it couples the SUT
  to one benchmark and weakens independent evaluation.
- Direct Braincrew database writes were rejected because they bypass AX validation,
  authorization, audit, and reproducibility contracts.
- A one-off SQL load was rejected because reviewers could not reproduce the contributing
  version through an official supported path.
- Adding only a version string was rejected because AX corpus provenance must derive from actual
  loaded records.
- Automatically restoring the database after a later preflight failure was rejected because a
  successful additive load is evidence-bearing state; deletion or restore requires its own
  destructive proposal gate.

The accepted cost is two coordinated implementations plus a separate authoring/sealing step.
The benefit is that a later `READY` result demonstrates real role-visible corpus provenance rather
than a self-fulfilling fixture.

## 13. Completion condition

This design phase is complete when both repository specs pass independent read-only review and
the user approves the written files. Provisioning is complete only when a sealed independent
pack passes cross-validation, AX dry-run and atomic load succeed from approved clean commits,
the three role corpus identities include `braincrew-evaluation-dataset@2.0.0`, all six strict
parse probes succeed, and a create-only preflight replays as `READY`.

No baseline, candidate, comparison, or live quality claim is part of this completion condition.

## 14. Implementation progress checkpoint

As of 2026-07-22, the `to-spec` parents and `to-tickets` graph are published. AX #33, #34, and
#35 are merged; AX #36 remains open. Braincrew #31 and #34 now have their external AX prerequisites
closed, while Braincrew #31 is the selected next implementation ticket because it opens both the
authoring-boundary and qualification branches. No Braincrew pack, operator snapshot, target load,
renewed preflight, baseline, candidate, comparison, or live quality claim exists.
