# AX `2bcaee34…` Is Acceptable as the Evaluation SUT Commit

Date: 2026-07-26  
Status: LOCKED FOR A SEPARATE RE-PIN IMPLEMENTATION; NOT IMPLEMENTED, NOT LIVE-VERIFIED  
Braincrew review baseline: `dfc41ff9c74c7ca8539f6d02318b607e6d6c3244` (`develop`)  
Previously pinned AX SUT: `72805930d9addd8ea41743d1922acf8de621c3f8`  
Reviewed AX SUT: `2bcaee3495fd7b3f624398819575cd86a5a15c47`  
Reviewed range: `72805930d9addd8ea41743d1922acf8de621c3f8..2bcaee3495fd7b3f624398819575cd86a5a15c47`  
Answers the question deferred by
[`docs/decisions/2026-07-26-preflight-receipt-derived-binding.md`](./2026-07-26-preflight-receipt-derived-binding.md)
§5.

## 1. Decision

**Accept `2bcaee3495fd7b3f624398819575cd86a5a15c47` as the exact AX Subject Under
Test (SUT, 평가 대상 시스템) commit for the next evaluation capture.**

This is approval to implement a separate, bounded re-pin. It is not the re-pin itself, does not
authorize a Git lifecycle action, does not start AX, and does not make
`braincrew_preflight_ready` true.

The implementation must:

1. change the one operative Braincrew-side SUT identity from `72805930…` to `2bcaee34…`;
2. keep the receipt's `repository.commit_sha == PINNED_AX_SHA` refusal;
3. update active source, packaged-contract, and test assertions together;
4. keep historical records historical rather than rewriting their old SHA in place;
5. preserve a negative test using a genuinely different, unreviewed 40-hex AX SHA.

> **[Superseded 2026-07-30 — item 2 was correct for this 2026-07-26 re-pin because the reviewed
> provisioning commit and the commit under test were still identical. That cycle's scope ended when
> the two meanings first legitimately diverged. The receipt now remains exact against
> `REVIEWED_PROVISIONED_AX_SHA`, while `PINNED_AX_SHA` independently names the SUT under test; see
> [the separate AX commit meanings decision](./2026-07-30-separate-provisioned-and-under-test-ax-commits.md).]**

No additional AX-side check is a prerequisite to this re-pin. The existing exact-SHA refusal is
the right check; this review changes which one exact SHA has passed the Braincrew-side review.

## 2. Review criterion

The provisioning commit and the evaluation SUT commit are different assertions:

- the provisioning assertion asks whether the operator executed reviewed write steps at a known
  clean commit;
- the SUT assertion asks whether Braincrew is willing to pin the covered evaluation read paths to
  code at that commit and publish only the observations supported by frozen corpus, provider, and
  receipt evidence.

For each changed AX file, this review therefore asked whether the range could change:

- extracted text, parser identity, chunk or span boundaries;
- embedding provider/model/vector lineage;
- retrieval selection or ranking;
- authorization at the evaluation HTTP boundary;
- corpus identity or counts;
- any parse, retrieval, or grounded-answer response field Braincrew retains.

Provisioning-only changes are not automatically harmless. They are acceptable only where their
effect is either outside the read path or is separately frozen as corpus, provider, principal, and
receipt evidence.

This is a delta review, not a standalone re-approval of the base commit. The repository records
`72805930…` as the packaged Adapter pin and Issue #42 substrate lock, but this review found no prior
decision that expressly approved it as an evaluation SUT commit. The conclusion below therefore
establishes that the range from `72805930…` to `2bcaee34…` introduces no disqualifying
evaluation-relevant change; it does not manufacture the missing base-case approval. That provenance
gap does not overturn the relative range judgment, but a later full SUT qualification must close it
explicitly.

## 3. Per-commit evidence

