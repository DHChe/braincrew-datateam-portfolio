# AX-B Bounded Upload Request Split — Superseding Decision

Date: 2026-07-25
Status: LOCKED FOR ISSUE AMENDMENT; NOT IMPLEMENTED OR LIVE-VERIFIED
Supersedes in part: [`docs/decisions/2026-07-24-ax-evaluation-principal-and-parse-restoration-scope-lock.md`](./2026-07-24-ax-evaluation-principal-and-parse-restoration-scope-lock.md), pinned at commit `fc1302d54ab3f3735800d31a321b6f70e947572e`
Braincrew decision baseline: `eace5eb5744355a5a03bb150b08ed4914a1066bc`
AX verification baseline: `fe16c0cedc1e64856d9e107e111665d0ba2e444d` (`origin/develop`, AX-A merge)

This record supersedes exactly one operative element of the 2026-07-24 scope lock: the requirement
that the six reviewed `.txt` sources enter AX through **one** multipart request. Every other locked
element of that document — identities, dataset versions, approval triple, provider lineage, count
deltas, failure codes, provenance representation, and operational gating — remains in force
unchanged.

## 1. Decision

The six reviewed `.txt` sources are uploaded as **two bounded requests of five and one** into
**one** target-owned conversation, through the existing route
`POST /v1/conversations/{thread_id}/attachments`.

```text
conversation: 1  (owned by AX-A subject 26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe)
  request A -> synthetic-rule-015.txt .. synthetic-rule-019.txt   (5 files)
  request B -> synthetic-rule-020.txt                             (1 file)
  result    -> 6 AX-generated attachment IDs, reviewed bundle order preserved
```

Request order follows the reviewed bundle order. The case-to-attachment mapping in the handoff
receipt is ordered by the bundle, not by request boundary, so the request split is an
implementation detail of ingestion and is not visible in the mapping contract.

This requires **zero AX source change**.

## 2. Why the previous wording could not be implemented

AX enforces a maximum of five files **per upload operation**. The locked instruction to upload six
files in one multipart request is therefore not executable against the merged AX baseline.

### Verified code basis

All citations are read-only from AX `origin/develop` = `fe16c0cedc1e64856d9e107e111665d0ba2e444d`.

| Fact | Location | Evidence |
| --- | --- | --- |
| The limit is five | `backend/src/ax_engine/attachments/intake.py:12` | `MAX_FILES_PER_OPERATION = 5` |
| The limit is enforced per call, on the passed file list | `backend/src/ax_engine/attachments/intake.py:54` | `def validate_file_count(files, *, max_files=MAX_FILES_PER_OPERATION)` → raises `AttachmentRejected("file_count_limit_exceeded")` |
| `stage_files` applies it unconditionally, with no override | `backend/src/ax_engine/attachments/service.py:64` | `validate_file_count(files)` — no `max_files=` argument at the only call site |
| The HTTP route passes every uploaded part straight through | `backend/src/ax_engine/api/routes/attachments.py:169-190` | `upload_thread_attachments` builds one `IntakeFile` per `UploadFile` and calls `stage_files` |
| **There is no per-thread total cap** | `backend/src/ax_engine/attachments/service.py:51-90` | `stage_files` resolves the thread via `get_thread` and then validates only the per-request `files` list; it issues no count query over existing `ThreadAttachment` rows for that thread |
| An existing AX test pins the six-file rejection | `backend/tests/unit/test_attachment_intake.py:25` | `test_maximum_five_files_per_operation` builds six `IntakeFile`s and asserts `pytest.raises(AttachmentRejected, match="file_count_limit_exceeded")` |

Because the cap is per request and no per-thread cap exists, `5 + 1` into one thread satisfies the
platform contract exactly as written, and
`test_maximum_five_files_per_operation` remains valid and untouched.

### Classification

This was a **design flaw in the ticket and in the 2026-07-24 lock**, not an AX defect and not an
implementation error. `MAX_FILES_PER_OPERATION` is a deliberate bounded-resource control on a
tenant-facing multipart endpoint. The lock asserted an ingestion shape that the platform it was
written against does not permit.

### Discovery and verification path

