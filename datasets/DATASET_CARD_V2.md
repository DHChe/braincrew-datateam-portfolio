# Braincrew Evaluation Dataset Card v2

Dataset ID: `braincrew-evaluation-dataset`

Dataset version: `2.0.0`

Frozen content digest: `sha256:ef6b0a1f50fcd2ecb8b5d7addc7bc5daaa54537899a1ac6faba7c784eee6e98a`

## Intended use

This public, synthetic engineering benchmark is the qualification identity for immutable
Braincrew corpus packs. It reuses the exact 100 scoring cases and component digests frozen by
dataset `1.0.0`; version `2.0.0` adds the post-seal corpus qualification boundary without changing
case inputs, expected evidence, split allocation, scoring behavior, or verification denominators.

The dataset contains 70 Calibration and 30 Verification cases: 20 parsing, 30 retrieval, 40
grounded-answer, and 10 visibility/abstention cases. It is not a statistical population estimate,
a secret holdout, a live product-quality claim, or Agent trajectory evaluation.

## Provenance and license

- Provenance status: complete
- License status: approved
- Source type: synthetic
- License: CC0-1.0
- No private customer, employee, or company document is included.

## Qualification and identity controls

- The integrated digest binds this v2 manifest and the unchanged parsing, retrieval, and grounded
  components.
- Qualification requires all 100 cases' source identities, frozen source-text digests where
  present, required and forbidden role visibility, and non-empty distractor coverage.
- A successful qualification binds the exact dataset digest, component digests, sealed corpus
  digest, sanitized qualification receipt, and AX import manifest.
- Any scoring-relevant component change requires a new dataset version and new component and
  integrated digests. Dataset `1.0.0` remains immutable and independently replayable.

## Minimum Verification denominators

EvidenceSpan recovery: 6; Recall@5: 9; claim-support precision: 10; citation precision: 10;
Answer Mode accuracy: 15; abstention accuracy: 5. A fixture run below any minimum is `INVALID` and
has no integrated aggregate claim.

## Explicit exclusions

This dataset card does not authorize corpus authoring, corpus or dataset repair, AX import apply,
provider or database operations, live preflight, baseline/candidate execution, comparison, release
gates, or Agent trajectory evaluation.
