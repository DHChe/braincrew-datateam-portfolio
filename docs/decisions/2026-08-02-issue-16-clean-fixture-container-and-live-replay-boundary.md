# Locked: the clean container validates committed fixtures, not owner-held published-live artifacts

Date: 2026-08-02
Status: locked
Implements: [Issue #16](https://github.com/DHChe/braincrew-datateam-portfolio/issues/16), except its
published-live-artifact replay criterion, which remains blocked

## 1. Measured boundary

Issue #16 requires a clean Docker execution path, named CI validation, a clear replay-versus-rerun claim
boundary, and no committed credentials or sensitive data. It also requires one-command deterministic
replay of published live artifacts. Those artifacts are owner-held outside this repository pending a
publication decision. They are not a substitute fixture, build input, or CI secret.

Issues #13 and #14 are closed. Issue #15 remains open, so no fresh live provider/SUT run belongs in this
cycle. The container and CI can therefore validate only the committed fixture plane without inventing a
live-equivalence claim.

## 2. Decision

`Dockerfile` pins Python 3.12 and `uv`, synchronizes the lockfile with `uv sync --frozen --all-groups`,
and runs the Python format, lint, type, full-suite, and Issue #6 fixture gates. `.dockerignore` excludes
local Git metadata, environment files, Python caches and bytecode, and dashboard `.next`/`out` build
outputs at every depth, from the build context. It also carries an `ax-live-verification-evidence/`
pattern, but that is defensive rather than effective: the directory lies outside the repository and so
was never in the build context. The documented run
has neither host volume mounts nor runtime network access.

The image intentionally does not install Bubblewrap. The source supports it on Linux, but Docker's default
namespace policy rejects Bubblewrap's user-namespace creation. With no `bwrap`, three authoring-boundary
tests are explicitly skipped; with it, those same tests fail. This is a bounded platform limitation, not a
reason to add a privileged or security-relaxed container run.

The fixture acceptance test reads Git provenance. Instead of importing the host `.git` directory, the
image initializes an internal source snapshot after copying only the allowed context. Any artifact made
inside that image is ephemeral fixture evidence; its synthetic Git identity is not a published commit
claim.

## 3. CI scope

The Python workflow names the full suite, the ten-test Issue #6 fixture benchmark, and the focused
fixture replay-digest check separately. A container job runs the fixture-only image without a host mount;
the existing frontend job retains dashboard format, lint, type, test, static-build, and browser-smoke
checks. A Gitleaks job scans tracked history for secrets and credential-like material.

These YAML steps are defined locally but are not described as passing until a pull request runs them.
They do not validate the external published-live artifacts.

## 4. Claim boundary

Replaying a stored artifact can recompute its logical metrics and gate decision from its fixed bytes. A
fresh live SUT/provider rerun occurs at a different time against mutable external behavior and produces a
new artifact. It is useful new evidence, never byte-identical reproducibility.

## 5. Rejected alternatives

- **Copy or commit the owner-held live artifacts.** Publication is an owner decision; copying would evade
  the review boundary and violate this cycle's hard scope.
- **Bind-mount a checkout or the external evidence directory.** It makes local state or unpublished
  evidence a hidden runtime input, so the resulting container is not clean verification.
- **Copy `.git` into the image.** It lets fixture provenance depend on developer-specific history and
  working metadata rather than the declared image context.
- **Call a fresh live rerun identical reproduction.** Only replay of a stored artifact can make an
  identity claim; live execution can at most produce a separately versioned measurement.

## 6. Validation evidence

On 2026-08-02, `docker build --no-cache --tag braincrew-evaluation-fixture:cycle180-final .`
completed and `docker run --rm --network none braincrew-evaluation-fixture:cycle180-final` reported
`71 files already formatted`, `All checks passed!`, `Success: no issues found in 71 source files`,
`595 passed, 3 skipped`, and `10 passed`. The three skips are the documented authoring-boundary cases
with no supported OS sandbox backend.

The image-local Git snapshot is load-bearing: deleting `.git` immediately after its synthetic commit made
the isolated run fail `30` tests (`565 passed, 3 skipped`) on Git-provenance checks. The Dockerfile was
then restored byte-for-byte to SHA-256 `77c883f08179db35ced106dfaefa71b1b146830312e3f8def979eebc8332f856`.
Installing Bubblewrap was also rejected empirically: its direct `--unshare-all` probe exited nonzero
because Docker's default kernel policy forbids unprivileged user namespaces. No privilege or security
policy exception was requested. GitHub Actions results remain pending a pull request. No AX container,
Docker Compose invocation, live artifact copy, or host-repository Git lifecycle write is part of this
decision.

## 7. Scope boundary

This decision adds a Dockerfile, Docker ignore rules, CI definitions, operational documentation, one
append-only status entry, and defense card D30. It does not change benchmark definitions or `src/`,
access AX, rerun calibration, execute a live SUT, or alter the publication status of any artifact.
