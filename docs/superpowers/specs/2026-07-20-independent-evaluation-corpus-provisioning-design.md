# Independent Evaluation Corpus Provisioning Design

Date: 2026-07-20
Status: independent spec review passed; user written-spec approved 2026-07-21; tracker graph published; Issue #35 authoring brief amended and independently reapproved after PR #45 review on 2026-07-23; Issue #46 selected source-first evaluation freeze and is closed after PR #48; PR #49 merged Issue #47 into `develop` as `4d80b9b8950f4d7356a9aa9806f492ae79126dab` with successful Python and frontend checks, and Issue #47 is closed; Issue #36 restricted authoring, manual provenance review, sealing, and replay completed on 2026-07-23 and now stop at the Git Lifecycle Proposal Gate before later qualification
Braincrew fixed point: `1185ba8a9e6bab038743531a56f8f2c5ce2b44eb`
AX fixed base: `a5391ae8aa2b0d1342809f3599283b7759d6e4e3`
Latest merged AX importer prerequisite: `6bfc27a7bf170172a20dd470d6fd877858c9fb80`
Pinned AX schema merge: `47673b83a9fb431f2bad550781db18c7bee8b67e`
Historical dataset: `braincrew-evaluation-dataset@2.0.0` (immutable; not an authoring or qualification target for this lane)
Future dataset: successor version greater than `2.0.0`, frozen only after the new corpus version is sealed
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
9. Issue #46 locks the source-order decision before restricted authoring. The independently
   sealed corpus is the predecessor of a successor evaluation dataset; the current dataset v2
   cannot be retrofitted as an authoring target.

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
        v
successor evaluation dataset freeze
        |
        +----> Braincrew cross-validator <---- successor dataset, read only
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

- the future corpus-pack path only after the pack is sealed;
- source files, an independently sealed `corpus-manifest.json`, license/provenance review,
  role-visibility declarations, and file digests;
- a cross-validator that compares only a sealed pack with its successor dataset;
- a post-validation `import-manifest.json` that binds the unchanged corpus digest to the successor
  dataset version and successful cross-validation receipt;
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
names, and the generic content schema. It must not read:

- `datasets/**` from the Braincrew repository;
- `tests/fixtures/**`;
- case queries, expected answers, expected evidence, scores, or split assignments;
- existing observed baseline/candidate output;
- private documents or credentials.

The exact future authoring inputs are:

- Braincrew `docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md`;
- Braincrew `schemas/ax-synthetic-seed-content-v1.schema.json`, whose SHA-256 is
  `372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb` and whose bytes must match
  the reviewed content schema published by the pinned AX implementation;
- an empty isolated staging directory outside the Braincrew repository.

Braincrew `schemas/ax-synthetic-seed-pack-v1.schema.json`, SHA-256
`4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa`, governs only the future
post-qualification `import-manifest.json`. It is not an authoring input and does not govern the
staged `corpus-manifest.json`.

Issue #35 now supplies the separately authored
`docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md`. Its approved exact bytes are 10,680
bytes with SHA-256
`121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3`, declared in the adjacent
`.sha256` file. The brief pins the AX external visibility-role contract at merge
`47673b83a9fb431f2bad550781db18c7bee8b67e`, content version
`ax-synthetic-seed-content-v1`, source path `backend/src/ax_engine/seed/pack_contract.py`, and file
SHA-256 `09fe230ca2e976bec156d72987b5cf1f39419c34829e323222d11bef35e1fc2a`.
That fail-closed contract permits exactly `Executive`, `HRAdmin`, `HRPractitioner`, and
`Employee`.

The fresh authoring and independent review contexts did not inspect evaluation cases, fixtures,
queries, answers/evidence, scores, split labels, prior results, PR #29, or its branch. The final
review decision is `APPROVE` with zero material findings and is recorded in
`docs/reviews/2026-07-22-braincrew-evaluation-corpus-v2-authoring-brief-leakage-review.md` against
the exact approved digest. Issue #46's source-first order and Issue #47's durable-provenance
sealer support are complete. The data-creation policy is approved for a new session; corpus
authoring remains blocked only until this approval record is merged and the new session binds its
clean execution SHA and authoring-tool digest before source-byte creation.

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
- exact per-source byte digests and a canonical sealed-content digest that binds them.

The strict content manifest's literal `provenance_status=reviewed` is necessary but does not prove
who reviewed which bytes, when, or what they decided. Durable approval therefore requires a
create-only provenance sidecar outside the staged pack. It binds the sealed content digest and each
source ID/content digest to `newly-authored-synthetic` origin, authoring owner, `CC0-1.0`
assignment, reviewer identity, review date/timezone, approve-or-reject decision, and a digest over
canonical sidecar bytes. The Issue #47 sealing path requires that external sidecar to be a single,
read-only regular file; it rejects missing, pending, mismatched, mutable, tampered, symlinked, or
staging-contained evidence. It copies only validated canonical sidecar bytes as
`provenance-review.json` beside the sealed pack and binds their digest in
`corpus-sealing-receipt-v2`. Replay revalidates both the pack and sidecar. Historical
`corpus-sealing-receipt-v1` replay remains supported; new seals require v2 evidence. An undeclared
sidecar cannot be smuggled into the strict pack.

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
cross-validation receipt digest. Historical replay continues to accept the original
`corpus-qualification-receipt-v1` contract bound to dataset `2.0.0`. New qualification accepts
only the exact frozen successor dataset `3.0.0`, emits `corpus-qualification-receipt-v2`, and uses
`seed_version = braincrew-evaluation-dataset-3.0.0` because the reviewed AX identifier grammar does
not permit `@`. The successor receipt separately binds exact dataset ID
`braincrew-evaluation-dataset`, semantic version `3.0.0`, integrated digest, component digests,
predecessor corpus identity and digests, and 100-case count. AX therefore receives the dataset
version only after actual content alignment is proven without weakening its generic schema. A
failed cross-validation cannot produce an import manifest, which prevents an arbitrary version
string from masquerading as provenance.

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

