# GitHub Pages deployment URL is verified after publication

**Status:** Cycle 15 repair complete; first workflow execution pending

## Decision

The Pages deploy job exposes `steps.deployment.outputs.page_url` as its
job-level `page_url` output. A dependent `smoke` job checks out the reviewed
revision and passes `needs.deploy.outputs.page_url` to
`scripts/verify-deployed-pages.sh`.

The script requires a successful HTTP response from that reported URL, then
checks the exported HTML for the dashboard heading, the byte-exact fixture
boundary `Fixture evidence — not a live AX verification`, and the fixture-only
PASS explanation. It extracts one `_next/static/` reference from the same
document and requires that asset to return a successful response as well. Both
fetches retry three times after five-second delays, including transient HTTP
errors, and each attempt has a 30-second maximum duration. This bounds a hung
endpoint while allowing GitHub Pages edge propagation to settle.

For root-anchored static assets, the script derives the asset origin from
curl's final `url_effective`, not the requested URL. A redirect therefore
checks the asset at the origin that served the verified page.

This keeps the verification tied to the URL returned by `actions/deploy-pages`,
not to a hardcoded repository address. It checks the public static surface
only; it neither contacts AX nor a provider, creates browser state, scores an
answer, or changes a release decision.

## Rejected alternatives

- **Inline the checks in workflow YAML.** A standalone script makes each
  failure mode directly runnable with controlled local HTTP responses, while
  keeping the job focused on passing the deployment-reported URL.
- **Hardcode the canonical Pages URL.** That would permit a green check even
  if the deployment action reported a different target.
- **Normalise or loosely match the fixture boundary.** The em dash is part of
  the visible evidence contract; a byte-exact fixed-string check is required
  to catch its removal or substitution.
- **Change the trigger or concurrency key to run the check elsewhere.** The
  prior main-only publication decision directs that `main` remain the sole
  trigger while `pages-${{ github.ref }}` remains the concurrency key.

## Failure modes and limits

- A failed fetch, a non-2xx final response, a missing required literal, no
  discoverable `_next/static/` reference, or a non-2xx asset response fails
  the smoke job.
- The check proves the served surface is coherent, not that the revision just
  built is already present at every edge: all asserted literals and the
  sampled asset can also exist in a previous deployment.
- The first real execution occurs only after an approved `main` integration.
  Local controlled-response checks prove the script can fail, but they do not
  constitute deployment evidence.
- The script samples one static asset from the deployed HTML. The build-output
  gate remains responsible for checking every emitted page reference.
- The fixture boundary deliberately matches literal UTF-8 bytes. An HTML
  entity such as `&mdash;` therefore fails even if a browser renders the same
  glyph. Protocol-relative asset references and relative references without a
  trailing-slash page URL also resolve incorrectly in the script, but the
  current static export emits root-anchored assets and deploy-pages reports a
  directory URL; both unsupported forms fail closed rather than passing.

## Validation evidence

- The workflow structure is parsed locally to retain one `push` trigger for
  `main`, the existing concurrency key, `deploy.needs == build`,
  `smoke.needs == deploy`, and the job-output-to-input data path.
- Controlled local HTTP responses exercise failures for an unavailable page,
  each required literal, and an unavailable static asset before the first
  hosted workflow run.
- The repository-pinned frontend and Python quality gates, plus workflow lint
  when a Docker daemon is available, are run before integration.

## Follow-up questions

- After approved integration into `main`, inspect the completed smoke job and
  `github-pages` environment, then manually check the reported URL in a
  browser before Issues #151 and #152 change public links.
- Consider passing a content-hashed asset filename from `build` to `smoke` and
  requiring the served HTML to reference it. That would prove deployment
  freshness, rather than the current coherent-surface guarantee.
