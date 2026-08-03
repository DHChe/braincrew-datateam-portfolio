# Three-minute portfolio demonstration

This walkthrough is intentionally offline and deterministic. It demonstrates the Evaluation Plane's
contracts, artifact integrity, and refusal boundaries. It does not claim a fresh live AX quality result.

## 0:00-0:30 — State the problem and ownership

> I built this portfolio to answer a narrower question than “does the RAG system look good?”: what
> evidence is required before a quality or release claim is allowed? AI coding agents produced most of
> the implementation. I owned the HR/labor problem framing, evaluation scope, orchestration, review
> criteria, corrections, and the decision to surface insufficient evidence as `INVALID`.

Show the first two README sections. Point out that AX_portfolio is a separate, evolving subject under
test, not a finished product copied into this repository.

## 0:30-1:30 — Run the 100-case fixture and replay

```bash
uv sync --frozen --all-groups
demo_dir="$(mktemp -d /tmp/evidence-first-rag-demo.XXXXXX)"

uv run braincrew-eval run-dataset \
  --manifest datasets/dataset_manifest_v1.json \
  --parsing-observations tests/fixtures/parsing_observations_v1.json \
  --retrieval-observations tests/fixtures/retrieval_observations_v1.json \
  --grounded-observations tests/fixtures/grounded_observations_v1.json \
  --output-dir "$demo_dir" --run-id demo \
  --sut-sha c318b2192006bdb36a5bd5b3a2bc403425b45701

uv run braincrew-eval replay --artifact "$demo_dir/demo.json"
```

Compare the two printed `logical_digest` values. Then open the artifact and show
`execution_mode: fixture` and `sut.executed: false`. Explain that replay proves deterministic
recomputation from fixed bytes, not live model reproducibility.

## 1:30-2:15 — Explain the fail-closed decision

Open `src/braincrew/comparison.py` and the README capability matrix. Explain that comparison requires
compatible, completed evidence. The live grounded-answer runs had zero answer-quality coverage, so the
system emitted `INVALID` and produced no comparison or release artifact. This is a deliberate refusal,
not a hidden failed benchmark.

## 2:15-2:45 — Show what the evaluation changed upstream

Open AX issues 60 and 61 from the README. Explain that the evaluator exposed an ambiguous failure label
and invisible discarded answers. The product fixed both, making citation-contract failures distinct
from safety blocks and making discarded provider output observable.

## 2:45-3:00 — Close with the transferable method

> HR/labor is my first deep domain, not my intended boundary. My method is to translate domain rules
> and exceptions into versioned cases, define what evidence permits a claim, test the refusal paths,
> and incorporate domain-expert feedback. I am now learning the core implementation deeply enough to
> defend each boundary rather than presenting agent-written code as unaided authorship.

## Stop condition

End the demo after the replay digest matches and the claim boundary is explained. Do not start a paid
live run during a recruiter walkthrough; a new provider invocation is new evidence, costs money, and is
not needed to prove the stored-artifact contract.
