# AX Evaluation Principal and Parse Restoration — Scope Lock

Date: 2026-07-24  
Status: LOCKED FOR ISSUE AUTHORING; NOT IMPLEMENTED OR LIVE-VERIFIED  
Braincrew decision baseline: `8242003f9ed30a4df4889c1c30abe6a36470bff0`  
AX investigation baseline: `e25f333b55fca34118a954a17e5e0cd88dc7ea39`

> **SUPERSEDED IN PART — 2026-07-25.** The requirement that the six reviewed `.txt` sources enter AX
> through **one** multipart request is not executable: AX enforces `MAX_FILES_PER_OPERATION = 5` per
> upload request (`backend/src/ax_engine/attachments/intake.py:12,54`, applied at
> `backend/src/ax_engine/attachments/service.py:64`), and
> `backend/tests/unit/test_attachment_intake.py:25` pins the six-file rejection. The authorized
> replacement is **two bounded requests of five and one into one target-owned thread**, which needs
> no AX source change. See
> [`2026-07-25-ax-b-bounded-upload-request-split.md`](./2026-07-25-ax-b-bounded-upload-request-split.md).
>
> Affected passages, by line number at pinned commit `fc1302d54ab3f3735800d31a321b6f70e947572e`:
> 376-377, 470, 522, 543-544, 866, 914. Their original wording is retained verbatim below.
> **Every other locked element of this document remains in force**, including the preserved
> invariant "one target-owned thread and six AX-generated attachment IDs".

## 1. Decision

Braincrew Issue #38 cannot truthfully reach `READY` through a principal-only AX repair. Read-only
database evidence reports that the imported target tenant has zero users and that
`thread_attachments` plus `attachment_extractions` are empty, so the six attachment UUIDs frozen
by Braincrew no longer name live AX records.

The follow-up is therefore split into two dependent AX issues:

```text
AX-A tenant-scoped evaluation subject
  -> AX-B six-source normal attachment lifecycle
      -> shared AX operational handoff
          -> Braincrew #38 receipt consumption, repin, capture, replay, READY
```

- **AX-A** implements a local/test-only, dry-run/apply evaluation-subject provisioning command and
  sanitized receipt.
- **AX-B** depends on AX-A and re-provisions the six reviewed parsing sources through the existing
  conversation, attachment, scan, parse, approval, and materialization lifecycle. It emits the new
  attachment mapping and sanitized operational evidence.
- **Braincrew #38** consumes the two AX receipts and live HTTP observations. It does not create
  users, upload attachments, approve sources, write AX tables, operate workers, or repair AX state.

The AX function `validated_evaluation_principal` remains unchanged. Its joined requirement that
`Tenant.id`, `User.id`, and `User.is_active` match one active subject is the tenant-isolation
invariant, not a defect.

## 2. Evidence and defect classification

### Measured facts

- AX Issue #37 loaded the qualified corpus into tenant
  `ae09ec7f-a7bc-5bf8-a645-8b3f1e623850`.
- The applied pack identity is `braincrew-independent-hr-corpus@1.0.0`.
- The applied AX seed version is `braincrew-evaluation-dataset-3.0.0`.
- The imported seed counts are 14 source documents, 77 chunks, 77 evidence spans, and 154 vector
  records.
- SELECT-only review reported zero users in the target tenant and zero rows in
  `thread_attachments` and `attachment_extractions` across the inspected database.
- User `22222222-2222-2222-2222-222222222222` exists in tenant
  `11111111-1111-1111-1111-111111111111`, not in the imported target tenant.
- The user confirmed that `OPENAI_API_KEY` rotation is complete. This decision record treats that
  security response as **RESOLVED** and does not inspect, reproduce, or retain the secret.

### Classification

| Class | Finding | Consequence |
| --- | --- | --- |
| Code failure | None reproduced in `validated_evaluation_principal`. | Do not relax or bypass the joined active-user check. |
| Design flaw | Braincrew froze one historical owner and six environment-specific attachment UUIDs while the new corpus was loaded into a different tenant. | Replace the live identity and mapping through reviewed receipts. |
| State/data gap | The target tenant has no user, and no live attachment or extraction exists for any tenant. | AX-A and AX-B are both required before live preflight. |
| Unverified assumption | HTTP services, workers, scanner, fake provider, request-scoped role projection, new snapshots, upload bytes, generated attachment IDs, and final responses have not been exercised in this documentation task. | No live, parsing-quality, corpus-identity, or `READY` claim is allowed. |
| Workflow gate | AX-A implementation/review, AX-B implementation/review, a separately approved operational gate, and Braincrew #38 repinning remain pending. | Stop after documentation until each later gate is explicitly authorized. |

## 3. Locked identities and wording

### Dataset wording

The current corpus qualification and import identity is:

- human-facing dataset bundle: `braincrew-evaluation-dataset@3.0.0`;
- exact AX `created_by_seed_version` / `contributing_versions` value:
  `braincrew-evaluation-dataset-3.0.0`;
- integrated dataset digest:
  `sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d`.

The six parsing cases retain the historical component contract:

- the integrated successor manifest is version `3.0.0`;
- its parsing, retrieval, and grounded component documents still declare component version
  `2.0.0`;
- the successor manifest freezes component digests
  `parsing=sha256:33e17fbb4d3f5485df1482de37e472e1b20fceef922c9b1dda90f8d9dfc25f73`,
  `retrieval=sha256:9687ead24590cab1b9d244ef876f226545a1fb1aa2013c50e4be7a63430c8408`,
  and
  `grounded=sha256:f76a9a1fa9a6a4b467f76ce7649dc7c15f5ad7c615d6cbb20ed3394e486d94b2`;
- the six parse probes therefore remain the historical dataset-v2 parsing Verification cases;
- the re-uploaded attachments are normal tenant-upload materializations, not seed-import records
  for `braincrew-evaluation-dataset-3.0.0`.

Braincrew Issue #38 must require that each role-visible corpus identity includes
`braincrew-evaluation-dataset-3.0.0`. It must not claim that the six tenant-upload materializations
carry that seed version.

### Target tenant and evaluation subject

The target tenant is fixed:

```text
ae09ec7f-a7bc-5bf8-a645-8b3f1e623850
```

The AX-A subject UUID is deterministic and review-pinned:

```text
uuid5(
  NAMESPACE_URL,
  "ax-evaluation-principal:braincrew-demo-tenant:braincrew-live-evaluation-v1"
) = 26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe
```