Only after sealing and the successor evaluation dataset freeze may the Braincrew cross-validator
read both the pack and the successor dataset. It is read-only and must never emit repaired corpus
or dataset bytes. It proves:

1. strict schema and forbidden-field compliance;
2. manifest and per-file digest reproduction;
3. complete 100-case required source-identity closure;
4. exact source-text digest equality wherever the successor dataset freezes source text;
5. required visibility for `Employee`, `Executive`, and `HRPractitioner`;
6. absence of every forbidden visibility exposure;
7. provenance and license review completion;
8. non-empty distractor coverage independent of expected answer sources.

On success, the validator creates a sanitized cross-validation receipt and the separate import
manifest described above. These files bind the sealed corpus digest to the successor dataset
version and digest but do not change corpus source bytes or the content digest. On failure,
neither file is emitted.

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

The original sequence nevertheless required a blind author to produce exact source identities and
digests already frozen inside a hidden evaluation dataset. That is circular and cannot be repaired
by qualification feedback without leaking evaluation-derived identifiers or hints into authoring.

### Issue #46 source-order decision lock

Selected source-order contract: **source-first evaluation freeze**.

Rejected alternative: pre-existing, evaluation-independent exact source bytes or generator.

Reason: no independently versioned, provenance-bearing artifact predates the evaluation-specific
freeze.

Failure mode: frozen evaluation identifiers, digests, or qualification feedback reach authoring.

`braincrew-evaluation-dataset@2.0.0` remains immutable and is not a target for authoring or
qualification in this lane.

A successor dataset version greater than `2.0.0` is required after the new corpus version is
sealed.

The successor qualification receipt must bind that successor dataset version and digest to the
unchanged sealed corpus digest.

Qualification remains read-only and cannot return feedback, identifiers, or digests to authoring.

The trade-off is a new dataset freeze and corresponding qualification binding before any later
live-preflight renewal. This cost prevents the circular exact-match request. The failure response
is terminal: keep Issue #36 blocked; do not author a corrective source, relabel dataset v2, or
use a failed qualification result to start another authoring pass.

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
- read-only access to the successor dataset during post-seal cross-validation;
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

The operator path below records dependency and convergence gates, not a strict start order:

- Braincrew #35's declared tracker blocker was Braincrew #32, but PR #45 review discovered two
  additional architecture prerequisites for the following ticket: durable provenance-sidecar
  support and a non-circular source-order contract.
- AX #36 may proceed independently of the Braincrew #35 commit lane after AX #35.
  AX #36 must be complete before operator load, but it is not an Issue #35 dependency.
- Braincrew Issue #36 remains blocked only until this approval record is merged and a new session
  passes its content-addressed entry checks. Neither hidden evaluation identifiers/digests nor
  qualification feedback may be supplied to an authoring context to make its output match.

Data-creation proposal gate: **APPROVED_FOR_NEW_SESSION**.

- Approval baseline: `5cec187af3e2d5b95b35f6e6f81fee55a73d5409`.
- The execution SHA is the clean `origin/develop` commit that contains this approval record,
  descends from the approval baseline, and reproduces the approved brief digest
  `sha256:121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3`.
- Authoring owner: `codex-issue-36-authoring-agent`.
- Manual provenance reviewer: `DHChe-corpus-provenance-reviewer`. This reviewer is the human
  approval authority and must differ from the authoring owner.
- External lifecycle root: `/Users/astralpig/braincrew-issue-36-authoring`.
- Exact lifecycle targets are
  `/Users/astralpig/braincrew-issue-36-authoring/authorization/data-creation-authorization.json`,
  `/Users/astralpig/braincrew-issue-36-authoring/tool/author-corpus`, empty
  `/Users/astralpig/braincrew-issue-36-authoring/staging`, absent
  `/Users/astralpig/braincrew-issue-36-authoring/receipts/authoring-independence-receipt.json`, absent
  `/Users/astralpig/braincrew-issue-36-authoring/review/provenance-review.json`, and absent
  `/Users/astralpig/braincrew-issue-36-authoring/sealed`. The staging target must be empty; all
  other create-only targets must be absent. All targets must be outside the repository and must not
  be symbolic links.
- Create-only authorization record:
  `/Users/astralpig/braincrew-issue-36-authoring/authorization/data-creation-authorization.json`
  uses schema `corpus-data-creation-authorization-v1`. It binds approval authority `DHChe`, the
  exact execution SHA, authoring-tool SHA-256, four exact input digests, all lifecycle target
  paths, authoring owner, manual reviewer, and its own canonical digest. The authorization record
  is create-only and must exist before authoring. Launch must reject any authorization-record
  mismatch.
