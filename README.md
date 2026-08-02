# Braincrew Evaluation Plane

An evidence-first evaluation plane for a Korean HR/labor RAG system.

It treats [AX_portfolio](https://github.com/DHChe/AX_portfolio) as a **Subject Under Test (SUT)** — a
separate, still-evolving product measured across a versioned HTTP contract — and it is built on one
rule: **claim only what was executed and reproducibly verified.**

That rule is why this README tells you what has *not* been measured before it tells you what has.

---

## The result worth reading first

On 2026-07-31 this plane ran its first live capture against an authorized local AX runtime: 24 live
calls, 9 retrieval and 15 grounded-answer.

**The evaluation refused to produce an answer-quality verdict, and that refusal is the finding.**

Twelve of the fifteen grounded cases came back HTTP 200, contract-valid, and carrying
`failure_reason="unsafe_provider_output"` — the provider answer had been discarded and a template
substituted. Every one of them *looks* like a cautious abstention from the outside. An evaluator that
scored the visible answer would have recorded twelve abstentions and computed a quality number from
them.

Instead the run came out `INVALID`, 18 of 30 cases scored, with
`citation_precision_cases` and `claim_support_cases` both **zero** — no case contributed
answer-quality evidence, so no answer-quality claim was published.

Two defects in the SUT were filed from that run:

- [AX#60](https://github.com/DHChe/AX_portfolio/issues/60) — one `failure_reason` string is emitted
  for two unrelated causes (a strict citation-contract failure and a Korean unsafe-advice blocklist),
  so a consumer recording it verbatim reports a safety event for what may be a grounding failure.
- [AX#61](https://github.com/DHChe/AX_portfolio/issues/61) — the discard is logged nowhere. Across the
  capture window the backend produced 294 log lines with zero errors or warnings and every request
  200. An operator watching logs or status codes sees a healthy service.

**A degraded answer path that is invisible to logs, status codes and response shape was surfaced by a
harness that inspects per-case provider metadata.** That is what this project is for.

---

## What is measured, and what is not

| | Offline / fixture | Live SUT |
| --- | --- | --- |
| Parsing | 20-case evaluator, completed | **not evaluated** |
| Retrieval | 30-case evaluator, completed | **Recall@5 = 17/18 (0.9444)**, MRR@10 = 2/3, authority priority 1/1, on the 9 Verification cases |
| Grounded answer / visibility / abstention | 50-case evaluator, completed | **not evaluated** — run `INVALID`, see above |
| Operational (latency, cost) | contract and comparison paths exercised | latency captured; **provider cost incurred and unmeasured** |
| Comparison and release gates | fixture pair compared, gate decision reproduced | **no compatible baseline/candidate pair exists** |
| Agent trajectory evaluation | — | **planned, not implemented, not claimed** |

Explicitly **not** claimed anywhere in this repository:

- any answer-quality result against live AX;
- any live release decision — the dashboard's `PASS` is fixture evidence with placeholder commit
  SHAs, and the page says so;
- a one-command replay of the published live artifacts: those owner-held artifacts remain outside this
  repository, and the clean container documented below validates committed fixture inputs only;
- Agent evaluation. The failure taxonomy reserves `TRJ-*` and leaves it unused; schema extension
  points exist and are labelled `planned`.

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

Concretely: **14 CLI commands**, **four evaluator families** (parsing, retrieval, grounded answer,
operational), all four versioned in the live capture's provenance, a **frozen HTTP adapter contract**
(`src/braincrew/ax-http-v1.yaml`) pinned to a specific SUT commit with per-operation schema digests
and a mocked contract suite, a create-only artifact store emitting canonical JSON — with Parquet
alongside it for comparison evidence — three ordered release gates, corpus sealing and qualification
receipts, a statically exported dashboard, and **598 tests**.

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

No customer, employee or company document is in this repository.

---

## Running it

```bash
uv sync --frozen --all-groups     # Python 3.12, locked
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest -q                  # 598 tests
uv run pytest tests/acceptance/test_cli_fixture_gate.py -q
uv run pytest tests/acceptance/test_cli_fixture_gate.py -q \
  -k test_replay_recomputes_the_same_logical_digest_and_gate_decision
```

The fastest end-to-end demonstration is the offline fixture path — a full 100-case evaluation, then a
replay that must reproduce the same digest:

```bash
uv run braincrew-eval run-dataset \
  --manifest datasets/dataset_manifest_v1.json \
  --parsing-observations tests/fixtures/parsing_observations_v1.json \
  --retrieval-observations tests/fixtures/retrieval_observations_v1.json \
  --grounded-observations tests/fixtures/grounded_observations_v1.json \
  --output-dir /tmp/braincrew --run-id demo --sut-sha <40-hex>

uv run braincrew-eval replay --artifact /tmp/braincrew/demo.json
```

Both print the same `logical_digest`, and the artifact's own provenance records
`execution_mode: fixture` and `sut.executed: false` — it is a determinism demonstration, not a
benchmark.

### Clean, fixture-only container

The clean container uses the locked Python environment and has no host mount. Its build context excludes
local Git metadata, environment files, Python caches and bytecode, and dashboard `.next`/`out` build
outputs at every depth. The `ax-live-verification-evidence/` pattern is defensive only: that directory
lies outside the repository, so nothing was excluded from the context on its account. The fixture
acceptance test receives only
an image-local Git snapshot because it checks its own provenance.

```bash
docker build --no-cache --tag braincrew-evaluation-fixture:local .
docker run --rm --network none braincrew-evaluation-fixture:local
```

The image runs the Python format, lint, type, full-test, and Issue #6 fixture gates. On Docker's default
Linux namespace policy, the three authoring-boundary tests that require Bubblewrap are explicitly skipped:
installing Bubblewrap makes them fail because the container may not create a user namespace, and this path
does not request privileged or security-relaxed execution. It does **not** contain or replay a published
live artifact, and it does not execute AX. The CI workflow has separate named fixture benchmark,
fixture-replay, container, dashboard, and secret-scan steps; the workflow itself remains unverified until a
pull request runs it.

**Three honest limits on reproduction**, both measured and explicitly bounded:

1. **There is no one-command replay of the published live evaluation.** The published live artifacts are
   owner-held outside this repository pending a publication decision. The container intentionally cannot
   see them, so it verifies fixture evidence only.
2. **A stored-artifact replay and a fresh live rerun prove different things.** Replay can reproduce the
   stored logical metrics and gate decision from fixed bytes. A live SUT/provider rerun produces a new
   observation at a new time and is never presented as byte-identical reproducibility.
3. **The current `v3` dataset has no complete offline run.** The only committed observation bundles
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

- **Independent review and a pre-commit audit before anything lands.** On the most recent ticket
  these produced five blocking findings — one in the code, four in the delivery record's own prose,
  one of which had already reached the interview dossier. Each was reproduced before being accepted,
  and where reproduction amounted to re-reading the author's own prose rather than measuring
  something, the audit record says so.
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

- **Met (4)** — the dataset freeze and recorded 70/30 digest; metric goldens and boundary tests;
  canonical artifacts reconstructing analytical outputs; and Agent evaluation left explicitly
  unimplemented and unclaimed.
- **Met for fixture evidence only (2)** — reproducible release-gate output with reasons; and a clean,
  network-isolated container executes the locked Python environment and fixture checks. This is not
  published-live-artifact validation.
- **Not met (3)** — a compatible baseline/candidate pair; a complete live Verification run; and
  evidence linkage for every submission claim.
- **Not separately assessed (1)** — the dashboard static-build and sanitized-export check.

The blocking dependency **for live answer quality** is in the SUT, not here: until AX#61 makes the discarded provider output
observable, the cause of the twelve failures cannot be identified, and a candidate run would spend
provider budget to break the same twelve cases again.

Licensed work in progress. Design decisions, their rejected alternatives and their failure modes are
in `docs/decisions/`; the reasoning behind each is defended in `docs/interview/`.
