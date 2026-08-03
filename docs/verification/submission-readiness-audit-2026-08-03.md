# Submission readiness audit — 2026-08-03

## Scope

This audit covers the local submission change on `develop` before any commit, push, pull request, or
merge. It verifies the public repository surface; the private CV and application materials live outside
the repository and are not publication candidates.

## Reproduced defect and repair

The first clean install used the declared `npm@11.12.1` and reported four high-severity findings. The
bounded repair updates Next.js and `eslint-config-next` to `16.2.12`, overrides PostCSS to `8.5.25` and
sharp to `0.35.3`, and makes CI install the pinned npm before `npm ci`.

The sharp override is outside Next.js `16.2.12`'s declared optional range `^0.34.5`. The application has
no `next/image` import or `<Image>` component use; the generated `dashboard/next-env.d.ts` type reference
is not an image path. Compatibility evidence is therefore local and bounded: clean install, Linux
container, static build, unit tests, and browser smoke. This is not an upstream support claim.

## Fresh local evidence

| Gate | Result |
| --- | --- |
| `uv sync --frozen --all-groups` | pass |
| Ruff format and lint | pass; 72 files |
| mypy | pass; 72 source files |
| pytest | pass; 610 tests |
| `npm@11.12.1 ci` | pass; 472 packages audited |
| npm high-severity audit | pass; zero known vulnerabilities |
| Prettier, ESLint, TypeScript | pass |
| Vitest | pass; 8 tests |
| Next.js static export | pass; Next.js 16.2.12, three static pages |
| Playwright | pass; 2 browser tests |
| no-cache, network-isolated Docker run | pass; 607 tests, 3 designed skips, 11 fixture-gate tests |
| `git diff --check` | pass |

The Docker execution predates the documentation-only synchronization in this same local audit but uses
the repaired dependency lock and application code. No source or container contract changed afterward.

## Reviewer-facing changes

- Repository title aligned with `evidence-first-rag-evaluation` while retaining the Braincrew origin.
- Three-minute reviewer path and deterministic demo script added.
- AI implementation share and author-owned design/review/claim responsibilities disclosed.
- Owner-local unpublished artifact path removed from the README while preserving the unpublished limit.
- Dashboard commands and CI now use the declared npm version.

## Remaining submission gates

- Hosted GitHub Actions has not run for this uncommitted change.
- The change is not on `main`; the public default branch therefore does not yet contain it.
- A clean remote clone cannot validate this local diff until it is published.
- Private CV placeholders for identity, employers, dates, bootcamp, and evidence-backed experience details
  must be filled by the owner before submission.

## Decision

The local change is ready for the Git lifecycle proposal. It is not yet ready to send to a recruiter
because remote CI, reviewed integration into `main`, and owner-provided CV facts remain outstanding.

## Post-publication verification and independent-review follow-up