- Allowed authoring inputs are exactly:
  `docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md` at
  `sha256:121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3`;
  `schemas/ax-synthetic-seed-content-v1.schema.json` at
  `sha256:372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb`;
  `schemas/ax-synthetic-seed-content-v1.schema.sha256` at
  `sha256:c9dae9c47ce20f2e4b5c954dbd467e051ebf33081e13a033cc23f9b418897dff`;
  and sandbox-mounted `input-digests.json` at
  `sha256:e707333d28fb9452b2823d1b6c125a1b6dcc3a0d5b118069e8bf7b502854061e`.
  These are the authoring brief, content schema, schema digest declaration, and canonical
  input-digest inventory. The pack schema, repository tree, datasets, fixtures, prior artifacts,
  credentials, network, database, AX, and qualification feedback remain denied.
- No source byte may be created before the clean execution SHA and external authoring tool SHA-256
  are recorded and revalidated. The new session may pin those two dynamic values under this
  delegated approval without another policy decision.
- Author, then review, then seal, then replay. The independence receipt and provenance sidecar are
  create-only; sealing starts only after the manual reviewer approves every exact source digest;
  qualification remains a later ticket.
- No automatic retry, in-place repair, overwrite, feedback-driven second pass, deletion, or
  alternate input is authorized. A dirty or wrong SHA, digest drift, unexpected input or
  capability, non-empty staging, existing target, unsupported sandbox, nonzero authoring exit,
  empty or invalid output, manual rejection, sidecar mismatch, sealing failure, or replay failure
  stops the lifecycle immediately.
- RED contract tests must first prove the entry pins, restricted inputs, create-only targets,
  distinct owner/reviewer authority, exact order, and every stop condition before any source-byte
  authoring attempt.

1. approve and review the Braincrew and AX design documents;
2. publish `to-spec` parents and the dependency-reviewed `to-tickets` graph;
3. implement and merge AX #33 schema/dry-run, AX #34 principal validation, and AX #35 atomic apply;
4. vendor and digest-check the reviewed AX JSON schema in Braincrew #31, then stop at its Git gate;
5. implement Braincrew #32 authoring isolation, #33 qualification, and #34 principal/mapping repair
   from separate clean baselines with RED/GREEN and independent review;
6. commit the independently approved Braincrew #35 brief and review-discovered blocker record, then
   prove its committed bytes equal the approved digest at the separate Git Lifecycle Proposal Gate;
7. design, implement, and independently review sealer support for accepting, preserving, and
   replaying the create-only provenance sidecar;
8. apply Issue #46's selected source-first evaluation freeze: seal a new independent corpus
   version before any successor evaluation case is frozen, without qualification feedback;
9. only after both prerequisites and this gate record are published, in a fresh restricted context, run Braincrew #36 after its RED entry contracts pin the clean execution SHA and authoring-tool digest;
10. freeze the successor evaluation dataset with a version greater than `2.0.0`, then use
    Braincrew #37 to cross-validate the unchanged sealed pack against the successor dataset;
11. at the separate AX #37 operational gate, run the exact importer dry-run;
12. create and verify a restricted PostgreSQL snapshot outside both repositories;
13. at the operator-load gate, require AX #36 disposable-PostgreSQL idempotency/concurrency proof
    to be complete;
14. perform the approved atomic AX load once and preserve sanitized evidence;
15. query and freeze all three role-visible corpus identities;
16. re-run all six strict parse observations through the reviewed principals and mappings;
17. create and replay the Braincrew #38 preflight artifact;
18. stop at `READY`.

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

`braincrew-eval seal-corpus` now requires one isolated staging directory, one output root, and one
external `--provenance-sidecar`. It reads only canonical `corpus-manifest.json`, the ordered
declared source files, and the sidecar; rejects undeclared files and unsafe/symlink/non-POSIX paths;
and copies the exact validated bytes into
`<output-root>/<corpus-id>/<corpus-version>/`. An existing destination returns
`SEALED_CORPUS_VERSION_EXISTS`; no existing byte is opened for write.

The validator mirrors the shared v1 byte contract: strict frozen Pydantic models, recursive
evaluation-derived-field rejection, no floats, UTF-8 without BOM, NFC, LF-only text, exact
per-source SHA-256, and a canonical ordered `sealed_content_digest`. Pack and source labels must
remain synthetic/demo, `CC0-1.0`, and reviewed. The generated `corpus-sealing-receipt-v2` stores
only corpus identity, fixed AX schema identity, ordered source IDs/digests, counts, byte total, the
provenance-sidecar digest, and its own digest. It stores no dataset version, query/answer, raw text,
credential, database location, or private path. `braincrew-eval replay` revalidates the receipt,
schema pin, manifest, current sealed source bytes, and the immutable sidecar, and rejects any
mutation.

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

### Issue #32 authoring-boundary implementation lock

`braincrew-eval launch-authoring` accepts a clean Git worktree, one committed repository-relative
brief, one empty staging directory outside that worktree, one create-only receipt path, and one
executable authoring tool outside both source and staging. Issue #47 corrects the restricted input
set to the brief, fixed `ax-synthetic-seed-content-v1.schema.json`, its committed digest declaration,
and a generated canonical digest inventory. The post-qualification
`ax-synthetic-seed-pack-v1.schema.json` is not mounted. The authoring tool receives only that
read-only input directory and the empty writable staging directory through a cleared environment.

