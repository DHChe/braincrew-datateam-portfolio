# Independent Evaluation Corpus Provisioning Design

Date: 2026-07-20
Status: independent spec review passed; user written-spec approved 2026-07-21; tracker graph published; Issue #35 authoring brief independently approved at its pre-commit gate 2026-07-22
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

Issue #35 now supplies the separately authored
`docs/corpus/braincrew-evaluation-corpus-v2-authoring-brief.md`. Its approved exact bytes are 8,531
bytes with SHA-256
`f21f5df1950ec0872e45c956f9c689b09c59362d2cae53dbd2f86635bbb690ae`, declared in the adjacent
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
the exact approved digest. Corpus authoring remains blocked until a separate Git Lifecycle
Proposal Gate creates a clean Braincrew commit and post-commit byte equality reproduces the same
digest.

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
cross-validation receipt digest. The reviewed AX identifier grammar does not permit `@`, so the
strict envelope sets `seed_version = braincrew-evaluation-dataset-2.0.0`. The qualification
receipt separately binds exact dataset ID `braincrew-evaluation-dataset`, semantic version
`2.0.0`, integrated digest, component digests, and 100-case count. AX therefore receives the
dataset version only after actual content alignment is proven without weakening its generic schema.
A failed cross-validation cannot produce an import manifest, which prevents an arbitrary version
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

The operator path below records dependency and convergence gates, not a strict start order:

- Braincrew #35's only blocker is Braincrew #32. Its separate commit gate must reproduce the
  independently approved brief digest before Braincrew #36 authoring starts.
- AX #36 may proceed independently of the Braincrew #35 commit lane after AX #35.
  AX #36 must be complete before operator load, but it is not an Issue #35 dependency.

1. approve and review the Braincrew and AX design documents;
2. publish `to-spec` parents and the dependency-reviewed `to-tickets` graph;
3. implement and merge AX #33 schema/dry-run, AX #34 principal validation, and AX #35 atomic apply;
4. vendor and digest-check the reviewed AX JSON schema in Braincrew #31, then stop at its Git gate;
5. implement Braincrew #32 authoring isolation, #33 qualification, and #34 principal/mapping repair
   from separate clean baselines with RED/GREEN and independent review;
6. commit the independently approved Braincrew #35 brief and prove its committed bytes equal the
   approved digest at the separate Git Lifecycle Proposal Gate;
7. in a fresh restricted context, run Braincrew #36 independent authoring/sealing without
   evaluation data access;
8. use Braincrew #37 to cross-validate the unchanged sealed pack against dataset v2;
9. at the separate AX #37 operational gate, run the exact importer dry-run;
10. create and verify a restricted PostgreSQL snapshot outside both repositories;
11. at the operator-load gate, require AX #36 disposable-PostgreSQL idempotency/concurrency proof
    to be complete;
12. perform the approved atomic AX load once and preserve sanitized evidence;
13. query and freeze all three role-visible corpus identities;
14. re-run all six strict parse observations through the reviewed principals and mappings;
15. create and replay the Braincrew #38 preflight artifact;
16. stop at `READY`.

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

### Issue #32 authoring-boundary implementation lock

`braincrew-eval launch-authoring` accepts a clean Git worktree, one committed repository-relative
brief, one empty staging directory outside that worktree, one create-only receipt path, and one
executable authoring tool outside both source and staging. The launcher reuses the Issue #31 fixed
`ax-synthetic-seed-pack-v1.schema.json` digest and its committed declaration. It copies only the
brief, pack schema, schema digest declaration, and a generated canonical digest inventory into a
temporary read-only input directory. The authoring tool receives only that input directory and the
empty writable staging directory through a cleared environment.

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
vendored AX pack schema and digest, Python execution settings, and the explicitly authorized AX
`VisibilityRole` source. No evaluation dataset, fixture, case/query, expected answer/evidence,
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
reviewer approved the exact 8,531-byte brief with zero material findings at SHA-256
`f21f5df1950ec0872e45c956f9c689b09c59362d2cae53dbd2f86635bbb690ae`.
The adjacent digest declaration and durable review record bind that decision to exact bytes.
Authoring remains prohibited until a clean committed Braincrew SHA reproduces the same digest;
commit, push, pull request, and merge remain behind the Git Lifecycle Proposal Gate.

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
#35 are merged; AX #36 remains open. Braincrew PR #44 merged #34 as
`67d7c104757f60194e59df20240ac47f8be9c027`; #34 is `CLOSED/COMPLETED`, and its worktree and
local/remote feature branches are removed. Braincrew #35 is active from that exact merge with
`ready-for-agent`. Its evaluation-blind brief, exact digest declaration, and independent approval
record are complete locally and still await ticket review, full verification, and the Git
Lifecycle Proposal Gate. No corpus source bytes, actually authored or sealed Braincrew pack, real
qualification receipt, operator snapshot, target load, renewed Issue #38 preflight, READY artifact,
baseline, candidate, comparison, or live quality claim exists. PR #29 and
`feat/issue-15-live-verification` remain untouched and read only.
