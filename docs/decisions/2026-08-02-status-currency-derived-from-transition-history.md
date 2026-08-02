# Locked: `Last updated` is a current-state claim, and the newest visible transition independently checks it

Date: 2026-08-02
Status: locked
Implements: [Issue #103](https://github.com/DHChe/braincrew-datateam-portfolio/issues/103)

## 1. Measured defect

`docs/status/braincrew-delivery-workflow.md` declared `Last updated: 2026-07-25` while its newest
Transition history entry was dated `2026-08-01`. The first date a reader saw therefore understated the
currency of the file. The acceptance test froze the old literal, so changing only the header turned the
suite red.

The field is not a preserved Issue #47 snapshot. It progressed from `2026-07-19` to `2026-07-20`,
`2026-07-22`, `2026-07-23`, `2026-07-24`, and finally `2026-07-25` before entries continued to be
appended without it moving. The last move, from `2026-07-24` to `2026-07-25`, was `f411fae`, which
also introduced the literal test assertion while implementing AX's five-file upload cap. Its
`Rejected:` and `Directive:` concern the upload contract only. The later `f9d9cfd` and `52ae146`
directives govern corpus-role and discard-predicate contracts respectively. None bears on the meaning
of this status header.

## 2. Decision

`Last updated` remains a current-state header. Its value is the maximum of every date captured from a
`### YYYY-MM-DD` heading under `## Transition history`. The test also requires every `###` heading in
that section to begin with such a date, so it cannot silently skip an unparseable transition entry.
The header is not derived at render time: it stays an independently hand-written claim that the
acceptance test parses and compares to the full transition-date set.

The scanned region is bounded at both ends — from `## Transition history` to the following
`## Transition record format` heading. That bound is load-bearing rather than cosmetic. Scanning to
the end of the file instead lets a `###` heading in the format section, which documents the entry
*format* and records no transition, decide the file's currency claim: **measured**, an example heading
`### 2099-01-01` plus a matching `Last updated: 2099-01-01` passed the unbounded check, and the
unbounded check simultaneously rejected a legitimate undated `### Required fields` subheading in that
same section. The bound closes the first and removes the second.

The chosen date is the entry date, not the Git commit date. A transition can describe work done on one
day and land on another; readers of this document can verify the entry heading but cannot infer a commit
timestamp from the document itself. The header therefore answers the visible-document question without
rewriting history.

## 3. Why this is the narrowest durable repair

Pinning a new literal would repeat the defect on the next entry. Renaming or deleting the field would
avoid maintenance by removing useful currency information. Comparing two independent statements keeps
the useful claim and makes a missed matching edit fail locally before publication.

The test deliberately reads every Transition heading and the fixed header line. It does not derive
either value from the other, does not depend on newest-first file order, and leaves every Issue #47-era
Current checkpoint assertion unchanged. Existing history remains append-only.

## 4. Rejected alternatives

- **Replace `2026-07-25` with a new test literal.** It makes the immediate test green while leaving
  the next append able to make the header silently stale again.
- **Treat the header as a snapshot and rename or relocate it.** The file has historical evidence that
  it was maintained as a current-state field, and hiding the claim reduces reader-visible information.
- **Drop the header.** The top entry has a date, but a current-state header is a useful orientation
  cue when it is enforceably true.
- **Use Git commit time.** It can diverge from the entry's effective date and is not a fact the reader
  can verify from this document alone.

## 5. Failure modes and guard

Three independently writable clauses can disagree:

1. A contributor inserts a later `### YYYY-MM-DD` entry anywhere in the history but forgets the
   header.
2. A contributor edits the header but leaves the maximum transition date unchanged.
3. A contributor adds an unparseable `###` Transition heading that a date-only scan might otherwise
   skip.

The derived acceptance check must reject all three. It requires at least one dated heading, requires
the dated-heading count to equal the count of every `###` heading, then compares the maximum captured
date with the header at line three. This is a guard against drift, not a claim that the file can update
itself.

The guard intentionally captures the **start** of a range heading. Thus
`### 2026-08-03 – 2026-08-04` captures `2026-08-03`; a truthful `Last updated: 2026-08-04` would fail
loudly rather than silently pass. There are zero range headings today. Until a range grammar is
designed and tested, use one date in the heading and describe a multi-day span in the entry body.

## 6. Validation evidence

The Cycle 176 first-heading guard was deliberately given an out-of-order `2026-08-05` entry below the
top `2026-08-02` entry and passed, reproducing the fail-open. Replacing that guard with the
maximum-date comparison made the same mutation fail `2026-08-02` versus `2026-08-05`. It also rejected
a stale `2026-08-01` header, an unparseable `### current` Transition heading, and a corrupted Issue #47
checkpoint token. Each temporary status mutation restored exactly to
`3507223b2082c34d771c7eb3834d9d309f894fefec3eef9a4380f73b94d01e37`. Sequential `ruff format
--check`, `ruff check`, `mypy`, and `pytest -q` passed, with 598 tests. No Git write is part of this
issue.

## 7. Scope boundary

This decision changes one status header, one acceptance assertion, one new Transition record, and this
decision plus defense card D29. It does not rewrite or delete any historical Transition entry, change
the Issue #47 preservation assertions, modify `src/`, run AX, or make a claim about an AX SUT.
