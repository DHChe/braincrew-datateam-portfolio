# Dataset Identity and AX Corpus Contribution Are Two Bridged Axes

Date: 2026-07-27  
Status: **DECIDED — OPTION C LOCKED** by the repository owner on 2026-07-27; NOT IMPLEMENTED, NOT
LIVE-VERIFIED. The analysis body below is preserved as written **before** the decision; §18 records
the decision itself.  
Braincrew analysis baseline: `2a2f4699e1db3161b16c6cd1d92f683bc313d276`
(`docs/dataset-identity-scope-analysis`)  
Reviewed AX SUT: `2bcaee3495fd7b3f624398819575cd86a5a15c47`  
Governing issue: [Braincrew Issue #38](https://github.com/DHChe/braincrew-datateam-portfolio/issues/38)  
Answers the question left open by
[`docs/decisions/2026-07-26-ax-sut-commit-for-evaluation-review.md`](./2026-07-26-ax-sut-commit-for-evaluation-review.md)
§9.

## 1. Analysis result

**The Braincrew integrated dataset identity and the AX role-visible corpus contribution identity are
two different axes with an explicit production-time bridge. They are not one stored value, and they
are not freely unrelated labels.**

A third axis is also present: **the six live parsing probe cases**.

| Axis | Governing artifact | What it means |
| --- | --- | --- |
| Braincrew integrated dataset | `datasets/dataset_manifest_v*.json` plus component files and digests | Which 100-case evaluation bundle, component versions, case content, and source binding Braincrew validates |
| AX corpus contribution | visible `SeedVectorRecord.created_by_seed_version` values, aggregated as `contributing_versions` | Which import or tenant-upload operations contributed the retrieval records visible to a role |
| Live parsing probe set | reviewed AX-B handoff receipt plus frozen expected source evidence | Which six attachment IDs Braincrew calls and which source bytes, parser identity, and spans those calls must prove |

The first two axes legitimately meet when Braincrew qualifies the exact integrated v3 manifest and
publishes the AX import manifest:

1. `corpus_qualification.py` validates exact
   `braincrew-evaluation-dataset@3.0.0` manifest and component digests;
2. that same qualified output writes
   `seed_version = "braincrew-evaluation-dataset-3.0.0"` into the AX import manifest;
3. AX persists that value on imported vector rows as `created_by_seed_version`;
4. AX later aggregates visible row values into `contributing_versions`.

That is a deliberate provenance bridge, not evidence that both sides are the same field.

AX-B does not reuse the base seed label for its six attachments. Its materializer writes
`tenant-upload-v1:<approval_id>`. The reviewed handoff receipt consequently contains the base
`braincrew-evaluation-dataset-3.0.0` contribution and, for Executive and HRPractitioner, six
additional tenant-upload contributions. Its attachment/source-digest mapping matches integrated
v2's historical parsing Verification documents 6 of 6 and integrated v3's parsing Verification
documents 0 of 6.

Issue #38 therefore compresses **three concerns** into one sentence:

- integrated dataset v3 identity;
- nested parsing component v2 identity;
- the historical six-source live probe set.

The first two describe the frozen v3 bundle. The third describes the existing AX-B operational
receipt, not a member set of v3's parsing component.

This structural result is evidence-supported. The policy choice that follows from it is not.

## 2. Why this is not yet a locked decision

> **[Annotation added 2026-07-27 — the section below is preserved verbatim and was not edited.]**
> The question it frames has since been **answered by the repository owner, who chose Option C.**
> See §18. This section is kept because it records *why the analysis refused to decide* and *what
> the owner was actually choosing between* — deleting it would leave the decision looking obvious in
> hindsight when it was not.

The repository does not answer this product-policy question:

> Must `READY` prove live parsing against the six Verification documents that belong to integrated
> dataset v3, or may it prove the parser boundary against a separately frozen six-source operational
> probe set while independently binding the full v3 dataset identity?

Both are technically coherent contracts, but they make different claims:

- requiring v3's `demo-*` cases makes the live probes representative of the selected integrated
  dataset;
- retaining `synthetic-rule-*` as an explicitly separate operational probe set preserves the
  independently reviewed create-only evidence chain but does not prove that v3's own parsing
  Verification documents were uploaded and parsed through the attachment boundary.

Code and data establish the cost of each choice. They do not grant authority to choose which claim
the portfolio should publish. This record therefore recommends an option but does not decide it for
the owner.

Issue #38 nevertheless contains material intent evidence about the delivery shape already chosen
for that ticket. Criterion 3 asks for fresh observations from six reviewed parsing **attachments**,
not specifically from v3 Verification cases. Criterion 5 restricts Braincrew to consuming the
reviewed AX-A principal receipt and **AX-B handoff receipt only**, with no AX user, attachment,
database, blob, worker, provider, or recovery mutation. Those criteria do not decide what `READY`
should mean, but they do make Option C compatible with the ticket's present receipt-consumer scope.
Option B cannot be executed inside that scope as written: it requires both a criterion-5 re-scope
and a separately authorized prerequisite provisioning ticket that produces a different reviewed
handoff receipt.

## 3. Evidence that settles the axis question

### 3.1 Braincrew manifest identity is a bundle contract

`live_preflight.py:45-54` freezes an integrated dataset ID, version, integrated digest, and all
three component digests. `_frozen_dataset_identity` then compares those values against the loaded
manifest and recomputed snapshot digests (`live_preflight.py:960-992`).

The manifest controls component selection:

| Integrated manifest | Parsing path | Nested `dataset.version` | Verification `document.id` |
| --- | --- | --- | --- |
| `dataset_manifest_v2.json` | `parsing/parsing_cases_v1.json` | `1.0.0` | `synthetic-rule-015` … `synthetic-rule-020` |
| `dataset_manifest_v3.json` | `parsing/parsing_cases_v2.json` | `2.0.0` | six `demo-*` documents |

The two parsing files reuse case IDs `parsing-015` through `parsing-020`, but their nested
`document.id` values differ. The document IDs, source text, and digests are the load-bearing
identity, not the outer case IDs.

The current preflight couples the probe set to the manifest: `_verification_cases` accepts only
integrated version `2.0.0` and returns that snapshot's Verification cases
(`live_preflight.py:945-957`); `_approved_mapping` requires that set to equal the receipt-derived
attachment mapping (`live_preflight.py:995-1004`).

### 3.2 AX contribution identity is a visible-row provenance contract

AX corpus identity queries visible embedded `SeedVectorRecord` rows and returns the sorted set of
their `created_by_seed_version` values (`AX_portfolio`,
`backend/src/ax_engine/evaluation/service.py:122-161`).

For the base corpus, Braincrew first validates exact v3 bytes and digests
(`corpus_qualification.py:407-430`), then writes
`seed_version = "braincrew-evaluation-dataset-3.0.0"` into the AX import payload
(`corpus_qualification.py:702-718,754-769`).

For AX-B attachments, AX constructs
`version = "tenant-upload-v1:<approval_id>"` and persists it on the source, chunk, span, and vector
rows (`AX_portfolio`, `backend/src/ax_engine/sources/materialization.py:220-384`).

The two contribution forms share one AX provenance field, but they identify different operations:

- base qualified seed import;
- individual approved tenant uploads.

### 3.3 The reviewed receipt proves both contribution classes and a separate probe set

The create-only handoff receipt re-hashed to the pinned file digest:

```text
sha256:8d59a7907894532d702d0b7c658b8b28bc8370670b69f04884c42d8d1843c767
```

Measured from its sanitized content:

| Role | Has base v3 contribution | Tenant-upload contributions |
| --- | --- | ---: |
| Employee | yes | 0 |
| Executive | yes | 6 |
| HRPractitioner | yes | 6 |

The six receipt attachment source digests overlap:

```text
integrated v2 parsing Verification: 6 / 6
integrated v3 parsing Verification: 0 / 6
```

This is not a role-visibility anomaly. Employee correctly cannot see the `hr_only` uploads while
still seeing the base v3 contribution.

### 3.4 Current Braincrew code does not yet enforce the bridge

`LivePreflightArtifact` stores `dataset_identity` and `corpus_observations` as separate fields
(`live_preflight.py:212-227`). Its validator recomputes corpus response digests, but it does not
compare `corpus_observations[*].response.contributing_versions` with
`dataset_identity.version` (`live_preflight.py:229-274`).

The implementation gap is larger than a missing comparison. `AxHttpAdapter.corpus_identity()`
exists, but there are zero production call sites in `src/`; every call site is in tests. The
principal-attachment capture path validates the frozen manifest and receipt-derived parse mapping,
then hard-codes `corpus_observations=()` (`live_preflight.py:319-390,454-463`). Its validator
explicitly rejects any non-empty corpus observations:

```python
# live_preflight.py:708-709
if artifact.corpus_observations:
    raise ValueError("principal attachment capture cannot contain corpus observations")
```

Issue #38 requires the cross-axis assertion. Current source preserves the two evidence shapes but
does not compose them in a production capture path and actively rejects that composition in the
principal-attachment contract. A capture path and contract or schema extension must therefore exist
before the bridge comparison can be added.

## 4. Current coherent and incoherent states

| State | Internal result |
| --- | --- |
| Integrated v2 → parsing v1 → historical `synthetic-rule-*` probes | Coherent inside current Braincrew preflight, but does not match Issue #38's integrated-v3 target or the applied AX base contribution label |
| Integrated v3 → parsing v2 → `demo-*` Verification probes | Coherent dataset lineage, but no current reviewed AX-B attachment receipt supplies those six probes |
| Integrated v3 + nested parsing v2 + historical `synthetic-rule-*` probes described as members of that component | Incoherent; repository data disproves membership |
| Integrated v3 + nested parsing v2 + historical `synthetic-rule-*` identified as a separate operational probe set | Coherent two-axis-plus-probe design, but not represented by the current preflight schema and not yet approved as the meaning of `READY` |

No current repository state satisfies Issue #38's present sentence literally.

## 5. Option costs

One material cost is common to every option. Issue #38 criterion 6 requires a create-only
`live-verification-preflight-artifact-v2`, but that schema name has zero occurrences in `src/` and
`tests/`. The implemented schema names are `live-preflight-evidence-v1` and
`principal-attachment-preflight-evidence-v1`; the current production capture paths do not combine
the frozen dataset identity, all three role-visible corpus observations, and the reviewed parsing
observations in the form #38 requires. Consequently, **no option satisfies criterion 6 today**.
Every viable option needs new artifact/contract work in addition to its option-specific work, so
"smallest" below is relative and must not be read as small in absolute terms.

| Option | Preserves | Invalidates or weakens | New work | AX-B provisioning consequence |
| --- | --- | --- | --- | --- |
| **A. Stay on coherent integrated v2**: v2 manifest, parsing v1, historical probes | Current preflight coupling and existing six-probe receipt | Issue #38's v3 target; v3 qualification/import identity as the selected evaluation bundle | Amend #38 to v2 or explicitly permit a v2 manifest beside a v3 AX contribution; review the resulting provenance claim | Existing AX-B receipt remains usable for probes. Realigning the base AX label to v2 would require separately authorized provisioning and may conflict with existing imported state; no such path was found or authorized |
| **B. Use coherent v3 end to end**: v3 manifest, parsing v2, six `demo-*` probes | Frozen v3 dataset and the meaning that live probes are actual v3 Verification cases | Existing AX-B six-attachment evidence chain as the #38 probe source | Upload, parse, approve, materialize, capture, and independently review six v3 `demo-*` sources; replace the receipt binding and expected evidence | Requires a new provisioning operation and new create-only receipt. The existing apply cannot be rerun or edited |
| **C. Separate v3 dataset identity from the historical operational probe set** | Frozen v3 dataset; current applied base contribution; existing independently reviewed AX-B receipt; receipt-consumer-only boundary | The stronger claim that the six live probes are v3 dataset members | Add an explicit probe-set identity and digest contract; decouple `_verification_cases` from manifest membership; validate both axes and their bridge; document that probe success is boundary readiness, not v3 case execution | No new AX provisioning. A separately authorized live runtime start and fresh Braincrew capture are still required |
| **D. Publish a new successor dataset that intentionally includes the historical probes** | Ability to make dataset membership and live probes identical again | Frozen v3 identity and its qualification/import evidence as the selected target | New dataset version, case/source review, digests, qualification, AX import, possibly new attachment provisioning, and independent review across both repositories | Requires new base-corpus provisioning evidence and likely a new AX-B receipt; highest cost |
| **E. Mutate v3 in place or relabel existing rows** | Nothing trustworthy | Frozen v3 digests, qualification receipt, import receipt, replay, provenance, and historical truth | Would require rewriting immutable evidence or SUT state | Not a valid option |

## 6. AX-B evidence chain under each viable option

### Option A: coherent v2

The six source digests, attachment IDs, parser observations, and approval lineage remain usable.
The base v3 contribution in all three role identities remains a true observed fact but no longer
names the selected integrated Braincrew manifest. If the owner treats the axes as independent,
that mismatch must be declared and defended. If the owner requires them to align, new base-corpus
provisioning is needed and the existing AX-B receipt alone cannot supply it.

### Option B: coherent v3

The existing handoff receipt remains valid historical evidence for the `synthetic-rule-*` operation,
but it cannot authorize or describe `demo-*` attachments. A new operation needs:

- explicit authorization for AX database, blob, worker, and provider-side writes;
- a new operation identity, thread, create-only receipt path, and reviewed source bundle;
- new attachment and approval IDs;
- new post-state counts, corpus identities, and independent receipt review;
- a new Braincrew pinned receipt digest.

Re-running the existing apply is both forbidden and ineffective. The handoff receipt is create-only,
and `AttachmentService.stage_files` returns an existing attachment when tenant, thread, and content
hash match (`AX_portfolio`, `backend/src/ax_engine/attachments/service.py:51-82`).

### Option C: separate operational probes

The existing receipt remains the evidence root for all six attachment addresses and source digests.
No AX mutation is needed. Braincrew must stop deriving the probe member set from the integrated
manifest and instead record two independently reviewable identities:

1. exact integrated v3 dataset and component digests;
2. exact historical operational probe-set case IDs and source digests bound to the reviewed receipt.

The artifact must not call the second identity the v3 parsing component. It must also add the missing
bridge check that all three role-visible corpus identities include the qualified base v3
contribution. This is not a one-line comparison: no production path currently calls
`AxHttpAdapter.corpus_identity()`, and the principal-attachment contract hard-codes empty corpus
observations and rejects non-empty ones at `live_preflight.py:708`. Braincrew must first add a
production corpus-capture or composition path, extend the capture contract or introduce the
required v2 artifact schema so it can carry corpus and principal-attachment evidence together, and
only then enforce the cross-axis comparison.

### Option D: new successor

Every v3 and AX-B artifact remains historical. None may be rewritten. A new dataset, qualification,
import, operational receipt, live capture, and independent review chain must be appended. This is a
new release slice, not a repair to the current preflight.

## 7. Requirements before `braincrew_preflight_ready` can be `true`

The five conditions from the receipt-derived binding decision remain unchanged. They are necessary
but not complete: Issue #38's sixth criterion also requires the presently nonexistent
`live-verification-preflight-artifact-v2` to report `READY` and replay its logical digest. That
common schema/contract and production-capture gap applies to A, B, C, and D.

| Condition | A: v2 | B: v3 `demo-*` | C: v3 + separate probes | D: new successor |
| --- | --- | --- | --- | --- |
| 1. Live AX runtime answered real probes | Still required | Still required after new provisioning | Still required; existing stopped runtime is insufficient | Still required after all new provisioning |
| 2. Evaluation principal was accepted and authorized for parsing | Still required | Still required for the new attachments | Still required for existing receipt-derived attachments | Still required |
| 3. Six sources parsed to frozen expected evidence | Existing receipt/source digests are compatible | Needs six newly provisioned `demo-*` attachments and new expected evidence | Existing receipt/source digests are compatible once named as a separate probe contract | Needs a newly approved probe set and receipt |
| 4. Capture bound to reviewed pinned SUT commit | Current `2bcaee34…` pin and receipt SHA can support it | New receipt must also bind the reviewed SUT | Current pin and receipt can support it | Every new receipt must bind a separately reviewed SUT |
| 5. Captured artifact passed independent review | Required | Required, plus provisioning receipt review | Required | Required at every new evidence layer |

No option makes the flag true through documentation or constant changes alone.

## 8. AX Issue #37 and #43 topology

[AX Issue #37](https://github.com/DHChe/AX_portfolio/issues/37) and
[AX Issue #43](https://github.com/DHChe/AX_portfolio/issues/43) were re-read on 2026-07-27. Both are
still `OPEN`. Braincrew Issue #38 still lists AX #37 as a blocker.

This is a workflow gate, not evidence that the applied rows or receipt are false. The repository and
reviewed receipt show that substantial work described by those issues occurred. The open issue
topology nevertheless prevents a truthful claim that all formal blockers of #38 are cleared.

- Options A and C reuse current operational evidence. Before `READY`, the owner must reconcile
  whether AX #37 and #43 are complete, superseded, or still have unmet acceptance criteria.
- Option B adds a new provisioning operation beyond the receipt those issues currently describe;
  it needs a new authorized dependency and cannot silently reuse their completion narrative.
- Option D expands the topology further with new qualification, import, and attachment operations.

Closing or amending an issue is not authorized by this analysis. Ignoring the open blockers is also
not an available option.

## 9. Issue #38 should be amended

The body should change before dataset-identity implementation begins. A comment records the defect,
but the executable acceptance checklist still contains the contradiction.

Only C and B receive paste-ready text below deliberately. C is the recommended receipt-preserving
choice, and B is the direct alternative when `READY` must prove v3-member probes. Option A changes
the selected integrated dataset and requires a broader checklist re-scope; Option D creates a new
release and evidence chain. Neither can be made safe by replacing only criteria 2 and 5, while
Option E is invalid. If the owner selects A or D, the complete Issue #38 checklist must be rewritten
and reviewed rather than borrowing either package below.

If the owner accepts **Option C**, replace the contradictory acceptance criterion 2 with:

> - [ ] Employee, Executive, and HRPractitioner corpus identities are fetched through the strict AX
> contract and each truthfully includes `braincrew-evaluation-dataset-3.0.0` in
> `contributing_versions`, with frozen role-visible record counts and digests. Braincrew binds the
> integrated evaluation dataset to `braincrew-evaluation-dataset@3.0.0` and validates
> `dataset_manifest_v3.json`, whose nested parsing component is
> `parsing/parsing_cases_v2.json@2.0.0`. Separately, the create-only live preflight consumes the six
> reviewed AX-B attachments for `synthetic-rule-015` through `synthetic-rule-020` as a frozen
> operational parsing probe set bound by the reviewed handoff receipt. It does not claim that those
> probes are members of the v3 parsing component or that their tenant-upload rows carry the base
> dataset seed version.

If the owner instead chooses **Option B**, replace both criterion 2 and criterion 5 with this
two-criterion package:

> - [ ] Employee, Executive, and HRPractitioner corpus identities are fetched through the strict AX
> contract and each truthfully includes `braincrew-evaluation-dataset-3.0.0` in
> `contributing_versions`, with frozen role-visible record counts and digests. Braincrew binds the
> integrated evaluation dataset to `braincrew-evaluation-dataset@3.0.0` and validates
> `dataset_manifest_v3.json`, whose nested parsing component is
> `parsing/parsing_cases_v2.json@2.0.0`. The six fresh strict parsing observations are captured from
> reviewed attachments whose source identities and digests correspond exactly to that component's
> six Verification documents.
>
> - [ ] Braincrew consumes the reviewed AX-A principal receipt and the newly reviewed handoff
> receipt for the selected v3 Verification probe set only; it performs no AX user, attachment,
> database, blob, worker, provider, or recovery mutation. That selected-probe receipt is produced
> and independently reviewed under a separately authorized prerequisite provisioning ticket before
> this issue begins its receipt-consumer run.

The first replacement preserves the current receipt. The second is inseparable from the
criterion-5 replacement and requires new provisioning before #38; #38 itself remains a
mutation-free receipt consumer.

## 10. Recommendation, not decision

**Recommend Option C: bind integrated v3 and its nested parsing v2 component as the evaluation
dataset, while naming the six existing `synthetic-rule-*` attachments as a separate operational
parsing probe set.**

Reasons:

1. it preserves the exact frozen v3 dataset and the truthful v3 base contribution already visible
   to all three roles;
2. it preserves the independently reviewed, create-only AX-B receipt instead of manufacturing a
   second write operation to make terminology line up;
3. it matches Issue #38's receipt-consumer-only architecture;
4. it makes the claim boundary explicit: the live probe proves attachment parsing readiness, while
   the manifest proves dataset identity;
5. it remains the smallest reversible total change among the viable options after a human chooses
   the contract, but it is not small in absolute terms: it requires a production corpus-capture or
   composition path, a new artifact/contract shape, a distinct probe-set identity, manifest-decoupled
   mapping, and the bridge check before fresh capture and review.

The trade-off is material: Option C does **not** prove live parsing of v3's own six `demo-*`
Verification documents. If the owner intends `READY` to mean that stronger statement, Option B is
the correct choice despite its operational cost.

The corrected cost does not change this recommendation. The new v2 artifact and role-corpus bridge
are common #38 work, while Option B adds a separately authorized AX provisioning operation and new
receipt review. Option C still has the lower total cost and better matches #38's current
receipt-consumer intent, but the earlier wording materially under-priced its Braincrew work.

That meaning of `READY` is the human decision still pending.

## 11. Rejected alternatives

### Treat the labels as one field

Rejected by code. Braincrew manifest identity is validated from files and digests; AX contribution
identity is aggregated from visible row provenance. They meet through qualification/import, not
through shared storage.

### Treat the two axes as freely independent

Rejected. Braincrew deliberately generates the base AX seed label only after validating exact v3
manifest and component digests. Permitting arbitrary label/manifest combinations would discard that
provenance bridge.

### Claim nested parsing `2.0.0` contains the historical six

Rejected by data. It contains six `demo-*` Verification documents and none of the six
`synthetic-rule-*` documents.

### Raise only `FROZEN_DATASET_VERSION`

Rejected. The integrated digest, component digests, manifest path, case member set, mapping, and
artifact semantics move with the version. The current digest checks fail closed, but a constants
sweep does not resolve the contract.

### Rewrite or relabel the existing receipt or AX rows

Rejected. It would destroy create-only provenance and turn observed operation identities into
author-authored expectations.

### Retry the AX-B apply

Rejected. The receipt path is create-only, the run contract forbids retry, and content-hash
de-duplication can return old IDs while creating no rows.

## 12. Trade-offs

| Choice pressure | Option B: v3 `demo-*` | Option C: separate probes |
| --- | --- | --- |
| Dataset-to-probe representativeness | Strongest | Explicitly limited |
| Existing reviewed evidence reuse | Low | Highest |
| New SUT mutation | Required | None |
| Operational authorization and recovery cost | High: prerequisite AX provisioning, runtime, and receipt review | No AX mutation; authorized runtime start and fresh Braincrew capture |
| Required Braincrew artifact work | New v2 artifact/composition path, role-corpus capture, bridge check, and new receipt binding | Same common v2 artifact, corpus-capture, and bridge work, plus explicit probe-set identity and manifest-decoupled mapping |
| Contract clarity | Simple membership model after new evidence exists | More explicit identities and artifact fields |
| Risk of overstating what `READY` proves | Lower if fully executed | Must clearly distinguish boundary readiness from v3 case execution |

## 13. Failure modes

| Failure | Required response |
| --- | --- |
| Integrated v3 is selected but historical probes are described as v3 members | Reject the contract as false |
| AX `contributing_versions` is copied into dataset identity without manifest replay | Reject; observed row provenance is not the manifest |
| Manifest v3 passes but no role-visible v3 base contribution is checked | Keep preflight blocked; the bridge is unverified |
| A proposed implementation lacks `live-verification-preflight-artifact-v2` or a production path that composes dataset, corpus, and parsing evidence | Keep preflight blocked; Issue #38 criterion 6 is not implemented |
| Existing receipt is used for `demo-*` cases | Reject; source-digest overlap is 0 of 6 |
| New provisioning overwrites or replaces the old receipt | Reject; append new evidence |
| Existing apply is retried after changing expected IDs or paths | Stop; this can produce de-duplicated fake success |
| AX #37/#43 remain open but #38 is declared unblocked | Reject the workflow transition |
| Controlled tests pass without live AX probes | Keep `braincrew_preflight_ready=false` |
| Option C is accepted but the artifact omits a distinct probe-set identity | Reject; the ambiguity would survive under new field names |

## 14. Validation evidence and evidence not found

### Reproduced

- Branch is `docs/dataset-identity-scope-analysis`; HEAD is
  `2a2f4699e1db3161b16c6cd1d92f683bc313d276`.
- Braincrew Issue #38 body and its sole specification-defect comment were read directly.
- AX Issue #37 and #43 both report `OPEN`.
- Integrated v2 selects parsing component `1.0.0` and the six historical
  `synthetic-rule-*` Verification documents.
- Integrated v3 selects parsing component `2.0.0` and six `demo-*` Verification documents.
- Receipt-to-v2 Verification source-digest overlap is 6 of 6.
- Receipt-to-v3 Verification source-digest overlap is 0 of 6.
- The handoff receipt file digest reproduces the pinned
  `8d59a790…1843c767` value.
- All three receipt corpus identities contain
  `braincrew-evaluation-dataset-3.0.0`.
- Executive and HRPractitioner each contain six
  `tenant-upload-v1:<approval_id>` contributions; Employee contains none.
- AX corpus identity derives contributions from visible vector-row provenance.
- AX-B materialization uses a per-approval tenant-upload version.
- AX-B handoff receipt reservation is create-only and attachment upload de-duplicates by content
  hash within a thread.
- Issue #38 criterion 3 names reviewed parsing attachments, and criterion 5 constrains Braincrew to
  the reviewed AX-A and AX-B receipts without AX mutation.

### Not found

- no manifest or parsing component in the repository that combines integrated v3, nested parsing
  `2.0.0`, and the historical six `synthetic-rule-*` Verification documents;
- no current reviewed AX-B receipt whose six attachments correspond to v3's `demo-*` Verification
  documents;
- no production call to `AxHttpAdapter.corpus_identity()`; only tests call it;
- no production Braincrew path that composes role-visible corpus observations with the frozen
  dataset and principal-attachment evidence; the principal contract rejects that composition;
- no `live-verification-preflight-artifact-v2` schema in `src/` or `tests/`;
- no explicit artifact field naming the historical six as an operational probe set independent of
  the integrated manifest;
- no authority that decides whether `READY` requires v3-member probes or permits an independent
  operational probe set;
- no closed or superseded state for AX #37 or #43;
- no live runtime evidence in this analysis.

## 15. What this analysis does not settle

This record does not:

- choose Option B or C for the owner;
- authorize changes to `src/`, `tests/`, `FROZEN_DATASET_VERSION`, or
  `live_preflight.py:951`;
- amend Issue #38 on GitHub;
- authorize a runtime start, upload, approval, materialization, database or blob write, provider
  call, recovery action, or new receipt;
- make `braincrew_preflight_ready` true;
- declare AX #37 or #43 complete;
- rewrite the older 2026-07-24 scope lock. Its inference that parsing component `2.0.0`
  “therefore” carries the historical six is factually contradicted by the files, but history must be
  superseded rather than edited;
- prove parsing, retrieval, or grounded-answer quality.

## 16. Brief and issue discrepancies

The eight measured inputs in the Cycle 66 brief were independently reproduced.

Two framing corrections are required:

1. the axes are separate, but the base AX seed version is not an arbitrary independent label;
   Braincrew creates it through the exact v3 qualification path;
2. “historical v2 parsing-component identity” is ambiguous and, when used to mean nested component
   version `2.0.0`, false. Integrated dataset v2 points to nested parsing component `1.0.0`.

Issue #38's body remains wrong because the defect exists in its acceptance checklist, not only in
the explanatory comment.

## 17. Likely follow-up questions

**“Why not just call the historical probes part of v3?”**  
Because v3 is frozen to different document IDs, texts, and component digests. The label would make
a false membership claim.

**“Does Option C weaken fail-closed behavior?”**  
It need not. It requires two exact identities instead of deriving one from the other: frozen v3
manifest digests and a frozen receipt-bound probe-set identity. Missing either must block.

**“Does the current receipt already prove `READY`?”**  
No. It proves applied state and receipt identities. A fresh live Braincrew capture must still
satisfy all five receipt-derived conditions, implement Issue #38's v2 artifact criterion, and pass
independent review.

**“Can Option B reuse the existing receipt path?”**  
No. The current receipt is create-only historical evidence for different sources. A new authorized
operation requires a new receipt identity and review.

**“Can AX #37 and #43 be ignored because the data exists?”**  
No. Their open state is a formal workflow gate. The issue owner must reconcile completion,
supersession, or remaining criteria before #38 can be declared unblocked.

**“What decision should the owner make?”**  
Choose Option C if `READY` means “the pinned parser boundary works against a separately reviewed
operational probe set while the v3 dataset identity is independently frozen.” Choose Option B if
`READY` must mean “the actual v3 parsing Verification documents were uploaded and parsed live.”

---

## 18. Decision — Option C, locked 2026-07-27

**The repository owner chose Option C.** Everything above §18 was written before that choice and is
preserved unedited; this section is the decision, not a summary of the analysis.

### The decision

**Bind the integrated evaluation dataset to `braincrew-evaluation-dataset@3.0.0` and its nested
parsing component `parsing/parsing_cases_v2.json@2.0.0`. Separately, name the six existing
`synthetic-rule-015…020` AX-B attachments as a frozen operational parsing probe set, bound by the
reviewed handoff receipt, and do not claim they are members of the v3 parsing component.**

### What this deliberately gives up

`READY` will mean **the pinned parser boundary works against a separately reviewed operational probe
set, while the v3 dataset identity is independently frozen.** It will **not** mean that v3's own six
`demo-*` Verification documents were uploaded and parsed live. Anyone reading a future `READY` claim
is entitled to that distinction, so it must appear wherever the claim appears — not only here.

Option B is the correct choice if that stronger statement is ever required. It remains costed in §5
and §6, and §9 carries usable replacement wording for it, so reversing this decision does not require
redoing the analysis.

### Why this option and not the others

1. It preserves the independently reviewed, create-only AX-B receipt instead of manufacturing a
   second write operation so that terminology lines up.
2. It matches the shape Issue #38 **already has**: criterion 3 asks for observations from reviewed
   parsing *attachments*, and criterion 5 restricts Braincrew to the AX-A and AX-B receipts with no
   AX mutation. Option B cannot be executed inside that scope without re-scoping criterion 5 **and** a
   prerequisite provisioning ticket.
3. It keeps the frozen v3 dataset and the truthful v3 base contribution already visible to all three
   roles.
4. It makes the claim boundary explicit rather than blurring two axes into one sentence, which is the
   defect this whole record exists to remove.

### What this decision does **not** authorize

Nothing is implemented by locking it. Specifically it does not authorize any `src/` or `tests/`
change, any Git lifecycle action, any AX runtime start, any new provisioning, or any edit to Issue
#38 — that amendment is a separate authorized step using §9's Option C wording.

### The cost that survives this choice

**No option removes it, including this one.** Issue #38's sixth criterion requires a create-only
`live-verification-preflight-artifact-v2`, and that schema does not exist — zero occurrences in
`src/` or `tests/`. The artifact it names must carry the frozen dataset identity, all three
role-visible corpus observations, and the reviewed parsing observations **together**.

The obstacle is not that the model forbids that combination. `dataset_identity` is an optional field
on the shared artifact model, and the generic `live-preflight-evidence-v1` branch forbids only a
declared `capture_contract` and a retained blocker request — it rejects neither corpus observations
nor a dataset identity, so it could structurally hold all three today. The obstacle is that **nothing
produces that combination**: no production path calls `AxHttpAdapter.corpus_identity()` at all, and
the principal-attachment contract rejects corpus observations outright at `live_preflight.py:708`.

So the next implementation ticket is **not** "add a cross-check". It is a capture-path and artifact
contract that can hold both axes at once, and only then the cross-check.

`braincrew_preflight_ready` remains `false`. **AX #37** is an open formal blocker listed in Issue
#38's body; **AX #43**, which inherited #37's HTTP-boundary criterion, is also open but is **not**
listed there. Both still have to be reconciled, and conflating the two overstates what #38 formally
records — see §8, which states this correctly.
