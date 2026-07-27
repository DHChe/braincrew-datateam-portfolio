from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal, cast

import httpx
import pytest
from typer.testing import CliRunner

from braincrew.ax_http_adapter import AxHttpFailure
from braincrew.comparison import ExperimentCaseResult, ExperimentRunSummary, compare_runs
from braincrew.contracts import RetrievalApplicability
from braincrew.dataset_registry import validate_dataset_bundle
from braincrew.repository import RepositoryState

PROJECT_ROOT = Path(__file__).parents[2]
DATASET_MANIFEST = PROJECT_ROOT / "datasets" / "dataset_manifest_v3.json"
PINNED_AX_SHA = "2bcaee3495fd7b3f624398819575cd86a5a15c47"
TENANT_ID = "ae09ec7f-e2b8-4f83-99bb-7031ef5eb6e2"
USER_ID = "12171ca4-a001-40da-881b-b87cce42e9b2"
CAPTURED_AT = datetime(2026, 7, 27, 9, 0, tzinfo=UTC)
ResponseMutation = Literal[
    "corpus_role",
    "retrieval_binding",
    "visibility",
    "answer_binding",
    "model_missing",
    "model_mismatch",
    "answer_mode",
]


def _check(condition: bool, message: str) -> None:
    if not condition:
        pytest.fail(message)


def _validated_dataset() -> Any:
    validation = validate_dataset_bundle(DATASET_MANIFEST)
    _check(validation.state == "VALID", "frozen v3 dataset must validate")
    _check(validation.snapshot is not None, "valid dataset must carry its snapshot")
    return validation


def _source_texts(validation: Any) -> dict[str, str]:
    snapshot = validation.snapshot
    _check(snapshot is not None, "source lookup requires a dataset snapshot")
    return {
        case.document.id: case.document.canonical_text for case in snapshot.parsing_dataset.cases
    }


def _retrieval_response(
    *,
    query: str,
    source_id: str | None = None,
    source_class: str | None = None,
    snippet: str = "",
) -> dict[str, object]:
    candidates: list[dict[str, object]] = []
    if source_id is not None and source_class is not None:
        candidate: dict[str, object] = {
            "vector_record_id": "vec-1",
            "record_kind": "source_chunk",
            "record_id": "chunk-1",
            "snippet": snippet,
            "source_id": source_id,
            "chunk_id": "chunk-1",
            "evidence_span_id": None,
            "source_class": source_class,
            "authority_level": 30,
            "provenance": {"source_id": source_id, "chunk_id": "chunk-1"},
            "metadata": {"answer_use": "grounding_allowed"},
            "retrieval_score": 0.12,
            "retrieval_score_kind": "pgvector_l2_distance",
            "visibility_decision": {"allowed": True, "reason": "executive_full_access"},
            "synthetic": True,
            "demo_company": True,
            "corpus_mode": "demo",
        }
        candidates.append(candidate)
    return {
        "query": query,
        "top_k": 5,
        "max_top_k": 10,
        "answer_mode": "direct_grounded",
        "candidates": candidates,
        "matched_evidence": candidates,
        "risk_tags": [],
        "visibility_decisions": [],
        "correlation_id": "retrieval:fixture",
        "audit_recorded": True,
        "precedent_capability_enabled": True,
        "provider_free": True,
        "notices": [],
        "currentness_checks": [],
        "natural_language_answer_generated": False,
    }


def _answer_response(
    *,
    query: str,
    source_id: str | None = None,
    source_class: str | None = None,
    snippet: str = "",
) -> dict[str, object]:
    citations: list[dict[str, object]] = []
    if source_id is not None and source_class is not None:
        citations.append(
            {
                "source_id": source_id,
                "chunk_id": "chunk-1",
                "evidence_span_id": None,
                "record_kind": "source_chunk",
                "record_id": "chunk-1",
                "source_class": source_class,
                "authority_level": 30,
                "synthetic": True,
                "demo_company": True,
                "corpus_mode": "demo",
                "snippet": snippet,
                "claim_paths": ["summary"],
            }
        )
    return {
        "query": query,
        "answer_mode": "direct_grounded",
        "structured_answer": {
            "summary": "선택된 근거에 따르면 검토가 필요합니다.",
            "answer": "검토가 필요합니다.",
            "grounds": [],
            "review_points": [],
            "additional_checks": [],
            "risk_warning": "",
            "citations": citations,
        },
        "citations": citations,
        "reference_context": [],
        "retrieval_correlation_id": "retrieval:fixture",
        "answer_correlation_id": "answer:fixture",
        "audit_recorded": True,
        "natural_language_answer_generated": True,
        "provider_metadata": {
            "provider_adapter": "fake-deterministic",
            "model": "fake-answer-model",
            "provider_store": False,
            "llm_call_performed": True,
            "llm_call_succeeded": True,
        },
        "evidence_packaging": {
            "selected_count": len(citations),
            "selected_record_ids": ["chunk-1"] if citations else [],
            "selected_source_ids": [source_id] if source_id is not None else [],
            "skipped_record_ids": [],
            "char_cap": 12000,
            "total_chars": len(snippet),
            "truncated": False,
            "llm_evidence_transfer_allowed": True,
        },
    }