Filesystem and network independence are operating-system capabilities, not prompt claims. On the
verified macOS path the launcher uses the built-in `sandbox-exec` deny-by-default profile; on Linux
it can use a preinstalled Bubblewrap backend and otherwise fails closed as
`AUTHORING_SANDBOX_UNAVAILABLE`. Neither path adds a repository package dependency. The sandbox
denies the Braincrew and AX repositories, evaluation datasets, test fixtures, prior artifacts,
database paths or sockets, inherited credential environment, private documents, undeclared
filesystem content, network access, and post-seal validator feedback. Unsupported or missing
sandbox support never falls back to an unrestricted process.

The create-only `corpus-authoring-independence-receipt-v1` binds the clean Braincrew commit, tool
name/version and executable/invocation digests, all input digests, the fixed denied-capability
classes, sandbox backend, opaque staging run identity, UTC start/end time, duration, exit status,
and path-redacted output file/tree digests. It records neither process stdout/stderr nor raw paths
or content. Prompt transcripts, source text, secret values, query/answer/expected-evidence material,
scores, and split labels therefore do not enter the retained receipt.

The authoring launcher never imports or invokes the Issue #31 sealer or any future qualification
validator. Its only output lane is the isolated staging directory plus the external sanitized
receipt. A post-seal result is an explicitly denied capability class, so a qualification failure
cannot become a new prompt, input mount, or mutation command in this process.

The first RED was five tests failing because `launch-authoring` did not exist. Minimal GREEN passed
those five. Review-driven RED/GREEN then rejected non-Braincrew source remotes, narrowed metadata
visibility to declared/runtime path ancestors, converted invalid tool labels into a typed error, and
removed broad `/Library` reads that exposed the system keychain. All seven authoring tests now pass,
including a real macOS sandbox probe that can read the four declared inputs and write staging while
repository, dataset, fixture, artifact, AX, database, credential, private-document,
undeclared-filesystem, system-keychain, network, and validator-feedback attempts all observe
denial. Actual brief approval, corpus text authoring, sealing execution, dataset-v2 qualification,
principal mapping, AX operation, and experiment execution remain later tickets. Final verification
reports `239 passed` across the repository and `32 passed` across the combined authoring/sealing
boundary, with frozen sync, Ruff format/lint, strict mypy, installed CLI help, and Git whitespace
validation also passing.

### Issue #33 post-seal qualification implementation lock

`braincrew-eval qualify-corpus` accepts only an Issue #31 sealed directory, the exact
`braincrew-evaluation-dataset@2.0.0` bundle, and bounded AX tenant/demo target identifiers. It first
replays the pinned AX schemas, strict manifest, every source digest, sealed-content digest, and
sealing receipt. It independently validates the 100-case dataset identity as
`sha256:ef6b0a1f50fcd2ecb8b5d7addc7bc5daaa54537899a1ac6faba7c784eee6e98a`; dataset v2 reuses the
unchanged v1 parsing, retrieval, and grounded component bytes while using a dedicated v2 card.

The validator projects all parsing, retrieval, grounded-answer, and visibility/abstention cases
into a complete source requirement set. It checks exact full-source digests wherever the dataset
freezes source text, `Employee`/`Executive`/`HRPractitioner` required roles, forbidden role
exposure, synthetic reviewed `CC0-1.0` provenance, and at least one source independent of every
required or forbidden dataset identity. It never changes corpus or dataset bytes and returns only
`CORPUS_PACK_SCHEMA_INVALID`, `CORPUS_PACK_DIGEST_MISMATCH`, `CORPUS_REQUIRED_SOURCE_MISSING`,
`CORPUS_SOURCE_TEXT_DIGEST_MISMATCH`, `CORPUS_REQUIRED_VISIBILITY_MISMATCH`,
`CORPUS_FORBIDDEN_VISIBILITY_MISMATCH`, or `CORPUS_PROVENANCE_REVIEW_REQUIRED` on failure.

Success publishes canonical `qualification-receipt.json` and `import-manifest.json` as a
create-only pair. The sanitized receipt binds corpus, sealing receipt, exact dataset/component
digests, case count, source identities, expected/observed digests, roles, and distractor count. The
strict AX envelope uses schema-valid `braincrew-evaluation-dataset-2.0.0` as `seed_version` while
the receipt carries the exact `braincrew-evaluation-dataset@2.0.0` identity. Pair publication is
rollback-safe on ordinary I/O failure; replay revalidates current pack, packaged exact dataset,
receipt, and import bytes and rejects tampering.

The first RED was 13 tests failing on the absent v2 manifest and qualification command. Review
then reproduced stale v1 card metadata, missing wheel replay resources, and partial pair-publication
risk before repair. All 15 focused tests and all 254 repository tests pass, with Ruff format/lint,
strict mypy, wheel-content validation, replay, tamper rejection, and Git whitespace validation.
Actual authoring/sealing/qualification execution and every AX operation remain Issues #35-#38.

### Issue #42 live-preflight substrate implementation lock

Issue #34 could not be isolated on merged `develop`: the strict AX corpus-identity and parse
operations plus a compatible create-only live evidence/replay boundary existed only inside the
unmerged Issue #15 branch. Importing that branch would also import prompt/model planning and live
experiment orchestration outside Issue #34. The accepted minimum extraction is therefore Braincrew
Issue #42, a native child of #30 and native blocker of #34.

Issue #42 pins `ax-sut-http-v1` to merged AX
`72805930d9addd8ea41743d1922acf8de621c3f8`. The Adapter exposes strict
`GET /v1/evaluation/corpus-identity` and
`GET /v1/evaluation/attachments/{attachment_id}/parse-observation` calls with canonical request
identity, safely encoded attachment paths, complete attempt history, exact response schemas, and
bounded permanent-error detail. The Issue #7 retry taxonomy is unchanged: timeout, `429`, and
`5xx` may use the three-attempt ceiling, while other HTTP and schema failures are permanent.

