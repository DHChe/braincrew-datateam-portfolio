# Locked: no test writes to the tracked schemas directory, and the affordance that allows it is safe by conjunction, not by one property

Date: 2026-08-01
Status: locked
Implements: [Issue #97](https://github.com/DHChe/braincrew-datateam-portfolio/issues/97)
Owner decision recorded here: a four-line environment override in production source is accepted so
that tests stop mutating tracked files — and the reason it is safe is written down, because it is a
property a future change could silently break

## 1. Measured defect

`tests/contract/test_corpus_pack_sealing.py` drifted the repository's **tracked** `schemas/`
directory, then restored bytes it had captured at the start of the test.

If a second run captures its "original" **inside the first run's drift window**, its `finally` writes
the **drifted** bytes back as if pristine. **Both `finally` blocks complete normally and the tree is
left durably corrupted** — and the resulting `(schema, digest)` pair is *self-consistent*, so every
recompute-and-compare check passes. Only the code-pinned `EXPECTED_SCHEMA_DIGESTS` constant, or
`git status`, can detect it.

No interruption is required; that first hypothesis was refuted by measurement when the defect was
found on 2026-07-30. It reproduced heavily under two concurrent suites and left the tracked schema and
its `.sha256` modified in the working tree.

**This repository's value is evidentiary integrity and its commit gate is `git status`.** A silent,
self-consistent drift in a vendored schema could be committed beside real work. It nearly was: the
Issue #94 commit was made minutes after the reproduction, and only an explicit
`git status --short schemas/` precondition caught the dirty tree. The hazard has since been a standing
constraint on every cycle, serialising every test run by hand.

## 2. The constraint that made this non-trivial

`seal()` invokes the CLI through a **subprocess**, so an in-process `monkeypatch` of
`_schema_directory()` cannot reach the code under test. Containing the test therefore required a way
for a *separate process* to be told where to read schemas from — which is production source, for a
need that is only a test's.

## 3. Decision

`_schema_directory()` consults a `BRAINCREW_SCHEMA_DIRECTORY` environment variable and returns it when
non-empty; otherwise the existing resolution is unchanged. Four lines plus a named constant. The drift
test copies the vendored directory into `tmp_path` and points the subprocess at the copy.

## 4. Why the affordance is acceptable — and why the obvious argument is not enough

The obvious argument is that the override cannot weaken the contract because whatever directory is
selected is still checked against the code-pinned `EXPECTED_SCHEMA_DIGESTS`. **That argument is sound
but incomplete, and independent review found the hole in it.**

`_verify_vendored_schemas()` iterates over `EXPECTED_SCHEMA_DIGESTS`, **not** over the directory's
contents. Extra files in an override directory are therefore never inspected. Measured: a pristine
copy plus an attacker-supplied `EXTRA-attacker.schema.json` is **accepted**. If any second consumer
ever read a schema from `_schema_directory()` by a data-derived name, that extra file would be
loadable and the override would change **outcomes**, not merely **location**.

What actually makes it safe is a **conjunction of three facts**, each verified rather than assumed:

1. **`_schema_directory()` has exactly one production call site** — `corpus_sealing.py:810`, inside
   `_verify_vendored_schemas()`. `grep -rn "_schema_directory" src/` returns the definition and that
   call, and nothing else. The directory is used **only for verification**; nothing loads a schema
   from it to validate anything.
2. **The expectation is a code constant**, not read from the directory, so only byte-exact pinned
   schemas pass.
3. **The other schema reader is out of reach.** `corpus_authoring.py:160-161` resolves its own
   `source_root / "schemas"` and independently checks the same pinned constant. The variable does not
   touch it.

Given (1), the extras hole is **unreachable — there is no second consumer to steer.** That is the
whole safety case, and it is contingent.

**Therefore: the affordance is safe only while `_schema_directory()` remains single-call-site and
verification-only.** A future change that loads a schema *from* that directory rather than merely
verifying it re-opens the hole. That sentence is the reason this document exists.

**The emptiness test is deliberate.** `if schema_directory_override:` lets an empty string fall
through to the tracked directory, which is correct and fail-safe: `VAR=""` is indistinguishable from
unset in most shells and CI, and the fallback is the directory the repository vouches for. A
whitespace-only value is truthy and **refuses** — a non-empty nonsense value is operator error and
should fail closed.

## 5. The residual capability, and an irony worth naming

An operator whose tracked tree is drifted can point the variable elsewhere and obtain a green seal.
This is self-inflicted rather than adversarial — anyone who can set your environment can also edit
your files — it requires deliberate action, and it is independently detected by
`test_vendored_ax_schema_bytes_and_declared_digests_match_merge_contract`, which reads the tracked
directory directly, and by `git status`. The sealing receipt is unaffected either way: it records
`EXPECTED_SCHEMA_DIGESTS` constants, not digests read from the directory, so it stays truthful
regardless of where verification looked.

The irony, recorded rather than discovered later: the fix for *"tests corrupt the tracked schemas
directory"* is an override that lets any process **ignore** that directory. On net the property is
strictly better, because tests no longer write to it at all.

`BRAINCREW_SCHEMA_DIRECTORY` is a **test-only bridge and not an operator feature.** It is deliberately
undocumented outside this file and the source, and nothing in the CLI advertises it.

## 6. Rejected alternatives

**A CLI flag for the schema directory.** Explicit and inspectable, but it puts a test-only need into
`--help` permanently and widens the user-visible contract. The environment variable is invisible to
users and reaches the subprocess by inheritance.

**Serialising the drift test with a file lock.** Rejected in the ticket and again on review: it does
not fix the underlying property. Tests would still write to tracked files, and an interrupted writer
remains a repository-state hazard.

**Dropping the subprocess test and verifying `_verify_vendored_schemas()` in-process.** Considered
explicitly so it would be rejected deliberately rather than by omission. It needs no affordance at
all, but the test exists precisely to prove drift fails closed *through the real CLI*, and that
coverage is what the ticket was protecting.

**Threading the directory as a parameter down the call chain.** Considered by review; it collapses
back into the same two options, because the CLI runs in a subprocess and would still need a flag or a
variable to receive the value. Changing the subprocess working directory does not help either — the
fallback resolves from `Path(__file__)`, the source tree.

**No precedent existed.** `git grep -n -E 'os\.(environ|getenv)' -- src/braincrew` returned nothing
before this change. This is the repository's first test-facing environment affordance, and it is
recorded as such rather than presented as following a pattern.

## 7. Validation evidence produced

Reviewed once, `APPROVE` with no blocking finding.

**Measured by pane 1 directly.** A schema directory whose contents are drifted **but self-consistent**
— schema mutated, `.sha256` recomputed to match — is **refused** with `AX_SCHEMA_DRIFT` when the
override points at it; with no override the real tree verifies. The extras hole above; the single call
site; `corpus_authoring.py`'s independent resolution; and the receipt recording constants. Gates:
Ruff format and check, mypy, **592 pytest tests**, `git diff --check`, `git status --short schemas/`
empty.

**Measured by independent review, and this is the part that matters.** Ten input shapes against the override, plus a no-override baseline — empty string,
whitespace, empty directory, partial directory, a file rather than a directory, pristine copy, pristine plus extra, symlink, relative path, and self-consistent drift — with
no input found where the override changes the outcome rather than the location. Removing the
four-line override turns three tests red with `assert 0 == 2`, proving the subprocess genuinely
consumes the variable rather than passing for an unrelated reason.

**And the demonstration that the ticket's actual goal is met:** review injected a delay inside the
drift window and **`SIGKILL`ed `pytest` there** — the exact shape #97 was found by, and one that runs
no `finally`. The tracked bytes were unchanged, because nothing is ever written to them now.

Per-clause mutation verification: the recomputed-digest comparison and the declared-digest comparison
were each neutralised alone and each turned exactly one named test red. Both clauses are byte-identical
to `a2f5b02`, so they are pre-existing guards re-confirmed — but by **new** single-clause tests, which
the previous suite could not isolate because its only drift test moved bytes and digest together.

## 8. Validation evidence still required

The `except OSError` path's mutation was not reproduced by review and is taken on trust from the
implementation report. Nothing here touches AX, the answer path, or any evaluation result; it is a
repository-hygiene fix with no bearing on any claim about the SUT.
