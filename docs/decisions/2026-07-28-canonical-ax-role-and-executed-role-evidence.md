# Locked: canonical AX roles and the executed-role evidence boundary

Date: 2026-07-28  
Status: locked  
Implements: [Issue #91](https://github.com/DHChe/braincrew-datateam-portfolio/issues/91)  
Owner decision recorded here: Braincrew sends `HRPractitioner` for the dataset alias `hr_manager`,
refuses roles outside AX's closed set, and compares the recorded executed role without normalizing
that observation back into the expected value

## 1. The measured defect

Braincrew mapped `hr_manager` to `HRManager`, but AX does not define that role. The pinned AX
checkout declares:

```python
VisibilityRole = Literal["Executive", "HRAdmin", "HRPractitioner", "Employee"]
```

and its evaluation provisioning creates corpus identities for:

```python
CORPUS_IDENTITY_ROLES = ("Employee", "Executive", "HRPractitioner")
```

`HRManager` has zero occurrences across the AX backend and frontend. In the controlled role probe,
GA-003, GA-006 and GA-009 all failed before retrieval with
`ask_question_permission_required` when sent as `HRManager`.

This is a Braincrew harness defect, not an AX provisioning defect. Changing AX would reshape the
system under test around a mistake in the measuring instrument.

## 2. The canonical role decision

**Decided:** map the dataset alias `hr_manager` to `HRPractitioner`.

The empirical probe does not distinguish `HRPractitioner` from `HRAdmin` by visibility:

| role | GA-003 | GA-006 | GA-009 |
| --- | ---: | ---: | ---: |
| `HRPractitioner` | 5 evidence items | 5 evidence items | 5 evidence items |
| `HRAdmin` | 5 evidence items | 5 evidence items | 5 evidence items |

The choice therefore rests on provisioning and role semantics, not document visibility:

- AX provisions `HRPractitioner` as a corpus identity and does not provision `HRAdmin` for that
  purpose.
- The reviewed handoff receipt records `HRPractitioner` for parse observations and `HRAdmin` for
  approval.
- `HRAdmin` is distinguished by write and approval authority. The evaluation asks questions and
  does not exercise that authority.

The superseded v1 fixture dataset also uses the historical reader-persona aliases `manager`,
`recruiter`, `interviewer`, `investigator` and `it_admin`. It is not the frozen live dataset:
`FROZEN_DATASET_MANIFEST` is manifest v3 and selects grounded v2. The v1 fixture dataset cannot be
renamed without changing its own digest, so Braincrew maps those known aliases to the same
provisioned read identity, `HRPractitioner`, and updates only the synthetic observation fixture to
record the wire identity it purports to have executed. This is a compatibility mapping, not a claim
that those five persona names are semantically identical or that AX provisions each persona. Any
other unknown value is still refused.

## 3. Where the closed set lives

**Decided:** Braincrew declares AX's four wire roles locally in `AX_WIRE_ROLES` and validates every
result of `canonical_ax_role` against that set before it can reach an AX request.

Braincrew must be able to reject an invalid role before AX is running. Importing the role literal
from the separate AX repository would couple two histories and violate the repository boundary;
deriving it from a live AX response or database would make the guard unavailable until after the
request it is supposed to protect. The local declaration has a real maintenance cost: a reviewed AX
role-contract change requires an explicit Braincrew update. That visible synchronization point is
preferable to silently forwarding an unknown string.

**Rejected:** `.get(role, role)` without validation. It converts every unknown dataset value into a
purported AX wire identity and makes ignorance indistinguishable from support.

An unsupported case role is a dataset-contract failure, not a scoreable answer failure. The
evaluator therefore lets the canonicalizer raise and abort the run instead of converting an
unrecognized identity into a case-level metric result. This is deliberately fail-closed: publishing
partial scores would hide that the harness did not know which AX principal it evaluated.

## 4. The executed-role evidence boundary

`GroundedObservation.executed_role` records the AX wire role used for the request. It is an
observation, not another dataset alias. The evaluator therefore compares it directly with the
canonical role expected from `GroundedCase.role`:

```python
observation.executed_role != canonical_ax_role(case.role)
```

Cycle 109 removed the evaluator's second normalization but left the live producer deriving
`executed_role` from `case.role`; independent review's M4 replaced the recorded value with the same
derivation and all 505 tests still passed. That measured the Cycle 109 claim of independent operands
false. The shared producer derivation, not only the idempotent second normalization, was the
tautology.

The repaired live path now combines two evidence boundaries:

1. Braincrew derives the complete canonical role set required by both retrieval and grounded
   Verification cases. For each role it calls AX's corpus-identity endpoint, records the
   AX-reported `principal_roles`, and requires the complete response map to equal the independently
   derived requirement map.
2. For each answer case, `GroundedObservation.executed_role` comes from
   `answer_observation.request.roles[0]`, the canonical request the adapter actually constructed,
   rather than a second derivation from the dataset case.

The answer endpoint still does not report a per-case role. The per-case guard therefore detects an
adapter/request divergence, while the corpus-identity evidence proves that AX confirmed the exact
role set the live experiment requires. Neither check alone is described as stronger evidence than
it is. A wrong-but-valid adapter request role now reaches `SYS-GROUNDED-ROLE-MISMATCH` during
evaluation, and M4 is detected by the live capture-to-evaluator regression.

## 5. Rejected alternatives and costs

- **Map `hr_manager` to `HRAdmin`: rejected.** It reaches the same evidence on the three measured
  cases, but selects the approver role even though the harness is a reader and AX provisions
  `HRPractitioner` for corpus access.
- **Rename the dataset role: rejected.** Changing `hr_manager` in the grounded datasets changes the
  dataset digest and invalidates the provenance of prior artifacts for no runtime benefit over the
  harness mapping.
- **Add `HRManager` to AX: rejected.** It expands the SUT's closed role contract to accommodate a
  harness invention.
- **Derive roles from a live AX database or response: rejected.** It requires the runtime to validate
  a pre-request input and risks turning the check into another comparison of a value with evidence
  produced by its neighbour.
- **Keep `LEGACY_FIXTURE_ROLES` and compare v1 personas literally: rejected.** It preserves persona
  discrimination in fixture replay, but makes `GroundedObservation.executed_role` mean an AX wire
  identity on the live path and a dataset persona on the fixture path. It also adds a dataset-version
  branch to the generic evaluator for distinctions AX never reported. The accepted cost is explicit:
  `hr_manager`, `manager`, `recruiter`, `interviewer`, `investigator` and `it_admin` collapse to
  `HRPractitioner`, so swapping those personas no longer fires `SYS-GROUNDED-ROLE-MISMATCH`.

## 6. Validation contract

Three named tests protect the three clauses independently:

- `test_hr_manager_alias_maps_to_provisioned_ax_reader_role`
- `test_canonical_ax_role_refuses_role_outside_ax_closed_set`
- `test_uncanonicalized_executed_role_is_role_mismatch`

The existing
`test_observation_from_a_different_executed_role_is_invalid` separately proves that a genuinely
different role reaches `SYS-GROUNDED-ROLE-MISMATCH`. Each clause was mutation-verified in isolation
and the fixed source hash was restored after every mutation.

The live-path repair adds:

- `test_live_capture_records_adapter_request_role_for_grounded_mismatch_evaluation`, which sends a
  wrong-but-valid role through the controlled adapter and requires
  `SYS-GROUNDED-ROLE-MISMATCH`; M4, re-deriving the recorded role from the case, must make it fail.
- `test_live_capture_canonicalizes_retrieval_dataset_role_before_ax_request`, which copies one
  retrieval case with `hr_manager` and requires the request to use `HRPractitioner`.
- the existing `corpus_role` response mutation, now checked against the complete
  AX-confirmed-to-required role map.

The MockTransport live-capture acceptance path sends all three grounded `hr_manager` Verification
cases as `HRPractitioner`; no AX runtime is required for this contract test. The dataset is not
modified.
The full-suite RED exposed the v1 fixture aliases above: 29 tests failed at the new closed-set guard
until the aliases were declared and the controlled observation fixture recorded canonical wire
roles. That ripple was outside the ticket's prediction but is part of keeping historical fixture
replay truthful under the new executed-role contract. Rewriting the fixture also preserves 43
existing tests' golden outcomes; it is both a semantic correction and a load-bearing compatibility
edit.

## 7. Honest limit

This decision settles which role the harness should send. It does **not** recover what the dataset
author meant by the phrase `hr_manager`: the corpus gives `HRPractitioner` and `HRAdmin` identical
read visibility on these three cases, so authored intent is not observable from the evidence.
The same limit applies more strongly to the v1 compatibility aliases: mapping them to the
provisioned reader preserves controlled fixture execution, but does not recover each persona
author's intended AX authority. The six reader personas collapse to one wire identity, so the
fixture path no longer detects swaps among them; four measured swap pairs changed from detectable to
undetectable.

It also does not establish answer quality. All six successful role probes still returned
`insufficient_evidence / unsafe_provider_output` after selecting five evidence items. The role fix
unblocks the run; it does not repair the separate citation-contract signal.

## 8. The recurring shape

The old mismatch check is the seventh recorded instance in this repository of a guard that compares
something to itself or validates a neighbouring fact instead of its subject. Cycle 109 repeated the
shape in its locked explanation by calling a case-derived producer value independent evidence; M4
survived all 505 tests and forced this correction. The repaired contract now names each operand's
actual strength: AX's corpus response independently confirms the complete required role set, and the
adapter's canonical request records the per-case role put on the wire. The case expectation remains
separate from both.