| Commit | What changed | Evaluation judgment |
| --- | --- | --- |
| `6bfc27a` | Added atomic seed-pack apply and embedding-lineage locks; changed `RetrievalRuntime.embed_pending_seed_vectors` to process one resolved tenant at a time; added the same lock before attachment materialization. | **Accept.** Two commits in the range modify pre-existing source (this one and `e25f333`); this is the only one that modifies retrieval/materialization runtime modules adjacent to the evaluation read path. The query-time `search` path, answer-mode selection, retrieval contracts, ranking repository, parser, chunker, evaluation route, evaluation service, and response schemas are unchanged. The pending-vector and materialization changes can affect later stored vectors under concurrent writes, but not the steady-state read algorithm. Evaluation must therefore run against a frozen corpus with provider lineage and no concurrent mutation. |
| `e25f333` | Strengthened seed-pack replay and PostgreSQL concurrency proof; moved `SEED_RUN_MANIFEST_SCHEMA_VERSION` to the pack contract and added stored-manifest/projection checks. | **Accept.** The changes classify and revalidate already loaded seed state. They do not alter normalized text, chunking, vectors, ranking, authorization, or response projection. |
| `fe16c0c` | Added local/test-only evaluation-principal CLI and provisioning that can create exactly one locked active `User` row plus a create-only receipt. | **Accept with the existing live guard.** This changes the database fact that determines whether the evaluation boundary accepts the subject, but it does not change `validated_evaluation_principal` or role permissions. The receipt-derived subject and a fresh live authorization probe remain required. |
| `cf3ae42` | Added the AX-B 5+1 upload, scan/parse, approval, materialization, strict-observation, corpus-identity, and handoff orchestration. It builds a bounded worker with `FakeEmbeddingProvider`. | **Accept with frozen state evidence.** These modules call the pre-existing AX routes and parser/materializer; they do not replace those routes or response schemas. Their execution added six sources and twelve vectors and therefore can change retrieval results through corpus state. That is intended dataset integration, not a hidden code-path change, and must remain bound to the reviewed source digests, count deltas, approval lineage, provider adapter/model/dimensions, corpus identities, and fresh Braincrew capture. |
| `2bcaee3` | Added required `--dry-run`/`--apply`, create-only eligibility evidence, read-only baseline and boundary probes, and stricter transport failure classification. | **Accept.** The commit changes the operator command and its client-side observation/receipt logic. It does not change the AX evaluation endpoint, parser, materializer algorithm, retrieval query path, authorization policy, or response schema. |

The range is five commits, 30 files, and `+11,439 / -40`, matching the independent measurement in
the cycle brief.

## 4. Per-file evidence

### 4.1 Production and operator files

| File | Commit(s) | Judgment |
| --- | --- | --- |
| `CONTEXT.md` | `6bfc27a`, `e25f333` | Repository context only; no executable observation path. |
| `backend/pyproject.toml` | `fe16c0c`, `cf3ae42` | Adds the principal and parse-source command entry points; no dependency or server entry-point change. |
| `backend/src/ax_engine/evaluation/parse_source_cli.py` | `cf3ae42`, `2bcaee3` | Operator CLI. It selects dry-run/apply and assembles dependencies; it does not serve evaluation responses. |
| `backend/src/ax_engine/evaluation/parse_source_provisioning.py` | `cf3ae42`, `2bcaee3` | Write orchestration and sanitized receipt construction. It validates observed parser/source/count/provider evidence but does not implement the parser or AX HTTP projection. |
| `backend/src/ax_engine/evaluation/parse_source_runtime.py` | `cf3ae42`, `2bcaee3` | Client and bounded-worker assembly. It invokes existing routes and worker handlers. `FakeEmbeddingProvider` affects the materialized vectors created by AX-B, so its provider lineage is evaluation-relevant state and must stay frozen; it does not change query-time ranking code. |
| `backend/src/ax_engine/evaluation/principal_cli.py` | `fe16c0c` | Local/test operator CLI only. |
| `backend/src/ax_engine/evaluation/principal_provisioning.py` | `fe16c0c` | Creates or revalidates one exact principal. It changes authorization data, not authorization logic. |
| `backend/src/ax_engine/retrieval/lineage_lock.py` | `6bfc27a` | Adds tenant-scoped PostgreSQL advisory locking for embedding writers. It changes writer serialization, not retrieved-candidate scoring. |
| `backend/src/ax_engine/retrieval/service.py` | `6bfc27a` | Only `embed_pending_seed_vectors` changed: it resolves one tenant, acquires the lineage lock, and filters records to that tenant. `search`, ranking, visibility, answer-mode, and response construction are unchanged. |
| `backend/src/ax_engine/seed/pack_apply.py` | `6bfc27a`, `e25f333` | New atomic import path. It prepares and persists vectors and their provider evidence; those rows are corpus state that the live evaluation must bind independently. |
| `backend/src/ax_engine/seed/pack_cli.py` | `6bfc27a` | Operator CLI routing only. |
| `backend/src/ax_engine/seed/pack_contract.py` | `e25f333` | Moves one manifest schema constant to shared contract authority; no pack normalization or chunking change. |
| `backend/src/ax_engine/seed/pack_dry_run.py` | `6bfc27a`, `e25f333` | Read-only eligibility and replay checks; no evaluator-facing read path. |
| `backend/src/ax_engine/seed/repository.py` | `6bfc27a` | Splits “add and flush” from commit ownership while preserving the same model projections. |
| `backend/src/ax_engine/sources/materialization.py` | `6bfc27a` | Adds one lineage-lock call before the existing materialization algorithm. `CHUNK_CHAR_CAP`, `chunk_extracted_text`, span computation, provider invocation, and stored response-relevant fields are unchanged. |

