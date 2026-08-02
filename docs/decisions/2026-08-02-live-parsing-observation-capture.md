# Live parsing observations are a separate capture, not a relabelled fixture

**Status:** implemented locally for Issue #131; live capture blocked by the current AX input set

## Decision

Capture the six dataset-v3 Verification parsing cases through AX's read-only
`GET /v1/evaluation/attachments/{attachment_id}/parse-observation` operation and
write them as a create-only `live-parsing-capture-v1` manifest plus a
`parsing-observation-batch-v1` labelled `ax-sut-http-v1`.

The capture accepts a versioned document-to-attachment mapping only to select an
AX endpoint. Before it writes an observation, the returned attachment ID, complete
extracted text, extracted-text digest, and every evidence span must reproduce the
frozen dataset-v3 document. Headings, metadata, tables, lists, parser name, and
parser version come from AX's response. The dataset case's `expected` value is not
read by the converter.

This is a separate six-case artifact. It does not alter
`capture-live-experiment`, its 24 live / 6 fixture partition, the
fixture-only `ParsingAdapterProvenance`, dataset-v3 bytes, or the
`parsing-quality-v2` identity guard.

## Why

Commit `af18c5e` deliberately rejected widening
`ParsingAdapterProvenance.execution_mode`: at the time no conversion existed, so
the only newly representable state was a fixture parser falsely declared live.
That reason still holds for the existing standalone parsing-run artifact, and it
is not bypassed here.

Issue #131 supplies the missing different route: AX now exposes a parse observation
endpoint, and the new converter binds each returned document to frozen v3 text
before converting it. A dedicated capture manifest preserves the live adapter
label, AX parser identity, SUT state warrant, dataset identity, and the truthful
dirty/clean state of the Evaluation Plane without changing the historical fixture
artifact's meaning.

The separate input mapping is not a quality assertion. A wrong mapping cannot
produce a successful observation because AX's returned text and digests must match
the selected frozen document. This avoids the rejected alternative of harvesting a
mapping from the same live state and treating that lookup as its own proof.

## Current execution boundary

Read-only inspection on 2026-08-02 found that the running AX instance has only the
six older `synthetic-rule-015` through `synthetic-rule-020` approved attachments.
It has no approved attachment corresponding to v3's `demo-terms-guide-002` through
`demo-conduct-policy-007` documents. The parse endpoint accepts attachment IDs,
not dataset document IDs.

Creating or attaching those v3 documents would change AX runtime data, which is
outside Issue #131's authorized execution and explicitly prohibited for this cycle.
Therefore this implementation deliberately writes no live parsing bundle and does
not re-evaluate the existing baseline or candidate captures. A later authorized
provisioning step must provide a six-entry
`live-parsing-attachment-mapping-v1` input, after which this capture can either
produce a document-bound batch or refuse with the exact failed identity.

## Rejected alternatives

- **Relabel `tests/fixtures/parsing_observations_v1.json` as live.** Its source
  digests identify different documents, and the v2 evaluator correctly rejects it.
- **Widen `ParsingAdapterProvenance.execution_mode`.** This repeats `af18c5e`'s
  false fixture-as-live state; the existing artifact remains fixture-only.
- **Derive headings, metadata, or spans from `case.expected`.** That makes an
  evaluator score its own answer key rather than AX's output.
- **Create v3 attachments in the current AX runtime.** It changes container-backed
  runtime data and exceeds this cycle's read-only scope.
- **Publish the new bundle into `evidence/`.** No bundle exists yet, and publication
  needs an independent review and owner authorization.

## Failure modes and validation

- A response for another attachment is rejected by attachment identity.
- A response for another document is rejected by full text and SHA-256 identity.
- A truncated response, missing parser identity, inconsistent parser identities, or
  an invalid span is rejected before any artifact is written.
- The new acceptance test poisons all six v3 parsing answer keys; the stored
  headings and metadata still equal AX's mocked response, not the poisoned values.
- The Evaluation Plane worktree state is recorded as observed rather than defaulted
  to clean, while the SUT warrant must still name the pinned clean checkout.

## Consequences

The prior 24 retrieval and grounded observations remain reusable and unchanged.
The 30-case evaluation remains `INVALID` until an authorized v3 attachment
provisioning step makes the six parser observations capturable. That is an
unresolved input precondition, not evidence that parsing quality is zero and not a
live-quality claim.
