# Issue #9 Retrieval Quality Smoke

Date: 2026-07-19

## Scope

This is a synthetic live retrieval contract and evaluator smoke against the pinned AX service. It is not the complete 30-case live benchmark and it does not claim retrieval quality, grounded-answer quality, or Agent quality.

## Pinned identities

- AX_portfolio repository: `https://github.com/DHChe/AX_portfolio`
- AX commit: `c318b2192006bdb36a5bd5b3a2bc403425b45701`
- live Adapter: `ax-sut-http-v1`
- dataset: `braincrew-retrieval-quality@1.0.0`
- declared corpus: `synthetic-hr-v1@1.0.0`
- evaluator: `retrieval-quality-v1`
- run: `issue-9-live-smoke`
- case: `retrieval-001`
- role: `Executive`
- query: `연차휴가 신청 기한은 언제인가`
- retrieval depth: `top_k=10`

## Environment and recovery evidence

AX ran locally from the exact pinned commit through Docker Compose on loopback-only alternate ports. PostgreSQL, Redis, Neo4j, ClamAV, backend, worker, and migrations became healthy before the smoke.

The first retrieval attempt exhausted the Adapter's three permitted retries because the new temporary database lacked tenant `11111111-1111-1111-1111-111111111111`. AX returned `500` while persisting the retrieval audit event, and the backend log identified the exact `audit_events_tenant_id_fkey` violation. This was an environment seed defect, not a retrieval metric result.

The temporary stack was repaired without changing AX code: the synthetic demo tenant was inserted, then the pinned `ax-seed-demo` command loaded 16 sources, 49 chunks, 49 EvidenceSpans, 134 vector records, and 36 operational records. The same query and pinned identities were then executed again.

## Final live result

- readiness and OpenAPI preflight: successful;
- corpus identity: declared but not verified by AX, with `AX_CORPUS_IDENTITY_NOT_EXPOSED`;
- retrieval HTTP attempt: one successful `POST /v1/retrieval/search`, status `200`;
- AX retrieval correlation: `retrieval:09dc3fa6-f52b-4804-a2a9-64540682a5ab`;
- returned candidates: `0`;
- retrieved identity, rank, and authority records: empty list;
- deterministic case scores: Recall@5 `0/1`, MRR@10 `0/1`, authority priority `0/1`, forbidden visibility `0/1`;
- failure labels: `R-RELEVANT-EVIDENCE-MISS`, `R-AUTHORITY-ORDER-INVERSION`;
- hard forbidden-visibility failure: absent.

The empty candidate list is preserved evidence. It proves that the pinned live request, Adapter normalization, and deterministic evaluator executed together, but it supplies no positive retrieval-quality evidence. Because AX does not verify the declared corpus identity and no expected identity was returned, this smoke cannot be promoted to a publishable 30-case benchmark or a release `PASS`.

## Cleanup and data boundary

Only synthetic data was used. No private customer, employee, company, or credential content was recorded. Temporary raw responses remained outside the repository. The alternate-port containers and network were removed after the smoke; the named temporary volumes were preserved.
