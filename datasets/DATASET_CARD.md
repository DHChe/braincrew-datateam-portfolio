# Braincrew Evaluation Dataset Card

Dataset ID: `braincrew-evaluation-dataset`

Dataset version: `1.0.0`

Frozen content digest: `sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b`

## Intended use

This public, synthetic engineering benchmark supports deterministic fixture evaluation of the evolving AX subject under test. It contains exactly 100 cases with a frozen 70 Calibration / 30 Verification split. It is not a statistical population estimate, a secret holdout, a live product-quality claim, or Agent trajectory evaluation.

| Primary focus | Calibration | Verification | Total |
| --- | ---: | ---: | ---: |
| Parsing | 14 | 6 | 20 |
| Retrieval | 21 | 9 | 30 |
| Grounded answer | 30 | 10 | 40 |
| Visibility and abstention | 5 | 5 | 10 |
| Total | 70 | 30 | 100 |

## Provenance and license

- Provenance status: complete
- License status: approved
- Source type: synthetic
- License: CC0-1.0
- Parsing and retrieval cases carry case-level provenance, license, and review metadata.
- Grounded cases inherit dataset-level provenance from `grounded_cases_v1.json`; every case in that component is synthetic, CC0-1.0, and reviewed.
- No private customer, employee, or company document is included.

## Risk classification

- Parsing cases are classified `standard`; they measure structural recovery and do not authorize an HR conclusion.
- Retrieval cases map `standard` difficulty to `standard` risk and `adversarial` difficulty to `high` risk.
- Grounded and visibility/abstention cases use their explicit `risk_level` field.
- Risk classification is part of the scoring-relevant dataset digest.

## Leakage and identity controls

- Stable case identifiers are unique across all three component datasets.
- Scoring-equivalent case content cannot appear in both Calibration and Verification.
- Free-text answer keys such as `reference_answer`, `gold_answer`, `answer_key`, and `expected_answer_text` are prohibited.
- The integrated digest covers the normalized component contracts, all case inputs and structured ground truth, split and allocation rules, applicability minima, risk policy, leakage policy, and provenance/license state.
- Any scoring-relevant change requires a new dataset version and updated component and integrated digests; artifacts from the prior digest remain immutable.

## Minimum Verification denominators

EvidenceSpan recovery: 6; Recall@5: 9; claim-support precision: 10; citation precision: 10; Answer Mode accuracy: 15; abstention accuracy: 5. A fixture run below any minimum is `INVALID` and has no integrated aggregate claim.

## Explicit exclusions

This dataset card does not introduce baseline/candidate comparison or release gates, live baseline/candidate execution, dashboard implementation, LLM-as-judge scoring, AX product changes, or Agent trajectory evaluation.