The scope, remaining-gate list, and decision above are the preserved pre-publication audit. They were
accurate before commit `a089b645a89321fb57905f60111f1a1343289e96` was pushed and
[PR #141](https://github.com/DHChe/evidence-first-rag-evaluation/pull/141) was opened; they are not the
current GitHub state.

The first hosted run on that exact commit passed all four jobs: `python`, `fixture-container`, `secrets`,
and `frontend`. Its frontend log reports `npm 11.12.1`, a clean locked install with zero known
vulnerabilities, a successful Next.js `16.2.12` static build, and two passing Playwright tests. The
container job also completed successfully without a host mount and with `--network none` at runtime.

Independent review after that run found a separate rename regression: the authoring launcher still
accepted only the repository's former GitHub name, while the public origin is now
`evidence-first-rag-evaluation`. The owner approved a bounded follow-up in the same Draft PR: retain the
former URLs as compatibility aliases, accept the current HTTPS/SSH forms, add a public-CLI regression
test, update the dashboard link, and synchronize the reviewer-facing status. No evaluation evidence,
metric, gate, live run, or private application material enters that repair.

The remaining submission gates are a successful hosted run and independent review on the repaired PR
head, reviewed integration through `develop` to `main`, and completion of the private CV facts. Draft
status and the explicit no-merge boundary remain unchanged.

## Repaired-head verification and current decision

The paragraph immediately above is the preserved pre-verification gate. It was superseded when
`2fc440b2f3da9f086e0a180fe90d70729790b15d` became the matching local, remote, and PR head. GitHub
Actions run `30795299567` executed that exact commit and passed all four required jobs: `python`,
`fixture-container`, `secrets`, and `frontend`. The run installed `npm 11.12.1`, reported zero known
install-time vulnerabilities, built the static dashboard, passed two Playwright tests, ran the Python
suite in both the Python and network-isolated container jobs, and passed the 11-test fixture gate.

Post-CI Standards and Spec review both returned `APPROVE` with zero findings. Submission-document
review found one blocking state-record defect and no product defect: this audit still described the
repaired head's hosted run and review as pending. This append-only section, together with the matching
workflow-status and claim-audit deltas, is the bounded repair. It changes no implementation, evaluation
evidence, metric, gate, live result, or private application material and must pass independent re-review
before publication.

The code-bearing repaired head is therefore verified. The repository is not yet ready to send as the
final recruiter URL: the documentation-only synchronization must be published and pass the same hosted
checks, PR #141 must undergo separately authorized reviewed integration through `develop` to `main`, and
the owner must complete the private CV facts. PR #141 remains Draft and merge remains unauthorized.

## Dynamic-head boundary and final audit rule

The remaining-publication sentence immediately above is now a dated pre-publication record.
Documentation-only commit `d53d6fabffa7e1aec534f366332713904477c8e4` was published, and GitHub
Actions run `30796490848` passed `python`, `fixture-container`, `secrets`, and `frontend` on that exact
head. Its final review found no executable defect; it found that a static document was again presenting
an earlier measured SHA as the continuously current branch head, plus a README count that did not
separate 613 collected tests from Linux's 610 passes and 3 designed skips.

The durable correction is a boundary rather than another self-expiring “latest SHA” claim. A Git
commit cannot include its own SHA because changing the document changes the object whose SHA is being
computed. Static audit records therefore name only commits and runs already measured. At any future
integration decision, current publication status must be read from PR #141: local, remote, and PR head
must match; all four required jobs must have succeeded on that exact head; and independent review must
have no unresolved blocker. A prior successful run does not certify a later documentation successor.

The README now binds the 613-test collection count to code-bearing commit `2fc440b` and separately
reports the platform outcomes; later submission-readiness commits through `d53d6fa` changed
documentation only. The remaining recruiter-submission gates are reviewed integration through
`develop` to `main` and owner completion of the private CV facts. PR #141 remains Draft and merge
remains unauthorized.

## Release-phase supersession after PR #141 integration

The final two sentences immediately above are preserved dated records, not the current GitHub state.
[PR #141](https://github.com/DHChe/evidence-first-rag-evaluation/pull/141) later passed its exact-head
checks and independent reviews, left Draft under separate owner authorization, and merged into
`develop` as `43c96aa9a63580aa0d13d60d2624281cd4cb9434`. Post-merge run `30815892795` passed `python`,
`fixture-container`, `secrets`, and `frontend` on that exact `develop` commit.

[PR #142](https://github.com/DHChe/evidence-first-rag-evaluation/pull/142) is now the active
`develop`-to-`main` release gate. Run `30816574010` passed all four required jobs at the pre-repair
release head `43c96aa9a63580aa0d13d60d2624281cd4cb9434`. This section records only publicly retrievable GitHub
evidence; it does not turn session-local command output into a durable receipt.

The release review found this audit's PR #141 live pointer stale; that is a documentation-state defect,
not a code, test, or evaluation-result failure. This append-only section supersedes it without claiming
that the prior run certifies a new documentation commit. At any release decision, current evidence must
come from the active release PR's actual head, four same-head successful jobs, and zero unresolved
independent-review blockers. PR #142 remains Draft, `main` merge remains unauthorized, and the private
CV facts remain owner-supplied work outside this repository.