The literal UUID is the runtime contract. Implementations may recompute it as a drift check but
must not generate a random replacement.

The fixed synthetic user metadata is:

```text
email: braincrew-live-evaluation@synthetic.invalid
display_name: Braincrew Live Evaluation Operator
is_active: true
authority_revision: 1
purpose: braincrew-live-evaluation-v1
```

AX-A creates exactly one active target-tenant `User`. It neither requires nor changes persisted
role or membership state. In local/test, each request supplies its exact role through
`x-ax-roles`; AX continues to derive permissions from its existing static permission mapping.

One target-local synthetic subject is intentionally used for the local/test evaluation workflow.
Every request sends one exact `x-ax-roles` value:

- `HRPractitioner` creates the conversation, uploads the six files, and reads strict parse
  observations;
- `HRAdmin` approves the six parsed attachments for materialization;
- `Employee`, `Executive`, and `HRPractitioner` are sent separately for the three corpus-identity
  probes.

This request-scoped role projection is an existing local/test authentication behavior, not
persisted membership or a production identity design. AX-A must not make it available outside
local/test.

## 4. Security and repository invariants

1. Do not change `validated_evaluation_principal`, the evaluation routes, shared
   `current_principal`, production bearer authentication, visibility predicates, or tenant-aware
   joins.
2. Never move user `22222222-2222-2222-2222-222222222222` or reuse its UUID in the target tenant.
3. Never update an existing user, reactivate an inactive user, or mutate persisted authorization
   state.
4. AX owns all database and attachment lifecycle actions. Braincrew receives only versioned files,
   sanitized receipts, and HTTP observations.
5. Do not store credentials, bearer tokens, database URLs, raw source text, extracted text,
   vectors, private paths, or environment values in receipts.
6. Keep the six source bytes synthetic and publicly releasable. No customer, employee, or company
   document may enter this workflow.
7. Existing immutable historical Braincrew artifacts remain replayable. Repinning applies only to
   the new live-preflight contract and artifact.
8. Every output path is create-only. A pre-existing output stops the operation.
9. No failure authorizes automatic retry with changed inputs, cleanup, deletion, rollback,
   snapshot restore, re-import, or alternate provider configuration.
10. No AX-A or AX-B success is a Braincrew `READY`, parsing-quality, retrieval-quality, or
    answer-quality claim.

## 5. AX-A issue contract

### Title

Provision a tenant-scoped local evaluation subject for the Braincrew live preflight

### Problem statement

AX correctly rejects the current Braincrew pair because the imported corpus tenant has no active
user matching the historical owner UUID. Braincrew cannot call either evaluation endpoint until AX
has one active, target-tenant subject. Relaxing the joined principal check would weaken tenant
isolation, so the missing state must be provisioned explicitly.

### Implementation boundary

Add an AX-owned local/test command, recommended entry point:

```text
ax-evaluation-principal
```

Recommended implementation surfaces:

```text
backend/src/ax_engine/evaluation/principal_provisioning.py
backend/src/ax_engine/evaluation/principal_cli.py
```

The command has two modes:

- **dry-run** validates environment, tenant, completed seed run, deterministic subject identity,
  and user absence/exact idempotent state with zero writes;
- **apply** reserves the create-only receipt path, repeats all checks in one transaction, validates
  the exact user before commit, attempts the commit, validates the exact stored user again, and
  writes a receipt only after that post-commit confirmation.

### Inputs

- environment, which must be `local` or `test`;
- target tenant ID, which must equal
  `ae09ec7f-a7bc-5bf8-a645-8b3f1e623850`;
- expected `demo_company_id=braincrew-demo-company`;
- expected completed `seed_version=braincrew-evaluation-dataset-3.0.0`;
- deterministic subject UUID and fixed metadata from section 3;
- create-only receipt path;
- explicit dry-run or apply mode.

No email, display name, purpose label, or user UUID is caller-selectable. Request roles are not
provisioning inputs; later local/test HTTP calls supply one exact `x-ax-roles` value and use AX's
existing static permission mapping.

### Outputs

Schema: `ax-evaluation-principal-receipt-v1`.

The receipt contains:

- schema version and state: `ELIGIBLE`, `PROVISIONED`, or `ALREADY_PROVISIONED`;
- exact AX commit SHA and clean/dirty status;
- target tenant ID, slug, demo-company ID, and visible `demo_company=true`;
- completed seed version, observed `DemoSeedRun` state, `corpus_mode=demo`, and visible
  `synthetic=true`;
- subject UUID, active state, authority revision, purpose label, and a digest of fixed metadata;
- created/existing user-row count;
- direct commit confirmation for apply;
- bounded failure identity when unsuccessful;
- canonical logical digest.

The receipt excludes the email value even though code fixes it; the metadata digest proves the
fixed constant without retaining a contact-shaped identifier.

### Failure codes and stop behavior

| Code | Condition |
| --- | --- |
| `EVALUATION_PRINCIPAL_ENVIRONMENT_FORBIDDEN` | Environment is not local/test. |
| `EVALUATION_PRINCIPAL_REPOSITORY_DIRTY` | AX checkout is dirty or SHA is not the reviewed issue SHA. |
| `EVALUATION_PRINCIPAL_ID_INVALID` | Tenant or deterministic subject UUID is noncanonical or drifts from the locked value. |
| `EVALUATION_PRINCIPAL_TARGET_INVALID` | Tenant is missing, not the locked demo tenant, or has the wrong demo-company identity. |
| `EVALUATION_PRINCIPAL_SEED_RUN_INVALID` | Exact completed `braincrew-evaluation-dataset-3.0.0` run is absent or mismatched. |
| `EVALUATION_PRINCIPAL_TENANT_CONFLICT` | The UUID already belongs to another tenant. |
| `EVALUATION_PRINCIPAL_STATE_CONFLICT` | Same-tenant user is inactive or its fixed metadata or authority revision differs. |
| `EVALUATION_PRINCIPAL_RECEIPT_EXISTS` | Create-only receipt path already exists. |
| `EVALUATION_PRINCIPAL_RECEIPT_UNAVAILABLE` | The receipt destination cannot be reserved or a reserved receipt cannot be written. |
| `EVALUATION_PRINCIPAL_COMMIT_INDETERMINATE` | Transaction outcome cannot be proven. |
| `EVALUATION_PRINCIPAL_DATABASE_UNAVAILABLE` | Read or write dependency fails before a proven commit. |

