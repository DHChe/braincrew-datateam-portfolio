# Locked: the live capture artifact gets a replay path, and its claim is enumerated rather than described

Date: 2026-08-01
Status: locked
Implements: [Issue #106](https://github.com/DHChe/braincrew-datateam-portfolio/issues/106)
Owner decision recorded here: the unrepeatable live capture artifact must be verifiable by committed
code, and what that verification establishes must be stated as a closed list rather than as a
general property

## 1. Measured gap

The first live experiment capture in this project's history ran on 2026-07-31: 24 live AX SUT calls,
exit 0, three artifacts. It is the one artifact in the chain that cannot be regenerated, because the
provider calls cost money and cannot be repeated identically.

Measured by pane 1 on `develop` at `a373e64`, against the real artifacts:

- `braincrew-eval replay` on the capture manifest exited **2** —
  `unsupported artifact schema: live-experiment-capture-v1`.
- `braincrew-eval replay` on the *evaluation* artifact exited **0** and reproduced its logical digest.
- `braincrew-eval build-run-summary` on the same pair exited **2** —
  `run artifact must contain one completed 30-case Verification evaluation`.

Two consequences follow, and both are measured rather than inferred.

**The reproducible half replayed; the irreproducible half did not.** The evaluation of the run is
recomputed by committed code. The recording of the live calls was refused.

**The only committed code that cross-checks the manifest against its observation files was
unreachable for this run.** `run_summary.py` recomputes both observation content digests and compares
case counts, but an earlier clause in the same function returns first unless the evaluation is
`COMPLETED` with 30 of 30 scored. The 2026-07-31 run is `INVALID` with 18 of 30 scored, because twelve
grounded cases returned `unsafe_provider_output`. That gate is correct — a comparison input must not
be built from an incomplete evaluation — but it coupled artifact integrity to answer quality, which
are unrelated concerns.

Until this decision, the artifact's integrity rested on an uncommitted script run once, which
recomputed the digests with the same functions that produced them. That detects tampering. It does
not detect an error in the generating logic, it is not reviewable, and nobody else can repeat it.

## 2. Decision

`replay_live_experiment_capture` is committed, reachable from the existing `replay` command, and
read-only. Given a capture manifest it re-opens the two sibling observation files named in that
manifest and refuses, with a typed `ValueError` and CLI exit 2, unless every one of the following
holds.

- **V1** The manifest validates strictly against `live-experiment-capture-v1`, which re-arms the
  existing partition, role/evidence-limit, execution-mode and SUT-warrant invariants.
- **V2** Each observation file exists, parses, and validates against its batch contract.
- **V3** Each observation batch reproduces the `content_digest` and `case_count` the manifest
  declares for it.
- **V4** The case identities present in the two files equal the manifest's declared `live_case_ids`
  exactly — nine retrieval, fifteen grounded, disjoint.
- **V5** Each batch's `adapter_version`, and the grounded batch's `sut_commit_sha`, agree with the
  manifest's provenance and state warrant.
- **V6** The manifest reproduces its own `logical_digest`, and the **recomputed** value is what the
  command returns.

`CaptureArtifactReference.file_name` is additionally constrained at the contract to a bare filename,
so a reference that escapes the manifest's own directory is unrepresentable rather than merely
refused by one reader.

## 3. The claim, stated as a closed list

This is the substantive half of the decision, and it exists because the first wording of Issue #106
did not survive review.

**What a successful replay establishes** is exactly V1 through V6 above, and nothing else.

**What it does not establish:**

- It does not re-run AX, and cannot. The live calls are unrepeatable and no stored artifact can
  re-derive what AX would have returned.
- It does not detect a forgery in which the manifest and every observation file were fabricated
  together consistently. Anyone who controls the manifest controls the digests it declares. This is
  inherent to the scheme, not a defect in it.
- It does not verify every fact the two sides record independently. Three such facts are compared
  (V5). Independent review found a fourth — each grounded observation's `executed_role` against the
  manifest's `corpus_digests_by_role` keys — and two declared bounds, `retrieval_top_k` and
  `evidence_limit`, that responses could exceed without refusal. All three are recorded as
  follow-ups, for two different reasons. `executed_role` is unreachable from the capture path: it is
  taken from the adapter the capture itself constructed, so a wrong value can only arrive by
  hand-editing a finished artifact. The two bounds **could** in principle be exceeded by an AX
  response, since AX supplies the candidate and citation lists; they are deferred because the real
  capture's margins are wide — 0 to 1 candidates and 0 to 1 citations against limits of 5 and 3.

The reason the claim is enumerated is a finding in its own right. The first wording said the replay
verifies that the manifest and its observation files are "mutually consistent." That phrase is
unbounded, so each review round could find one more fact it did not cover, and each such fact would
read as a defect against the stated claim. An enumerated claim is true, checkable line by line, and
finishable. It also does not silently expand as the document is re-read.

## 4. Why the blocking finding was blocking

The first implementation compared digests and case identities but not provenance. Independent review
constructed capture triples where the manifest and its observation files **contradict each other**
and every stored digest is nonetheless internally consistent; the committed CLI accepted them at
exit 0.

pane 1 independently reproduced this against the **real** 2026-07-31 capture, in a scratch directory
outside the repository. A grounded observation file declaring `fixture-grounded-sut-v1` and SUT commit
`bbbb…` — under a manifest still declaring `execution_mode: live`, adapter `ax-sut-http-v1` and
warrant commit `1ead1331…` — replayed at exit 0.

The second reproduction is why this was blocking rather than untidy. Once the grounded batch declares
the fixture adapter, its contract no longer requires answer-path health, so **all fifteen
`answer_path` records were deleted** — including the **twelve `unsafe_provider_output` records that
constitute the entire X1 measurement.** Digests recomputed, manifest rehashed, and the replay reported
success on a capture stripped of the only evidence of AX's answer-path failure, while the manifest
still said the run was live.

An artifact that reports exit 0 on that input is worse than one that refuses to replay at all,
because the refusal is honest and the exit 0 is an affirmative false assurance.

## 5. Rejected alternatives

**Narrow the claim instead of adding the checks.** The wording could have been weakened to match the
code. Rejected: the three facts are recorded on both sides precisely so they can be compared, the
comparison is six lines, and `run_summary.py` already establishes the convention of checking
provenance agreement before digests. The claim was narrowed *as well*, but as a second step, not
instead.

**Enforce the sibling constraint at the replay site.** Rejected in favour of the contract, so the
escape is unrepresentable rather than refused by one reader. Verified before adopting by pane 2, and
independently re-derived by pane 3 in cycle 141: every
`CaptureArtifactReference` this project constructs uses `f"{run_id}.…json"` with `run_id` matching
`^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$`, no separator is representable, no capture artifact is committed
to this repository, and the real 2026-07-31 manifest's two names are accepted unchanged.

**Return the stored logical digest.** The first implementation returned the value read from the file
after comparing it. Rejected: every other replay in `result_store.py` returns the recomputed value,
and the two are equal only because the comparison immediately above guarantees it — so a weakened
comparison would leave the command printing a confident digest.

**Relax the `COMPLETED`/30-case gate in `run_summary.py`** so the existing cross-check becomes
reachable. Rejected as out of scope and wrong in itself: that gate protects comparison inputs, and
the correct fix is a separate integrity path, which is this one.

## 6. Trade-offs and failure modes

The contract constraint on `file_name` is a genuine narrowing of `live-experiment-capture-v1`. Any
future capture layout that puts observation files in a subdirectory now needs a contract change and a
schema decision, which is the intended cost.

Refusal ordering places the provenance comparison before the digest comparison, so an artifact with
both faults is described by the provenance fault. No false accept is possible — the reordering only
adds refusals ahead of others — but the diagnostic message can name the less fundamental problem, and
in one measured case it named the grounded file while the corrupt one was retrieval. Recorded, not
fixed.

`require_bare_file_name` constrains the file *name*, not the resolution *target*. A bare-named symlink
in the manifest's own directory still reads outside it. The operator supplies both the manifest path
and the directory, so this is self-inflicted rather than attacker-controlled, but the property
"resolves within the manifest's own directory" is not guaranteed, and nobody should read the
constraint as stronger than it is.

## 7. Validation evidence produced

Implemented under TDD across cycles 138, 140 and 142, with independent review at 139 and a scoped
re-review at 141.

Reviewed twice by pane 3. Cycle 139 returned **REQUEST CHANGES** on the provenance-agreement gap,
having constructed six forged triples of which all six were accepted. Cycle 141 returned **APPROVE**
with no blocking finding and re-ran that harness unchanged against the repaired tree. **The four
forgeries the repair targets are now refused**, each with a distinct message naming the right fact.
**Two remain accepted**: one that was inconclusive when it was built, because the two runs'
observation files were byte-identical under the mock transport, and one — a `run_id` disagreeing with
the file names it points at — which is a recorded follow-up. pane 1 independently reproduced that
second acceptance against the real capture: changing `run_id` alone and rehashing replays at exit 0.

Mutation verification was performed one clause at a time, each in its own run, each restore proved by
SHA-256 rather than by a passing test. Cycle 139 checked all fourteen of cycle 138's labels against
`a373e64` byte-identity and found every one correct; cycle 141 did the same for cycle 140's six and
reproduced all six independently.

Measured by pane 1 directly, against copies of the real 2026-07-31 capture outside the repository:
the untouched triple replays to `sha256:775a8529…` at exit 0 with 9 and 15 observations, and **seven**
forgeries each refuse at exit 2 with their own message and no traceback — a case identity swapped with
every digest rehashed, a grounded adapter disagreement, an `answer_path`-stripped variant, a grounded
`sut_commit_sha` changed alone, a retrieval `adapter_version` changed alone, a missing sibling file,
and a `sub/` file name. An eighth probe, a `run_id` changed alone, is **accepted** — the deferred
follow-up recorded above. Gates reproduced solo by pane 1: Ruff format and check, mypy,
**581 pytest tests**, `git diff --check`, and `git status --short schemas/` empty.

Not run by pane 1: the six npm and Playwright gates. pane 2 ran them green, and pane 3 verified
independently that no changed path lies inside any of their input globs. That is an inference from
the gate configuration, not a measurement of the gates.

## 8. Validation evidence still required

No live AX runtime was started for this work and none was needed. Nothing here bears on AX's answer
path, the `unsafe_provider_output` conflation, or the twelve unscoreable grounded cases; those remain
open against AX. No candidate run exists, so there is still no comparison, no gate decision and no
answer-quality claim.

The follow-ups this work deliberately did not take: `executed_role` membership against the manifest's
role keys; the `retrieval_top_k` and `evidence_limit` bounds; recomputing
`fixed_retrieval_config_digest`, which is derivable from two fields in the same manifest and would
have caught a forgery in which the manifest and both observation files agree on a fixture adapter
while `execution_mode` still says `live`; `run_id` agreement with the file names it points at;
byte-canonicality refusal as the sealing receipt performs; return-shape alignment with the preflight
replay; and asserting the 9/15 split on the capture side as well as the replay side.

One further follow-up is **not** this change's to make and is recorded because the audit measured it:
a pathologically nested manifest raises `RecursionError` inside the CLI's own pre-dispatch
`json.loads`, which `except (UnicodeError, ValueError)` does not catch, so it exits 1 with a
traceback. The same input fails the same way against the pre-existing `run-artifact-v1` schema, and
`corpus_sealing.py` already guards it with a nesting validator that catches `RecursionError`. The
`replay` command should adopt that guard.
