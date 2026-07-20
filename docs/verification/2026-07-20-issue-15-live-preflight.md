# Issue #15 Live Verification Preflight

Date: 2026-07-20

## Scope and current result

This is fail-closed evidence for the pinned 30-case live Verification experiment. The current create-only preflight is `BLOCKED`; neither baseline nor candidate started. This is a provenance and workflow gate, not a product-quality failure or live quality claim.

## Verified repository and experiment identities

- Evaluation Plane branch: `feat/issue-15-live-verification`
- Evaluation Plane HEAD before the next authorized commit: `c4e5d900fa645025763e74f23204cfb6e3bb988a`
- Evaluation Plane state: dirty with the reviewed AX boundary adaptation; not yet an immutable producer SHA
- AX repository: `/Users/astralpig/portfolio/AX_portfolio`
- AX commit: `a5391ae8aa2b0d1342809f3599283b7759d6e4e3`
- AX state: clean, exact match with merged PR #31
- dataset: `braincrew-evaluation-dataset@1.0.0`
- dataset digest: `sha256:7fb0b58c5ad7c242696bcaef13773eb5dc6358e8127219fa7dc65c19c7a5d71b`
- Verification cases: exactly `30`
- candidate plan: `candidate-plan-v1`
- baseline: `top_k=5`, `evidence_limit=3`
- candidate: `top_k=5`, `evidence_limit=5`

## AX local/test environment

AX was started from the exact pinned commit in isolated local Docker services. PostgreSQL, Redis, Neo4j, ClamAV, the worker, and the API all reported ready. Only the repository's official synthetic B-prime seed was installed; no private document, credential value, bearer token, or raw secret was written to a Braincrew artifact. Embeddings used the deterministic local fake provider. The configured OpenAI answer credential was present, but its value was neither printed nor persisted.

The direct Adapter capability check against `http://127.0.0.1:18000` succeeded for:

- `GET /health/ready`;
- `GET /openapi.json`;
- `GET /v1/evaluation/corpus-identity`;
- `GET /v1/evaluation/attachments/{attachment_id}/parse-observation` path discovery;
- the existing retrieval, answer, and source-text operations.

The updated `ax-sut-http-v1` contract mirrors the strict AX response schemas for parse observation and corpus identity. Contract tests reject unknown fields, malformed digests, and ragged tables without retrying. No actual parse observation was claimed because the seeded corpus does not contain a reviewed attachment mapping for the six Verification parsing cases.

## SUT-verified corpus and execution configuration

Under local/test role `HRPractitioner`, AX returned:

- corpus ID: `ax-visible-retrieval:11111111-1111-1111-1111-111111111111`
- corpus version: `retrieval-inventory-v1`
- corpus digest: `sha256:e1d2c986edb048a8afd893fea7bc5eb31bdd9f56257cc36e3bd2e60be66fde9b`
- visible inventory: `119` records
- contributing version: `bprime-2026-07-04`
- record kinds: `44` evidence spans, `31` operational summaries, and `44` source chunks

The frozen answer configuration was derived from the executable pinned AX code, not guessed:

- prompt ID: `ax-answer-instructions-v1`
- prompt digest: `sha256:fb2b7b41b4fc6730c9a4c58912e23f69198d05c947e4579b3f7f134174840fd6`
- prompt digest input: canonical JSON containing both outputs of `AnswerGenerationRuntime._instructions(reference_only=False|True)`
- model provider/name: `openai` / `gpt-5.4-mini`
- model parameters: `{"store": false}`

## Create-only preflight and replay

The installed CLI ran with the exact repository, authority, corpus, prompt, and model identities above:

```bash
uv run braincrew-eval preflight-live \
  --manifest datasets/dataset_manifest_v1.json \
  --output-dir /tmp/braincrew-issue15-final-preflight.7OhjQJ \
  --preflight-id issue-15-a5391ae8-final-precommit-20260720
```

