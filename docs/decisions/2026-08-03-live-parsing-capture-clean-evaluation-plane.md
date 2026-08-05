# Live parsing capture must refuse a dirty Evaluation Plane before it contacts AX

**Status:** implemented locally for Issue #131; no live capture was run in this decision cycle

## Decision

`capture_live_parsing_observations()` now applies the same first precondition as
its `capture_live_experiment()` sibling: a dirty Evaluation Plane worktree raises
`ValueError("live parsing capture requires a clean committed Evaluation Plane")`
before the SUT warrant, dataset, mapping, or AX transport is used.

`LiveParsingCaptureManifest.evaluation_plane_dirty` remains part of the schema and
continues to describe provenance. It is no longer reachable as `True` through the
live parsing capture function: a dirty caller is refused rather than recorded as a
successful capture.

The control intentionally lives in the capture function rather than in
`LiveParsingCaptureManifest` validation because a schema-level check would make
the project's one historical live parsing artifact, which truthfully reports
`evaluation_plane_dirty: true`, fail validation and lose its record of the gap.

## Why this was necessary

The parsing capture artifact reported the gap itself. Its manifest at
`<external-evidence-root>/run-2026-08-02-parsing/issue-131-parsing-2026-08-02.parsing-capture-manifest.json`
records `evaluation_plane_dirty: true`, even though its SUT warrant names clean AX
`5b0f5f2ae2cfb4c4870a2228f9aa226e009241f5`. The sibling live-experiment capture
already refuses a dirty Evaluation Plane, and the comparison gate reports
`SYS-COMPARISON-DIRTY-STATE` when either comparison side is dirty. Letting parsing
capture proceed made its provenance less trustworthy than the comparison that
would consume it.

Commit `14c1270` records this as the next control gap to close. Commit `4279ba9`'s
`Directive:` remains applicable: do not relax either half of the
adapter-version/execution-mode boundary. This repair changes neither adapter label,
execution mode, manifest schema, parsing partition, nor either documented
refusal; it only aligns the clean-plane precondition with the sibling capture.

## Test and consequence

The new focused test passes a dirty `RepositoryState` plus a mock transport that
fails if contacted. It asserts the precise clean-Evaluation-Plane refusal, proving
the control is observed rather than merely exercising a successful capture. The
existing response-bound success test had deliberately constructed a dirty
Evaluation Plane and asserted a dirty manifest; it was changed to a clean state
and now asserts clean provenance. That test was relying on the gap, so preserving
it unchanged would have made the suite reject the intended control.

No override, environment variable, warning path, or dirty-capture escape hatch is
introduced. No runtime, container, attachment, provider, `evidence/`, dataset,
or Git lifecycle operation occurs in this cycle. Pane 1 must take any replacement
live capture only after this repair lands on a clean committed Evaluation Plane.

## Known limitation

`live-parsing-capture-v1` has no `replay` route. `replay_run_artifact()` dispatches
comparison, live-experiment capture, dataset-run, and parsing-run artifacts, but
not this schema; its logical digest therefore cannot currently be independently
reproduced through `replay`. This pre-existing gap is recorded for the next clean
capture and remains out of scope here: no replay route is implemented.

## Replacement clean capture

The replacement `live-parsing-capture-v1` exists outside the repository at
`<external-evidence-root>/run-2026-08-03-parsing/`. Its
manifest names run `issue-131-parsing-2026-08-03` with logical digest
`sha256:a29848fb58bfaf361ad848459fcfff878d96186e9de12913c9deff3d0aa692a8`.
It records `evaluation_plane_dirty: false` at Evaluation Plane commit
`6c4f5ae1bf2f59751224e487e2a3c7c601b13976`, a clean
`5b0f5f2ae2cfb4c4870a2228f9aa226e009241f5` SUT warrant, six exact frozen-dataset
heading sequences, and zero evidence spans across all six observations.

This successful capture resolves `6c4f5ae`'s `Not-tested:` statement: "the guard
is proven to refuse and unproven to permit - no live capture has been taken since
it landed." It supersedes the 2026-08-02 capture as the artifact of record; the
2026-08-02 record remains unchanged as the artifact that reported the gap.

The known limitation remains: `live-parsing-capture-v1` has no `replay` route, so
this digest is not independently reproducible through `replay`. Neither parsing
capture is published under `evidence/`, and neither has had a public-suitability
review.