def _capture_transport(validation: Any) -> tuple[httpx.MockTransport, list[tuple[str, str]]]:
    snapshot = validation.snapshot
    _check(snapshot is not None, "transport fixture requires a dataset snapshot")
    retrieval_cases = {
        case.id: case for case in snapshot.retrieval_dataset.cases if case.split == "verification"
    }
    grounded_cases = {
        case.case_id: case
        for case in snapshot.grounded_dataset.cases
        if case.split == "Verification"
    }
    sources = _source_texts(validation)
    first_retrieval_id = sorted(retrieval_cases)[0]
    first_grounded_id = sorted(grounded_cases)[0]
    calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        case_id = request.headers["x-eval-case-id"]
        role = request.headers["x-ax-roles"]
        calls.append((request.url.path, case_id))
        _check(request.headers["x-ax-tenant-id"] == TENANT_ID, "tenant must come from receipt")
        _check(request.headers["x-ax-user-id"] == USER_ID, "subject must come from receipt")
        if request.url.path == "/v1/evaluation/corpus-identity":
            return httpx.Response(
                200,
                json={
                    "schema_version": "ax-corpus-identity-v1",
                    "corpus_id": "live-corpus-v1",
                    "corpus_version": "retrieval-inventory-v1",
                    "corpus_digest": "sha256:" + "7" * 64,
                    "principal_roles": [role],
                    "inventory_count": 166,
                    "counts": {
                        "record_kind": {
                            "source_record": 20,
                            "source_chunk": 83,
                            "evidence_span": 83,
                            "vector": 166,
                        },
                    },
                    "contributing_versions": ["braincrew-evaluation-dataset-3.0.0"],
                    "generated_at": "2026-07-27T00:00:00Z",
                },
            )
        if request.url.path == "/v1/retrieval/search":
            case = retrieval_cases[case_id]
            body = json.loads(request.read())
            _check(body == {"query": case.query, "top_k": 5}, "retrieval request drifted")
            if case_id != first_retrieval_id:
                return httpx.Response(200, json=_retrieval_response(query=case.query))
            expected = case.expected.evidence_groups[0].alternatives[0]
            text = sources[expected.record_id]
            return httpx.Response(
                200,
                json=_retrieval_response(
                    query=case.query,
                    source_id=expected.record_id,
                    source_class=expected.record_kind,
                    snippet=text[:80],
                ),
            )
        if request.url.path == "/v1/answers/generate":
            case = grounded_cases[case_id]
            body = json.loads(request.read())
            expected_role = {
                "employee": "Employee",
                "hr_manager": "HRManager",
            }.get(case.role, case.role)
            _check(role == expected_role, "grounded role must derive from the dataset")
            _check(body["query"] == case.query, "answer query drifted")
            _check(body["top_k"] == 5, "answer top_k drifted")
            if case_id != first_grounded_id:
                return httpx.Response(200, json=_answer_response(query=case.query))
            alternative = case.propositions[0].supporting_evidence_groups[0].alternatives[0]
            text = sources[alternative.record_id]
            return httpx.Response(
                200,
                json=_answer_response(
                    query=case.query,
                    source_id=alternative.record_id,
                    source_class=alternative.record_kind,
                    snippet=text[:80],
                ),
            )
        pytest.fail(f"unexpected HTTP request: {request.method} {request.url.path}")

    return httpx.MockTransport(handler), calls