The new `live-preflight-evidence-v1` boundary accepts already collected Adapter observations. It
stores corpus identity, applied request roles, lifecycle/parser/source digests, span
identities/digests/offsets, structure counts, attempts, and caller-supplied typed blockers. It
never stores raw extracted text or span text. Publication uses create-only file semantics, and the
installed replay command strictly reloads the complete schema and recomputes its logical digest.
The artifact state is only `captured`; Issue #42 cannot report `READY`, create a parsing-quality
result, call providers, or run a baseline/candidate/comparison.

Issue #34 still owns every evaluation policy decision: pre-HTTP canonical principal UUID checks,
mapping AX principal detail to `EVALUATION_PRINCIPAL_*`, projecting the current dataset-v2
Verification documents onto the six reviewed attachment UUIDs, proving the active owner and exact
`HRPractitioner` role, distinguishing mapping failures from existing `LIVE_*` blockers, and
qualifying the six raw-text-free response digests. Issue #38 remains the only ticket that may renew
the actual live preflight and create a READY artifact.

The clean baseline passed all 254 pre-change tests before RED. The first contract/acceptance run
failed on the absent response models, artifact module, and new AX pin. Review-driven tests then
reproduced nested response-digest rehash bypass, private-path retention, stale capability evidence,
ambiguous attachment naming, mixed run identity, and the stale grounded Adapter test pin. All 26
focused tests including that grounded regression and all 264 repository tests pass after repair,
with Ruff format/lint, strict mypy, and Git whitespace validation also green.

### Issue #34 principal and attachment preflight implementation lock

Issue #34 consumes the merged Issue #42 seam without importing Issue #15. `AxHttpAdapterConfig`
now rejects any tenant or user value that is not the canonical lowercase UUID spelling before an
HTTP request can be constructed. The policy collector additionally requires the reviewed active
owner `22222222-2222-2222-2222-222222222222` and applies only `HRPractitioner`. A malformed
identifier yields non-retryable `EVALUATION_PRINCIPAL_ID_INVALID`; a well-formed unknown or
inactive AX subject yields non-retryable `EVALUATION_PRINCIPAL_SUBJECT_INVALID`.

Dataset `braincrew-evaluation-dataset@2.0.0` intentionally reuses the v1 parsing component bytes.
Its six Verification documents `synthetic-rule-015` through `synthetic-rule-020` must match the
reviewed immutable attachment map in section 8 exactly. Missing, malformed, extra, unreviewed,
nonexistent, or response-mismatched attachment identities yield
`PARSE_ATTACHMENT_MAPPING_INVALID`. Inaccessible or otherwise failed operations retain the
existing `LIVE_PARSE_OBSERVATION_*` family and the Adapter's timeout, `429`, and `5xx` retry
history. Before any parse call, the collector also requires the exact frozen dataset ID, version,
integrated digest, and parsing/retrieval/grounded component digests. The accepted identity is
retained in the artifact and replay rejects a substituted identity even if its top-level logical
digest is recomputed. Every capture produced after that identity is accepted uses schema
`principal-attachment-preflight-evidence-v1` and carries explicit
`capture_contract="principal-attachment-preflight-v1"`; that schema requires the frozen identity on
partial and blocked parse captures, not only on a complete six-probe capture. The older generic
Issue #42 substrate remains `live-preflight-evidence-v1` and retains its complete caller-supplied
observation/blocker compatibility. Replay returns the schema version so an Issue #34 consumer can
require the principal-attachment schema rather than treating a generic v1 artifact as qualified
policy evidence. The logical digest proves internal replay consistency, not artifact origin or
authenticity. Replay of the Issue #34 schema also revalidates the exact ordered six-case attachment
map, reviewed owner, sole `HRPractitioner` role, fixed timeout, run/case/correlation identity, and
parse-only request shape. Query, corpus, record, retrieval-limit, and evidence-limit fields must be
absent. An unblocked artifact must contain all six probes; an incomplete artifact must contain one
terminal blocker for the next expected probe, or the pre-probe mapping blocker when no request was
eligible to run. An operation blocker retains the same canonical request, so even a first-probe
connection or authorization failure proves which tenant, subject, role, and attachment were tried.

A successful capture requires all six responses to bind the requested attachment, exact pinned
AX parser identity `utf8-text`/`stdlib-1`, canonical source-text digest, and valid span
offsets/text digests for every span that is present. An available parse with zero spans remains a
quality observation for the downstream evaluator rather than becoming a transport blocker. An
available parse carrying a failure code is internally inconsistent and yields
`LIVE_PARSE_OBSERVATION_FAILED`. The retained artifact records exact request role, structure
counts, successful attempts, failed-operation retry attempts on the blocker, dataset identity,
and sanitized response digests, but no raw extracted or span text. Untrusted response correlation
headers are retained only as SHA-256 digests across successful and blocked attempts. A retryable
failure followed by an HTTP success whose parser, source, span, or attachment evidence is rejected
retains the complete attempt sequence on its blocker. Replay keeps
field-presence semantics for legacy v1 artifacts that predate dataset identity and blocker-attempt
fields, while the Issue #34 schema requires its contract and frozen identity. Both schemas retain
`capture_state="captured"`; transport success creates neither parsing-quality output nor READY.
Issue #38 alone owns an actual renewed preflight and READY publication.

