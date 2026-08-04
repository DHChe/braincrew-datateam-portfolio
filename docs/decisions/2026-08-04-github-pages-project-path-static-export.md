# GitHub Pages project path is a build-time static-export contract

**Status:** Cycle 6 implementation complete; independent re-reviews passed;
pending owner-authorized Git lifecycle proposal

## Decision

Configure the dashboard's static export with the canonical GitHub Pages project
path, `/evidence-first-rag-evaluation`, through Next.js `basePath`. The path is
declared once in `dashboard/site-config.cjs`; `dashboard/next.config.ts`, the
local static server, Playwright configuration, and the build-output assertion
consume that value.

Do not add `assetPrefix`. The emitted entry HTML is the proof that `basePath`
prefixes the static resources needed by this project site. A separate prefix
mechanism would create two settings that can drift while producing a plausible
local root-path build.

The local E2E server mounts `dashboard/out/` only below the configured project
path and returns a real 404 for an absent file. The browser test uses a relative
navigation from that configured path and fails when any Next static resource
returns a 4xx response.

## Failure mode measured

Before this decision, `serve -s dashboard/out -l 4173` rewrote an absent request
such as `/evidence-first-rag-evaluation/_next/static/chunks/does-not-exist.js`
to `index.html` with HTTP 200 and `text/html`. The existing browser assertions
could therefore render statically generated text while JavaScript or CSS was
missing at the deployed project URL.

The project-path assertion was first run against the prior root-path build. It
failed on an emitted resource beginning `/_next/static/...` instead of
`/evidence-first-rag-evaluation/_next/...`.

## Rejected alternatives

- **Keep `serve -s` and test the root path.** Its single-page fallback masks a
  missing static resource as a successful HTML response, so it cannot prove the
  deployment seam.
- **Use `page.goto("/")` with a project-path `baseURL`.** A leading slash resets
  navigation to the origin root; it exercises the wrong route. Relative
  navigation preserves the configured project path.
- **Set both `basePath` and `assetPrefix`.** The emitted static HTML already
  proves `basePath` is sufficient here; another independent value adds a drift
  surface without solving a measured problem.
- **Commit `dashboard/out/` or add a deployment workflow.** Generated output is
  deliberately untracked, and hosted deployment belongs to Issue #149.

## Trade-offs and boundaries

The small static server is intentionally narrower than a general development
server: it serves only exported files under the project path and exposes missing
files as 404. That strictness is required for the test control. It does not
introduce AX, provider, browser-database, scoring, or deployment behavior.

`dashboard/site-config.cjs` is loaded through an absolute project path in
`next.config.ts` because Next's TypeScript-config compiler did not resolve a
relative shared module from its compiled configuration location. This keeps one
literal source while remaining executable in both Next and Node.

## Validation evidence

- The new Vitest build-output assertion failed against the old root-path export
  and passed after the `basePath` build.
- A real emitted JavaScript chunk was renamed only in ignored `dashboard/out/`.
  The browser test failed with `404
  /evidence-first-rag-evaluation/_next/static/chunks/2qzl-x5xxvnfd.js`.
  A fresh build restored the output and the browser test passed again.
- The fixture data, displayed fixture boundary, and read-only data path were not
  changed.

## Follow-up questions

- Issue #149 must build this export in GitHub Actions and deploy the generated
  artifact without changing this path contract.
- After deployment, the public Pages URL still needs its release-facing browser
  smoke check before Issue #151 adds a public documentation link.

## Cycle 3 superseding control limits and CI ordering

This section supplements the Cycle 1 record; it does not rewrite the earlier
decision or its evidence.

### CI ordering

The build-output assertion reads ignored `dashboard/out/index.html`, so it is
not a unit test and cannot run in the default `npm test` suite. A fresh CI
checkout has no such output. It now runs through `npm run test:build-output`
only after `npm run build`, both in the frontend workflow and in `AGENTS.md`'s
documented frontend command sequence. The test reports the missing entry page
and tells a local contributor to run `npm run build` first.

