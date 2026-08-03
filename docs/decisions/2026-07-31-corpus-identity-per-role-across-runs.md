# Locked: compare visible corpus identity per role across runs

Date: 2026-07-31  
Status: locked  
Implements: [Issue #101](https://github.com/DHChe/braincrew-datateam-portfolio/issues/101)  
Owner decision recorded here: one corpus ID must bind every required role within a live run, while
each role's visible corpus digest must match between the baseline and candidate runs

## 1. Measured conflict

The authorized AX measurement used one tenant and subject for the three roles required by the
Verification dataset. AX returned one `corpus_id` for all three roles. Executive and
HRPractitioner returned visible digest `sha256:ecba4eea…` with seven contributing versions;
Employee returned `sha256:85b57bb2…` with only the frozen dataset contribution.

Those are measured facts. The inference is that the digest difference is expected visibility
behaviour: AX's `employee_visibility_invariant` excludes the six tenant uploads from Employee.
Braincrew's former `set[(corpus_id, corpus_digest)]` required one pair across all roles, so the live
capture refused before any answer request even though every role included the frozen dataset.

## 2. Decision and invariants

“Baseline and candidate ran against the same corpus” means equality per required principal role
between the two runs.

- **W1:** one non-empty `corpus_id` must be identical across every required role within a live run.
- **W2:** AX-confirmed corpus-role evidence must cover exactly the required dataset role set.
- **B1:** the complete `corpus_digests_by_role` mapping must be equal between baseline and candidate.
  A changed digest, missing role, extra role, or different role set produces
  `SYS-COMPARISON-CORPUS_DIGESTS_BY_ROLE-MISMATCH` and an `INVALID` comparison.
- **B2:** the scalar `corpus_id` must remain equal between baseline and candidate. Drift produces
  `SYS-COMPARISON-CORPUS_ID-MISMATCH`.

No path accepts an arbitrary count of unrelated identities.

## 3. Field shape and fixture meaning

`ExperimentProvenance` keeps `corpus_id` scalar because W1 defines it as the corpus identity proper.
Digest evidence has two mutually exclusive shapes:

- `execution_mode="live"`: `corpus_digest=None` and a non-empty, immutable
  `corpus_digests_by_role: role -> sha256 digest` mapping.
- `execution_mode="fixture"`: one `corpus_digest` and `corpus_digests_by_role=None`.

A fixture digest means only the unscoped digest assigned to the hand-authored fixture observation
family. It does not claim that AX was called or that any role-scoped visibility was observed.
Keeping the two shapes mutually exclusive prevents a scalar live digest from silently collapsing
the visibility split.

## 4. Conformance judgment

This is **conformance with an explicit representation clarification**, not a new comparison
contract. The Issue #13 design already required exact corpus IDs/digests in provenance, equality of
every locked compatibility dimension between runs, and fail-closed missing provenance. It never
required visible digests to be identical across roles within one run. The live producer's scalar
collapse under-implemented that existing intent once AX's role-dependent visibility became
observable. `experiment-run-summary-v1` therefore remains the schema version, while the design now
states the previously missing role resolution.

The JSON shape changes for live provenance. A previously valid v1 payload with
`execution_mode="live"`, one scalar `corpus_digest`, and no role map is now refused at parse by
`validate_corpus_digest_scope`; this is a backward-incompatible narrowing of the published schema
version. Keeping v1 is safe because Issue #101 was found before any live run summary was published,
and `schemas/` seals only the two `ax-synthetic-seed-*` schemas, so no pinned schema digest moves.
Those facts make migration unnecessary; they are not the reason this is conformance.

Fixture-mode `ComparisonArtifact.logical_digest` values also change because the digest payload now
includes `corpus_digests_by_role: null`. Repository search found no pinned comparison logical
digest in tests or documentation, so this representation clarification invalidates no published
comparison identity.

## 5. Rejected alternatives

1. **Accept any number of `(corpus_id, corpus_digest)` pairs.** Rejected because it deletes the
   confound control instead of scoping it. A genuinely different corpus could pass.
2. **Bind only `corpus_id` plus the frozen-dataset contribution and keep per-role digests as
   evidence.** Rejected because it demotes visible-corpus equality to a note; a between-run change
   would no longer invalidate comparison.
3. **Restrict the experiment to one visibility class.** Rejected because it changes the evaluated
   dataset. Verification deliberately spans Executive, Employee and HRPractitioner.
4. **Store one `corpus_digest` computed over the per-role mapping.** Rejected because it silently
   changes the scalar field's meaning and hides the split the artifact must expose.

## 6. Trade-offs and failure modes

The artifact is larger and every new AX role becomes a compatibility dimension. That maintenance
cost is intentional: a role-set change is experiment drift, not ignorable metadata.

Failure modes are explicit. A different within-run `corpus_id` aborts capture. An AX-confirmed role
set that differs from the dataset requirement aborts capture. A malformed or empty digest map fails
model validation. Baseline/candidate map drift invalidates all gates. Fixture provenance cannot
carry a role map, and live provenance cannot carry the old unscoped scalar.

The mapping records AX's report; it does not independently prove AX calculated the digest correctly.
The comparison also does not decide whether Employee's narrower visibility is desirable product
policy.

## 7. Validation evidence

Baseline before edits: `552 passed in 35.84s`; `git status --short` and
`git status --short schemas/` were empty.

TDD RED:

- `test_live_capture_accepts_stable_role_scoped_corpus_digests_across_runs` failed at the former
  `ValueError("corpus identity differs across dataset roles")`.
- `test_comparison_refuses_one_roles_corpus_digest_change_between_runs` failed because
  `ExperimentProvenance` did not yet accept `corpus_digests_by_role`.
- the two execution-mode boundary tests failed with `DID NOT RAISE` when the scope validator was
  removed.

Focused GREEN after implementation: the acceptance/comparison files passed `133` tests before the
two execution-mode boundary tests were added; those two tests then passed independently.

### Clause-by-clause mutation table

| Clause                          | Guard status                     | Isolated mutation                                                                    | Named test(s) that turned red                                                                                                                                            | Failure                                                                                                                                   |
| ------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- |
| W1                              | new equality protection; non-empty is a pre-existing model constraint | replace `if len(corpus_ids) != 1` with `if False`                                    | `test_live_capture_refuses_inconsistent_role_corpus_id`                                                                                                                  | `Failed: DID NOT RAISE <class 'ValueError'>`                                                                                              |
| W2                              | pre-existing guard, re-confirmed | replace `if confirmed_roles_by_request != expected_role_evidence` with `if False`    | `test_live_capture_refuses_incomplete_role_scoped_corpus_coverage`                                                                                                       | `Failed: DID NOT RAISE <class 'ValueError'>`                                                                                              |
| B1                              | new protection                   | remove `"corpus_digests_by_role"` from `_compatibility_violations.comparable_fields` | `test_comparison_refuses_one_roles_corpus_digest_change_between_runs`; `test_comparison_refuses_role_scoped_corpus_coverage_change_between_runs[missing]`; `[extra]`     | all three: `AssertionError: assert 'FAIL' == 'INVALID'`                                                                                   |
| B2                              | pre-existing guard, re-confirmed | remove `"corpus_id"` from `_compatibility_violations.comparable_fields`              | `test_comparison_refuses_corpus_id_change_between_runs`                                                                                                                  | `AssertionError: assert 'FAIL' == 'INVALID'`                                                                                              |
| mode-scoped required provenance | new protection                   | replace the fixture/live digest branches with `or not provenance.corpus_digest`      | `test_baseline_and_candidate_capture_provenance_passes_the_existing_compatibility_check`; `test_run_summary_builder_derives_the_comparison_input_and_writes_create_only` | `Failed: existing comparison compatibility must accept the capture pair`; `Failed: built baseline/candidate summaries must be compatible` |
| per-role map shape              | new — sole guard for empty role key, defence-in-depth for empty map | replace `validate_corpus_digests_by_role` with `return digests`                      | `test_corpus_digests_by_role_refuses_an_empty_map`; `test_corpus_digests_by_role_refuses_an_empty_role_key`                                                              | both: `Failed: DID NOT RAISE <class 'pydantic_core._pydantic_core.ValidationError'>`                                                      |

The W1 row isolates only the new equality guard. Its non-empty half remains enforced by the
pre-existing `ExperimentProvenance.corpus_id: str = Field(min_length=1)` model constraint and is
not claimed by that mutation.

For the last row, an empty live map also fails closed downstream as `SYS-PROVENANCE-MISSING`,
which makes that half defense-in-depth. Without the validator, a baseline/candidate pair carrying
an empty role key has no corpus/provenance violation and the comparison decides `PASS`; the field
validator is the sole refusal protecting that shape.

Every mutation was restored before the next. After each restore, `__pycache__` directories were
removed, the source SHA-256 and the corresponding `git diff` SHA-256 matched the pre-mutation
values, and the named test returned green.

Final gates passed: Ruff format/check over 71 files, mypy over 71 source files, `562` pytest tests,
Prettier, ESLint, TypeScript, `7` Vitest tests, the static Next.js build, and `2` Playwright tests.
`git diff --check` and both final status views were run after this document was finalized; literal
output is preserved in the cycle 130 report.

## 8. Honest limits

No AX runtime was started. No live endpoint was called. No experiment, answer request, provider
cost, or quality result was produced. T-ACCEPT drives capture through `httpx.MockTransport`;
T-REFUSE compares two constructed run summaries entirely in memory and uses no transport. Neither
touches live AX. Independent pane 3 review returned `APPROVE` in cycle 129, and the scoped cycle
131 re-review returned `APPROVE` after the repair.

## 9. Likely follow-up questions

- **Why keep `corpus_id` scalar?** AX returned one ID across all roles, and W1 treats different IDs
  as different corpora rather than visibility slices. Repeating it in every map entry adds no
  independent evidence.
- **Why compare the whole map instead of only common roles?** Intersection comparison would let a
  missing role disappear from the control. Role coverage is part of the experiment identity.
- **Why can fixtures keep a scalar?** They contain hand-authored, role-unscoped observations. A fake
  role key would claim execution evidence that does not exist.
- **Does this prove Employee's smaller corpus is correct?** No. It preserves the measured split and
  stops the harness from declaring it impossible; AX policy remains outside this ticket.
