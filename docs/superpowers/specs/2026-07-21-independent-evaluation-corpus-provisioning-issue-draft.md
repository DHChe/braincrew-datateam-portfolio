# Independent Evaluation Corpus Provisioning — `to-spec` Issue Draft

Date: 2026-07-21
Status: published as [Braincrew Issue #30](https://github.com/DHChe/braincrew-datateam-portfolio/issues/30) on 2026-07-21; local source retained
Implementation tickets: [#31](https://github.com/DHChe/braincrew-datateam-portfolio/issues/31) through [#38](https://github.com/DHChe/braincrew-datateam-portfolio/issues/38)
Implementation checkpoint: Braincrew #31/#32/#33/#42 merged; Braincrew #34 reviewed and fully verified locally at its Git gate on 2026-07-22
Proposed title: Provision an independently authored corpus for pinned live Verification
Tracker relationship: new Braincrew prerequisite that blocks Issue #15
Approved design: `2026-07-20-independent-evaluation-corpus-provisioning-design.md`
Companion AX design: `DHChe/AX_portfolio` generic synthetic seed-pack importer
Fixed points: Braincrew `1185ba8a9e6bab038743531a56f8f2c5ce2b44eb`; AX base `a5391ae8aa2b0d1342809f3599283b7759d6e4e3`
Latest merged AX importer prerequisite: `6bfc27a7bf170172a20dd470d6fd877858c9fb80`

## Problem Statement

Braincrew Issue #15 cannot honestly run its pinned 30-case live baseline/candidate comparison.
The current AX-visible corpora for `Employee`, `Executive`, and `HRPractitioner` contain only
records contributed by `bprime-2026-07-04`, so they do not prove that
`braincrew-evaluation-dataset@2.0.0` is materially represented. The strict parsing preflight also
uses nonexistent placeholder attachment identifiers and a non-UUID evaluation user, causing a
denied-access audit path to be misreported as HTTP 503 `audit_persistence_failed`.

Braincrew needs a reproducible prerequisite that supplies independently authored public or
synthetic evidence without deriving that evidence from evaluation expectations. It also needs to
validate corpus identity, visibility, parse observations, and sanitized receipts without writing
directly to AX or weakening the existing fail-closed preflight.

## Solution

Create a Braincrew-owned, independently authored synthetic corpus pack and a fail-closed
qualification path. Authoring receives only a reviewed domain brief, the exact generic AX pack
schema, and an empty isolated staging directory. The produced bytes are validated and sealed
before any process may compare them with evaluation data.

After sealing, a separate Braincrew cross-validator compares the immutable pack with dataset v2.
Only a complete match may produce a sanitized qualification receipt and an import manifest that
binds the unchanged corpus digest to `braincrew-evaluation-dataset@2.0.0`. Any mismatch returns a
typed blocker and produces no repaired data or import manifest.

The qualified pack then crosses the repository boundary through the versioned
`ax-synthetic-seed-pack-v1` file and JSON-receipt contract. AX remains solely responsible for
database validation and loading. Braincrew consumes only sanitized AX receipts, the three
role-visible corpus identities, and six strict parse observations. A new create-only preflight
may report `READY` only when all identities and observations match the pinned contracts. The
workflow stops at `READY`; baseline and candidate execution require separate authorization.

## User Stories

1. As an evaluation owner, I want corpus evidence authored without access to expected answers or evidence, so that the benchmark cannot manufacture the facts it later claims to retrieve.
2. As an independent author, I want an allowlisted input directory and an empty writable staging directory, so that I cannot accidentally read evaluation datasets, fixtures, prior runs, credentials, or private documents.
3. As a provenance reviewer, I want every source explicitly labeled synthetic/demo, licensed `CC0-1.0`, and marked reviewed, so that only publishable evidence can be sealed.
4. As a provenance reviewer, I want the authoring brief to exclude case IDs, queries, answer keys, expected evidence, scores, and split labels, so that guidance cannot leak evaluation expectations.
5. As a corpus operator, I want source bytes and manifest fields validated before sealing, so that invalid UTF-8, line endings, Unicode, paths, fields, or digests fail before publication.
6. As a corpus operator, I want the sealed content digest to bind the ordered source manifest and exact source bytes, so that any later mutation is detectable.
7. As an evaluation owner, I want source or visibility changes to require a new corpus version, so that evidence-bearing bytes are never repaired in place.
8. As an evaluation owner, I want the independently authored content manifest to omit the dataset seed version, so that provenance cannot be asserted before alignment is proven.
9. As a cross-validation operator, I want the sealed pack compared read-only with all 100 dataset cases, so that required source identity closure is proven across the complete evaluation surface.
10. As a cross-validation operator, I want exact source-text digest equality checked wherever dataset v2 freezes source text, so that a matching label cannot hide different content.
11. As an authorization reviewer, I want required and forbidden visibility checked for `Employee`, `Executive`, and `HRPractitioner`, so that role-visible evidence matches the frozen authorization contract.
12. As an evaluation owner, I want distractor coverage validated independently of expected answer sources, so that the corpus remains a realistic retrieval surface rather than an answer-only index.
13. As an operator, I want every qualification failure returned as a typed blocker, so that schema, digest, source, visibility, and provenance failures are distinguishable without raw content disclosure.
14. As an operator, I want a successful cross-validation to create a separate import manifest bound to the sealed digest and qualification receipt, so that AX receives the dataset version only after actual alignment is proven.
15. As an AX maintainer, I want Braincrew to exchange only versioned files and strict JSON receipts, so that no AX source code, ORM object, migration, fixture, or database access crosses repositories.
16. As a preflight operator, I want evaluation tenant and user identifiers validated as UUIDs before HTTP requests, so that malformed local configuration becomes a non-retryable configuration blocker rather than a false service outage.
17. As a preflight operator, I want the six parsing documents mapped to their real synthetic attachment identifiers and owner subject, so that each probe requests an existing authorized record.
18. As an evaluation reviewer, I want six fresh strict parse observations with exact applied role and response digests, so that parsing availability is measured rather than inferred from attachment state or fixtures.
19. As an evaluation reviewer, I want missing structure fields to remain later quality observations, so that transport success cannot be mislabeled as parsing quality success.
20. As a security reviewer, I want receipts to exclude raw text, queries, answers, vectors, credentials, database URLs, authorization material, and private paths, so that the evidence is safe to retain and review.
21. As an experiment owner, I want `READY` to freeze corpus, code, model/provider, prompt, roles, dataset, and configuration, so that baseline and candidate differ only by the approved experiment variable.
22. As an experiment owner, I want any provisioning or preflight failure to stop without auto-edit, retry with changed data, delete, restore, or baseline execution, so that failures remain diagnosable and evidence is not silently rewritten.

## Implementation Decisions

- Braincrew owns independent authoring constraints, the sealed corpus pack, qualification logic, import-manifest creation, sanitized qualification receipts, and fail-closed stop decisions.
- AX owns the generic pack importer, all database access, provider verification, transactionality, idempotency, audit, and authoritative role-visible corpus identity.
- Repository integration is limited to `ax-synthetic-seed-pack-v1` bytes plus versioned JSON receipts. Neither repository imports the other's implementation.
- The content-authoring process and post-seal validator are separate processes and contexts. The authoring process has no repository, dataset, fixture, database, or network access.
- Authoring is not part of the initial code implementation slice. It remains a later child ticket that begins from a reviewed clean commit in a fresh restricted context.
- The pack uses two manifests. The sealed content manifest contains source identity and bytes but no `seed_version`; the post-qualification import manifest binds the unchanged content digest to the dataset version and qualification receipt.
- The generic AX identifier grammar excludes `@`; the import manifest therefore uses schema-valid `seed_version = braincrew-evaluation-dataset-2.0.0`, while the qualification receipt binds exact ID `braincrew-evaluation-dataset`, version `2.0.0`, integrated digest, component digests, and 100-case count.
- Canonical identity rejects rather than normalizes invalid bytes. Accepted source bytes are UTF-8 without BOM, NFC, and LF-only. Canonical JSON uses sorted object keys, compact separators, preserved array order, materialized defaults, no floats, and NFC strings without carriage returns.
- The pack covers the complete 100-case required source-identity surface and contains non-empty distractor coverage. It is not required to contain one document per case.
- Every source is synthetic/demo, licensed `CC0-1.0`, and explicitly provenance-reviewed. Private/customer content and mixed public-source labeling are excluded from this version.
- Forbidden evaluation-derived fields are rejected recursively in both manifests rather than checked only by review convention.
- Cross-validation is read-only. Failure may emit typed blockers but may not emit repaired corpus bytes, repaired dataset bytes, or an import manifest.
- Qualification failures preserve the stable blocker family `CORPUS_PACK_SCHEMA_INVALID`, `CORPUS_PACK_DIGEST_MISMATCH`, `CORPUS_REQUIRED_SOURCE_MISSING`, `CORPUS_SOURCE_TEXT_DIGEST_MISMATCH`, `CORPUS_REQUIRED_VISIBILITY_MISMATCH`, `CORPUS_FORBIDDEN_VISIBILITY_MISMATCH`, and `CORPUS_PROVENANCE_REVIEW_REQUIRED`.
- Qualification receipts store bounded identities and digests only. They never store raw content, evaluation answers, vectors, secrets, database locations, or authorization material.
- Evaluation principals are validated before the first HTTP operation. Malformed identities, unknown/inactive subjects, and invalid attachment mappings are separate non-retryable blockers.
- Principal and mapping failures remain distinguishable as `EVALUATION_PRINCIPAL_ID_INVALID`, `EVALUATION_PRINCIPAL_SUBJECT_INVALID`, and `PARSE_ATTACHMENT_MAPPING_INVALID`; existing `LIVE_*` operation blockers remain fail closed.
- All six dataset-v2 parsing cases use the frozen `HRPractitioner` authorization role and the reviewed active owner subject. Braincrew never infers authorization from persona text.
- The existing create-only live-preflight and replay boundary remains authoritative. A `READY` result still requires exact role-isolated corpus identity and all six strict parse observations.
- Braincrew #42 is the minimum merged-base substrate for that boundary. It pins the strict AX corpus-identity and parse-observation transports, preserves the existing retry taxonomy, and adds raw-text-free `live-preflight-evidence-v1` create/replay mechanics. Its artifact state is only `captured`; #34 still owns principal, mapping, role, blocker, and six-observation policy, while #38 owns an actual READY renewal.
- No corpus, database, service, or experiment execution is authorized by this specification. Those operations remain behind later proposal gates.

## Testing Decisions

- Tests assert externally visible contracts rather than internal helper structure.
- The highest Braincrew seam is the installed CLI and its create-only receipts: invalid inputs must fail closed, successful qualification must produce reproducible sanitized digests, and replay must reject tampering.
- Contract tests cover strict pack schema, recursive forbidden fields, canonical byte rules, path containment, manifest defaults, per-source digests, and single-byte tampering.
- Qualification tests cover complete required-source closure, duplicate identities, frozen source-text digests, required and forbidden visibility, reviewed license/provenance, and distractor coverage.
- Failure tests require the exact typed blocker family and prove that no import manifest or repaired output is emitted on mismatch.
- Independence tests launch the authoring boundary with only allowlisted inputs and prove that repository, dataset, fixture, network, and undeclared filesystem reads are denied.
- Preflight tests cover malformed UUID configuration, well-formed unknown/inactive subjects, invalid attachment mapping, exact role isolation, and preservation of the existing live-operation blocker taxonomy.
- Principal/attachment preflight tests bind the accepted input to the exact dataset-v2 integrated and component digests before HTTP, retain that identity for replay, and reject a rehashed substituted identity.
- Parse qualification tests preserve exhausted retry attempts on the blocker, reject a failure code on an available response, and allow zero recovered spans to reach parsing-quality evaluation while validating every span that is present.
- Artifact tests digest untrusted attempt correlation headers, preserve replay of legacy v1 artifacts that omitted the new defaulted fields, and reject removal or substitution of frozen identity from a rehashed successful six-probe capture.
- Adapter and acceptance tests require six fresh strict parse responses plus three role-specific corpus identities before `READY` can be created.
- Substrate tests independently require exact AX response schemas and digests, safely encoded attachment paths, bounded permanent details, retained retry attempts, create-only sanitized capture, CLI replay, and tamper/raw-field rejection without asserting READY or parsing quality.
- Receipt tests scan for raw source text, query/answer material, vectors, credentials, database URLs, HTTP authorization material, prompt transcripts, and private paths.
- Existing dataset v1/v2 validation, fixture execution, live preflight, create-only persistence, artifact replay, and all current repository regressions must remain unchanged.
- A full clean repository baseline runs before the first RED. Each new behavior is observed failing before implementation and passes through targeted tests before the full quality gate.

## Out of Scope

- Authoring corpus source text in a context that has inspected evaluation cases or fixtures.
- Generating corpus content from queries, expected answers, expected evidence, scores, split labels, or prior observed results.
- Copying or importing AX implementation internals into Braincrew.
- Direct AX database writes, migrations, service restarts, importer execution, snapshot creation, or corpus loading.
- Private company, employee, or customer documents; credentials; raw secrets; or live legal APIs.
- Automatic corpus repair, version-string relabeling, corrective re-import, deletion, snapshot restore, or retry with changed data/provider configuration.
- Changes to evaluation scores, calibration, comparison gates, parser semantics, retrieval ranking, prompts, models, or answer generation.
- Baseline/candidate execution, manual result review, dashboard changes, Agent trajectory evaluation, or any live quality claim.
- Commit, push, pull-request modification, ready transition, merge, or Issue #15 closure without a separate Git Lifecycle Proposal Gate.

## Further Notes

- This specification is a prerequisite to, not an expansion of, Braincrew Issue #15. The new tracker issue should block #15 until provisioning and preflight can truthfully reach `READY`.
- AX #33 has published the reviewed generic schema and no-write dry-run, AX #34 has published typed evaluation-principal validation, and AX #35 has published the atomic apply path. Braincrew #31 may now vendor and digest-pin the exact schema; AX #36 and every data/operational gate remain incomplete.
- The current clean preflight artifact remains `BLOCKED`; neither this draft nor later ticket publication changes that measured state.
- `to-tickets` published Braincrew #31-#38 with the approved dependencies. #42 was later added as the minimum extraction required to keep #34 independent of unmerged Issue #15 work; #42 is a native child of #30 and native blocker of #34.
- Braincrew #31, #32, #33, and #42 are merged and closed. PR #43 merged #42 as `93c8e8dabab855b7f2f700df73cd04ce38995f29`; its clean local/remote branch and dedicated worktree still await cleanup. #34 is now open with `ready-for-agent` and implements its policy independently on that merged base. Actual brief approval remains #35, independent authoring/sealing remains #36, real qualification remains #37, and actual preflight renewal remains #38.

Issue #34 implementation checkpoint:
: The collector rejects noncanonical tenant/user UUIDs before HTTP, requires reviewed owner
  `22222222-2222-2222-2222-222222222222`, sends exactly `HRPractitioner`, and requires the six
  approved parsing attachment UUIDs. The input must also match the frozen dataset ID, version,
  integrated digest, and three component digests, which are retained and replay-validated. It maps
  malformed principals, unknown/inactive subjects, and attachment mapping failures to distinct
  non-retryable blockers while preserving existing live retry/failure blockers and their exhausted
  attempts. Every post-dataset Issue #34 capture uses
  `principal-attachment-preflight-evidence-v1` with
  `capture_contract="principal-attachment-preflight-v1"`, so replay requires frozen identity for
  complete, partial, and blocked parse captures. The generic Issue #42
  `live-preflight-evidence-v1` schema remains fully backward compatible, including arbitrary
  caller-supplied observations and `LIVE_PARSE_*` blockers. Replay exposes the schema version and
  Issue #34 consumers must require the principal-attachment schema; the logical digest proves
  internal consistency rather than origin authenticity. The Issue #34 replay validator additionally
  requires the exact ordered six-case attachment map, reviewed owner, sole `HRPractitioner` role,
  fixed timeout, correlation identity, and parse-only request shape. A blocker-free artifact
  requires all six probes; an incomplete artifact requires the one terminal blocker that explains
  the next probe, or the pre-probe mapping blocker. Every operation blocker retains its canonical
  request so the first failed probe still proves the tenant, subject, role, and attachment.
  Untrusted response correlation values are digest-only at the retention boundary. An
  available response with a failure code is blocked, while an available response with zero spans
  remains a downstream quality observation. Successful transport is retained only as six
  sanitized strict parse observations in the Issue #42 create-only artifact; it emits no
  parsing-quality result or READY. A connection failure remains non-retryable but now retains one
  `request_error` attempt on `LIVE_PARSE_OBSERVATION_UNREACHABLE`. Legacy v1 artifacts without the
  newly introduced optional fields retain their original logical-digest semantics.
  A 264-test clean baseline preceded the first 15-test RED. Ticket review separately reproduced a
  non-matching parser defect before repair. PR #44 review remediation separately reproduced the
  initial four bot findings, legacy replay drift, correlation-header retention, and rehashed
  identity removal before repair. A later re-review separately reproduced retry-history loss after
  a recovered invalid response and identity removal from a blocked partial capture. Focused
  independent review then reproduced simultaneous discriminator-and-identity removal before the
  semantic downgrade repair, then overbroad classification of generic reviewed-attachment evidence
  and unrelated legacy `LIVE_PARSE_*` blockers. Fingerprint inference was removed in favor of a
  separate required-field Issue #34 schema while preserving generic v1 replay. The latest Codex
  re-review then reproduced an incomplete five-probe artifact replay and an evidence-free
  connection failure before both contracts were repaired. Independent review then reproduced the
  unavailable blocker being rejected, rehashed parser/source drift replaying, and a blocked receipt
  replaying without attempts. A final adversarial pass also bound span digests to frozen source
  substrings, one tenant to the retained probe set, and blocker codes to their terminal attempt
  outcomes. Terminal timeout/retryable failures must also retain all three exhausted attempts.
  A fourth Codex review then reproduced missing first-blocker principal evidence, taxonomy
  relabeling, unrelated parse-request payload, impossible response correlation, and unsafe span-ID
  retention. Six tests first failed before canonical blocker requests, exact request and
  code/detail/outcome/status validation, response-aware correlation, and bounded span identifiers
  reached GREEN. Those paths are repaired while preserving generic v1. Focused preflight/adapter
  coverage first reported 52 passes. Independent review then reproduced a generic-v1 legacy span
  ID rejection and raw query retention through a generic blocker request. Shared span compatibility
  is restored, generic blocker requests are forbidden, and safe span-ID checks remain confined to
  Issue #34; focused coverage reports 54 passes and all 293 repository tests pass.
