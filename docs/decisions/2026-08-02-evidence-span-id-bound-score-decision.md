# Evidence-span recovery remains an ID-bound metric, not a parser-failure verdict

**Status:** owner decision recorded for Issue #131; no evaluator code/test change, live AX, attachment,
container, evidence, or Git change is made by this decision

## Decision

For the separately authorized Issue #131 provisioning step, the owner chooses the unapproved-v3-upload
route. If the six fresh attachments pass `capture-live-parsing`'s text, digest, parser-identity, and
span checks, publish the resulting `evidence_span_recovery` value of `0.0000` with this explanation:
the frozen dataset's span-ID convention makes the current five-tuple metric unreachable for AX's
structurally different internal IDs. It is not a claim that AX failed to recover the frozen text windows.

The evaluator tuple remains unchanged. Issue #136 holds the separate question of whether the recovery
metric should eventually compare four document-derived fields instead; it authorizes no implementation.
This decision neither uploads attachments nor creates a parsing bundle. It records which authorized
future route should be used and how its narrow metric is to be described.

## Measured basis

At AX `5b0f5f2`, replaying AX's pure `chunk_extracted_text()` over the six frozen Verification documents
found exactly one matching chunk per expected span:

| Case | AX chunks | Frozen window | Exact text/window chunk |
| --- | ---: | --- | --- |
| `parsing-015` | 3 | `(251, 611)` | yes |
| `parsing-016` | 8 | `(193, 210)` | yes |
| `parsing-017` | 3 | `(220, 542)` | yes |
| `parsing-018` | 8 | `(219, 229)` | yes |
| `parsing-019` | 3 | `(202, 528)` | yes |
| `parsing-020` | 8 | `(203, 222)` | yes |

AX creates `evidence_id = f"{chunk_id}:evidence"`, so a returned ID has the structural form
`<source_id>:chunk:NNNN:evidence`; it cannot equal a frozen case ID such as `parsing-015-span`.
`text`, `start_char`, `end_char`, and `source_text_digest` are exact in the replay. `id` is the sole
mismatch.

The conclusion is conditional on the live extraction: each text/window statement requires live
`extracted_text` to be byte-identical to frozen `canonical_text`. The six canonical documents have no
leading whitespace, so the pure chunker's `text.strip()` does not move the replayed offsets. If AX
normalizes whitespace or otherwise changes text, that prediction is void and Braincrew's capture guard
refuses rather than scores the bundle.

The **empty-observation evidence-span-only probe** built six available response-shaped observations with
empty spans, headings, metadata, table, and list; no observed field was derived from `case.expected`.
It reported only `evidence_span_recovery`, run state, and coverage: all six cases were `SCORED`, the run
was `COMPLETED`, and the aggregate recovery display was `0.0000`. It does not support a claim about any
other parsing dimension.

For any bundle that actually passes `capture-live-parsing`, the v2 document-identity `INVALID` guard is
unreachable: capture binds returned text and its SHA-256 to the frozen document, then binds every span's
digest to that same document digest. Expected and observed non-empty digest sets therefore intersect;
an identity mismatch aborts capture before evaluator input exists.

## Baseline trade-off

The two desirable conditions cannot coexist under the present AX design:

- Non-empty spans require a current `TenantSourceDocument`.
- `TenantSourceDocument(...)` is constructed only in materialization.
- The same materialization path creates `SeedVectorRecord` rows for chunk and evidence records.
- Issue #131's measured runtime note says the visible corpus digest covers those embedded seed-vector
  records; an unapproved attachment leaves it unchanged for precisely that reason.

Approval is therefore required for non-empty spans, and approval moves the corpus identity that the
2026-08-02 baseline/candidate captures bind. Preserving those captures and obtaining non-empty spans are
mutually exclusive until an owner approves the resulting re-capture work.

## Historical constraint and rejected alternatives

`git log -1 a2f5b02 --format=%B` was read before recording this evaluator-bound vocabulary. Its relevant
`Rejected:` clause is exact:

> Keying the predicate on (span id, digest) | the digest is the document identity and the span id never was, and the tuple misdiagnosed a correct document carrying a SUT-assigned span id — which is what the live path produces.

Its relevant `Directive:` is exact:

> parsing-quality-v1 must remain reachable from stored provenance on both replay paths forever, or published artifacts stop replaying. Do not add a fresh route that selects it; every default is v2 so a forgotten call site fails closed. Do not widen the guard to catch partial document rewriting — that direction produced both misdiagnoses review had to remove, and the bound is stated in the decision document instead. And do not record anywhere that this removed the published zero: it does not.

Accordingly, this decision rejects:

- **Approving attachments to obtain spans now.** It would add the seed records whose digest membership
  changes the preserved baseline/candidate identity and would require a separate re-capture decision.
- **Dropping `id` from the recovery tuple now.** That is an evaluator-contract change which would
  overturn the reviewed #118 decision surface; Issue #136 owns the decision question and no code change
  is authorized here.

## Consequence

The next safe, bounded action is Issue #131's separately authorized unapproved attachment provisioning,
followed by document-bound capture. If it produces the prevalidated empty-span path, the published
metric must carry the ID-convention reason and must not be presented as an AX parser-quality failure.
No live outcome is claimed by this decision record.