An explicit range diff was empty for all of these load-bearing evaluation read surfaces:

- `backend/src/ax_engine/api/routes/evaluation.py`;
- `backend/src/ax_engine/evaluation/service.py`;
- `backend/src/ax_engine/evaluation/schemas.py`;
- `backend/src/ax_engine/attachments/extraction.py`;
- `backend/src/ax_engine/attachments/jobs.py`;
- `backend/src/ax_engine/attachments/service.py`;
- `backend/src/ax_engine/retrieval/contracts.py`;
- `backend/src/ax_engine/retrieval/repository.py`;
- `backend/src/ax_engine/services/rbac.py`.

The unchanged route at both endpoints of the range still performs the same tenant-plus-active-user
lookup and calls the same `EvaluationService` for
`GET /v1/evaluation/corpus-identity` and
`GET /v1/evaluation/attachments/{attachment_id}/parse-observation`.

### 4.2 Test files

| File | What it proves about the range |
| --- | --- |
| `backend/tests/integration/test_evaluation_parse_source_cli.py` | CLI and operator-boundary behavior only. |
| `backend/tests/integration/test_evaluation_parse_source_dry_run.py` | Dry-run is read-only, bound, and fail-closed; it cannot prove live parse or retrieval quality. |
| `backend/tests/integration/test_evaluation_parse_source_lifecycle.py` | The orchestration rejects bad lifecycle evidence and count deltas; it is not the Braincrew benchmark. |
| `backend/tests/integration/test_evaluation_principal_cli.py` | Principal command and receipt behavior. |
| `backend/tests/integration/test_seed_pack_apply_postgresql.py` | Atomicity, replay, locks, and PostgreSQL state validation. |
| `backend/tests/unit/test_attachment_materialization.py` | The new lineage lock is taken; the materialization algorithm remains otherwise unchanged. |
| `backend/tests/unit/test_evaluation_parse_source_bundle.py` | Six-source bundle bytes, order, and digests. |
| `backend/tests/unit/test_evaluation_principal_provisioning.py` | Exact one-row principal contract and fail-closed receipt behavior. |
| `backend/tests/unit/test_retrieval_runtime.py` | The modified pending-vector writer is tenant-scoped; it does not exercise a changed search path. |
| `backend/tests/unit/test_seed_pack_apply.py` | Provider lineage, atomic apply, replay, and receipt evidence. |
| `backend/tests/unit/test_seed_pack_dry_run.py` | Read-only eligibility and stored-state checks. |
| `backend/tests/unit/test_seed_pack_repository.py` | The refactored add/flush boundary preserves stored projections. |

These tests support the code-path classification. They do not substitute for fresh Braincrew live
HTTP observations.

### 4.3 AX documentation files

| File | Judgment |
| --- | --- |
| `docs/superpowers/specs/2026-07-20-generic-synthetic-seed-pack-importer-design.md` | Updates importer safety and replay decisions; it does not define evaluation response behavior. |
| `docs/superpowers/specs/2026-07-21-generic-synthetic-seed-pack-importer-issue-draft.md` | Historical issue-contract update only. |
| `docs/verification/2026-07-25-issue-45-evaluation-parse-source-code-contract.md` | Records the provisioning contract and its limits; it is evidence for the operator path, not a live-quality result. |