A non-timeout HTTP request failure such as a connection error remains non-retryable under the
existing policy, but it is no longer evidence-free. The Adapter records one `request_error` attempt
with operation, ordinal, method, path, and elapsed time and the collector preserves it on the
existing `LIVE_PARSE_OBSERVATION_UNREACHABLE` blocker. Attempts with no response cannot carry a
response-correlation digest. Blocker code, detail, terminal outcome, and the fixed principal or
not-found HTTP status must agree; replay rejects relabeling one failure as another after rehashing.
Server-controlled span identifiers must match the bounded safe-ID grammar before sanitization or
the response becomes `LIVE_PARSE_OBSERVATION_FAILED` without retaining the unsafe value.

The clean Issue #34 baseline passed all 264 pre-change tests before RED. The first 15 new
contract/acceptance tests failed on the absent policy collector and canonical user UUID contract;
minimal GREEN passed those 15. Ticket review then reproduced acceptance of a non-matching parser
as `1 failed, 14 passed` before the exact pinned parser repair reached 16 focused passes. The
affected regression set initially reported 52 passing tests. PR #44 review remediation then
reproduced the initial four bot findings plus legacy replay drift, correlation-header retention,
and rehash-with-identity-removal before repair. A later Codex re-review separately reproduced
retry-history loss after a recovered but invalid response and frozen-identity removal from a
blocked partial capture before the discriminator repair. Independent re-review then reproduced
simultaneous discriminator-and-identity removal before semantic downgrade protection, then
reproduced overbroad classification of generic reviewed-attachment evidence and unrelated legacy
`LIVE_PARSE_*` blockers. Fingerprint inference was rejected in favor of a separate Issue #34 schema:
new-schema removal is rejected, while the complete generic v1 schema remains compatible. The
latest Codex re-review then reproduced replay acceptance after deleting a successful probe and
missing attempt evidence for a connection failure. Both were observed RED before the exact
six-probe / terminal-blocker replay contract and `request_error` retention reached GREEN.
Independent review then reproduced rejection of the existing unavailable blocker, replay of
rehashed parser/source policy drift, and replay after blocker-attempt removal. The Issue #34
validator now rechecks strict response/source/span and attempt evidence while preserving the full
existing `LIVE_PARSE_OBSERVATION_*` family. A final adversarial pass additionally bound each span's
digest to its frozen canonical substring, required one tenant across retained observations, and
required each blocker code to agree with its terminal attempt outcome. A terminal timeout or
retryable HTTP failure must retain the Adapter's full three-attempt exhaustion history. A fourth
Codex review then reproduced five more replay gaps: first-probe blockers without principal request
evidence, code/detail taxonomy relabeling, parse requests carrying unrelated payload, response
correlations on response-less attempts, and unsafe span identifiers. Six focused tests first
failed across those contracts; canonical blocker requests, exact request/taxonomy validation,
response-aware correlation rules, and safe span-ID rejection then reached GREEN. The five focused
preflight/adapter files first reported 52 passes. Independent Standards/Spec review then reproduced
generic-v1 span-ID rejection, and Standards also reproduced raw query retention through the new
generic blocker request field. Both became RED before shared span compatibility was restored,
generic blocker requests were forbidden, and safe span IDs remained principal-schema-only. The
five focused files now report 54 passes and all 293 repository tests pass. No AX
operation, corpus mutation, experiment run, READY artifact, or PR #29 modification occurred.

### Issue #35 evaluation-blind authoring brief lock

Issue #35 was authored in fresh contexts restricted to `AGENTS.md`, the Issue #35 body, the
vendored AX content and pack schemas and digests, Python execution settings, and the explicitly
authorized AX `VisibilityRole` source. No evaluation dataset, fixture, case/query, expected answer/evidence,
score, split, benchmark artifact, prior run output, PR #29, or Issue #15 branch content entered the
authoring or leakage-review contexts.

The brief limits future content to generic HR/labor families and requires every source to be newly
authored synthetic/demo material, licensed `CC0-1.0`, and explicitly provenance-reviewed.
Public-source ingestion or adaptation is excluded so the pack-wide `synthetic=true` label remains
truthful. Korean or English, canonical BOM-free UTF-8/NFC/LF text, normalized relative POSIX paths,
explicit source authority, generic authority-based distractors, and the exact AX role vocabulary
`Executive`, `HRAdmin`, `HRPractitioner`, and `Employee` remain fail-closed boundaries. It creates
no corpus bytes, manifest, AX operation, qualification, preflight, experiment, or evaluation result.