Any failure rolls back the current database transaction when its state is known. It preserves
evidence and stops. It does not change an existing row, select a new UUID, overwrite a receipt, or
restore a snapshot automatically.

The database transaction and filesystem receipt cannot be one atomic operation. AX-A therefore
reserves the create-only receipt path before any database mutation. A failure before commit removes
that reservation after rollback. A lost commit response or failed post-commit confirmation returns
`EVALUATION_PRINCIPAL_COMMIT_INDETERMINATE` and retains the empty reserved path. A later receipt
write failure returns `EVALUATION_PRINCIPAL_RECEIPT_UNAVAILABLE` and also retains the reservation.
Neither path claims rollback; the retained path prevents an unreviewed retry from overwriting the
evidence boundary.

### Backward compatibility

- The historical user and Braincrew artifacts remain unchanged.
- Existing unknown, cross-tenant, and inactive-subject requests keep returning the current typed
  `401 evaluation_principal_subject_invalid`.
- Existing malformed UUID behavior and corpus principal lookup `503` behavior remain unchanged.
- No migration is required; AX-A uses the existing `User` table only.
- Production bearer authentication and local/test header behavior remain unchanged.

### In scope

- deterministic local/test user provisioning;
- dry-run/apply split;
- idempotency and conflict detection;
- sanitized create-only receipts;
- regression coverage for `validated_evaluation_principal`.

### Out of scope

- changing authentication, authorization, role permissions, tenant isolation, or HTTP routes;
- changing request-role parsing, the static permission mapping, or persisted authorization data;
- uploading or parsing attachments;
- corpus identity, provider, or worker operation;
- migration, seed importer, snapshot creation, or restore;
- Braincrew code or artifact publication;
- GitHub, commit, push, PR, or merge actions without their own lifecycle gates.

### Test matrix

| Layer | Required proof |
| --- | --- |
| Unit | UUIDv5 literal reproduction, fixed metadata digest, exact receipt shape and JSON types, canonical digest, and secret/raw-field scan. |
| Service | Dry-run is no-write; apply creates exactly one active target-tenant user; exact rerun is `ALREADY_PROVISIONED`. |
| Conflict | Wrong tenant, cross-tenant UUID, inactive same-tenant row, metadata drift, wrong seed run, existing receipt, and non-exact concurrent insert all fail closed. An exact concurrent insert is reread once and returns `ALREADY_PROVISIONED`. |
| Transaction | Pre-commit failure leaves no user or receipt. An unprovable commit or post-commit confirmation preserves the empty reserved path and emits no success receipt. |
| Filesystem | An unavailable destination fails before mutation; a write failure returns the dedicated typed code and preserves the reserved path. |
| API regression | Malformed, unknown, cross-tenant, and inactive evaluation subjects retain current 400/401 behavior and zero denied-access audit for invalid subjects. |
| CLI | Registration, help, dry-run, apply, receipt creation, create-only collision, and unsupported environment. |

Recommended tests:

```text
backend/tests/unit/test_evaluation_principal_provisioning.py
backend/tests/integration/test_evaluation_principal_cli.py
backend/tests/integration/test_evaluation_api.py
backend/tests/unit/test_evaluation_principal_cli_registration.py
```

### Acceptance criteria

1. The literal subject UUID is exactly `26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe`.
2. Dry-run against a valid target state returns `ELIGIBLE` and changes no row.
3. Apply creates exactly one active target-tenant user in one transaction and creates no other
   database row.
4. An exact rerun is idempotent; any non-exact existing state is a typed conflict and is not
   repaired.
5. `(target tenant, historical user 2222...)` still returns 401, as do unknown, cross-tenant, and
   inactive subjects.
6. `validated_evaluation_principal`, routes, visibility, shared auth, and production bearer code
   have no semantic diff.
7. Receipt replay requires the exact locked tenant, subject, state, row counts, confirmation mode,
   visible demo labels, JSON types, and logical digest; a raw/secret scan passes.
8. Targeted tests and the full AX quality gate pass on a clean reviewed SHA.
9. Receipt reservation, write failure, concurrent exact insert, post-commit confirmation, and lost
   commit-response behavior all fail closed with the documented evidence semantics.
10. No attachment, provider, live corpus, or Braincrew `READY` claim is made.

### Definition of done

AX-A is done only when implementation, independent code review, targeted and full tests, clean Git
evidence, and the separate Git lifecycle are complete. Database apply is not part of code-issue
completion; it remains inside the later shared operational gate.

## 6. AX-B issue contract

### Title

Re-provision six reviewed parsing attachments through the target-tenant AX lifecycle

### Dependency

Blocked by AX-A implementation, review, merge, and a valid AX-A dry-run contract. Operational apply
also requires the fresh checkpoints in section 7.

### Problem statement

Braincrew freezes six parse cases and source-text digests, but the live AX database contains no
attachment or extraction row. Provisioning a user alone would move the failure from 401 to 404.
The six source bytes must enter AX through the supported lifecycle, receive new AX attachment IDs,
produce stored extractions and evidence spans, and be handed back to Braincrew without direct table
inserts or caller-invented IDs.

### Reviewed source bundle

AX-B accepts a create-only external bundle with schema `braincrew-parse-source-bundle-v1`. It
contains exactly six UTF-8, NFC, LF-only `.txt` files:

| Case / filename | Required source-text digest |
| --- | --- |
| `synthetic-rule-015.txt` | `sha256:6e418e4be8e4de344d6b3e0162d00177668483c21e864b477fae6b1b044bf7a2` |
| `synthetic-rule-016.txt` | `sha256:620ad58790745f5d1852c3e97a36ce40ca74d8b6dd6e010469ea44b2ec4b3a75` |
| `synthetic-rule-017.txt` | `sha256:3982c372a75d30b3b1699a58a9d567ad0072fb088f3a10ab929dcbb6096319c6` |
| `synthetic-rule-018.txt` | `sha256:9070d1c9cab7d54d7836d1ef28369f2ab9a4968a23208e10a9e66585ecca8d1f` |
| `synthetic-rule-019.txt` | `sha256:0937ba63f9fde634c13bea38c3974e0226b083fb299bfdd5a111789c190d0042` |
| `synthetic-rule-020.txt` | `sha256:333a023c2e477249aa2b16718826c897f4efed6c4358bd86fe4f6d9cc386a23d` |