## 5. What the re-pin changes, and what stops being checked

Two current Braincrew checks reject today's substrate:

1. `LivePreflightArtifact` rejects any `sut_commit_sha` other than `72805930…`;
2. `_load_reviewed_handoff_binding` rejects the reviewed receipt because its
   `repository.commit_sha` is `2bcaee34…`.

Changing `PINNED_AX_SHA` to `2bcaee34…` deliberately turns off **that one specific mismatch
refusal**. The real reviewed receipt will pass the repository-commit comparison, and an artifact may
declare `2bcaee34…`.

The protection is not replaced by deriving or deleting the check. It is **discharged by this
independent review**. The general protection remains:

- a receipt from any other AX commit still refuses;
- an artifact naming any other AX commit still refuses;
- the pinned receipt digest, completed state, six-case mapping, subject identity, and all live
  observation guards remain unchanged.

The existing test
`test_receipt_from_unreviewed_sut_commit_refuses` currently uses `2bcaee34…` as its negative
example. A re-pin implementation must not delete that test. It must change the negative example to
a different unreviewed 40-hex SHA and add or retain success coverage showing that the reviewed
`2bcaee34…` binding proceeds to the next guard.

## 6. Braincrew blast radius: active contract versus history

At committed Braincrew `HEAD=dfc41ff`, the old SHA or `PINNED_AX_SHA` occurs on **50 matching lines
across 15 files**. The older decision's “36 occurrences across 13 files” is stale after Issue #67.
“50” is a matching-line count; counting both the symbol and literal separately on a line produces a
larger token-match count.

### Change together in the later implementation

- `src/braincrew/live_preflight.py` — operative SUT constant and both refusals;
- `src/braincrew/ax-http-v1.yaml` — packaged SUT Adapter contract;
- `tests/unit/test_grounded_run.py`;
- `tests/contract/test_ax_http_adapter.py`;
- `tests/contract/test_principal_attachment_preflight.py`;
- `tests/contract/test_preflight_receipt_binding.py`;
- `tests/contract/test_ax_live_preflight_substrate.py`;
- `tests/acceptance/test_cli_live_preflight_substrate.py`;
- `tests/acceptance/test_cli_principal_attachment_preflight.py`.

These are active contract assertions or fixtures. They must move atomically with the pin.

### Do not rewrite old statements to look current

- `docs/decisions/2026-07-24-ax-evaluation-principal-and-parse-restoration-scope-lock.md`;
- `docs/decisions/2026-07-26-preflight-receipt-derived-binding.md`;
- `docs/superpowers/specs/2026-07-18-evidence-first-evaluation-plane-design.md`;
- `docs/superpowers/specs/2026-07-20-independent-evaluation-corpus-provisioning-design.md`.

Their old SHA records what was locked or implemented at that time. This new decision supersedes the
operative pin without erasing that audit trail.

`docs/status/braincrew-delivery-workflow.md` is a living record, but its historical
entries must also remain intact. It requires appended current-state entries, not a global
replacement. It is intentionally outside this cycle's pane-2 write scope.

## 7. Why a future re-pin could be wrong, and how to notice

This approval is exact, not forward-compatible. It becomes wrong if the AX runtime is later started
from any other commit or from a dirty checkout.

A future AX change requires a new review if it touches any of:

- parser selection, extracted-text normalization, table/list extraction, chunking, or span offsets;
- evaluation principal lookup, permissions, visibility, or role projection;
- embedding adapter/model/dimensions or vector generation;
- retrieval candidate pools, ranking, filtering, top-k, answer-mode, citation, or answer shaping;
- corpus-identity or parse-observation routes, services, schemas, or response fields;
- source materialization fields that feed corpus identity or retrieval;
- the exact dataset/corpus/provider state used by the evaluation.

Detection remains layered:

1. exact `PINNED_AX_SHA` equality rejects a different receipt or artifact;
2. the packaged Adapter contract freezes the same SUT SHA and response schemas;
3. Issue #38 must verify clean Braincrew and AX checkouts before capture;
4. fresh corpus-identity and parse observations must be captured and replayed;
5. every later pin change requires another range review rather than a constants sweep.

