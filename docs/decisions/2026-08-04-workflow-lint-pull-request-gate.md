# Workflow linting is a pull-request control for main-only publication

**Status:** Cycle 10 implementation complete; hosted CI validation pending

## Decision

Add a `workflow-lint` job to the existing `Quality gates` workflow. That
workflow already runs for pull requests, so the job checks every GitHub Actions
workflow in `.github/workflows/` before a change can reach `main`. It does not
modify the `pages-deploy.yml` trigger, permissions, jobs, or deployment path.

The job checks out the repository and runs the official
`rhysd/actionlint` v1.7.12 OCI image by immutable manifest digest. With no file
arguments, actionlint discovers and validates all workflow files in
`.github/workflows/`, including YAML, workflow schema, expressions, and shell
snippets in `run:` steps. The mounted checkout is read-only.

The same Docker command is recorded in `AGENTS.md`, the repository's operational
command contract, so a contributor with a running Docker daemon can run the
identical image before opening a pull request. It is deliberately not in the
recruiter-facing README `## Running it` sequence, whose `uv` commands have no
Docker prerequisite. The local environment used for Cycle 10 has no running
Docker daemon; that is an environment limitation, not a reason to leave the
gate untestable. The checksum-verified official v1.7.12 release binary proved
the YAML, workflow-schema, and expression rules only. The image additionally
bundles `shellcheck` and `pyflakes`, so that binary-only proof did not exercise
shell or Python checking inside workflow `run:` steps.

## Rejected alternatives

- **A third-party GitHub Action wrapper.** It would require a SHA pin under the
  repository convention and would add wrapper behavior without giving local
  contributors the exact CI command.
- **Download an actionlint binary during every CI run.** Both that approach and
  `docker pull` need the network; the distinction is integrity. The selected
  OCI manifest is content-addressed by digest and cannot silently change,
  whereas a download URL alone does not provide that immutable identity.
- **Lint only `pages-deploy.yml`.** The production-only workflow exposed the
  gap, but every workflow is part of the same repository control plane.
- **Change the Pages workflow to make it runnable on pull requests.** Its
  main-only trigger is a publication safeguard; static linting supplies the
  pull-request validation seam without reopening public deployment.

## Failure modes and limits

- A Docker daemon unavailable to a local contributor prevents the documented
  local invocation. Hosted Ubuntu Actions runners supply Docker; the CI job is
  still the authoritative merge gate.
- The manifest digest prevents image-tag drift but intentionally does not
  auto-upgrade actionlint. Updating it requires a reviewed version decision and
  the same failure-and-restore control proof.
- actionlint validates workflow structure, expressions, and shell syntax. It
  cannot prove an action tag exists remotely or prove a hosted Pages deployment
  succeeds; those are separate checks. Pane 3 measured
  `actions/checkout@v99` passing this gate with exit status 0, validating the
  action-tag limit rather than leaving it as an unexamined caveat.
- Pane 1 measured that actionlint exits 3 for an empty directory and for a
  workflow directory with no `.git` ancestor. A bad mount or moved checkout
  therefore fails closed instead of producing the vacuous pass this ticket
  prevents.

## Validation evidence

- GitHub's v1.7.12 release listed the Darwin arm64 binary and checksums file.
  The downloaded archive's SHA-256 matched the published checksum before its
  temporary binary ran. The binary reported `1.7.12` and passed the unmodified
  workflow directory.
- A deliberate `malformed: [` line in tracked `pages-deploy.yml` failed with
  `could not parse as YAML: did not find expected node content [syntax-check]`
  and exit status 1. `git checkout -- .github/workflows/pages-deploy.yml`
  restored the file; `git status --short` then named only this ticket's
  `python-ci.yml`, `AGENTS.md`, `README.md`, and decision record changes.
- A deliberate unterminated `${{ steps.deployment.outputs.page_url` expression
  in that same tracked file failed with `unexpected EOF while lexing expression
  [expression]` and exit status 1. The same explicit `git checkout --` restore
  again removed `pages-deploy.yml` from status, and actionlint then passed.
- The pinned frontend gates passed: dependency installation; Prettier; ESLint;
  TypeScript; 3 Vitest files / 9 tests; static build; the one build-output test;
  and 2 Playwright tests. Ruff formatting and lint, and mypy, passed; the
  separately captured full Python footer was `613 passed in 41.07s`.
- The local Docker command could not run in Cycle 10 because this machine's
  Docker daemon is unavailable. The hosted CI job uses the same digest-pinned
  official image; its hosted execution remains integration evidence to obtain.
- `git diff --check` alone does not inspect newly untracked files, so the final
  verification also uses explicit no-index whitespace checks for each changed
  file.
- Cycle 12 adds an acceptance test that extracts the actionlint image reference
  from `AGENTS.md` and `python-ci.yml` and requires exact equality. Its
  deliberate red-to-green mutation proves the CI and documented local command
  cannot silently drift.

## Follow-up questions

- A future actionlint version update must re-check both the OCI manifest digest
  and the local Docker command before changing the CI image.
- Pages settings and the public deployed URL remain outside this control; Issue
  #150 still owns browser validation of the hosted site.

## Cycle 12 evidence correction and parity control

Pane 1's Cycle 12 inspection measured that the image includes `shellcheck` and
`pyflakes`, while bare `actionlint` on this machine silently accepted a genuine
bash syntax error because neither companion tool was on `PATH`. The Cycle 10
release-binary control proof therefore covered YAML, workflow-schema, and
expression checks only; it did not prove the image's shell or Python `run:`
checking. This corrects the earlier false equivalence without weakening the CI
gate, whose image is strictly stronger.

Pane 1 also measured exit status 3 for both an empty directory and a workflow
directory without a `.git` ancestor. This rules out a vacuous green result from
a broken mount or moved checkout. Pane 3 separately measured an
`actions/checkout@v99` reference exiting 0, confirming that actionlint does not
verify action tags remotely.

`README.md` no longer carries the Docker invocation; its running sequence is a
Docker-free `uv` narrative. `AGENTS.md` remains the one operational command
contract and the new acceptance test requires its digest-pinned image reference
to equal the reference in `python-ci.yml`. Changing the final digest character
in `AGENTS.md` produced the test's explicit assertion failure; after
`git checkout -- AGENTS.md` restored that temporary mutation, the intended
command block was reapplied and the test passed. The Cycle 12 frontend gates
passed, and the full Python suite reported `614 passed in 41.01s`.