The bundle manifest binds file order, byte size, digest, case ID, source provenance
`reviewed_synthetic`, reviewer identity, review time/timezone, and its own digest. It contains no
dataset query, expected answer, score, credential, or private source.

### Implementation boundary

Add an AX-owned local/test operator command, recommended entry point:

```text
ax-evaluation-parse-sources
```

Recommended implementation surfaces:

```text
backend/src/ax_engine/evaluation/parse_source_provisioning.py
backend/src/ax_engine/evaluation/parse_source_cli.py
```

The command orchestrates existing AX boundaries:

1. verify the clean reviewed AX SHA, local/test environment, target tenant, AX-A receipt, exact
   source bundle, and absent target operation identity;
2. create one conversation owned by the AX-A subject under singleton `HRPractitioner`;
3. upload all six files in one multipart request through
   `POST /v1/conversations/{thread_id}/attachments`;
   **[Superseded 2026-07-25 — not executable; `MAX_FILES_PER_OPERATION = 5` is enforced per
   request. Read as two bounded requests of five and one into the same thread, preserving reviewed
   bundle order. See [the request-split decision](./2026-07-25-ax-b-bounded-upload-request-split.md).]**
4. wait for each scan/parse job to reach clean `parsed` state and for exactly one succeeded
   `AttachmentExtraction`;
5. approve each attachment as `source_class=company_reference`,
   `visibility_policy=hr_only`, `policy_version=1` under singleton `HRAdmin`;
6. run materialization with the reviewed fake provider lineage:
   `provider_adapter=fake-deterministic`, model label `text-embedding-3-small`, 1536 dimensions;
7. wait for all six attachments to become `materialized`;
8. call the strict parse-observation endpoint for every generated attachment ID under singleton
   `HRPractitioner`;
9. call corpus identity under singleton `Employee`, `Executive`, and `HRPractitioner` after all
   materialization completes;
10. emit the sanitized handoff receipt only after every check succeeds.

AX-B may use SELECT-only database verification for exact row and tenant binding. Every mutation
must use existing AX services, HTTP routes, jobs, approvals, and materialization. No direct
attachment, extraction, source, chunk, span, vector, job, or audit insert is permitted.

### Materialization and provenance lock

Non-empty strict `evidence_spans` require normal materialization. Extraction-only success is
insufficient because `EvaluationService._stored_evidence_spans` reads current
`TenantSourceDocument`, `SeedSourceChunk`, and `SeedEvidenceSpan` rows.

For the six short, single-paragraph inputs, successful materialization must add exactly:

- 6 `ThreadAttachment` rows;
- 6 succeeded `AttachmentExtraction` rows;
- 6 current `TenantSourceDocument` rows;
- 6 `SeedSourceDocument` rows;
- 6 `SeedSourceChunk` rows;
- 6 `SeedEvidenceSpan` rows;
- 12 embedded `SeedVectorRecord` rows.

The four imported seed-table counts therefore move from `14/77/77/154` to `20/83/83/166`.
Different deltas stop the operation. AX-B does not claim that seed counts remain unchanged.

The existing tenant-upload lifecycle stores:

```text
synthetic=false
demo_company=false
corpus_mode=tenant
created_by_seed_version=tenant-upload-v1:<approval_id>
```

The handoff receipt must state both facts without rewriting either:

- the external source bytes have reviewed synthetic provenance;
- AX classifies their materialized rows as normal tenant uploads.

This is a documented representational limitation. AX-B may not silently describe the rows as
seeded synthetic records and may not bypass the lifecycle to force different flags.

`company_reference` plus `hr_only` is locked to minimize answer-grounding authority and exposure.
The records remain visible to `HRPractitioner`, so the HRPractitioner corpus identity changes.
Employee and Executive corpus identities must still be captured after AX-B, not assumed from the
pre-B import evidence.

### Outputs

Schema: `ax-evaluation-parse-source-handoff-v1`.

The create-only sanitized receipt contains:

- AX SHA, clean status, environment, tenant ID, and AX-A receipt digest;
- source-bundle manifest digest and six case/source digests;
- conversation ID;
- ordered case-to-generated-attachment-ID mapping;
- attachment state, extraction state, parser name/version, extracted-text digest, and
  materialization state;
- approval source class, visibility policy, policy version, and role;
- materialization version identities and exact bounded row-count deltas;
- provider adapter/model/dimensions, never credentials;
- six strict parse-response digests and sanitized span counts/coordinate summaries;
- three post-B corpus identities with exact singleton role, corpus digest, inventory count, counts,
  and full `contributing_versions`;
- explicit presence of `braincrew-evaluation-dataset-3.0.0` in all three corpus identities;
- AX lifecycle classification and external reviewed-synthetic provenance as separate fields;
- canonical logical digest and direct completion state.

It excludes raw/extracted text, span text, embeddings, queries, answers, tokens, credentials,
database URLs, blob root paths, authorization headers, and private paths.

### Failure codes and stop behavior

| Code | Condition |
| --- | --- |
| `PARSE_SOURCE_ENVIRONMENT_FORBIDDEN` | Environment is not local/test. |
| `PARSE_SOURCE_REPOSITORY_DIRTY` | AX checkout is dirty or wrong SHA. |
| `PARSE_SOURCE_PRINCIPAL_INVALID` | AX-A receipt, subject, target tenant, or request-scoped `x-ax-roles` value does not match. |
| `PARSE_SOURCE_INPUT_INVALID` | Bundle schema, order, count, byte policy, provenance, or digest is wrong. |
| `PARSE_SOURCE_PREEXISTING_STATE` | Operation identity, receipt, target thread, or any mapped target row already exists unexpectedly. |
| `PARSE_SOURCE_UPLOAD_FAILED` | Conversation or multipart upload fails or returns the wrong count/tenant/owner. |
| `PARSE_SOURCE_SCAN_FAILED` | Scanner reports infection/failure or exceeds its bounded wait. |
| `PARSE_SOURCE_EXTRACTION_FAILED` | Extraction is absent, duplicated, failed, or exceeds its bounded wait. |
| `PARSE_SOURCE_PARSER_MISMATCH` | Parser is not exact `utf8-text` / `stdlib-1`. |
| `PARSE_SOURCE_DIGEST_MISMATCH` | Extracted-text digest differs from the reviewed source digest. |
| `PARSE_SOURCE_APPROVAL_FAILED` | Exact `company_reference` / `hr_only` / policy-version approval fails. |
| `PARSE_SOURCE_MATERIALIZATION_FAILED` | Provider, policy, job, or materialization state fails. |
| `PARSE_SOURCE_COUNT_MISMATCH` | Exact bounded database deltas do not reproduce. |
| `PARSE_SOURCE_OBSERVATION_FAILED` | Any strict parse response is non-200, unavailable, schema-invalid, role-wrong, digest-wrong, or span-invalid. |
| `PARSE_SOURCE_CORPUS_IDENTITY_FAILED` | Any singleton-role corpus identity is unavailable, schema-invalid, or lacks the v3 seed contribution. |
| `PARSE_SOURCE_RECEIPT_EXISTS` | Create-only output path exists. |
| `PARSE_SOURCE_COMMIT_INDETERMINATE` | Any lifecycle transition cannot be proven. |