Found during pre-implementation review of AX Issue #45 against the merged AX-A baseline, before AX-B
implementation reached the upload step. Independently re-verified, then escalated for authorization.
The resolution below is the user-authorized option.

## 3. Rejected alternatives

### Raise `MAX_FILES_PER_OPERATION` to six or more

Rejected. The constant governs **every** tenant HTTP caller of
`POST /v1/conversations/{thread_id}/attachments`, not only the local/test operator command. Raising
it would weaken a deliberate bounded-resource control for all tenants in order to satisfy the
convenience of one evaluation-support operation, and it would require deleting or rewriting
`test_attachment_intake.py:25`, which exists to pin exactly that boundary. It also contradicts the
locked AX-B constraint that existing HTTP services, jobs, and approvals are the only mutation
boundary and that AX-B changes no platform policy.

### Add an operator-only override argument to `stage_files`

Rejected. A `max_files=` override on a security-relevant validator creates a permanent bypass
surface that any future caller can reach, in exchange for a purely cosmetic gain — the ticket
sentence would still need amending, because the locked mutation boundary is the HTTP route, not the
service method. The cost is a weakened control; the benefit is wording.

### Retain "one multipart request" and treat the limit as a bug to fix in AX

Rejected. Nothing in the AX contract, tests, or documentation presents the five-file cap as
defective. Reclassifying a working control as a bug so that a Braincrew-authored ticket can stand
unchanged inverts the SUT/Evaluation Plane relationship: the Evaluation Plane would be dictating
product policy to satisfy its own evidence-collection convenience.

## 4. Failure mode introduced by the split

Splitting one request into two introduces a **durable partial-batch state**, because the commit
boundary is per request:

- `backend/src/ax_engine/api/routes/attachments.py:191` — `session.commit()` runs inside
  `upload_thread_attachments`, once per request.
- `backend/src/ax_engine/attachments/service.py:105-115` — each staged attachment is flushed and
  immediately enqueued as an `ATTACHMENT_SCAN_PARSE` job with idempotency key
  `attachment-scan-parse:{attachment_id}:{content_hash}`.

Therefore, if request A succeeds and request B fails, five `ThreadAttachment` rows are already
committed and five scan/parse jobs are already running. There is no cross-request transaction and
none may be manufactured.

Required behavior, consistent with the unchanged stop semantics of the 2026-07-24 lock:

1. Fail with `PARSE_SOURCE_UPLOAD_FAILED` on whichever request fails.
2. Retain the partial state as evidence. Do **not** delete, purge, cancel, or roll back the
   committed attachments; deletion and cleanup are out of scope for AX-B.
3. Do **not** retry either request, and do **not** emit a partial-success receipt.
4. A later rerun must be refused by the pre-existing-state check
   (`PARSE_SOURCE_PREEXISTING_STATE`), not by attempting the upload again.

### Why rule 4 is load-bearing

`stage_files` de-duplicates by content hash **within the thread**
(`backend/src/ax_engine/attachments/service.py:68-76`): if an attachment with the same
`(tenant_id, thread_id, content_hash)` already exists and is not deleted, the existing row is
appended to the result and the loop continues without creating a new row.

A naive retry of a partially completed upload would therefore return HTTP 201 with the **existing**
attachment IDs and create nothing — a silent success that produces no new state. The operation must
be blocked by an explicit pre-existing-state check before upload, because the platform will not
signal the error on its own. This is the single most important consequence of the split and the
reason the count-delta assertion must be computed against a pre-run baseline rather than inferred
from HTTP responses.

## 5. Preserved invariants

The following are unchanged and remain binding:

- **One target-owned thread.** Exactly one conversation, owned by the AX-A subject
  `26d7eebf-e4a1-583d-a43c-4bff0b5bb7fe` in tenant `ae09ec7f-a7bc-5bf8-a645-8b3f1e623850`, created
  under singleton `HRPractitioner`.
- **Six AX-generated attachment IDs.** Caller-forced attachment IDs remain forbidden.
- **Existing HTTP services, jobs, and approvals are the only mutation boundary.** No direct table
  write; SELECT-only verification.
- **Exact reviewed six-file bundle**, its order, byte policy, provenance, and digests.
- Approval `company_reference` / `hr_only` / policy version 1 under singleton `HRAdmin`.
- `fake-deterministic` provider lineage; seed-table deltas `+6/+6/+6/+12`; expected
  `14/77/77/154` → `20/83/83/166`.
