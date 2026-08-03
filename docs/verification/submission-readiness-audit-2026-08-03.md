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