> **[Superseded 2026-07-30 — item 1's receipt and artifact identities no longer share one
> `PINNED_AX_SHA`. Receipt equality is now exact against `REVIEWED_PROVISIONED_AX_SHA`;
> artifact and live-capture SUT equality remain exact against the under-test `PINNED_AX_SHA`.
> See
> [the separate AX commit meanings decision](./2026-07-30-separate-provisioned-and-under-test-ax-commits.md).]**

One limitation remains: the Braincrew artifact validates the SHA it is given; it does not
cryptographically attest which binary a remote AX server is actually running. The controlled
runtime-start procedure must establish that link from clean checkout to running service.

## 8. Keep one SUT constant

`PINNED_AX_SHA` should remain one Braincrew-side SUT constant for this cycle.

The receipt does not become its authority. The direction remains:

```text
Braincrew review decision: PINNED_AX_SHA = 2bcaee34…
observed receipt fact:      repository.commit_sha = 2bcaee34…
required check:             observed fact == reviewed decision
```

That equality is now legitimate because the same commit has separately passed both reviews. A
second constant would add ceremony without distinguishing two current values.

If a later workflow produces a handoff at commit A but intentionally evaluates runtime commit B,
the shape must be reconsidered. At that point the honest model may need separate
`REVIEWED_HANDOFF_PRODUCER_SHA` and `PINNED_SUT_SHA` values plus an explicit compatibility review.
It must not silently loosen the current equality or derive B from A.

> **[Superseded 2026-07-30 — "for this cycle" was a correct and deliberately bounded decision, not
> an error. Its anticipated later-workflow condition has now occurred: the receipt was produced at
> commit A and the evaluation intentionally moved to commit B. The successor design uses the two
> separate identities and explicit compatibility review this section anticipated; see
> [the separate AX commit meanings decision](./2026-07-30-separate-provisioned-and-under-test-ax-commits.md).]**

## 9. `FROZEN_DATASET_VERSION`: the two records do not agree

This review found a separate design defect in the existing record.

Current `live_preflight.py` uses:

```text
FROZEN_DATASET_VERSION = "2.0.0"
manifest.dataset_version == FROZEN_DATASET_VERSION
DatasetIdentityEvidence.version = FROZEN_DATASET_VERSION
```

That constant is therefore the **integrated Braincrew dataset version**, not the nested parsing
component version.

The durable artifacts say:

- `datasets/dataset_manifest_v2.json` — integrated dataset `2.0.0`, parsing component
  `parsing/parsing_cases_v1.json`; that parsing file declares nested version `1.0.0` and its
  Verification split is `synthetic-rule-015` through `synthetic-rule-020`;
- `datasets/dataset_manifest_v3.json` — integrated dataset `3.0.0`, parsing component
  `parsing/parsing_cases_v2.json`; that parsing file declares nested version `2.0.0` and its
  Verification split is `demo-terms-guide-002` through `demo-conduct-policy-007`;
- `datasets/parsing/parsing_cases_v2.json` contains no `synthetic-rule-*` document in any split, and
  its Verification document-ID set has an empty intersection with the six historical Verification
  document IDs in parsing component v1;
- Braincrew Issue #38 — integrated dataset `3.0.0`, nested parsing component `2.0.0`, **and** the six
  reviewed historical parsing Verification cases.

The receipt-derived binding decision's statement that the current
`FROZEN_DATASET_VERSION = "2.0.0"` is correct because of a “name collision” does **not** agree with
the current code. The constant is the integrated version, and today's binding is internally
consistent as integrated `2.0.0` → nested parsing `1.0.0` → the six `synthetic-rule-*` cases.
Measured repository data rules out the earlier byte-identity hedge: parsing component v2 does not
contain the historical documents at all. A v2 integrated manifest still does not become v3 merely
because the nested parsing v2 file also declares `2.0.0`.

Issue #38 is not a coherent target as currently written. Its acceptance criterion requires nested
parsing component `2.0.0` and the six historical Verification cases together, but the former is
`parsing_cases_v2.json` while the latter exist only in nested parsing `1.0.0`,
`parsing_cases_v1.json`. No manifest/component relationship currently in the repository satisfies
both conditions. This is a **specification defect**, not a code defect or documentation typo, and it
blocks the follow-up dataset-identity work until the criterion chooses a coherent case-set lineage.

