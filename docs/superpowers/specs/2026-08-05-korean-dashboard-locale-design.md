# Korean locale for the recruiter-facing dashboard

- Date: 2026-08-05
- Status: implemented
- Scope: `dashboard/`, `tests/frontend/`

## Problem

The deployed dashboard is English-only. The reader it is built for is a Korean
hiring team, so the applicant wants to submit an English URL and a Korean URL
side by side.

The dashboard is not an ordinary marketing page. It renders one immutable
comparison artifact and it makes two claims about itself on screen:

- `Fixture evidence — not a live AX verification`
- `Gate order and decisions are rendered exactly as exported.`

A translation that weakens the first claim, or that rewrites values covered by
the second, would break the property this whole repository exists to
demonstrate. That constraint drives every decision below.

## Decisions

### 1. Two routes, not a runtime toggle

`/` stays English. `/ko/` is Korean. Each page carries a link to the other.

Rejected: a client-side language toggle on a single URL. It would give the
applicant one link to submit instead of two, but a reader who never presses the
toggle never sees Korean, and a shared URL cannot express which language it
points at.

Rejected: making Korean the default at `/`. The URL already printed on the
applicant's CV would silently change meaning.

### 2. Only dashboard-authored prose is translated

Translated: headings, lede, section descriptions, tab names, form labels, empty
states, and the fixture-boundary sentences.

Not translated, in either locale:

| Value | Why |
| --- | --- |
| `PASS` / `INVALID` | the artifact's recorded decision |
| metric names (`abstention accuracy`, …) | artifact field names |
| gate names (`Compatibility`, …) | gate identity, ordered as exported |
| `logical digest`, case identifiers | evidence identity |
| dataset version and license | artifact provenance |
| `Baseline` / `Candidate` column headers | the two runs' axis names, kept aligned with the values under them |

This is what keeps *"rendered exactly as exported"* true on the Korean page. A
reader comparing the two pages sees the same artifact values in both.

### 3. Locale identifier crosses the boundary, not the copy object

`DashboardExplorer` is a client component; the pages are server components. The
copy carries count-formatting functions (`15 publishable cases` versus
`공개 가능 사례 15건` — the number's position differs), and **functions cannot be
passed from a server component to a client component**. The build fails outright
if they are.

So the pages pass `locale="en" | "ko"` and the client component resolves its own
copy through `copyFor(locale)`.

Measured 2026-08-05: passing the copy object directly failed the static export
with `Functions cannot be passed directly to Client Components`.

### 4. One component, two dictionaries

`dashboard/lib/copy.ts` holds `DashboardCopy`, `enCopy`, `koCopy`, `copyFor`.
`dashboard-explorer.tsx` keeps all rendering logic and holds no literal user-facing
prose.

Rejected: a second copy of the component for Korean. 367 duplicated lines means
one side eventually gets fixed and the other does not, and two pages that
describe the same artifact differently is not a cosmetic bug here.

Rejected: an i18n library. Two static pages do not need a runtime dependency.

### 5. Verification

| Check | What it protects |
| --- | --- |
| `dashboard-copy.test.ts` — key parity | a key added to one locale and missing from the other |
| `dashboard-copy.test.ts` — every string differs, except an explicit allow-list | an untranslated string pasted into `koCopy` |
| `dashboard-copy.test.ts` — Korean boundary wording | the fixture disclaimer cannot be softened away |
| `dashboard-explorer.test.ts` — artifact values in both locales | translation creeping into exported values |
| `dashboard-ko.spec.ts` — boundary, `PASS`, 3 gates, digest, `lang="ko"` | the deployed Korean page states its limits |
| `dashboard-ko.spec.ts` — round trip between locales | either link breaking under `basePath` |

The two existing English browser tests are unchanged, so the English page is
proven to render exactly as before.

## Deployment

No workflow change. `output: "export"` emits `out/ko/index.html`, and the Pages
workflow already publishes the whole `out/` directory under the project
`basePath`.

## Known limitation

The root layout sets `<html lang="en">` for both pages; a static export cannot
vary it per route without restructuring the layout. The Korean page sets
`lang="ko"` on its `<main>` element instead, which scopes the language correctly
for assistive technology over all rendered content. The outer `html` attribute
remains inaccurate on `/ko/` and is recorded here rather than hidden.
