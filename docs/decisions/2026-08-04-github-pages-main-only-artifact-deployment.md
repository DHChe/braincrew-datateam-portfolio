# GitHub Pages deployment is a main-only artifact handoff

**Status:** Cycle 7 implementation complete; hosted deployment validation pending

## Decision

Deploy the dashboard through `.github/workflows/pages-deploy.yml`. Its only
event is a `push` whose branch filter is `main`; it has no `pull_request`,
manual-dispatch, scheduled, reusable-workflow, or broad-push trigger. As a
result, a pull request or feature-branch revision cannot start either its build
or deployment job.

The build job checks out the triggering `main` revision, installs the locked
dependency graph with `npx --yes npm@11.12.1 ci`, builds the Next.js static
export, runs `npm run test:build-output` after that build, and uploads only
`dashboard/out` with `actions/upload-pages-artifact`. The dependent deploy job
uses `actions/deploy-pages`; no `gh-pages` branch, committed generated output,
or developer-produced artifact is a publication source.

The workflow-level token has only `contents: read`. The deploy job replaces that
scope with only GitHub Pages' required `pages: write` and `id-token: write`
permissions. It uses the standard `github-pages` environment, exposes
`steps.deployment.outputs.page_url` as the deployment URL, and uses a
`pages-${{ github.ref }}` concurrency key without cancellation. Since `main` is
the sole trigger branch, at most one active publication for that branch exists
while an accepted earlier publication is allowed to finish.

## Rejected alternatives

- **Build on pull requests or all branches and guard deployment with `if:`.** A
  later edit to one condition could publish unreviewed portfolio evidence. The
  trigger restriction makes the deployment workflow unreachable from those
  events in the first place.
- **Use GitHub Pages branch publishing or commit `dashboard/out`.** That would
  make generated output, rather than a locked rebuild of the reviewed revision,
  the deployment input and would add a `gh-pages` history surface.
- **Upload a broad workspace artifact.** The deployment contract is the static
  export only. Uploading the repository or another directory could disclose
  unrelated files and would weaken the build-to-deploy boundary.
- **Omit `npm run test:build-output`.** The #148 build-output and browser gates
  prove different controls: the former catches every emitted entry-page
  reference, including no-module assets Chromium does not request; the latter
  checks HTTP behavior for browser-requested assets. Both remain required.

## Failure modes and limits

- A malformed workflow or missing action tag would fail only after a revision
  reaches `main`; YAML parsing and remote tag checks are therefore required
  before integration.
- A broken static export can still build. The build-output gate catches missing
  emitted references, while Issue #150 must exercise the resulting public URL
  and static assets in a browser.
- GitHub Pages is presently disabled. The repository owner must explicitly set
  GitHub Actions as the Pages publishing source before the first deployment;
  this workflow does not change repository settings or create a public URL.
- A failed or unapproved `main` integration cannot be repaired by a feature
  branch deployment. The next approved `main` revision is the only recovery
  path, by design.

## Validation evidence

- `python3` with PyYAML 6.0.3 parsed the workflow AST and asserted one trigger
  event (`push`), one matching branch (`main`), and `deploy.needs == build`.
  This proves from the file itself that no pull-request or non-`main` event can
  start the deployment job.
- Cycle 7 used `git ls-remote --exit-code --refs` to confirm its then-current
  action tags: `actions/checkout@v6` (`d23441a`), `actions/setup-node@v6`
  (`2499707`), `actions/upload-pages-artifact@v3` (`56afc60`), and
  `actions/deploy-pages@v4` (`d6db901`). Cycle 9 re-verifies the upgraded
  Pages-action tags separately below.
- The pinned frontend commands passed: dependency installation; Prettier;
  ESLint; TypeScript; 3 Vitest files / 9 tests; static build; the one
  build-output test; and 2 Playwright tests.