- All seventeen `PARSE_SOURCE_*` failure codes and their stop-on-first-failure, retain-evidence,
  no-cleanup semantics.
- The external `reviewed_synthetic` versus AX tenant-upload classification distinction.

Only the phrase asserting a single six-file multipart request is superseded.

## 6. Text superseded in the 2026-07-24 scope lock

The scope-lock file is **not** byte-identical between its pinned commit and current Braincrew HEAD
(`git diff fc1302d eace5eb` reports 78 insertions and 15 deletions for this path), so line numbers
are given for both. The pinned-commit column is authoritative for anyone arriving from the AX Issue
#45 link. The pinned bytes are unchanged by this decision.

| Line @ `fc1302d` (pinned) | Line @ `eace5eb` (HEAD before this change) | Original | Superseded by |
| --- | --- | --- | --- |
| 376-377 | 391-392 | "upload all six files in one multipart request through `POST /v1/conversations/{thread_id}/attachments`" | "upload the six files as two bounded requests of five and one through `POST /v1/conversations/{thread_id}/attachments`, into the same thread, preserving reviewed bundle order" |
| 470 | 485 | "`PARSE_SOURCE_UPLOAD_FAILED` \| Conversation or multipart upload fails or returns the wrong count/tenant/owner." | "…\| Conversation creation or **either** bounded upload request fails, or the combined result returns the wrong count/tenant/owner." |
| 522 | 537 | "One owned thread, one six-file upload, correct tenant/owner…" | "One owned thread, two bounded uploads of five and one totalling six attachments, correct tenant/owner…" |
| 543-544 | 558-559 | "…obtains six new AX-generated attachment IDs through one normal upload." | "…obtains six new AX-generated attachment IDs through two bounded normal uploads into that one thread." |
| 866 | 909 | "Create one owned conversation, upload all six `.txt` files under singleton `HRPractitioner`…" | "Create one owned conversation, upload the six `.txt` files as two bounded requests of five and one under singleton `HRPractitioner`…" |
| 914 | 957 | "- [ ] One target-owned thread and one six-file upload produce six AX-generated IDs." | "- [ ] One target-owned thread and two bounded uploads of five and one produce six AX-generated IDs." |

The last two rows are the embedded AX Issue #45 draft. The corresponding amendment to the live
GitHub issue body was authorized separately and applied on 2026-07-25: the Build paragraph,
acceptance checkbox 2, and a new paragraph clarifying the `PARSE_SOURCE_UPLOAD_FAILED` trigger,
the partial-batch retention rule, and the content-hash de-duplication hazard. The published body was
refetched after the edit and matches the intended text.

One drafted edit was deliberately **not** applied: the footer pointer from AX Issue #45 to this
decision. It must cite a pinned Braincrew commit SHA, which does not exist until this document is
committed and merged. Applying it earlier would publish a link that resolves to nothing and would
break this repository's convention of pinning cross-repository references by commit rather than by
branch. Apply it as a separate authorized action after merge.

## 7. Validation evidence and explicit limits

Produced:

- Read-only inspection of AX `origin/develop` at `fe16c0cedc1e64856d9e107e111665d0ba2e444d`
  establishing the per-request cap, the absence of a per-thread cap, the per-request commit
  boundary, the per-attachment job enqueue, and the content-hash de-duplication branch, at the exact
  file and line references in sections 2 and 4.
- Confirmation that `backend/tests/unit/test_attachment_intake.py:25` remains valid and untouched
  under this decision.

Not produced, and not claimed:

- No AX source was modified and no AX test was executed for this decision.
- No live upload, conversation, attachment, extraction, approval, materialization, parse
  observation, or corpus identity was created or observed.
- No database, service, container, blob store, provider, or secret was accessed.
- This decision does not assert AX-B completion, live operational readiness, parse quality, or
  Braincrew `READY`. AX-B implementation is in progress and unreviewed at the time of writing.
- The `14/77/77/154` starting counts remain an unverified pre-existing database claim recorded in
  documentation; only the `+6/+6/+6/+12` delta is derivable from AX code.