This does not invalidate `2bcaee34…` as the AX SUT commit, but it means the re-pin alone cannot
satisfy Issue #38. A separate dataset-identity implementation must bind three concerns explicitly:
the integrated manifest identity, the nested parsing component identity, and the reviewed case-set
identity. Merely assigning integrated `3.0.0` and nested parsing `2.0.0` to differently named fields
would select a parsing case set that cannot resolve any of the six current
`REVIEWED_PARSING_SOURCE_EVIDENCE` keys. Case-set selection must therefore be designed independently
from version labelling and protected by its own document-ID and source-digest evidence. This review
does not choose the corrected Issue #38 lineage or implement that fix.

## 10. Relationship to open AX Issue #37

AX Issue #37's open state does not decide whether `2bcaee34…` is acceptable as SUT code.

Issue #37 governs the operator-controlled snapshot/import sequence. Its remaining HTTP-boundary
criterion was explicitly deferred to AX Issue #43. Those are operational state, recovery, and
handoff gates. They are important to whether a live evaluation run is trustworthy, but they do not
show a parser, retrieval, authorization, or response-contract change in the reviewed commit range.

The open issue still matters procedurally:

- Braincrew Issue #38 formally lists AX #37 as a blocker;
- AX #37 and #43 remain open even though later Braincrew records say AX-B and sanitized handoff
  evidence exist;
- pane 1 should reconcile that issue topology before claiming `READY`.

It is not a reason to keep the obsolete `72805930…` SUT pin. It is a separate workflow gate that
must not be mistaken for code-review evidence.

## 11. Rejected alternatives

### Keep `72805930…`

Rejected. The live substrate and reviewed receipt are at `2bcaee34…`, while the evaluation route,
service, schemas, parser, retrieval query path, and authorization logic are unchanged across the
range. Keeping the ancestor would block every real artifact without preserving an
evaluation-relevant behavior boundary.

### Derive the SUT commit from the receipt

Rejected. It would still delete the independent review assertion. The receipt reports what ran;
Braincrew decides what it accepts.

### Re-pin only after adding another SHA check

Rejected as unnecessary for this exact range. The two existing exact-SHA refusals are sufficient
once their accepted value is independently reviewed. The needed change is to preserve their tests,
not stack a duplicate comparison beside them.

### Split the constant immediately

Rejected for the current equal-commit case. There is one accepted runtime SUT identity, and the
receipt happened to be produced at that same commit. Splitting becomes justified only when those
facts intentionally diverge.

### Rewrite every old SHA in documentation

Rejected. It would turn historical implementation and decision records into a false claim that
they had always targeted `2bcaee34…`.

### Treat the dataset-version problem as part of the SHA re-pin

Rejected. The defect is real, but coupling it to this re-pin would mix SUT code identity with
Braincrew dataset identity and make both changes harder to review.

## 12. Trade-offs

- **Benefit:** the reviewed live receipt and the exact AX runtime checkout can pass the same
  Braincrew-side SUT gate.
- **Cost:** `2bcaee34…` includes substantial provisioning code not needed by evaluation reads,
  increasing the reviewed surface.
- **Accepted risk:** writer-path changes can alter corpus state and stored vectors when executed.
  Reproducibility therefore depends on frozen corpus/provider/receipt evidence and no concurrent
  mutation, not on the Git pin alone.
- **Constraint preserved:** the pin is still an exact commit, not a branch, tag, receipt-derived
  value, or “latest” pointer.
- **Audit cost preserved:** future AX commits require another behavior-focused range review.

## 13. Failure modes

