# A live parsing capture is a separate measurement partition, not a 30-case run

**Status:** owner decision recorded on 2026-08-02; documentation-only Cycle 195

## Decision

Keep the 2026-08-02 baseline/candidate comparison at
`3bb27f870d244fbc8debba91eb408e825caa9e03` as its own valid, no-difference
comparison, and record the new six-case parsing capture at
`5b0f5f2ae2cfb4c4870a2228f9aa226e009241f5` as a separate live measurement.

The owner rejects re-capturing answer and retrieval observations at `5b0f5f2` in
this cycle. That would incur a new provider run, answer a newly constructed
same-SHA comparison question, and replace rather than extend the existing baseline/candidate
partition. The Issue #15 single-commit 30-case acceptance condition is therefore
not met. No parsing score or release claim follows from this capture.

## Runtime record and measured facts

The owner authorized pane 1 to start `ax_portfolio-clamav`,
`ax_portfolio-worker`, and `ax_portfolio-backend` with `docker start` (not Docker
Compose), create AX conversation
`e4b89381-3818-4ba6-b42d-5916d651c813`, and upload the six frozen v3 documents.
They remained unapproved; no attachment approval was authorized.

| Fact | Result | Evidence source and Cycle 195 treatment |
| --- | --- | --- |
| SUT warrant | AX `5b0f5f2ae2cfb4c4870a2228f9aa226e009241f5`, clean | Rechecked from the parsing capture manifest. |
| Attachment state | Six scans clean; six parses parsed; approval pending; materialization `not_materialized` | Pane 1's live runtime measurement. Cycle 195 did not query AX again. |
| Capture | `issue-131-parsing-2026-08-02.parsing-capture-manifest.json` and `issue-131-parsing-2026-08-02.parsing-observations.json` under `/Users/astralpig/ax-live-verification-evidence/run-2026-08-02-parsing/` | Rechecked from the two immutable external files. |
| Capture logical digest | `sha256:34932d8ec5c03589f644a280ff3f442621aece91963a4daa372e2ab42f830349` | Rechecked from the manifest. |
| Heading structure | All six cases match the frozen heading sequences element-for-element | Independently recomputed from the observation bundle and `datasets/parsing/parsing_cases_v2.json`. |
| Evidence spans and metadata | Six of six have zero evidence spans and zero metadata fields | Rechecked from the observation bundle. |
| Visible corpus count after upload | Employee `130`, Executive `166`, HRPractitioner `166`, unchanged | Pane 1's live runtime measurement. The capture directory contains no post-upload corpus receipt, so Cycle 195 does not relabel this as an independently remeasured artifact fact. |
| Existing comparison compatibility | Baseline and candidate manifests both name SUT `3bb27f870d244fbc8debba91eb408e825caa9e03` and the same role-digest mapping | Independently rechecked from the two stored capture manifests. |

The bounded positive claim is: **AX parser recovers exact expected document
structure for all six Verification docs.** This is the first live positive
parsing measurement, limited to the observed heading structure. It does not turn
empty spans or empty metadata into a parser-quality failure.

### Independent heading comparison

| Case | Heading count | Exact element-for-element result |
| --- | ---: | --- |
| `parsing-015` | 1 | yes |
| `parsing-016` | 4 | yes |
| `parsing-017` | 1 | yes |
| `parsing-018` | 4 | yes |
| `parsing-019` | 1 | yes |
| `parsing-020` | 4 | yes |

The capture's `evidence_spans` are empty because the unapproved uploads have no
materialized source document. A non-empty-span capture requires approval, and
that materialization moves the corpus identity bound by the existing comparison.
Neither state is a parser-quality verdict.

## The two observed refusal boundaries

1. **Single-SHA dataset assembly refused.** The pane 1 `run-dataset` invocation
   returned `Invalid dataset observations: --sut-sha does not match grounded
   observation SUT SHA`. The guard is at
   `src/braincrew/cli.py:371-376`: it compares the requested SUT SHA with the
   grounded-observation SUT SHA before evaluation. The old grounded observations
   remain at `3bb27f870d244fbc8debba91eb408e825caa9e03`; the new parsing manifest
   warrants `5b0f5f2ae2cfb4c4870a2228f9aa226e009241f5`. The same command also
   guards a supplied capture manifest's run ID and SUT SHA at
   `src/braincrew/cli.py:386-391`.

2. **Standalone live parsing artifact refused.** The pane 1 `run-parsing`
   invocation raised `ValueError: standalone parsing-run artifacts require fixture
   parsing observations`. `build_parsing_run_artifact()` raises that exact message
   at `src/braincrew/result_store.py:153-154` unless
   `adapter_version == "fixture-parsing-sut-v1"`; this capture truthfully names
   `ax-sut-http-v1` instead.

These are deliberate partition checks, not parser defects. Commit `4279ba9` is
the relevant history: its `Rejected:` trailer rejects widening
`ParsingAdapterProvenance.execution_mode`, and its `Directive:` says the standalone
artifact must explicitly refuse a live batch and that neither half of the
adapter-version/execution-mode boundary may be relaxed alone. Cycle 195 changes
neither contract.

## Consequences and rejected alternative

The retained baseline/candidate pair remains a valid comparison of its own
`3bb27f8` partition and retains its recorded no-difference conclusion. The live
parsing capture remains a separate `5b0f5f2` partition with real observed
structure, but cannot be fused into that comparison or presented as a complete
30-case run.

Re-capturing answer and retrieval data at `5b0f5f2` is rejected for this cycle:
it spends additional provider budget and creates a new evaluation question rather
than a continuation of the already captured baseline/candidate question. Approving
the uploads merely to obtain spans is also rejected here because approval would
materialize sources and move the corpus identity to which the old captures bind.

No source, test, fixture, `evidence/`, AX runtime, provider, container, or Git
lifecycle action occurs in this documentation record. The external capture remains
outside the repository and unreviewed for publication.