- `uv run ruff format --check .`, `uv run ruff check .`, and `uv run mypy`
  passed. `uv run pytest -q` was started once and the command runner reported
  completion, but its streamed output stopped at 35% without a final pytest
  footer. Treat the full-suite test count as unconfirmed until an integration
  runner captures that footer; do not infer it from this record.
- `git diff --check` and the final working-tree check are run after this
  decision record is updated. These checks validate workflow structure and the
  build input, not a hosted deployment or public-page behavior.

## Follow-up questions

- Before the first `main` deployment, who will enable GitHub Pages with GitHub
  Actions as its publishing source, and where will that one-time setting be
  recorded?
- Issue #150 must prove the reported public URL responds successfully, displays
  the dashboard heading and exact fixture boundary, preserves the fixture-only
  PASS explanation, and resolves deployed static assets.
- Issues #151 and #152 remain blocked on #150's verified canonical URL; this
  decision intentionally changes neither public documentation nor the CV.

## Cycle 9 repair: publishing-path coverage and durable limits

Cycle 7 correctly recorded that the build-output and browser gates are both
required repository controls. At that point, the Pages build job ran only the
build-output gate, so the phrase did not mean that the publishing path itself
ran both controls. This repair retains that historical fact and closes the gap:
after building, the Pages build job runs `npm run test:build-output` and then
`npm run test:e2e` before it uploads `dashboard/out`. The first checks every
emitted entry-page reference on disk, including a no-module asset Chromium does
not request; the second serves this same build over HTTP at the project path and
catches hard 4xx and HTML-fallback asset failures. Both gates are now required
and run by the publishing path itself.

The artifact and deployment actions now use `actions/upload-pages-artifact@v5`
and `actions/deploy-pages@v5`. At v5, the upload action still requires `path`
and still defaults its artifact name to `github-pages`; the deployment action
still defaults `artifact_name` to `github-pages`, requires a token supplied by
default as `github.token`, and exposes `page_url`. Its documented deployment
permissions remain exactly `pages: write` and `id-token: write`. No new input
or permission is needed for this workflow. The deploy action's Node 24 runtime
also avoids retaining the prior v4 Node 20 production-only runtime risk.

The #149 request to validate this workflow from a pull request or
non-production branch without deploying is superseded by the accepted design:
there is no pull-request, manual, reusable-workflow, schedule, or non-`main`
trigger, and a `main` run deploys. Adding one merely to exercise this workflow
would reopen the exact publication path the ticket prohibits. Structure and
local artifact behavior are therefore validated before integration; the first
hosted execution is the later approved `develop` to `main` release, after the
owner enables GitHub Pages with GitHub Actions as its publishing source. This
precondition is not required before this feature branch merges into `develop`,
which cannot match the workflow trigger.

**Directive:** Keep `main` as the sole trigger while the concurrency key is
`pages-${{ github.ref }}`. Adding another branch to the trigger and changing
nothing else would both permit that branch to publish and let independent
per-ref deployments race for the one Pages site. Treat the trigger and
concurrency key as one control; changing either requires an explicit
single-publication design review.

Cycle 7's missing pytest footer is superseded by pane 1's attributed 2026-08-04
measurement of **613 passed**. Cycle 9 reran the Python suite once, but the
command stream again stopped at 35% before its final footer; this document does
not attribute a test count to that run or infer one from the completion signal.

Cycle 9's PyYAML AST validation confirmed exactly one event (`push`), exactly
one branch (`main`), no `if:` key, `deploy.needs == build`, and the pre-upload
order `test:build-output`, `test:e2e`, then artifact upload. Remote tag checks
resolved `actions/checkout@v6` (`d23441a`), `actions/setup-node@v6`
(`2499707`), `actions/upload-pages-artifact@v5` (`fc324d3`), and
`actions/deploy-pages@v5` (`cd2ce8f`). The pinned frontend gates passed:
Prettier, ESLint, TypeScript, 3 Vitest files / 9 tests, static build, the one
build-output test, and 2 Playwright tests. The Python formatter, linter, and
type check passed; its full-suite count remains attributed only to pane 1 as
stated above.