On the first failure, preserve the completed evidence and stop. Do not retry with changed bytes,
select a new principal, approve with a different policy, switch provider, delete partial rows,
purge blobs, restore a snapshot, re-import the corpus, or write a partial success receipt.
Corrective mutation requires a new proposal naming the exact state and recovery action.

### Backward compatibility

- Historical Braincrew artifacts replay without live DB access and remain unchanged.
- New attachment IDs are generated by AX; no historical UUID is recreated or caller-forced.
- Existing attachment, parser, approval, materialization, evaluation, and corpus-identity contracts
  remain authoritative.
- No migration is required for the locked implementation.
- Tenant isolation and inaccessible/cross-tenant 404 behavior remain unchanged.

### In scope

- strict external six-file bundle validation;
- normal conversation/upload/scan/parse/approve/materialize orchestration;
- exact target tenant, subject, role, parser, digest, visibility, provider, and count validation;
- strict parse and three-role corpus-identity capture after materialization;
- sanitized create-only handoff receipt and replay.

### Out of scope

- direct database writes or caller-forced attachment IDs;
- parser, chunker, visibility, role-permission, provider, evaluation-route, or tenant-isolation
  changes;
- rewriting tenant-upload provenance flags;
- corpus re-import, deletion, restore, or automatic cleanup;
- changing the six source bytes or expected digests;
- Braincrew scoring, experiment execution, or `READY` publication;
- baseline, candidate, comparison, dashboard, or Issue #15 work;
- GitHub or Git lifecycle changes without separate authorization.

### Test matrix

| Layer | Required proof |
| --- | --- |
| Bundle | Exact six filenames/order/digests, UTF-8/NFC/LF-only policy, reviewed-synthetic provenance, forbidden-field scan, tamper rejection. |
| HTTP lifecycle | One owned thread, one six-file upload, correct tenant/owner, bounded job polling, exact extraction/parser/digest. |
| Permission | HRPractitioner upload/read succeeds; Employee/Executive upload and non-owner/cross-tenant reads fail; only HRAdmin approval succeeds. |
| Materialization | Exact source class/visibility/provider, one chunk and span per source, two vectors per source, exact count deltas, idempotent job behavior. |
| Observation | Six strict schemas, exact IDs/digests/role, non-empty valid spans, raw-text-free retained evidence. |
| Corpus | Three singleton roles captured after B; each includes v3 seed contribution; actual post-B counts/digests and tenant-upload versions are frozen. |
| Receipt | Create-only, canonical digest, replay, tamper rejection, raw/secret/path/vector scan. |
| Failure | Each typed blocker stops without alternate input, cleanup, restore, or partial success. |

Recommended tests:

```text
backend/tests/unit/test_evaluation_parse_source_bundle.py
backend/tests/integration/test_evaluation_parse_source_cli.py
backend/tests/integration/test_evaluation_parse_source_lifecycle.py
backend/tests/integration/test_evaluation_api.py
backend/tests/unit/test_evaluation_parse_source_cli_registration.py
```

### Acceptance criteria

1. AX-B rejects any source bundle other than the exact reviewed six-file contract.
2. It creates one target-tenant thread owned by the AX-A subject and obtains six new AX-generated
   attachment IDs through one normal upload.
   **[Superseded 2026-07-25 — "through two bounded normal uploads of five and one into that one
   thread". The thread count and the six AX-generated IDs are unchanged; see
   [the request-split decision](./2026-07-25-ax-b-bounded-upload-request-split.md).]**
3. All six scan/parse jobs succeed with exact `utf8-text` / `stdlib-1` and matching source digest.
4. All six receive exact `company_reference`, `hr_only`, policy version 1 approval under
   `HRAdmin`.
5. All six materialize with fake-deterministic lineage and exact `+6/+6/+6/+12` seed-table deltas.
6. All six strict parse calls under singleton `HRPractitioner` return 200, `parse_available=true`,
   matching attachment and extracted-text digests, and valid non-empty stored spans.
7. Post-B Employee, Executive, and HRPractitioner corpus identities are captured under the AX-A
   subject, each includes `braincrew-evaluation-dataset-3.0.0`, and actual role-specific counts,
   digests, and contributing versions are frozen.
8. Cross-tenant and wrong-owner attachment reads remain hidden, and the old target plus historical
   user pair remains 401.
9. The receipt replays, rejects tampering, contains no raw text or secret, and preserves the
   external-provenance versus AX-lifecycle-classification distinction.
10. Targeted and full AX gates pass on a clean reviewed SHA.
11. No Braincrew `READY` or quality claim is made.

### Definition of done

AX-B code is done after independent review, targeted/full tests, and its Git lifecycle. AX-B
operational completion is separate: it requires the shared gate, successful lifecycle, live
observations, sanitized handoff receipt, and independent evidence review.

## 7. Shared operational gate

AX-A and AX-B code completion does not authorize database, blob, service, worker, provider, or HTTP
operation. A separate proposal must name the exact AX SHA, commands, external paths, roles, and stop
conditions.

### Required checkpoints

1. **Post-import, pre-A database snapshot.** Create a fresh restricted external PostgreSQL
   custom-format dump after the successful corpus import and before AX-A apply. Record SHA-256,
   permissions, catalog count, and `pg_restore --list` readability. The older Issue #37 snapshot
   predates import and is not an acceptable recovery point.
2. **Post-A, pre-B database checkpoint.** After AX-A apply and independent receipt review, create a
   second restricted dump so a later recovery proposal can preserve the imported corpus and exact
   principal.