TDD first observed two failures for the absent brief. Review-driven cycles then observed four
failures for an unpinned role authority and missing reviewed-to-committed byte binding, two
failures for overbroad public-domain licensing and incomplete byte/path constraints, and two
failures for absent digest/review evidence. A later Standards review found that the brief still
described its now-completed review and lock as pending. One new contract test failed before a fresh
evaluation-blind context corrected only that state, which intentionally invalidated the earlier
approval. New exact-byte expectations then produced two failures against the stale lock artifacts
before the independent re-review and relock restored all ten focused tests. The independent leakage
reviewer approved those exact bytes with zero material findings. PR #45 review then correctly
found that staged authoring exposed the later import-pack schema, that the strict manifest could
not retain independent provenance-approval evidence, and that matching a hidden dataset's frozen
source identities would make authoring circular. Focused contract tests failed before the brief
pinned staged authoring to `schemas/ax-synthetic-seed-content-v1.schema.json` at SHA-256
`372118334771854c867d3e7168331ed4cabb9380db95d4aa624345bbe004b1cb` and limited the pack schema at
SHA-256 `4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa` to the post-qualification
import manifest. Issue #47 repaired staged authoring to expose the content schema and its
pinned digest only. A fresh evaluation-blind context added the provenance sidecar and source-order
gates without reading evaluation material,
and a separate blind reviewer
approved the exact 10,680-byte brief with zero material findings at SHA-256
`121e2fa1f2c25eb57e714a25acf662c7a3d928ab68e5ea5f9a081f7368e93fe3`.
The adjacent digest declaration and durable review record bind that decision to exact bytes.
PR #49 merged and verified Issue #47; Issue #46's source-first evaluation freeze is also closed.
The data-creation proposal gate is now `APPROVED_FOR_NEW_SESSION` on baseline
`5cec187af3e2d5b95b35f6e6f81fee55a73d5409`. Issue #36 remains blocked only until this approval
record is merged and the fresh session pins a clean descendant execution SHA plus the external
authoring-tool digest before creating any source byte.

## 12. Rejected alternatives and consequences

- Reverse-generating the corpus from expected evidence, source identities, or frozen source
  digests was rejected because the evaluator would
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
pack passes cross-validation against its successor dataset version, AX dry-run and atomic load
succeed from approved clean commits, the three role corpus identities include that successor
dataset version, all six strict parse probes succeed, and a create-only preflight replays as
`READY`.

No baseline, candidate, comparison, or live quality claim is part of this completion condition.

## 14. Implementation progress checkpoint

As of 2026-07-23, the `to-spec` parents and `to-tickets` graph are published. AX #33, #34, and
#35 are merged; AX #36 remains open. Braincrew PR #44 merged #34 as
`67d7c104757f60194e59df20240ac47f8be9c027`; #34 is `CLOSED/COMPLETED`, and its worktree and
local/remote feature branches are removed. Braincrew #35 is closed after PR #45 merged. Issue #46
now selects source-first evaluation freeze: the next dataset must be a successor version created
only after a new independently sealed corpus version, while dataset v2 remains immutable and
outside this authoring lane. PR #49 has merged and verified Braincrew Issue #47, and Issue #47 is
closed. The separate data-creation proposal gate was `APPROVED_FOR_NEW_SESSION`; Issue #36 then
passed its clean-SHA, brief-digest, tool-digest, lifecycle-path, and RED-contract entry checks at
`8e669db46b698b8791739feee910ba1b561a0936`, received `ready-for-agent`, and executed the required
Author → manual Review → Seal → Replay order without retry. The immutable
`braincrew-independent-hr-corpus@1.0.0` contains 14 exact source digests and has sealed content
digest `sha256:5f0c254b3dc64b23470029b1004106dc078a9602062da8fa8041623bf91fb7e4`,
provenance digest `sha256:eb43fc824cd54bf10e8805b5fdeb1915bcaac368cb458ce8981a481cd7d4fce1`,
and replayed receipt digest
`sha256:bc508b6001facbef67bacd7e0c1d4d5123f04bc1e33d2849b5e7d455183df62b`.
Issue #53 then produced the source-first successor **candidate**
`braincrew-evaluation-dataset@3.0.0` in `datasets/dataset_manifest_v3.json`,
`datasets/DATASET_CARD_V3.md`, and the three v2 component files. It rebinds every case to the
immutable `braincrew-independent-hr-corpus@1.0.0` above while preserving the locked 100-case
identity: 20/30/40/10 primary-focus allocation, 70/30 Calibration/Verification split, and
unchanged evaluator semantics, metric applicability, risk policy, and threshold policy. Its
integrated digest is
`sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d`, with component digests
`sha256:33e17fbb4d3f5485df1482de37e472e1b20fceef922c9b1dda90f8d9dfc25f73` (parsing),
`sha256:9687ead24590cab1b9d244ef876f226545a1fb1aa2013c50e4be7a63430c8408` (retrieval), and
`sha256:f76a9a1fa9a6a4b467f76ce7649dc7c15f5ad7c615d6cbb20ed3394e486d94b2` (grounded). Thirteen of
the 14 sealed sources are cited; `demo-lifecycle-checklist-014` remains an uncited distractor.
`braincrew-evaluation-dataset@2.0.0` and its receipt-v1 replay remain byte-for-byte unchanged.

The candidate was bound to the
`docs/reviews/2026-07-23-issue-53-successor-dataset-review.md` checklist with external approval
authority. On 2026-07-23 `DHChe-successor-dataset-reviewer` confirmed all eight checks and recorded
`Decision: APPROVED`, freezing the exact integrated/component bytes and predecessor binding above.
The accepted retrieval-role concentration is a constraint-induced limitation, not evidence of
multi-role retrieval execution.

### Issue #37 terminal qualification evidence

Issue #37 actual qualification: **SUCCEEDED_ONCE**.

