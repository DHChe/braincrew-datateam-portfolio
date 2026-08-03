# Submission security maintenance decision

Date: 2026-08-03

## Decision

Advance only the bounded vulnerable dashboard dependency surface before portfolio submission: Next.js and
`eslint-config-next` from `16.2.10` to `16.2.12`, transitive PostCSS from `8.5.10` to `8.5.25`, and
sharp from `0.34.5` to `0.35.3`. Keep npm at `11.12.1`, make CI install that exact version, and
preserve the static-export and readonly evidence-projection contracts.

## Why this decision was necessary

A clean install with the declared npm version reported four high-severity findings. One was in the
direct Next.js dependency and the others were in transitive build dependencies. A portfolio that
claims evidence-first verification cannot knowingly leave that measured state unexplained or rely on
an older audit recorded under a different npm runtime.

## Rejected alternatives

- Ignore the findings because the dashboard is statically exported. Rejected because build
  dependencies execute on developer and CI machines even when no application server is deployed.
- Upgrade the complete frontend stack or change package managers. Rejected because the evidence
  supports a bounded patch repair, while a broader migration would expand submission risk without
  improving the evaluation claim.
- Lower the declared npm engine to match a convenient default. Rejected because the project already
  selected and verified npm `11.12.1`; CI should satisfy the contract instead of weakening it.

## Trade-offs and failure modes

The lockfile becomes larger and sharp's platform packages move to a newer line. Sharp `0.35.3` is
outside Next.js `16.2.12`'s declared optional dependency range `^0.34.5`; this is a measured override,
not an upstream compatibility claim. The current application does not import `next/image`. The principal
failure modes are a future image path depending on that unsupported range, a platform-specific native
package installation failure, or a patch release changing static export behavior. They are bounded for
the current application by a clean pinned install, npm audit, no-`next/image` search, Linux container
build, static Next.js build, unit tests, and Playwright smoke test.

## Verification evidence

- `npx --yes npm@11.12.1 audit --audit-level=high`: zero known vulnerabilities.
- `rg -n "from ['\"]next/image['\"]|<Image\\b" dashboard tests`: no application import or component use;
  the generated `dashboard/next-env.d.ts` type reference is not an application image path.
- formatting, ESLint, TypeScript, eight Vitest tests, static export, and two Playwright tests: pass.
- `docker build --no-cache` and `docker run --rm --network none`: pass; 607 Python tests pass and the
  three OS-capability sandbox tests skip as designed, followed by 11 fixture-gate tests passing.
- Hosted GitHub Actions: not yet tested because no pull request contains this local change.

## Interview defense

The important choice was not “always use the newest package.” It was to reproduce the finding with the
declared toolchain, repair the smallest supported version surface, and rerun the checks that could catch
behavioral or platform regressions. The evaluation semantics and dashboard evidence boundary did not
change.