3. **Pre-B blob checkpoint.** Record a canonical inventory of every existing blob relative path,
   size, and SHA-256, plus root permissions, and preserve a restricted external copy or filesystem
   snapshot. Bind the inventory and checkpoint digests in the operational proposal.

These checkpoints provide evidence and a separately usable recovery point. They do not authorize
restore. No automatic restore is allowed.

### Ordered execution

```text
verify clean merged AX SHA and exact code receipts
  -> verify fresh post-import/pre-A DB snapshot
  -> AX-A dry-run
  -> independent dry-run review
  -> AX-A apply
  -> verify AX-A receipt and principal regression probes
  -> create post-A/pre-B DB and blob checkpoints
  -> AX-B dry-run
  -> independent dry-run review
  -> start separately approved HTTP/worker boundary
  -> AX-B lifecycle apply
  -> verify exact database deltas
  -> six strict parse observations
  -> three post-B singleton-role corpus identities
  -> create and replay sanitized handoff
  -> stop and hand receipts to Braincrew #38
```

### Exact stop conditions

Stop on:

- wrong or dirty Braincrew/AX SHA;
- non-local/test environment;
- missing/mismatched target tenant, completed seed run, corpus import counts,
  provider lineage, snapshot, checkpoint, or digest;
- any create-only path already existing;
- principal identity, metadata, or tenant conflict;
- source bundle schema, provenance, byte, order, or digest mismatch;
- pre-existing operation state;
- upload, scan, extraction, parser, approval, materialization, provider, or count failure;
- any principal 400/401, attachment 404, corpus/parse non-200, schema mismatch, digest mismatch,
  `x-ax-roles` mismatch, missing v3 contribution, or invalid span;
- indeterminate transaction, job, HTTP, or receipt state;
- any raw text, secret, database URL, authorization value, vector, or private path in retained
  evidence.

On a stop, retain evidence in place and end the run. Do not auto-retry, clean up, delete, purge,
restore, re-import, rotate credentials again, switch provider, alter expected values, or continue
to Braincrew.

## 8. Braincrew Issue #38 handoff and repins

Braincrew #38 must start in a fresh implementation session after both operational receipts are
independently reviewed. It consumes evidence only and updates:

- `src/braincrew/live_preflight.py`
  - `PINNED_AX_SHA`;
  - `ACTIVE_OWNER_USER_ID` to `26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe`;
  - `REVIEWED_PARSING_ATTACHMENT_IDS` to the ordered AX-B mapping;
  - `FROZEN_DATASET_VERSION` to integrated version `3.0.0`;
  - `FROZEN_DATASET_DIGEST` to
    `sha256:c07c561963f7d7f82159a2554370a77a4f5f26b495f7378f10af4a80f420a19d`;
  - `FROZEN_COMPONENT_DIGESTS` to the successor manifest digests in section 3;
  - `DatasetIdentityEvidence.version`, `_verification_cases`, `_frozen_dataset_identity`, and
    their callers so the accepted manifest is integrated v3 while the nested parsing component
    remains version 2.0.0;
- `src/braincrew/ax-http-v1.yaml`
  - `sut_commit_sha` to the same reviewed AX SHA;
- contract and acceptance fixtures that freeze the old user, attachment IDs, AX SHA, tenant, or v2
  integrated identity/corpus contribution, including the input manifest path changing from
  `datasets/dataset_manifest_v2.json` to `datasets/dataset_manifest_v3.json`;
- the new create-only `live-verification-preflight-artifact-v2` contract;
- durable status/design/interview records for the final reviewed identities.

The new `READY` artifact must bind:

- clean Braincrew and AX SHAs;
- integrated dataset `braincrew-evaluation-dataset@3.0.0` and digest;
- historical v2 parsing-component identity and the six reviewed source digests;
- qualified pack, corpus, import, provider, model, prompt, adapter, tenant, principal, roles, and
  configuration;
- both AX receipt digests and checkpoint evidence identities;
- three actual post-B role-specific corpus identities;
- six actual strict parse observations and response digests.

Issue #38 stops at `READY`. Baseline, candidate, comparison, dashboard, and Issue #15 remain separate
authorization and workflow stages.

## 9. Rejected alternatives

### Principal-only AX issue

Rejected because it can change the first live failure from 401 to 404 but cannot recreate the six
missing observations.

### One combined AX issue

Rejected because user-row provisioning and attachment/provider lifecycle have different code,
tests, permissions, recovery surfaces, and review evidence. Combining them hides the safe stop
between principal apply and blob/database mutation.

### Parse restoration inside Braincrew #38

Rejected because it would make the Evaluation Plane mutate the SUT it is supposed to verify,
violate repository boundaries, and let a verifier repair its own missing evidence.

### Reuse or move the historical user

Rejected because `User.id` is a global primary key, the user is tenant-bound, and moving it would
weaken or break tenant isolation.

### Recreate historical attachment UUIDs

Rejected because the supported lifecycle generates AX identities. Caller-forced IDs or direct
table inserts would bypass ownership, audit, job, and lifecycle contracts.

### Extraction-only success with unchanged seed counts

Rejected because strict non-empty spans are read from materialized source/chunk/span rows. A
successful extraction without materialization cannot satisfy the Braincrew parse-evidence
contract.

### Automatic rollback or snapshot restore

Rejected because the lifecycle spans database, blob, worker, provider, and HTTP boundaries and is
not one atomic transaction. Recovery requires a separately reviewed proposal that names exact
state.

## 10. Verification commands for future implementation

AX-A:

```bash
uv lock --project backend --check
uv sync --project backend --locked --group dev
uv run --project backend ruff format --check backend/src/ax_engine/evaluation backend/tests
uv run --project backend ruff check backend/src backend/tests
uv run --project backend python -m compileall -q backend/src backend/tests backend/alembic
uv run --project backend pytest -q \
  backend/tests/unit/test_evaluation_principal_provisioning.py \
  backend/tests/integration/test_evaluation_principal_cli.py \
  backend/tests/integration/test_evaluation_api.py
uv run --project backend pytest -q backend/tests
git diff --check
git status --short
```

AX-B:

```bash
uv lock --project backend --check
uv sync --project backend --locked --group dev
uv run --project backend ruff format --check backend/src/ax_engine/evaluation backend/tests
uv run --project backend ruff check backend/src backend/tests
uv run --project backend python -m compileall -q backend/src backend/tests backend/alembic
uv run --project backend pytest -q \
  backend/tests/unit/test_evaluation_parse_source_bundle.py \
  backend/tests/integration/test_evaluation_parse_source_cli.py \
  backend/tests/integration/test_evaluation_parse_source_lifecycle.py \
  backend/tests/integration/test_evaluation_api.py
uv run --project backend pytest -q backend/tests
git diff --check
git status --short
```

These commands verify code contracts only. They do not prove a live subject, attachment, corpus
identity, parse observation, snapshot recovery, or Braincrew `READY`.

## 11. Copy-ready GitHub issue body — AX-A

### Title

Provision a tenant-scoped local evaluation subject for the Braincrew live preflight

### Parent and dependency

Follow-up to AX Issue #37. AX-B must depend on this issue.

### Problem

The Braincrew corpus is loaded in tenant
`ae09ec7f-a7bc-5bf8-a645-8b3f1e623850`, which currently has no user. The Braincrew historical
subject belongs to another tenant, so AX correctly returns
`401 evaluation_principal_subject_invalid`. Do not weaken `validated_evaluation_principal` or
tenant isolation.

### Build

Add local/test-only `ax-evaluation-principal` dry-run/apply behavior and
`ax-evaluation-principal-receipt-v1`.

Lock the subject to:

```text
uuid5(NAMESPACE_URL, "ax-evaluation-principal:braincrew-demo-tenant:braincrew-live-evaluation-v1")
= 26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe
```

Use fixed code-owned metadata. Apply creates exactly one active target-tenant `User` atomically and
creates no other database row. Local/test requests later supply one exact role through
`x-ax-roles`, and AX continues to derive permissions from its existing static permission mapping;
AX-A does not provision or validate persisted authorization state. It never moves,
reactivates, or updates a user, chooses another UUID, or overwrites a receipt.

Eligibility requires local/test, the exact demo tenant/company, and completed
`braincrew-evaluation-dataset-3.0.0`. Dry-run writes nothing. Apply repeats every check, requires
direct commit confirmation, and emits a sanitized create-only receipt.

### Required failures

- `EVALUATION_PRINCIPAL_ENVIRONMENT_FORBIDDEN`
- `EVALUATION_PRINCIPAL_REPOSITORY_DIRTY`
- `EVALUATION_PRINCIPAL_ID_INVALID`
- `EVALUATION_PRINCIPAL_TARGET_INVALID`
- `EVALUATION_PRINCIPAL_SEED_RUN_INVALID`
- `EVALUATION_PRINCIPAL_TENANT_CONFLICT`
- `EVALUATION_PRINCIPAL_STATE_CONFLICT`
- `EVALUATION_PRINCIPAL_RECEIPT_EXISTS`
- `EVALUATION_PRINCIPAL_RECEIPT_UNAVAILABLE`
- `EVALUATION_PRINCIPAL_COMMIT_INDETERMINATE`
- `EVALUATION_PRINCIPAL_DATABASE_UNAVAILABLE`

Reserve the create-only receipt path before database mutation. A pre-commit failure rolls back and
removes the reservation. An unprovable commit or post-commit confirmation retains the empty
reserved path and returns `EVALUATION_PRINCIPAL_COMMIT_INDETERMINATE`. A receipt write failure
retains the reservation and returns `EVALUATION_PRINCIPAL_RECEIPT_UNAVAILABLE`; neither case claims
cross-resource atomicity or rollback.

On failure, preserve evidence and stop. No alternate UUID, auto-repair, cleanup, restore, or retry
with changed state.

### Acceptance

- [ ] Literal deterministic UUID and fixed metadata are tested.
- [ ] Dry-run is no-write and apply creates exactly one active target-tenant user and no other
      database row.
- [ ] Exact rerun is idempotent; every drift/conflict fails closed.
- [ ] Existing malformed, unknown, cross-tenant, and inactive subject behavior is unchanged.
- [ ] `(target tenant, historical user 2222...)` remains 401.
- [ ] No semantic diff to evaluation routes, shared auth, bearer auth, visibility, or tenant joins.
- [ ] Receipt reservation/write failure, exact replay shape and JSON types, concurrent insertion,
      post-commit confirmation, and indeterminate commit evidence are tested.
- [ ] Receipt replay and raw/secret scan pass.
- [ ] Targeted and full AX gates pass on a clean SHA.
- [ ] No live apply, attachment, corpus, or Braincrew `READY` claim is part of code completion.

### Out of scope

Request-role or permission-mapping changes, persisted authorization changes, migration, attachment
work, provider/workers, corpus import, Braincrew changes, live operational apply, and remote Git
actions without separate authorization.

### Verification

Run from the AX_portfolio repository:

```bash
uv lock --project backend --check
uv sync --project backend --locked --group dev
uv run --project backend ruff format --check backend/src/ax_engine/evaluation backend/tests
uv run --project backend ruff check backend/src backend/tests
uv run --project backend python -m compileall -q backend/src backend/tests backend/alembic
uv run --project backend pytest -q \
  backend/tests/unit/test_evaluation_principal_provisioning.py \
  backend/tests/integration/test_evaluation_principal_cli.py \
  backend/tests/integration/test_evaluation_api.py
uv run --project backend pytest -q backend/tests
git diff --check
git status --short
```