On 2026-07-23 the read-only qualifier ran exactly once against the unchanged
`braincrew-independent-hr-corpus@1.0.0` sealed content digest
`sha256:5f0c254b3dc64b23470029b1004106dc078a9602062da8fa8041623bf91fb7e4` and exact
`braincrew-evaluation-dataset@3.0.0` integrated digest
`sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d`.
The parsing, retrieval, and grounded component digests remained
`sha256:33e17fbb4d3f5485df1482de37e472e1b20fceef922c9b1dda90f8d9dfc25f73`,
`sha256:9687ead24590cab1b9d244ef876f226545a1fb1aa2013c50e4be7a63430c8408`, and
`sha256:f76a9a1fa9a6a4b467f76ce7649dc7c15f5ad7c615d6cbb20ed3394e486d94b2`.
The create-only pair uses `corpus-qualification-receipt-v2` and
`braincrew-evaluation-dataset-3.0.0`.

- Receipt logical digest: `sha256:c564b1442c135fef5d5430b313914951e2b5ab4cc7e0fd0bbbdefb0b928ea6ce`
- Qualification receipt file digest: `sha256:8843c87597db779ece932585445bae9dbdf9b5f26f4f81a7b9d069a1699968ed`
- Import logical digest: `sha256:9df8dbd212c6e0253b3c58feb392869bffb226d816805ee7ed166072596003bd`
- Import manifest file digest: `sha256:b1899d6be6017a2485d93c67066023a87f8aaa78b0b63012fb9f8d8a040f3821`

Replay reproduced the receipt and import digests, redaction checks passed, historical receipt-v1
compatibility remained green, and the sealed input tree was unchanged. No retry, repair, AX
import, database, service, snapshot, preflight, or experiment execution was performed. The next
operator-controlled step is AX Issue #37; PR #29 and `feat/issue-15-live-verification` remain
untouched and read only.

### Issue #56 AX-canonical publication-byte boundary

Braincrew Issue #56 repairs a serialization-contract mismatch without changing qualification
identity. PR #55 published `import-manifest.json` as strict canonical JSON followed by one trailing
line feed. AX PR #42 accepts only the exact canonical JSON bytes, so the historical file is rejected
with `AX_SEED_PACK_CANONICAL_BYTES_INVALID` even though its parsed content and logical
`import_digest` are correct.

Newly created import manifests therefore use newline-free canonical JSON bytes. The qualification
receipt contract remains unchanged: receipt files still use canonical JSON plus exactly one trailing
line feed. The identity split is explicit:

- Qualification receipt logical digest remains
  `sha256:c564b1442c135fef5d5430b313914951e2b5ab4cc7e0fd0bbbdefb0b928ea6ce`.
- Qualification receipt file digest remains
  `sha256:8843c87597db779ece932585445bae9dbdf9b5f26f4f81a7b9d069a1699968ed`.
- Import logical digest remains
  `sha256:9df8dbd212c6e0253b3c58feb392869bffb226d816805ee7ed166072596003bd`.
- Historical PR #55 import file digest with one trailing line feed is
  `sha256:b1899d6be6017a2485d93c67066023a87f8aaa78b0b63012fb9f8d8a040f3821`.
- The locally generated AX-canonical candidate file digest is
  `sha256:e00c7036bd67f93347957215fddc4185a18eb2e62e90bfb58657f0b7598f20ac`.

Replay remains backward compatible with receipt-v1 and with both the historical PR #55
canonical-plus-one-line-feed import representation and the new exact-canonical representation.
Leading or trailing spaces, pretty-printed JSON, multiple line feeds, and every other
non-canonical representation fail closed.

Rejected alternative:
: Loosen AX to normalize whitespace. This would weaken AX's exact publication-byte and tamper
  boundary while moving a producer defect into the consumer.

Trade-off:
: Replay carries one narrow historical exception for PR #55 canonical JSON plus exactly one line
  feed. That small compatibility branch is preferable to invalidating already published evidence,
  but it must never expand into general whitespace normalization.

Failure modes:
: A new import manifest with any trailing byte remains unusable by AX; a changed receipt byte would
  alter qualification evidence; and accepting any representation beyond the two digest-known import
  forms would hide non-canonical or tampered artifacts.

Validation evidence:
: Acceptance TDD reproduced the trailing-line-feed mismatch, preserved the receipt and logical
  digests, replayed receipt-v1 and both receipt-v2 import forms, and rejected all other tested
  whitespace forms. Exact AX SHA `e25f333b55fca34118a954a17e5e0cd88dc7ea39` accepted the locally
  generated canonical candidate read only with 14 sources and 11,528 total source bytes while
  database and provider settings were absent.

Likely follow-ups:

- "Does this authorize publication?" — No. It proves the producer implementation only.
- "What must the later operator proposal bind?" — The clean execution SHA, immutable inputs, output
  path, one-run boundary, and independent digest reviewer.
- "When may AX resume?" — Only after that separately approved create-only publication completes and
  its digest is independently verified.

This is an implementation contract, not an operational execution record. The existing external
Issue #37 qualification artifacts remain immutable. No pack was republished or requalified, and no
AX code, database, provider, snapshot, dry-run, apply, service verification, baseline, or candidate
path ran. Read-only compatibility at exact AX SHA
`e25f333b55fca34118a954a17e5e0cd88dc7ea39` accepted the new canonical bytes with 14 sources and
11,528 total source bytes while database and provider settings were absent.

Actual create-only republish remains blocked on a separate proposal that fixes the clean execution
SHA, immutable inputs, output path, one-run boundary, and independent digest reviewer. AX Issue #37
remains blocked until that republish is complete and reviewed. Braincrew Issue #38 remains blocked
until AX Issue #37 completes its own operator-controlled load and verification gates.