| Failure | Required response |
| --- | --- |
| AX runtime commit or checkout differs from `2bcaee34…` | Stop; do not capture or publish. |
| Receipt digest, state, subject, six-case mapping, or repository SHA differs | Existing fail-closed refusal remains. |
| Corpus/provider/count identities differ from reviewed evidence | Stop; the Git pin cannot bless state drift. |
| A writer runs concurrently with evaluation | Stop or restart from a newly reviewed frozen state; lineage locks protect writes, not benchmark reproducibility. |
| Future commit changes an evaluation-relevant surface | Perform a new range review before changing the pin. |
| Implementation rewrites historical documents | Reject the diff; append a superseding record instead. |
| Re-pin implementation deletes the unreviewed-commit negative test | Reject the diff; the general protection would become unobserved. |
| Dataset v2 is presented as integrated v3 because the six case **IDs** are identical in both parsing components | Reject the claim. The case `id` values are `parsing-015…020` in both files, while the `document.id` sets are **disjoint** — `synthetic-rule-*` under integrated v2, `demo-*` under integrated v3. A probe that reads case `id` and stops concludes the splits match; this exact trap has already produced one wrong fact-check in review. Integrated and nested component identities are also different. |
| All controlled tests pass but no live AX capture occurred | Keep `braincrew_preflight_ready=false`. |

## 14. Validation evidence and evidence not found

Available:

- AX detached checkout reported `HEAD=2bcaee3495fd7b3f624398819575cd86a5a15c47`;
- the reviewed range is five commits and 30 files with `+11,439 / -40`;
- every production diff was classified above;
- explicit diffs for the evaluation route/service/schemas, parser/jobs/intake, retrieval
  contracts/repository, and RBAC logic were empty;
- the evaluation route content is byte-for-byte the same at both range endpoints;
- Braincrew `HEAD=dfc41ff9c74c7ca8539f6d02318b607e6d6c3244`;
- committed Braincrew blast radius is 50 matching lines across 15 files;
- Issues #67 and #38 and AX Issues #37, #43, and #48 were read directly.

Not found or not proven:

- no live AX runtime was started or queried in this review;
- no proof was produced that a running server binary corresponds to the detached checkout;
- no new parsing, retrieval, or grounded-answer benchmark was run;
- no proof makes `braincrew_preflight_ready` true;
- AX #37 and #43 do not contain a formal completed/closed state matching the later Braincrew
  operational narrative;
- no code evidence supports treating the current `FROZEN_DATASET_VERSION` as the nested parsing
  component version; the code shows it is the integrated manifest version;
- recovery against the live AX cluster remains outside this review.

## 15. What this decision does not settle

This decision does not:

- perform or authorize the re-pin implementation;
- change `src/`, tests, the packaged contract, the status record, or the interview dossier;
- authorize commit, push, pull request, merge, runtime start, container start, or live HTTP capture;
- approve integrated dataset v3 wiring or resolve Issue #38's contradictory case-set requirement;
- prove provider availability beyond the recorded deterministic fake lineage;
- close AX #37/#43 or Braincrew #38;
- produce a live parsing/preflight observation or any retrieval, grounded-answer, or release-quality
  result; the recorded deterministic fake lineage does not support those wider quality claims;
- make `braincrew_preflight_ready` true.

## 16. Likely follow-up questions

**“Why approve a commit that contains code unrelated to evaluation reads?”**  
Because the exact runtime must match the applied substrate, and the unrelated additions do not
change the evaluation read contract. Their state effects are separately frozen and checked.

**“What protection disappears when the receipt starts passing?”**  
Only the refusal of this exact, now-reviewed `2bcaee34…` receipt. The check itself remains and still
rejects every other commit.

**“Does the unchanged evaluation route prove the results will be identical?”**  
No. Corpus rows and vectors changed intentionally, so retrieval and grounded answers may change.
The claim is that `2bcaee34…` is an acceptable SUT identity, not that its state produces the same
outputs as `72805930…`.

**“Why not approve future descendants that only say ‘provisioning’ in their titles?”**  
Commit titles are not evidence. Every future range must be diffed against the evaluation-relevant
surface and its state effects.

**“Can the SHA re-pin and dataset v3 change land together?”**  
They should be separate reviewable slices. The SHA decision is ready; the dataset identity has a
confirmed representation defect and needs its own contract and tests.

**“What is the next completion condition?”**  
A separate TDD implementation updates only active SUT contract assertions to `2bcaee34…`,
preserves the generic unreviewed-commit refusal, leaves historical records intact, and passes all
repository gates. Independent review must then verify that bounded diff before any Git lifecycle or
live-runtime proposal.