This decision extends the frontend command contracts in
`docs/decisions/2026-07-18-evaluation-scope-and-skill-flow-lock.md` and
`docs/superpowers/specs/2026-07-18-evidence-first-evaluation-plane-design.md`
with `npm run test:build-output`. Those dated records retain their prior scope;
this supersession adds only the build-output verification step.

**Failure mode:** putting the assertion back in default Vitest, or running it
before the build in a workflow, makes a fresh checkout fail independently of the
project-path contract. The selected ordering keeps the prerequisite explicit for
Issue #149's future Pages workflow.

### Vitest default exclusions

The default frontend Vitest configuration now spreads `configDefaults.exclude`
before excluding the build-output test. Pane 3 measured in a scratch project
that a configured `exclude` replaces Vitest's built-in defaults; pane 1 tried
twice to reproduce that mechanism but both probes failed during config loading,
before collection. This decision therefore records pane 3's mechanism as not
independently reproduced by pane 1. The change is safe in either case and the
collection check remains the repository-local evidence: default Vitest collects
three files and nine tests, while the build-output configuration collects one
file and one test.

### Browser control limits

The browser guard fails both when a Next static resource returns a hard 4xx and
when it returns `text/html` with HTTP 200. The latter is the soft failure that a
single-page fallback creates: a JavaScript or CSS request receives an HTML page
and an assertion that checks only status codes becomes inert.

Both browser scenarios install this guard. A page that renders server-generated
text is not evidence that its assets loaded.

**Directive:** Do not replace the strict `scripts/serve-static.mjs` server with
a general fallback server without preserving a control that makes missing
project-path assets observable. The browser assertion cannot protect itself if
the server turns every missing asset into a successful HTML response.

### Remaining limits and deliberate exclusions

The build-output assertion derives its expected prefix from `pagesBasePath`, so
it detects an inconsistent build but cannot prove that a changed constant is the
canonical repository path. That proof belongs to Issue #150's deployed-URL
smoke check, not Issue #148; this cycle deliberately does not add a second
repository-name mechanism.

`dashboard/site-config.cjs` remains paired with an unchecked `.d.cts`
declaration because `allowJs: false`, `skipLibCheck: true`, and the TypeScript
include set do not compare them. A default Vitest assertion pins the runtime
value to the reviewed literal, converting a silent runtime drift into a failing
test. Adding `scripts/` to TypeScript coverage is a separate test-infrastructure
decision and remains out of scope.

The `serve` dependency remains installed. It is useful as the comparative
single-page-fallback control and may be needed by Issue #150; removing it would
erase that evidence path without improving the Pages contract.

## Cycle 4 superseding complementary-gate coverage

This section appends pane 1's 2026-08-04 measurement; it does not change the
earlier implementation or evidence.

The exported entry page references
`dashboard/out/_next/static/chunks/0cz1d0mv5g_q7.js` as a `noModule` script:

```html
<script src="/evidence-first-rag-evaluation/_next/static/chunks/0cz1d0mv5g_q7.js" noModule=""></script>
```

`noModule` is the legacy fallback for browsers without ES-module support, so
Chromium does not request this file. Pane 1 removed it, confirmed the strict
static server returned `404 text/plain` for its project-path URL, and observed
both E2E tests pass because neither browser scenario fetched it. This is correct
browser behavior, not a listener defect.

The same removal made `npm run test:build-output` fail at the referenced-path
`existsSync` check. The browser guard therefore proves that a modern browser's
requested assets resolve over HTTP at the project path, including detection of
soft HTML fallbacks; the build-output assertion proves every emitted entry-page
`href` and `src` reference exists, including references a modern browser never
fetches.

**Directive:** Keep both gates. Do not remove the build-output assertion because
the E2E suite exercises the deployed path, and do not remove the E2E guard
because the build-output assertion sees files without proving their HTTP
behavior. The specific trap is treating the browser suite as complete coverage:
it cannot observe a `noModule` reference it never requests.
