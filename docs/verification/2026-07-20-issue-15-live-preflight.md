# Issue #15 Live Verification Preflight

Date: 2026-07-20

## Scope

This is a fail-closed preflight result for the pinned 30-case live Verification experiment. It is not a baseline run, candidate run, comparison result, product-quality failure, or live quality claim.

## Verified identities

- Evaluation Plane base commit: `e33de765dc54ac76159f249525456d5ab4e63667`
- Evaluation Plane state: dirty and uncommitted during preflight implementation; not publishable live provenance
- AX repository commit: `c318b2192006bdb36a5bd5b3a2bc403425b45701`
- AX repository state: clean and exact match with the pinned `ax-sut-http-v1` contract
- dataset: `braincrew-evaluation-dataset@1.0.0`
- dataset digest: `sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b`
- Verification cases: exactly `30`
- candidate plan: `candidate-plan-v1`
- baseline: `top_k=5`, `evidence_limit=3`
- candidate: `top_k=5`, `evidence_limit=5`

## Current-environment preflight

The installed CLI command was executed with only the local pinned AX repository path supplied:

```bash
AX_REPOSITORY=/Users/astralpig/portfolio/AX_portfolio \
  uv run braincrew-eval preflight-live \
  --manifest datasets/dataset_manifest_v1.json \
  --output-dir /tmp/braincrew-issue15-final.bI45ot \
  --preflight-id issue-15-final-environment
```

The command returned exit `2` and wrote a create-only `BLOCKED` artifact. Replay returned the same state and logical digest:

```text
sha256:9d78a9c4713fca610588b6477ec4031dcdfdab5262361ec8a578fd01c02486d1
```

The artifact contains no bearer token or inferred credential value.

A second create attempt returned exit `2` and preserved the original artifact bytes at file SHA-256 `03046a60fc929dbd4828e3d295a656daba093be6c974382d8772edd9b406d8dd`.

## Exact blockers

Current live authority and fixed execution identity were unavailable for:

- `AX_BASE_URL`
- `AX_TENANT_ID`
- `AX_USER_ID`
- `AX_ROLES`
- `AX_CORPUS_ID`
- `AX_CORPUS_VERSION`
- `AX_CORPUS_DIGEST`
- `AX_PROMPT_ID`
- `AX_PROMPT_HASH`
- `AX_MODEL_PROVIDER`
- `AX_MODEL_NAME`
- `AX_MODEL_PARAMETERS_JSON`

The Evaluation Plane worktree was also dirty because the reviewed Issue #15 preflight implementation had not crossed the Git Lifecycle Proposal Gate. A clean committed Evaluation Plane SHA is required to make both live runs reproducible.

Because those blockers are evaluated before network access, this preflight did not probe current AX readiness or OpenAPI. It makes no current endpoint-availability claim.

## Known capability boundary

The earlier live smoke against the same pinned AX SHA recorded:

- `parse`: unavailable with `AX_PARSE_OBSERVABILITY_UNAVAILABLE`
- corpus identity: not verified by the SUT with `AX_CORPUS_IDENTITY_NOT_EXPOSED`

Controlled Issue #15 tests prove that a capability manifest with those values yields `LIVE_REQUIRED_OPERATION_UNAVAILABLE` and `LIVE_CORPUS_IDENTITY_UNVERIFIED`. These are separate from credentials: a complete 30-case run still requires a separately reviewed AX observability and corpus-verification boundary. No AX behavior was changed during this work.

Ticket review also proved that nested model/evaluator/Adapter/capability mappings cannot be mutated after the digest is returned, non-finite model parameters are invalid, missing operations and capability-manifest SUT SHA drift fail closed, create-only collisions preserve the first artifact bytes, and modified artifact content cannot replay under the stored digest.

## No-claim boundary

Neither the baseline nor candidate began. Therefore there are no case-level live artifacts, quality or safety scores, latency/token/cost measurements, failure analysis, comparison-gate result, or manual critical-failure/provenance approval. Fixture evidence and the Issue #14 dashboard do not substitute for this missing live evidence.

## Resume conditions

Before either live run starts:

1. review and commit the Evaluation Plane preflight implementation;
2. supply an authorized live AX endpoint and synthetic tenant/user/role authority;
3. freeze the exact corpus, prompt, and model identities and parameters;
4. provide required parse observability and SUT-verifiable corpus identity without changing AX during the comparison;
5. execute a new create-only preflight and require state `READY`.

Only then may the 30-case baseline execute, followed by the compatible candidate, artifact replay, Issue #13 comparison gates, and manual critical-failure/provenance review.

## Final local verification

The reviewed preflight slice passed the required fresh local gates:

- `uv sync --frozen --all-groups`
- `uv run ruff format --check .` — 43 files formatted
- `uv run ruff check .`
- `uv run mypy` — 43 source files
- `uv run pytest -q` — `218 passed in 10.77s`
- `git diff --check`

The 30-case baseline, candidate, comparison gate, and manual critical-failure/provenance review were not executed because the mandatory preflight is `BLOCKED`. This is an explicit verification gap, not a passing or failing live result.