It returned exit `2`, wrote a create-only `BLOCKED` artifact, and replay returned exit `0` with the same logical digest:

```text
sha256:75c1a31a6c81b3840f8244e1e68131e932d01670227b431451cf91059d11386e
```

The formal artifact contains one blocker because preflight intentionally stops before HTTP capability discovery when its own producer is dirty:

```text
LIVE_EVALUATION_PLANE_DIRTY
```

Required action: commit the reviewed Issue #15 implementation so baseline and candidate can name the same immutable Evaluation Plane SHA.

## Corpus provenance blocker discovered by direct capability review

The AX endpoint proves the B-prime corpus identity, but it does not prove that corpus is the frozen 30-case Verification corpus. The dataset expects reviewed `synthetic-rule-*`, EvidenceSpan, retrieval identity, grounded proposition, and parsing attachment mappings. AX reports only `bprime-2026-07-04` as a contributing version, and the isolated seed has no reviewed attachment mapping for the six parsing Verification cases.

The preflight contract therefore adds typed blocker `LIVE_CORPUS_DATASET_PROVENANCE_MISMATCH`. After the Evaluation Plane becomes clean and HTTP discovery runs, the current AX seed must remain `BLOCKED` until a reviewed public or synthetic AX-visible corpus is mapped to `braincrew-evaluation-dataset@1.0.0`. Results must not be inferred from the B-prime corpus or fixture observations.

## No-claim boundary

The 30-case baseline, candidate, artifact replay, comparison gates, critical-failure review, and provenance approval were not executed because preflight is not `READY`. No latency, token, cost, score, failure, comparison, or candidate-superiority claim exists. Calibration, dashboard behavior, Issue #13 gate meaning, AX product behavior, and Agent trajectory evaluation remain unchanged.

## Resume conditions

1. finish ticket-level Standards and Spec review plus repository verification;
2. cross the Git Lifecycle Proposal Gate and create the reviewed local commit;
3. provision and review an AX-visible public or synthetic corpus mapped to every frozen Verification case, including parsing attachment identities;
4. rerun a new create-only preflight from clean Evaluation Plane and AX commits and require `READY`;
5. only then run and replay baseline and candidate, compare them, and manually review critical failures and provenance.

Issue #15 remains open until those conditions and the full live evidence path are complete.

## Ticket review and final local verification

Standards review found no unresolved code blocker. The change reuses the existing pinned Adapter, strict Pydantic models, bounded retry policy, create-only result store, repository-state capture, and replay path; it adds no dependency and changes no AX behavior. Review-driven TDD additionally sealed the new nested corpus evidence before digest publication.

Spec review found one intentional external blocker, not a code defect: the current B-prime seed has no reviewed mapping to the 30-case dataset. The new typed blocker prevents a false READY result. The complete Issue #15 live acceptance criteria remain incomplete until a dataset-aligned corpus is provisioned and the full pair runs.

Fresh local evidence:

- `uv sync --frozen --all-groups` — 29 packages checked;
- `uv run ruff format --check .` — 43 files already formatted;
- `uv run ruff check .` — all checks passed;
- `uv run mypy` — no issues in 43 source files;
- `uv run pytest -q` — `220 passed in 11.56s`;
- `git diff --check` — passed;
- targeted Adapter/live-preflight/CLI suites — `28 passed`;
- create-only preflight exit `2`, replay exit `0`, identical logical digest;
- direct capability review — all six operations available, prospective blockers exactly `LIVE_CORPUS_DATASET_PROVENANCE_MISMATCH` and `LIVE_EVALUATION_PLANE_DIRTY`.

GitHub remains unchanged: Issue #15 is open; draft PR #29 is open, mergeable, and `CLEAN` at remote head `c4e5d900fa645025763e74f23204cfb6e3bb988a`. Its description still names the superseded AX SHA and old endpoint blockers, so any later PR edit must cross the separate Git Lifecycle Proposal Gate.