def _mutate_transport(
    original: httpx.MockTransport,
    mutation: ResponseMutation,
) -> httpx.MockTransport:
    mutated = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal mutated
        response = original.handle_request(request)
        payload = response.json()
        if not isinstance(payload, dict):
            pytest.fail("test transport response must be a JSON object")
        if mutation == "corpus_role" and request.url.path.endswith("corpus-identity"):
            payload["principal_roles"] = ["UnreviewedRole"]
            mutated = True
        elif (
            mutation == "retrieval_binding"
            and request.url.path.endswith("retrieval/search")
            and not mutated
        ):
            payload["query"] = "drifted query"
            mutated = True
        elif (
            mutation == "visibility"
            and request.url.path.endswith("retrieval/search")
            and payload["candidates"]
            and not mutated
        ):
            candidates = cast(list[dict[str, object]], payload["candidates"])
            visibility = cast(dict[str, object], candidates[0]["visibility_decision"])
            del visibility["reason"]
            mutated = True
        elif (
            mutation == "answer_binding"
            and request.url.path.endswith("answers/generate")
            and not mutated
        ):
            payload["query"] = "drifted query"
            mutated = True
        elif (
            mutation == "model_missing"
            and request.url.path.endswith("answers/generate")
            and not mutated
        ):
            metadata = cast(dict[str, object], payload["provider_metadata"])
            metadata["model"] = None
            mutated = True
        elif (
            mutation == "model_mismatch"
            and request.url.path.endswith("answers/generate")
            and request.headers["x-eval-case-id"] == "GA-002"
        ):
            metadata = cast(dict[str, object], payload["provider_metadata"])
            metadata["model"] = "different-model"
            mutated = True
        elif (
            mutation == "answer_mode"
            and request.url.path.endswith("answers/generate")
            and not mutated
        ):
            payload["answer_mode"] = "unreviewed-mode"
            mutated = True
        return httpx.Response(response.status_code, json=payload)

    return httpx.MockTransport(handler)


def _capture(
    tmp_path: Path,
    *,
    role: Literal["baseline", "candidate"] = "baseline",
    evaluation_dirty: bool = False,
    sut_sha: str = PINNED_AX_SHA,
    sut_dirty: bool = False,
    response_mutation: ResponseMutation | None = None,
    invalid_dataset: bool = False,
) -> Any:
    from braincrew.live_experiment import (
        ReviewedPrincipalBinding,
        SutStateSubject,
        SutStateWarrant,
        capture_live_experiment,
    )

    validation = _validated_dataset()
    transport, calls = _capture_transport(validation)
    if response_mutation is not None:
        transport = _mutate_transport(transport, response_mutation)
    capture_validation = (
        validation.model_copy(update={"state": "INVALID", "snapshot": None})
        if invalid_dataset
        else validation
    )
    sut_source_root = tmp_path / "ax"
    prompt_source = sut_source_root / "backend/src/ax_engine/answers/service.py"
    prompt_source.parent.mkdir(parents=True)
    prompt_source.write_text("def prompt_contract():\n    return 'pinned'\n", encoding="utf-8")
    result = capture_live_experiment(
        run_id=f"{role}-live",
        role=role,
        captured_at=CAPTURED_AT,
        evaluation_state=RepositoryState(
            commit_sha="a" * 40,
            dirty_worktree=evaluation_dirty,
        ),
        sut_state=SutStateWarrant(
            schema_version="sut-state-warrant-v1",
            method="read-only-git-check",
            subject=SutStateSubject(
                repository="AX_portfolio",
                checkout_path=str(sut_source_root.resolve()),
                checked_at=CAPTURED_AT,
            ),
            commit_sha=sut_sha,
            dirty_worktree=sut_dirty,
        ),
        sut_source_root=sut_source_root,
        base_url="https://ax.example.test",
        principal=ReviewedPrincipalBinding(
            tenant_id=TENANT_ID,
            user_id=USER_ID,
        ),
        dataset_validation=capture_validation,
        dependency_lock_path=PROJECT_ROOT / "uv.lock",
        transport=transport,
    )
    return result, calls