These commands verify code contracts only. They do not prove a live subject or Braincrew `READY`.
The immutable cross-repository scope reference is
[Braincrew decision at `fc1302d54ab3f3735800d31a321b6f70e947572e`](https://github.com/DHChe/braincrew-datateam-portfolio/blob/fc1302d54ab3f3735800d31a321b6f70e947572e/docs/decisions/2026-07-24-ax-evaluation-principal-and-parse-restoration-scope-lock.md).

## 12. Copy-ready GitHub issue body — AX-B

### Title

Re-provision six reviewed parsing attachments through the target-tenant AX lifecycle

### Dependency

Blocked by AX-A implementation/review/merge:
https://github.com/DHChe/AX_portfolio/issues/44. Operational execution also requires fresh
post-import pre-A and post-A pre-B database checkpoints plus a pre-B blob checkpoint.

### Problem

The database contains no live `ThreadAttachment` or `AttachmentExtraction`, so principal
provisioning alone only changes the parse failure from 401 to 404. Braincrew requires six new,
strict, owner-authorized parse observations with exact parser/source digests and stored evidence
spans.

### Build

Add local/test-only `ax-evaluation-parse-sources` orchestration and
`ax-evaluation-parse-source-handoff-v1`.

Accept only `braincrew-parse-source-bundle-v1` containing:

```text
synthetic-rule-015.txt sha256:6e418e4be8e4de344d6b3e0162d00177668483c21e864b477fae6b1b044bf7a2
synthetic-rule-016.txt sha256:620ad58790745f5d1852c3e97a36ce40ca74d8b6dd6e010469ea44b2ec4b3a75
synthetic-rule-017.txt sha256:3982c372a75d30b3b1699a58a9d567ad0072fb088f3a10ab929dcbb6096319c6
synthetic-rule-018.txt sha256:9070d1c9cab7d54d7836d1ef28369f2ab9a4968a23208e10a9e66585ecca8d1f
synthetic-rule-019.txt sha256:0937ba63f9fde634c13bea38c3974e0226b083fb299bfdd5a111789c190d0042
synthetic-rule-020.txt sha256:333a023c2e477249aa2b16718826c897f4efed6c4358bd86fe4f6d9cc386a23d
```

Use target tenant `ae09ec7f-a7bc-5bf8-a645-8b3f1e623850` and AX-A subject
`26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe`. Create one owned conversation, upload all six `.txt`
files under singleton `HRPractitioner`, wait for clean exact `utf8-text` / `stdlib-1` extraction,
approve exact `company_reference` / `hr_only` / policy version 1 under singleton `HRAdmin`, and
materialize with reviewed fake-deterministic lineage.

Use existing HTTP/services/jobs only for mutation. SELECT-only verification may confirm exact
tenant binding and row deltas. Direct table writes and caller-forced attachment IDs are forbidden.

Expected additions are six attachments, extractions, tenant sources, seed sources, chunks, and
spans plus twelve vectors. Imported seed counts therefore move from `14/77/77/154` to
`20/83/83/166`. Extraction-only or unchanged-count success is invalid because strict non-empty
spans require materialization.

After materialization, capture six strict parse responses under singleton `HRPractitioner` and
three corpus identities under singleton `Employee`, `Executive`, and `HRPractitioner`. Every corpus
identity must include `braincrew-evaluation-dataset-3.0.0`; freeze actual post-B counts, digests,
and `tenant-upload-v1:<approval_id>` versions.

The receipt must distinguish external `reviewed_synthetic` provenance from existing AX tenant-upload
classification `synthetic=false`, `demo_company=false`, `corpus_mode=tenant`. Do not rewrite or
misstate either.

### Required failures

- `PARSE_SOURCE_ENVIRONMENT_FORBIDDEN`
- `PARSE_SOURCE_REPOSITORY_DIRTY`
- `PARSE_SOURCE_PRINCIPAL_INVALID`
- `PARSE_SOURCE_INPUT_INVALID`
- `PARSE_SOURCE_PREEXISTING_STATE`
- `PARSE_SOURCE_UPLOAD_FAILED`
- `PARSE_SOURCE_SCAN_FAILED`
- `PARSE_SOURCE_EXTRACTION_FAILED`
- `PARSE_SOURCE_PARSER_MISMATCH`
- `PARSE_SOURCE_DIGEST_MISMATCH`
- `PARSE_SOURCE_APPROVAL_FAILED`
- `PARSE_SOURCE_MATERIALIZATION_FAILED`
- `PARSE_SOURCE_COUNT_MISMATCH`
- `PARSE_SOURCE_OBSERVATION_FAILED`
- `PARSE_SOURCE_CORPUS_IDENTITY_FAILED`
- `PARSE_SOURCE_RECEIPT_EXISTS`
- `PARSE_SOURCE_COMMIT_INDETERMINATE`

Stop on first failure and retain evidence. No changed input, alternate principal/provider/policy,
cleanup, delete, purge, restore, re-import, or partial success receipt.

### Acceptance

- [ ] Exact six-file schema, byte policy, order, provenance, and digests are tested.
- [ ] One target-owned thread and one six-file upload produce six AX-generated IDs.
- [ ] Exact parser and extracted-text digests pass for all six.
- [ ] Exact approval and fake-provider materialization pass.
- [ ] Exact database additions and final `20/83/83/166` counts reproduce.
- [ ] Six strict parse responses return matching IDs/digests, `parse_available=true`, exact
      `HRPractitioner`, and valid non-empty spans.
- [ ] Three post-B singleton-role corpus identities include the v3 seed version and freeze actual
      counts/digests/contributing versions.
- [ ] Cross-tenant/owner isolation and historical-user 401 remain unchanged.
- [ ] Sanitized receipt replays, rejects tampering, and passes raw/secret/path/vector scans.
- [ ] Targeted and full AX gates pass on a clean SHA.
- [ ] No Braincrew `READY` or quality claim is part of AX-B code completion.

### Out of scope

Direct database writes, migrations, parser/chunker/visibility/provider/auth changes, provenance-flag
rewrites, corpus re-import, automatic recovery, Braincrew scoring/READY, experiments, and remote
Git actions without separate authorization.

### Verification

Run from the AX_portfolio repository:

```bash
uv lock --project backend --check
uv sync --project backend --locked --group dev
uv run --project backend ruff format --check backend/src/ax_engine/evaluation backend/tests
uv run --project backend ruff check backend/src backend/tests
uv run --project backend python -m compileall -q backend/src backend/tests backend/alembic
uv run --project backend pytest -q \
  backend/tests/unit/test_evaluation_parse_source_bundle.py \
  backend/tests/integration/test_evaluation_parse_source_cli.py \
  backend/tests/integration/test_evaluation_parse_source_lifecycle.py \
  backend/tests/integration/test_evaluation_api.py
uv run --project backend pytest -q backend/tests
git diff --check
git status --short
```

These commands verify code contracts only. They do not prove a live attachment, corpus identity,
parse observation, snapshot recovery, or Braincrew `READY`. The immutable cross-repository scope
reference is
[Braincrew decision at `fc1302d54ab3f3735800d31a321b6f70e947572e`](https://github.com/DHChe/braincrew-datateam-portfolio/blob/fc1302d54ab3f3735800d31a321b6f70e947572e/docs/decisions/2026-07-24-ax-evaluation-principal-and-parse-restoration-scope-lock.md).
