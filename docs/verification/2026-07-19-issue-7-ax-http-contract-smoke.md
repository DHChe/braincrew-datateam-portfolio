# Issue #7 AX HTTP Contract Smoke

Date: 2026-07-19

## Scope

This is a capability and response-contract smoke, not a benchmark result. It used only a synthetic Korean HR question and does not claim retrieval, answer, parsing, or Agent quality.

## Pinned identities

- AX_portfolio repository: `https://github.com/DHChe/AX_portfolio`
- AX commit: `c318b2192006bdb36a5bd5b3a2bc403425b45701`
- Adapter contract: `ax-sut-http-v1`
- Declared corpus: `synthetic-hr-v1@1.0.0`
- Evaluation branch: `feat/issue-7-ax-http-contract`, based on `230f90fb53df950173896bd6824792e3a70945ae`
- Evaluation worktree state: dirty and uncommitted during smoke; this evidence is development verification, not a publishable experiment artifact.

## Environment

AX ran locally through its Docker Compose stack with loopback-only alternate host ports because the default Redis port was occupied. The API was exposed at `127.0.0.1:58000`; PostgreSQL, Redis, Neo4j, ClamAV, backend, worker, and frontend reported healthy before the smoke.

## Capability preflight

The create-only temporary manifest recorded:

- readiness: `ready`;
- `preflight`, `retrieve`, `answer`, and `source_text`: available;
- `parse`: unavailable with `AX_PARSE_OBSERVABILITY_UNAVAILABLE`;
- corpus identity: declared but not SUT-verified with `AX_CORPUS_IDENTITY_NOT_EXPOSED`;
- HTTP attempts: two successful attempts, one for readiness and one for OpenAPI discovery;
- pinned AX commit: exact match with the contract.

The missing parse operation is an external AX observability blocker. The Evaluation Plane did not infer parse output from attachment status and did not weaken the parsing acceptance criteria.

## Synthetic retrieval and answer smoke

Input query: `연차 사용 신청 절차`

Retrieval completed with one successful HTTP attempt, returned a valid AX correlation ID, and normalized zero candidates. This proves request/response contract execution only; zero candidates provide no positive retrieval-quality evidence.

Answer execution also completed with one successful HTTP attempt. It returned `answer_mode=insufficient_evidence`, zero citations, and `natural_language_answer_generated=false`. This is the expected fail-closed behavior for missing evidence and does not claim an answer-quality pass.

After code-review repairs, the smoke was repeated as run `issue-7-live-review`. The preserved case identities were `preflight`, `retrieve-synthetic`, and `answer-synthetic`; readiness and all three live requests succeeded with the same capability gaps and fail-closed answer outcome. This rerun confirms that the newly frozen evaluation run/case headers are accepted by the pinned AX service.

`source_text` success remains covered by controlled HTTP contract tests. It was not live-executed because the retrieval smoke produced no permission-checked source identity to resolve.

## Validation boundary

Temporary raw manifests and observations remained outside the repository. No customer, employee, company, credential, or private document content was recorded. The durable evidence here is the reviewed summary of the exact SUT identity, inputs, observable outcomes, and limitations.

The alternate-port AX Compose containers and network were removed after verification. Named data volumes were preserved.
