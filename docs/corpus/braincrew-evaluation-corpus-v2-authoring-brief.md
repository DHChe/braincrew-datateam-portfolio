# Braincrew Evaluation Corpus v2 Authoring Brief

Independent exact-byte review approval: **recorded**. This document defines generic authoring
boundaries only. It does not authorize corpus authoring, import, AX execution, or evaluation.

## Pinned AX schema contract

Any future seed pack governed by this brief must conform to
`schemas/ax-synthetic-seed-pack-v1.schema.json`, reviewed at
`sha256:4ddc71d7408324bfed6e7a25024899a7f689431f5f024fb2329f3f844352bffa`.
The schema pin fixes the packaging contract; it does not supply corpus content or authorize
creation of any schema artifact. The accompanying `.sha256` digest file and independent
leakage-review record hold the approved brief-byte lock.

The authoritative AX visibility-role contract is pinned to repository
`https://github.com/DHChe/AX_portfolio`, ref
`47673b83a9fb431f2bad550781db18c7bee8b67e`, path
`backend/src/ax_engine/seed/pack_contract.py`, content contract version
`ax-synthetic-seed-content-v1`, and reviewed file digest
`sha256:09fe230ca2e976bec156d72987b5cf1f39419c34829e323222d11bef35e1fc2a`.
This second pin fixes only the authoritative role vocabulary; it does not authorize AX access
or corpus creation.

## Generic HR/labor domain families

Future synthetic sources may cover only broad HR and labor families:

- employment terms, workplace policies, and worker responsibilities;
- working time, attendance, leave, and flexible-work rules;
- compensation, benefits, expenses, and payroll procedures;
- conduct, grievance, discipline, anti-harassment, and reporting procedures;
- workplace safety, accommodation, wellbeing, and return-to-work processes;
- performance, learning, internal mobility, and manager responsibilities; and
- onboarding, organizational change, separation, and personnel-record handling.

These families are topic boundaries, not evaluation cases. Authors must not add concrete
evaluation questions, answer mappings, or evidence hints to this brief.

## Source-authority guidance

Each future synthetic source must identify its generic authority class, issuer class,
jurisdiction or organizational scope, effective period, and supersession status. Conflicts are
resolved by an explicit hierarchy appropriate to the fictional setting: applicable public law
or regulator guidance first, then collective or contractual terms, then organization policy,
then procedures, handbooks, training material, and informal guidance.

No synthetic company document may claim real legal authority. Any jurisdiction-specific legal
or regulator content must be newly authored for a clearly fictional jurisdiction and must not
present itself as legal advice. Authors must not ingest or adapt external authority material;
unsupported authority claims must be omitted. Lower-authority material must never silently
override a higher-authority source.

## Synthetic and demo policy

Every future corpus source must be newly authored synthetic/demo content. Company names, people,
events, identifiers, dates, amounts, and policy text must be newly authored for a fictional demo
organization. This synthetic-only branch keeps pack-wide `synthetic=true` truthful. Do not copy
private employee, customer, or company documents, AX product internals, or evaluation material.
Do not use real personal data or imply that the demo corpus describes a real employer.

Synthetic content must remain internally consistent, plainly labeled as demo material, and
usable without external confidential context. Its purpose is reproducible product evaluation,
not legal or employment advice.

## CC0 policy

Every future corpus source must be licensed `CC0-1.0`. The authoring owner must apply that license
to the newly authored synthetic/demo bytes and record the authority to do so. Public-domain
status or an external publisher's license does not make external material eligible.

Every future corpus source must have an independently reviewed provenance decision before it is
eligible. The review must record the synthetic origin, authoring owner, license assignment, and
approve-or-reject decision. Missing or pending provenance must block authoring approval and pack
inclusion.

Public-source ingestion or adaptation is prohibited in this version, including externally
published `CC0-1.0` material. No external source bytes, excerpts, translations, paraphrases, or
adaptations may enter the corpus. Exclude any source with ambiguous authorship or ownership,
incompatible terms, or an unverified license assignment.

## Allowed AX visibility roles

The authoring vocabulary is limited to the fail-closed `VisibilityRole` values from the pinned
AX contract:

- `Executive`
- `HRAdmin`
- `HRPractitioner`
- `Employee`

A source may name more than one role, but must follow least-privilege visibility. Do not encode
real-person access grants, tenant-specific identities, or hidden per-case visibility. The
independent reviewer must confirm that every role is an exact, case-sensitive member of this
closed vocabulary before approving authoring; unknown or guessed aliases must fail closed.

## Language bounds

Future sources are limited to Korean or English. Each source must declare one primary language
and use the other only for a faithful translation, a standard HR/legal term, or an explicitly
labeled bilingual passage. Do not assume that translated text has identical legal force.
Exclude other languages until a separately reviewed change expands this brief.

## Format bounds

Future source files are limited to Markdown or plain-text files. Source bytes must be BOM-free
UTF-8, use Unicode NFC normalization, and use LF-only line endings. Source paths must be
normalized relative POSIX paths with no empty, `.`, or `..` segments. Use clear headings,
paragraphs, lists, and simple text tables. Files must be self-contained and readable without
scripts, remote embeds, or credentials. Scans, images, audio, video, office binaries, encrypted
files, executable content, and OCR-dependent content are out of scope.

This ticket creates no source file, manifest, receipt, or other seed-pack artifact.

## Distractor policy

Future distractors may be topically plausible but must differ through a generic, explainable
authority condition such as lower authority, superseded status, different jurisdiction,
different organizational scope, or inaccessible visibility. The relevant sources must contain
enough explicit metadata for that conflict to be resolved without guessing.

Do not fabricate a public authority, hide decisive exceptions, introduce adversarial noise, or
derive distractors from evaluation queries, answers, evidence, failures, or observed behavior.
Distractors must test authority resolution rather than exploit wording overlap or secret clues.

## Explicit exclusions

This brief contains and authorizes none of the following:

- evaluation datasets, fixtures, queries, answers, evidence, case identifiers, source
  identifiers, source digests, mappings, scores, metrics, split labels, or prior run output;
- corpus source bytes, an import manifest, a qualification receipt, or corpus or seed-pack
  digest artifacts;
- AX import, mutation, API, command-line, or other product operations;
- evaluation, qualification, benchmark, or release-gate execution; or
- private, proprietary, personal, or license-ambiguous material.

Any request to add one of these items is a separate scoped change and cannot be inferred from
this brief.

## Independent review and authoring gate

Only the clean-commit and post-commit byte-equality gate remains **pending**. A reviewer separate
from this evaluation-blind authoring lane must verify the schema pin, generic-only scope, role
vocabulary, authority model, content-license boundary, format bounds, and absence of
evaluation-derived hints. The reviewer must record their identity, review date, review base HEAD,
exact brief SHA-256 and size, findings, and an explicit approve-or-reject decision. The review
base HEAD identifies the review environment; it is not the future committed Braincrew SHA.

The independent review evidence must record the exact brief SHA-256 and a post-commit
byte-equality verification before corpus authoring may open.

Corpus authoring remains prohibited until the independent decision is recorded as approved and
this brief reaches a clean committed Braincrew SHA through the separate Git Lifecycle Proposal
Gate. This document records the digest-bound independent approval but does not create that future
committed SHA or satisfy its post-commit byte-equality verification.
