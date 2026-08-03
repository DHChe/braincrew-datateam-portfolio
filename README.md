# Evidence-First RAG Evaluation Plane

An evidence-first evaluation plane for a Korean HR/labor RAG system, originally built as a
Braincrew Data Team portfolio case study.

It treats [AX_portfolio](https://github.com/DHChe/AX_portfolio) as a **Subject Under Test (SUT)** — a
separate, still-evolving product measured across a versioned HTTP contract — and it is built on one
rule: **claim only what was executed and reproducibly verified.**

That rule is why this README tells you what has *not* been measured before it tells you what has.

---

## Three-minute reviewer path

1. Read **The result worth reading first** below: the central result is a justified refusal to issue
   an answer-quality verdict when the evidence coverage is zero.
2. Scan [How it works](#how-it-works) and the [repository map](#repository-map) to see the boundary
   between the Evaluation Plane and the evolving AX product under test.
3. Run the offline 100-case fixture and deterministic replay in [Running it](#running-it). This proves
   the stored logical result can be recomputed; it is not presented as a fresh live benchmark.
4. Use the [three-minute demonstration script](docs/submission/three-minute-demo.md) for the shortest
   guided walkthrough, including what each step does and does not prove.

The author used AI coding agents for most implementation work and owned the problem framing,
evaluation scope, agent orchestration, review criteria, correction decisions, and claim boundaries.
That division of work is disclosed because the portfolio is evidence of evaluation judgment and
domain-to-system translation, not a claim of unaided code authorship.

---

## The result worth reading first

Across three recorded live measurement sessions at `1ead133` → `3bb27f8` →
`5b0f5f2`, this plane has repeated one honest result: when no grounded case
supplies answer-quality evidence, it refuses to manufacture an answer-quality
verdict.

The 2026-07-31 live capture first surfaced that refusal. On 2026-08-03, an
owner-authorized same-commit re-capture put all 30 Verification cases at AX
`5b0f5f2`: parsing reached `COMPLETED` for 6 of 6 cases and retrieval reached
`COMPLETED` for 9 of 9. That removes the earlier parsing-partition barrier; it
does not make an AX answer-quality claim.

**The grounded evaluation still refuses to produce a quality verdict, and that
refusal is the finding.** In each unpublished 2026-08-03 same-commit artifact,
thirteen of fifteen grounded cases returned HTTP 200 after the provider answer
was discarded under `citation_contract_violation=True`; all thirteen have
`unsafe_provider_output=False`, so they are not safety blocks. The two remaining
answer paths are abstention/review paths and also provide no usable grounded
answer-quality evidence. Both same-commit runs therefore remain `INVALID` with
`citation_precision_cases` and `claim_support_cases` at **zero**.

The count is run-specific, not a repository-wide aggregate. The published
2026-07-31 [capture](evidence/capture-baseline-2026-07-31/issue-15-phase1-baseline-2026-07-31.capture-manifest.json)
and [evaluation](evidence/eval-baseline-2026-07-31/issue-15-phase1-baseline-2026-07-31.json)
artifacts record twelve discarded answer paths under the older
`failure_reason="unsafe_provider_output"` label. The 2026-08-03 thirteen-and-zero
predicate result belongs to owner-held artifacts that are not published in this repository; their
exact external storage path is intentionally omitted from this reviewer-facing page. The count changed from twelve to
thirteen between runs, but neither run supplies citation-precision or
claim-support evidence, so the conclusion did not change.

### Upstream defects this plane found

This evaluation plane surfaced two defects in its SUT, and both are now fixed
upstream:

- [AX #60](https://github.com/DHChe/AX_portfolio/issues/60) (**CLOSED**) used one
  `failure_reason` string for unrelated citation-contract and safety causes, so a
  consumer could report a safety event when the answer instead failed grounding.
- [AX #61](https://github.com/DHChe/AX_portfolio/issues/61) (**CLOSED**) left a
  discarded provider answer invisible in logs; its capture window had 294 lines,
  zero errors or warnings, and HTTP 200 for every request.

The upstream [fix `3bb27f8`](https://github.com/DHChe/AX_portfolio/commit/3bb27f870d244fbc8debba91eb408e825caa9e03)
closes both issues. The current SUT pin, `5b0f5f2`, descends from that fix, whose
additive predicate fields make the 2026-08-03 observation legible as thirteen
citation-contract violations and zero safety blocks instead of one ambiguous
failure label.

No comparison artifact exists: `comparison.py` requires both baseline and
candidate runs to be `COMPLETED`, while both are `INVALID`. The recruiter-facing
dashboard consequently keeps its golden fixture rather than receiving made-up
live comparison data; it now labels that fixture **“Fixture evidence — not a
live AX verification,”** and its [end-to-end assertion](tests/frontend/e2e/dashboard.spec.ts)
pins both that label and the fixture-only comparison boundary.

**The parsing partition was a real barrier, but the grounded failure was already
in the 2026-08-02 artifact and was misattributed.** The new run corrects that
record: re-pinning and re-capturing cannot fix this SUT answer-path behavior. The
full measured table and correction are in the
[same-commit run decision](docs/decisions/2026-08-03-same-commit-30-case-run-and-grounded-coverage-correction.md).

---

## What is measured, and what is not

| | Offline / fixture | Live SUT |
| --- | --- | --- |
| Parsing | 20-case evaluator, completed | **COMPLETED** — 6 of 6 Verification heading sequences at one SUT commit; zero spans are not a parser-quality score |
| Retrieval | 30-case evaluator, completed | **COMPLETED** — 9 of 9 Verification cases at that same commit; earlier 9-case metrics remain a separate measurement |
| Grounded answer / visibility / abstention | 50-case evaluator, completed | **unmeasurable** — both same-commit runs are `INVALID` with zero answer-quality coverage, see above |
| Operational (latency, cost) | contract and comparison paths exercised | latency captured; **provider cost incurred and unmeasured** |
| Comparison and release gates | fixture pair compared, gate decision reproduced | **no live comparison artifact exists** — compatible same-commit runs are both `INVALID` |
| Agent trajectory evaluation | — | **planned, not implemented, not claimed** |

### Capability status matrix

The table above describes measurement detail. This matrix separately records
whether a capability was executed and verified, never executed, or only reserved
for future work.

| Capability | Status | Executed evidence or boundary |
| --- | --- | --- |
| Parsing | **evaluated** | 6 of 6 `COMPLETED` in the unpublished 2026-08-03 `run-2026-08-03-30case/` artifacts; zero spans are not a parser-quality score. |
| Retrieval | **evaluated** | 9 of 9 `COMPLETED` in the same unpublished 2026-08-03 artifacts. |
| Grounded answer, visibility, and abstention | **evaluated; no answer-quality result** | Both unpublished 2026-08-03 artifacts are `INVALID` with zero citation-precision and claim-support coverage. |
| Operational latency | **evaluated** | Captured in the unpublished 2026-08-03 baseline and candidate artifacts. |
| Provider cost | **not evaluated** | The live artifacts record cost as unmeasured; no cost value is claimed. |
| Stored-artifact replay | **evaluated** | The published [2026-07-31 capture](evidence/capture-baseline-2026-07-31/issue-15-phase1-baseline-2026-07-31.capture-manifest.json) and [evaluation](evidence/eval-baseline-2026-07-31/issue-15-phase1-baseline-2026-07-31.json) can be replayed; this does not validate live AX. |
| Live comparison and release decision | **not evaluated** | No live comparison artifact exists because both compatible 2026-08-03 runs are `INVALID`. |
| Agent trajectory evaluation | **planned — not implemented, not claimed** | The [scope-lock decision](docs/decisions/2026-07-18-evaluation-scope-and-skill-flow-lock.md) reserves `TRJ-*` as an unused failure-taxonomy code; no source-level trajectory extension point, capability, run, or artifact exists. |

Explicitly **not** claimed anywhere in this repository:

- any answer-quality result against live AX;
- a live comparison artifact, answer-quality verdict, or release decision from the
  same-commit 30-case run;
- any live release decision — the dashboard's `PASS` is fixture evidence with placeholder commit
  SHAs, and the page says so;
- a fresh live rerun as byte-identical reproducibility: the repository-resident stored artifacts can be replayed
  from fixed bytes, but a new SUT or provider invocation is a new measurement at a new time;
- Agent evaluation. The [scope-lock decision](docs/decisions/2026-07-18-evaluation-scope-and-skill-flow-lock.md)
  reserves the unused `TRJ-*` failure-taxonomy code; it does not introduce a source-level trajectory
  extension point, capability, run, or artifact.

---

## How it works

```
dataset (100 synthetic cases, frozen)
        │
        ▼
SUT adapter ──HTTP──▶ AX_portfolio          preflight: health, corpus identity,
  ax-sut-http-v1        (separate repo)     role visibility, parse observability
        │
        ▼
normalized observations ──▶ evaluators ──▶ run artifact (canonical JSON)
                            parsing          canonical digest, create-only
                            retrieval               │
                            grounded                ▼
                            operational        replay ──▶ recompute and compare
                                                    │
                                                    ▼
                          baseline ⇄ candidate comparison (JSON + Parquet)
                                     │
                                     ▼
                          three ordered release gates ──▶ PASS / FAIL / INVALID
```

Concretely: **15 [CLI commands](src/braincrew/cli.py)**, **four evaluator families** (parsing, retrieval, grounded answer,
operational), all four versioned in the live capture's provenance, a **frozen HTTP adapter contract**
(`src/braincrew/ax-http-v1.yaml`) pinned to a specific SUT commit with per-operation schema digests
and a mocked contract suite, a create-only artifact store emitting canonical JSON — with Parquet
alongside it for comparison evidence — three ordered release gates, corpus sealing and qualification
receipts, a statically exported dashboard, and **610 tests**.

**Every artifact is create-only, and every artifact the `replay` command accepts re-derives its
stored digest through committed code and refuses on any mismatch.** One class — the corpus
authoring-independence receipt — is create-only but has no replay path yet. The unrepeatable one — the live
capture, whose provider calls cost money and cannot be reproduced — carries a deliberately
[enumerated replay contract](docs/decisions/2026-08-01-live-capture-replay-and-its-enumerated-claim.md):
six named conditions, and an explicit statement of what it does *not* establish.

**The plane fails closed.** A run whose evidence is insufficient becomes `INVALID` rather than
producing a number; a comparison whose two runs are not provably compatible refuses to decide.

### Dataset

Synthetic, CC0-1.0, reviewed, sealed and qualified against its own provenance receipt. Version
`3.0.0`, 100 cases, digest `sha256:c07c5619…`, split 70 Calibration / 30 Verification, allocated
20 parsing / 30 retrieval / 40 grounded answer / 10 visibility-abstention.

Its source corpus was authored **evaluation-blind** — inside an OS capability sandbox with denied
capability classes, leaving an independence receipt. That property attaches to the corpus, which the
dataset then binds to; the dataset manifest itself records `synthetic`, `CC0-1.0`, `reviewed`.

The reviewed [evaluation dataset](datasets/DATASET_CARD_V3.md) uses source material declared
`synthetic` and `CC0-1.0` in its [manifest](datasets/dataset_manifest_v3.json), rather than customer,
employee, or company documents. The [four published evidence files](docs/decisions/2026-08-02-published-live-evidence-replay.md)
were separately approved with no redaction, and the [`secrets` CI job](.github/workflows/python-ci.yml)
scans tracked history for secrets and credential-like material.

---

## Running it

```bash
uv sync --frozen --all-groups     # Python 3.12, locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest -q                  # 610 tests
uv run pytest tests/acceptance/test_cli_fixture_gate.py -q
uv run pytest tests/acceptance/test_cli_fixture_gate.py -q \
  -k test_replay_recomputes_the_same_logical_digest_and_gate_decision
```

The dashboard uses the repository-pinned `npm@11.12.1` contract:

```bash
npx --yes npm@11.12.1 ci
npx --yes npm@11.12.1 run format:check
npx --yes npm@11.12.1 run lint
npx --yes npm@11.12.1 run typecheck
npx --yes npm@11.12.1 test -- --run
npx --yes npm@11.12.1 run build
npx playwright install --with-deps chromium
npx --yes npm@11.12.1 run test:e2e
```

The fastest end-to-end demonstration is the offline fixture path — a full 100-case evaluation, then a
replay that must reproduce the same digest:

```bash
demo_dir="$(mktemp -d /tmp/braincrew-demo.XXXXXX)"

uv run braincrew-eval run-dataset \
  --manifest datasets/dataset_manifest_v1.json \
  --parsing-observations tests/fixtures/parsing_observations_v1.json \
  --retrieval-observations tests/fixtures/retrieval_observations_v1.json \
  --grounded-observations tests/fixtures/grounded_observations_v1.json \
  --output-dir "$demo_dir" --run-id demo \
  --sut-sha c318b2192006bdb36a5bd5b3a2bc403425b45701

uv run braincrew-eval replay --artifact "$demo_dir/demo.json"
```

Both print the same `logical_digest`, and the artifact's own provenance records
`execution_mode: fixture` and `sut.executed: false` — it is a determinism demonstration, not a
benchmark. Its recorded SUT SHA differs from the live `5b0f5f2` pin because this is fixture evidence
with its own recorded provenance, not a live AX run.

### Clean, network-isolated container

The clean container uses the locked Python environment and has no host mount. Its build context excludes
local Git metadata, environment files, Python caches and bytecode, and dashboard `.next`/`out` build
outputs at every depth. The `ax-live-verification-evidence/` pattern is defensive only: that directory
lies outside the repository, so nothing was excluded from the context on its account. The fixture
acceptance test receives only an image-local Git snapshot because it checks its own provenance.

```bash
docker build --no-cache --tag braincrew-evaluation-fixture:local .
docker run --rm --network none braincrew-evaluation-fixture:local
```

The image runs the Python format, lint, type, full-test, and Issue #6 fixture gates. It includes the four
owner-authorized stored-live evidence files under `evidence/`, and the Issue #6 replay test exercises
them through the existing CLI path. On Docker's default
Linux namespace policy, the three authoring-boundary tests that require Bubblewrap are explicitly skipped:
installing Bubblewrap makes them fail because the container may not create a user namespace, and this path
does not request privileged or security-relaxed execution. It does not execute AX. The CI workflow has separate named fixture benchmark,
fixture-replay, container, dashboard, and secret-scan steps; the workflow itself remains unverified until a
pull request runs it.

**What the container does reproduce:** a one-command replay of the four reviewed stored-live
artifacts under `evidence/`. It can see them, and the replay test recomputes their stored logical
results through the committed CLI. That is artifact-integrity evidence, not a live-quality or release
claim.

**Two honest limits on reproduction**, both measured and explicitly bounded:

1. **A stored-artifact replay and a fresh live rerun prove different things.** Replay can reproduce the
   stored logical metrics and gate decision from fixed bytes. A live SUT/provider rerun produces a new
   observation at a new time and is never presented as byte-identical reproducibility.
2. **The current `v3` dataset has no complete offline run.** The only committed observation bundles
   are `v1`; running `v3` against them yields `INVALID` with 34 of 100 scored — principally because
   the retrieval queries changed between versions, and additionally on grounded coverage and overall
   dataset coverage. The `v1` path above is a legacy fixture, and its dataset digest is not the frozen
   `v3` digest quoted above.

The container command is intentionally a clean **fixture** reproduction, not a release or live-quality
claim.

---

## Repository map

| Path | What it holds |
| --- | --- |
| `src/braincrew/` | evaluators, SUT adapter, artifact store and replay, comparison, release gates, CLI |
| `datasets/` | frozen dataset manifests and case bundles |
| `dashboard/` | statically exported Next.js dashboard (renders fixture evidence, labelled as such) |
| `docs/decisions/` | locked design decisions, each with rejected alternatives and failure modes |
| `docs/interview/` | defense dossier — every locked decision with its trade-offs and likely questions |
| `docs/status/` | append-only delivery record |
| `docs/superpowers/specs/` | the design specification this release is measured against |

---

## Engineering conventions

- **Independent review and a pre-commit audit before anything lands.** The current
  [claim-to-evidence audit](docs/verification/claim-to-evidence-audit-2026-08-03.md) makes the
  review traceable: it lists each README claim, its primary-evidence category, and any unsupported
  or stale wording.
- **A worker's report is not evidence.** Load-bearing claims are reproduced independently before they
  enter a durable document, and each is labelled measured or inferred with the measurer named.
- **Guards are mutation-verified one clause at a time**, and each row is labelled either new
  protection or a pre-existing guard re-confirmed — because a passing suite proves a test exists, not
  what it protects.
- **Durable records are append-only.** Superseded statements are marked, not rewritten; several
  documents here record the author's own corrected errors for that reason.

---

## Status

First production release is **not complete.** Against the design specification's ten acceptance
criteria:

- **Met (6)** — the dataset freeze and recorded 70/30 digest; metric goldens and boundary tests;
  canonical artifacts reconstructing analytical outputs; Agent evaluation left explicitly unimplemented
  and unclaimed; a clean, network-isolated container replays the four repository-resident
  stored-live artifacts; and the static dashboard build plus sanitized-export boundary pass in the
  local submission audit.
- **Met for fixture evidence only (1)** — reproducible release-gate output with reasons. It remains
  fixture evidence rather than a live AX quality or release claim.
- **Not met (3)** — a live comparison artifact (the compatible same-commit runs are both `INVALID`),
  a complete live Verification run with answer-quality coverage, and evidence linkage for every
  submission claim.

The local submission audit ran the pinned npm 11 toolchain, reported zero known npm-audit
vulnerabilities, built the static dashboard, and passed its unit and browser tests. Hosted CI for these
uncommitted changes remains pending until a pull request exists.

The blocking dependency **for live answer quality** is in the SUT, not here:
thirteen citation-contract violations discard provider answers and the remaining
two grounded paths add no usable quality evidence. A same-commit re-capture
reproduced that behavior rather than fixing it.

Work in progress. **No licence is granted for this repository** — it carries no `LICENSE` file, so the
default applies and all rights are reserved. The evaluation dataset is a separate matter and declares
its own provenance: `datasets/dataset_manifest_v3.json` records `source_type: synthetic` and
`license: CC0-1.0`.

Design decisions, their rejected alternatives and their failure modes are in `docs/decisions/`; the
reasoning behind each is defended in `docs/interview/`.