def test_live_capture_issues_only_the_pinned_verification_requests_and_derives_provenance(
    tmp_path: Path,
) -> None:
    result, calls = _capture(tmp_path)

    _check(
        sum(path == "/v1/evaluation/corpus-identity" for path, _ in calls) == 3,
        "capture must bind corpus identity for all three dataset roles",
    )
    _check(
        sum(path == "/v1/retrieval/search" for path, _ in calls) == 9,
        "capture must retrieve the nine Verification retrieval cases",
    )
    _check(
        sum(path == "/v1/answers/generate" for path, _ in calls) == 15,
        "capture must answer the fifteen Verification grounded cases",
    )
    _check(len(result.manifest.verification_case_ids) == 30, "manifest must bind all 30 cases")
    _check(len(result.manifest.live_case_ids) == 24, "exactly 24 query-bearing cases are live")
    _check(len(result.manifest.fixture_case_ids) == 6, "six parsing cases remain fixture-carried")
    _check(
        result.retrieval_observations.adapter_version == "ax-sut-http-v1",
        "retrieval batch must name the live adapter",
    )
    _check(
        result.grounded_observations.adapter_version == "ax-sut-http-v1",
        "grounded batch must name the live adapter",
    )
    provenance = result.manifest.provenance
    _check(provenance.execution_mode == "live", "live capture must say it was live")
    _check(provenance.evaluation_plane_sha == "a" * 40, "Evaluation Plane SHA must derive")
    _check(provenance.evaluation_plane_dirty is False, "clean Evaluation Plane must derive")
    _check(provenance.sut_sha == PINNED_AX_SHA, "SUT SHA must come from read-only warrant")
    _check(provenance.sut_dirty is False, "SUT dirtiness must come from read-only warrant")
    _check(provenance.dataset_version == "3.0.0", "dataset version must derive from manifest")
    _check(provenance.corpus_id == "live-corpus-v1", "corpus ID must derive from AX response")
    _check(
        provenance.model_provider == "fake-deterministic",
        "provider must derive from answer responses",
    )
    _check(provenance.model_name == "fake-answer-model", "model must derive from responses")
    _check(
        provenance.model_parameters == {"reporting_status": "not_exposed_by_ax-http-v1"},
        "unobservable generation parameters must be recorded as unavailable",
    )
    _check(provenance.retrieval_top_k == 5, "top_k must be the frozen contract")
    _check(provenance.evidence_limit == 3, "baseline evidence limit must derive from role")
    _check(
        set(provenance.evaluator_versions)
        == {
            "parsing",
            "retrieval",
            "grounded",
            "operational",
        },
        "all comparison-required evaluator versions must be populated",
    )
    _check(
        provenance.adapter_versions
        == {
            "parsing": "fixture-parsing-sut-v1",
            "retrieval": "ax-sut-http-v1",
            "grounded": "ax-sut-http-v1",
        },
        "adapter versions must record the deliberate mixed capture",
    )
    first_retrieval = result.retrieval_observations.observations[0]
    _check(
        first_retrieval.candidates[0].record_id == "demo-safety-policy-009",
        "physical AX candidate must normalize to frozen logical source identity",
    )
    first_grounded = result.grounded_observations.observations[0]
    _check(
        first_grounded.citations[0].record_id == "demo-terms-policy-001",
        "physical AX citation must normalize to frozen logical source identity",
    )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"evaluation_dirty": True}, "clean committed Evaluation Plane"),
        ({"sut_sha": "b" * 40}, "pinned AX commit"),
        ({"sut_dirty": True}, "clean SUT checkout"),
    ],
)
def test_live_capture_refuses_unwarranted_repository_state(
    tmp_path: Path,
    overrides: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        if "evaluation_dirty" in overrides:
            _capture(tmp_path, evaluation_dirty=cast(bool, overrides["evaluation_dirty"]))
        elif "sut_sha" in overrides:
            _capture(tmp_path, sut_sha=cast(str, overrides["sut_sha"]))
        else:
            _capture(tmp_path, sut_dirty=cast(bool, overrides["sut_dirty"]))


def test_live_capture_refuses_inconsistent_role_corpus_identity(tmp_path: Path) -> None:
    from braincrew.live_experiment import (
        ReviewedPrincipalBinding,
        SutStateSubject,
        SutStateWarrant,
        capture_live_experiment,
    )

    validation = _validated_dataset()
    original_transport, _ = _capture_transport(validation)

    def handler(request: httpx.Request) -> httpx.Response:
        response = original_transport.handle_request(request)
        if (
            request.url.path == "/v1/evaluation/corpus-identity"
            and request.headers["x-ax-roles"] == "Employee"
        ):
            payload = response.json()
            payload["corpus_digest"] = "sha256:" + "8" * 64
            return httpx.Response(200, json=payload)
        return response

    sut_source_root = tmp_path / "ax"
    prompt_source = sut_source_root / "backend/src/ax_engine/answers/service.py"
    prompt_source.parent.mkdir(parents=True)
    prompt_source.write_text("def prompt_contract():\n    return 'pinned'\n", encoding="utf-8")
    with pytest.raises(ValueError, match="corpus identity differs across dataset roles"):
        capture_live_experiment(
            run_id="baseline-live",
            role="baseline",
            captured_at=CAPTURED_AT,
            evaluation_state=RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
            sut_state=SutStateWarrant(
                schema_version="sut-state-warrant-v1",
                method="read-only-git-check",
                subject=SutStateSubject(
                    repository="AX_portfolio",
                    checkout_path=str(sut_source_root.resolve()),
                    checked_at=CAPTURED_AT,
                ),
                commit_sha=PINNED_AX_SHA,
                dirty_worktree=False,
            ),
            sut_source_root=sut_source_root,
            base_url="https://ax.example.test",
            principal=ReviewedPrincipalBinding(tenant_id=TENANT_ID, user_id=USER_ID),
            dataset_validation=validation,
            dependency_lock_path=PROJECT_ROOT / "uv.lock",
            transport=httpx.MockTransport(handler),
        )


def test_live_capture_refuses_an_invalid_frozen_dataset(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="validated frozen dataset"):
        _capture(tmp_path, invalid_dataset=True)


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        ("corpus_role", "corpus identity does not bind the requested dataset role"),
        ("retrieval_binding", "retrieval response does not bind the requested case"),
        ("visibility", "retrieval visibility decision is incomplete"),
        ("answer_binding", "answer response does not bind the requested case"),
        ("model_missing", "answer response omits model identity"),
        ("model_mismatch", "model identity differs across answer responses"),
        ("answer_mode", "answer mode is not representable"),
    ],
)
def test_live_capture_refuses_unbound_live_response_identity(
    tmp_path: Path,
    mutation: ResponseMutation,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        _capture(tmp_path, response_mutation=mutation)


def test_live_capture_files_are_create_only(tmp_path: Path) -> None:
    from braincrew.live_experiment import write_live_experiment_capture

    result, _ = _capture(tmp_path)
    output_dir = tmp_path / "capture"
    written = write_live_experiment_capture(result, output_dir)
    _check(len(written) == 3, "capture must publish manifest and two observation batches")
    _check(all(path.is_file() for path in written), "all capture files must exist")

    with pytest.raises(FileExistsError, match="capture artifact already exists"):
        write_live_experiment_capture(result, output_dir)


def test_written_manifest_logical_digest_recomputes_from_the_written_file(
    tmp_path: Path,
) -> None:
    from braincrew.digest import canonical_digest
    from braincrew.live_experiment import write_live_experiment_capture

    result, _ = _capture(tmp_path)
    manifest_path, _, _ = write_live_experiment_capture(result, tmp_path / "capture")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored_digest = payload.pop("logical_digest")

    _check(
        stored_digest == canonical_digest(payload),
        "written manifest logical digest must recompute from its serialized payload",
    )


def test_live_manifest_refuses_a_warrant_that_disagrees_with_provenance(
    tmp_path: Path,
) -> None:
    from braincrew.live_experiment import LiveExperimentCaptureManifest

    result, _ = _capture(tmp_path)
    payload = result.manifest.model_dump(mode="json")
    payload["sut_state_warrant"]["commit_sha"] = "b" * 40

    with pytest.raises(ValueError, match="SUT provenance must match"):
        LiveExperimentCaptureManifest.model_validate(payload)


def test_live_manifest_refuses_an_incomplete_case_partition(tmp_path: Path) -> None:
    from braincrew.live_experiment import LiveExperimentCaptureManifest

    result, _ = _capture(tmp_path)
    payload = result.manifest.model_dump(mode="json")
    payload["live_case_ids"][-1] = "UNBOUND-CASE"

    with pytest.raises(ValueError, match="partition must cover all Verification cases"):
        LiveExperimentCaptureManifest.model_validate(payload)


def test_baseline_and_candidate_capture_provenance_passes_the_existing_compatibility_check(
    tmp_path: Path,
) -> None:
    baseline_capture, _ = _capture(tmp_path / "baseline", role="baseline")
    candidate_capture, _ = _capture(tmp_path / "candidate", role="candidate")
    baseline_provenance = baseline_capture.manifest.provenance
    candidate_provenance = candidate_capture.manifest.provenance
    left = baseline_provenance.model_dump(mode="json", exclude={"evidence_limit"})
    right = candidate_provenance.model_dump(mode="json", exclude={"evidence_limit"})
    _check(left == right, "capture provenance may differ only in evidence_limit")

    def summary(
        role: Literal["baseline", "candidate"],
        provenance: Any,
    ) -> ExperimentRunSummary:
        cases = tuple(
            ExperimentCaseResult(
                case_id=case_id,
                metrics={
                    "evidence_span_recovery": Decimal("0.8"),
                    "recall_at_5": Decimal("0.8"),
                    "claim_support_precision": Decimal("0.8"),
                    "citation_precision": Decimal("0.8"),
                    "answer_mode_accuracy": Decimal("0.8"),
                    "abstention_accuracy": Decimal("0.8"),
                },
                retrieval_metrics={
                    "mrr_at_10": Decimal("0.8"),
                    "authority_priority": Decimal("0.8"),
                },
                applicability=RetrievalApplicability(
                    recall_at_5=True,
                    mrr_at_10=True,
                    authority_ordering=True,
                    forbidden_visibility=False,
                ),
                latency_ms=Decimal("1"),
                cost_usd=Decimal("1"),
                failures=(),
            )
            for case_id in baseline_capture.manifest.verification_case_ids
        )
        return ExperimentRunSummary(
            schema_version="experiment-run-summary-v1",
            run_id=f"{role}-run",
            role=role,
            split="verification",
            state="COMPLETED",
            candidate_plan_version="candidate-plan-v1",
            provenance=provenance,
            cases=cases,
        )

    comparison = compare_runs(
        summary("baseline", baseline_provenance),
        summary("candidate", candidate_provenance),
        comparison_id="live-compatibility",
    )
    _check(
        comparison.compatibility_violations == (),
        "existing comparison compatibility must accept the capture pair",
    )


def test_run_contracts_represent_live_execution_without_overclaiming_fixture_parsing() -> None:
    from braincrew.contracts import (
        AdapterProvenance,
        ParsingAdapterProvenance,
        RetrievalAdapterProvenance,
        RetrievalObservationBatch,
        RunEnvelope,
        SutProvenance,
    )
    from braincrew.dataset_run import DatasetAdapterProvenance
    from braincrew.grounded_contracts import (
        GroundedAdapterProvenance,
        GroundedObservation,
        GroundedObservationBatch,
        GroundedStructuredAnswer,
    )

    envelope = RunEnvelope(
        run_id="live-run",
        execution_mode="live",
        created_at=CAPTURED_AT,
    )
    sut = SutProvenance(
        commit_sha=PINNED_AX_SHA,
        dirty_worktree=False,
        executed=True,
        claim="live AX called; clean state warranted by read-only checkout check",
    )
    retrieval_adapter = RetrievalAdapterProvenance(
        version="ax-sut-http-v1",
        execution_mode="live",
    )
    grounded_adapter = GroundedAdapterProvenance(
        version="ax-sut-http-v1",
        execution_mode="live",
    )
    parsing_adapter = ParsingAdapterProvenance(
        version="fixture-parsing-sut-v1",
        parser_version="fixture-parser-v1",
        execution_mode="fixture",
    )
    with pytest.raises(ValueError, match="execution_mode"):
        ParsingAdapterProvenance.model_validate(
            {
                "version": "fixture-parsing-sut-v1",
                "parser_version": "fixture-parser-v1",
                "execution_mode": "live",
            }
        )
    generic_adapter = AdapterProvenance(version="ax-sut-http-v1", execution_mode="live")
    dataset_adapter = DatasetAdapterProvenance(
        execution_mode="live",
        parsing_version="fixture-parsing-sut-v1",
        retrieval_version="ax-sut-http-v1",
        grounded_version="ax-sut-http-v1",
    )
    retrieval_batch = RetrievalObservationBatch(
        schema_version="retrieval-observation-batch-v1",
        adapter_version="ax-sut-http-v1",
        observations=[],
    )
    grounded_batch = GroundedObservationBatch(
        schema_version="grounded-observation-batch-v1",
        adapter_version="ax-sut-http-v1",
        sut_commit_sha=PINNED_AX_SHA,
        observations=(
            GroundedObservation(
                case_id="GA-001",
                executed_role="Executive",
                available=True,
                error=None,
                answer_mode="direct_grounded",
                structured_answer=GroundedStructuredAnswer(
                    summary="검토가 필요합니다.",
                    answer="검토가 필요합니다.",
                    grounds=(),
                    review_points=(),
                    additional_checks=(),
                    risk_warning="",
                ),
                citations=(),
                source_texts=(),
            ),
        ),
    )

    _check(envelope.execution_mode == "live", "run envelope must represent live")
    _check(sut.executed is True, "SUT provenance must represent an executed live SUT")
    _check(retrieval_adapter.execution_mode == "live", "retrieval adapter must represent live")
    _check(grounded_adapter.execution_mode == "live", "grounded adapter must represent live")
    _check(
        parsing_adapter.execution_mode == "fixture",
        "fixture parsing provenance must not claim live execution",
    )
    _check(generic_adapter.execution_mode == "live", "generic run contract must allow live")
    _check(dataset_adapter.execution_mode == "live", "dataset run contract must allow live")
    _check(
        retrieval_batch.adapter_version == "ax-sut-http-v1",
        "retrieval observations must name live adapter",
    )
    _check(
        grounded_batch.adapter_version == "ax-sut-http-v1",
        "grounded observations must name live adapter",
    )


@pytest.mark.parametrize(
    ("executed", "dirty_worktree", "claim"),
    [
        (
            True,
            None,
            "live AX called; clean state warranted by read-only checkout check",
        ),
        (
            True,
            False,
            "identity placeholder only; live AX was not called",
        ),
        (
            False,
            False,
            "identity placeholder only; live AX was not called",
        ),
        (
            False,
            None,
            "live AX called; clean state warranted by read-only checkout check",
        ),
    ],
)
def test_sut_provenance_refuses_invalid_execution_claim_combinations(
    executed: bool,
    dirty_worktree: bool | None,
    claim: str,
) -> None:
    from braincrew.contracts import SutProvenance

    with pytest.raises(ValueError):
        SutProvenance.model_validate(
            {
                "commit_sha": PINNED_AX_SHA,
                "dirty_worktree": dirty_worktree,
                "executed": executed,
                "claim": claim,
            }
        )


def test_capture_cli_derives_principal_and_sut_state_without_dirty_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from braincrew import cli
    from braincrew.live_experiment import ReviewedPrincipalBinding

    captured: dict[str, object] = {}

    def fake_binding(path: Path) -> ReviewedPrincipalBinding:
        captured["receipt"] = path
        return ReviewedPrincipalBinding(tenant_id=TENANT_ID, user_id=USER_ID)

    def fake_repository_state(path: Path | None = None) -> RepositoryState:
        if path is None:
            return RepositoryState(commit_sha="a" * 40, dirty_worktree=False)
        captured["sut_checkout"] = path
        return RepositoryState(commit_sha="c" * 40, dirty_worktree=True)

    def fake_capture(**kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    def fake_write(capture: object, output_dir: Path) -> tuple[Path, Path, Path]:
        captured["capture"] = capture
        captured["output_dir"] = output_dir
        return (
            output_dir / "baseline-live.capture-manifest.json",
            output_dir / "baseline-live.retrieval-observations.json",
            output_dir / "baseline-live.grounded-observations.json",
        )

    monkeypatch.setattr(cli, "load_reviewed_principal_binding", fake_binding)
    monkeypatch.setattr(cli, "capture_repository_state", fake_repository_state)
    monkeypatch.setattr(cli, "capture_live_experiment", fake_capture)
    monkeypatch.setattr(cli, "write_live_experiment_capture", fake_write)
    receipt = tmp_path / "handoff.json"
    receipt.write_text("{}\n", encoding="utf-8")
    sut_checkout = tmp_path / "ax"
    sut_checkout.mkdir()
    result = CliRunner().invoke(
        cli.app,
        [
            "capture-live-experiment",
            "--output-dir",
            str(tmp_path / "output"),
            "--run-id",
            "baseline-live",
            "--role",
            "baseline",
            "--base-url",
            "https://ax.example.test",
            "--handoff-receipt",
            str(receipt),
            "--sut-checkout",
            str(sut_checkout),
        ],
    )

    _check(result.exit_code == 0, f"CLI failed: {result.output}")
    _check(captured["receipt"] == receipt, "CLI must derive principal from reviewed receipt")
    _check(captured["sut_checkout"] == sut_checkout, "CLI must inspect the SUT checkout")
    warrant = cast(Any, captured["sut_state"])
    _check(warrant.commit_sha == "c" * 40, "warrant SHA must report the inspected checkout")
    _check(warrant.dirty_worktree is True, "warrant dirtiness must report the inspected checkout")
    _check(
        warrant.subject.checkout_path == sut_checkout.name,
        "warrant subject must identify the inspected checkout",
    )
    _check(
        warrant.subject.checked_at == captured["captured_at"],
        "warrant subject timestamp must match the capture timestamp",
    )
    _check("sut_dirty" not in captured, "CLI must not accept or default a SUT dirty flag")
    _check("--tenant-id" not in result.output, "CLI must not expose a tenant option")


def _ax_failure(
    failure_type: type[AxHttpFailure],
    *,
    failure_code: str,
) -> AxHttpFailure:
    from braincrew.ax_http_adapter import AxCanonicalRequest

    request = AxCanonicalRequest(
        operation="retrieve",
        run_id="baseline-live",
        case_id="RET-FAILURE",
        eval_correlation_id="eval-baseline-live-RET-FAILURE",
        tenant_id=TENANT_ID,
        user_id=USER_ID,
        roles=("Employee",),
        timeout_seconds=30.0,
    )
    return failure_type(
        operation="retrieve",
        failure_code=failure_code,
        request=request,
        attempts=[],
    )


def _invoke_capture_cli_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    failure: Exception,
) -> Any:
    from braincrew import cli
    from braincrew.live_experiment import ReviewedPrincipalBinding

    monkeypatch.setattr(
        cli,
        "_capture_repository_state",
        lambda: RepositoryState(commit_sha="a" * 40, dirty_worktree=False),
    )
    monkeypatch.setattr(
        cli,
        "capture_repository_state",
        lambda _: RepositoryState(commit_sha=PINNED_AX_SHA, dirty_worktree=False),
    )
    monkeypatch.setattr(
        cli,
        "load_reviewed_principal_binding",
        lambda _: ReviewedPrincipalBinding(tenant_id=TENANT_ID, user_id=USER_ID),
    )

    def fail_capture(**_: object) -> object:
        raise failure

    monkeypatch.setattr(cli, "capture_live_experiment", fail_capture)
    receipt = tmp_path / "handoff.json"
    receipt.write_text("{}\n", encoding="utf-8")
    sut_checkout = tmp_path / "ax"
    sut_checkout.mkdir()
    return CliRunner().invoke(
        cli.app,
        [
            "capture-live-experiment",
            "--output-dir",
            str(tmp_path / "output"),
            "--run-id",
            "baseline-live",
            "--role",
            "baseline",
            "--base-url",
            "https://ax.example.test",
            "--handoff-receipt",
            str(receipt),
            "--sut-checkout",
            str(sut_checkout),
        ],
    )


def test_capture_cli_reports_ax_http_failure_without_a_traceback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from braincrew.ax_http_adapter import AxHttpFailure

    result = _invoke_capture_cli_failure(
        monkeypatch,
        tmp_path,
        _ax_failure(AxHttpFailure, failure_code="AX_PERMANENT_HTTP_FAILURE"),
    )

    _check(result.exit_code == 2, "HTTP failure must use the no-artifact exit code")
    _check(
        "AX_PERMANENT_HTTP_FAILURE" in result.output,
        "HTTP failure output must name its failure code",
    )
    _check("Traceback" not in result.output, "HTTP failure must not print a traceback")


def test_capture_cli_reports_ax_transient_failure_without_a_traceback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from braincrew.ax_http_adapter import AxTransientFailure

    result = _invoke_capture_cli_failure(
        monkeypatch,
        tmp_path,
        _ax_failure(AxTransientFailure, failure_code="AX_TRANSIENT_RETRIES_EXHAUSTED"),
    )

    _check(result.exit_code == 2, "transient failure must use the no-artifact exit code")
    _check(
        "AX_TRANSIENT_RETRIES_EXHAUSTED" in result.output,
        "transient failure output must name its failure code",
    )
    _check("Traceback" not in result.output, "transient failure must not print a traceback")
