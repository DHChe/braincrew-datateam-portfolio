# Evaluation Plane Specification Review Record

Date: 2026-07-18  
Original review limit: three independent critic iterations  
Original-cycle final verdict: `ISSUES FOUND`  
Current-cycle final verdict: `APPROVED` at `7f4cce7`

## Review history

### Iteration 1

The reviewer found five blocking gaps: an unfrozen evaluation coverage denominator, subjective critical-failure identities, an incomplete SUT adapter contract, an ambiguous replay claim, and a candidate experiment selected too late to protect the ten-day schedule.

Repairs were committed in `6793f6f`.

### Iteration 2

The reviewer found two remaining blockers: changing `top_k` from 3 to 5 confounded Recall@5 measurement opportunity, and primary metric formulas and aggregation rules were not independently implementable.

Repairs were committed in `2523d0c` by freezing `metric-contract-v1` and changing the first comparison to `evidence_limit=3` versus `evidence_limit=5` while both runs retain `top_k=5`.

### Iteration 3

The reviewer confirmed that the Recall@5 confound was resolved but returned one critical blocker:

> Claim-support precision currently verifies that a generated claim path links to an expected evidence identity, but it does not verify that the cited evidence supports the generated claim's proposition. A contradictory or hallucinated claim can therefore receive full credit and evade an unsupported-high-risk gate.

Minimum acceptable resolution:

1. introduce a versioned claim-proposition contract and a deterministic claim-to-evidence support predicate; or
2. rename the current metric to evidence-link precision and exclude it from groundedness claims and unsupported-conclusion gates.

## Historical workflow stop

The independent-review budget is exhausted. The branch must not be pushed, opened as a pull request, merged, or used for implementation planning until the user chooses the semantic-support contract or explicitly accepts a narrower evidence-link scope. After that decision, the affected specification must be revised and independently reviewed under a new review cycle.

## User resolution and new review cycle

The user selected option A: a versioned claim-proposition contract with deterministic semantic-support predicates. `metric-contract-v2` now separates citation linkage from claim support, preserves unsupported or unrecognized claims in the denominator, and fails closed on unscorable high-risk conclusions.

This decision starts a new independent specification review cycle. The earlier final verdict remains preserved as historical evidence and is not rewritten as an approval.

### New cycle iteration 1

The reviewer found two critical consistency gaps: mixed supporting and contradicting citations could produce different outcomes across the canonical documents, and manually authored high-risk path coverage could omit a generated answer path. The repair makes any linked contradiction fail support and derives high-risk guard coverage from every generated structured-answer path rather than a case-authored list.

### New cycle iteration 2

The independent reviewer approved the specification. The approval confirmed that atom support requires at least one supporting citation and zero contradictory citations, that `high-risk-guard-v1` cannot be narrowed by dataset authors, and that the fixed traversal and exact matching rules remain deterministic and feasible within the ten-day plan.

The written specification now returns to the user-review gate. Approval authorizes GitHub publication for review, not implementation or merge.
