from __future__ import annotations

import hashlib
import importlib
from fractions import Fraction
from pathlib import Path
from types import ModuleType

import httpx
import pytest

from braincrew.ax_http_adapter import AxHttpAdapter, AxHttpAdapterConfig, AxRequestContext
from braincrew.grounded_contracts import GroundedCitation

DATASET_PATH = Path("datasets/grounded/grounded_cases_v1.json")
OBSERVATIONS_PATH = Path("tests/fixtures/grounded_observations_v1.json")
PINNED_AX_SHA = "c318b2192006bdb36a5bd5b3a2bc403425b45701"


def grounded_run_module() -> ModuleType:
    try:
        return importlib.import_module("braincrew.grounded_run")
    except ModuleNotFoundError:
        pytest.fail("grounded run orchestration is not implemented")


def test_ten_case_grounded_run_matches_hand_calculated_macro_goldens() -> None:
    grounded_run = grounded_run_module()
    dataset = grounded_run.load_grounded_dataset(DATASET_PATH)
    observations = grounded_run.load_grounded_observations(OBSERVATIONS_PATH)

    result = grounded_run.execute_grounded_fixture(dataset, observations)

    assert result.state == "COMPLETED"
    assert len(result.case_evaluations) == 10
    assert result.coverage.total_cases == 10
    assert result.coverage.verification_cases == 10
    assert result.coverage.verification_claim_support_cases == 10
    assert result.coverage.verification_citation_precision_cases == 10
    assert result.aggregate.claim_support_precision.exact == "1/4"
    assert result.aggregate.claim_support_precision.display == "0.2500"
    assert result.aggregate.citation_precision.exact == "9/20"
    assert result.aggregate.citation_precision.display == "0.4500"
    assert result.aggregate.citation_coverage.exact == "13/20"
    assert result.aggregate.citation_coverage.display == "0.6500"
    assert result.hard_failure_cases == ("GA-003", "GA-008")


def test_grounded_goldens_preserve_case_counts_and_zero_replay_gate_delta() -> None:
    grounded_run = grounded_run_module()
    result = grounded_run.execute_grounded_fixture(
        grounded_run.load_grounded_dataset(DATASET_PATH),
        grounded_run.load_grounded_observations(OBSERVATIONS_PATH),
    )

    assert [case.claim_support_precision.exact for case in result.case_evaluations] == [
        "1/1",
        "0/1",
        "0/1",
        "0/1",
        "0/1",
        "0/1",
        "1/2",
        "0/1",
        "0/1",
        "1/1",
    ]
    assert [case.citation_precision.exact for case in result.case_evaluations] == [
        "1/1",
        "1/2",
        "0/1",
        "0/1",
        "0/1",
        "0/1",
        "1/1",
        "1/1",
        "0/1",
        "1/1",
    ]
    assert [case.citation_coverage.exact for case in result.case_evaluations] == [
        "1/1",
        "1/1",
        "1/1",
        "0/1",
        "0/1",
        "0/1",
        "1/2",
        "1/1",
        "1/1",
        "1/1",
    ]
    assert result.aggregate is not None
    baseline_goldens = {
        "claim_support_precision": Fraction(1, 4),
        "citation_precision": Fraction(9, 20),
        "citation_coverage": Fraction(13, 20),
    }
    expected_gate_delta_percentage_points = {}
    for name, baseline in baseline_goldens.items():
        numerator, denominator = getattr(result.aggregate, name).exact.split("/")
        delta = (Fraction(int(numerator), int(denominator)) - baseline) * 100
        expected_gate_delta_percentage_points[name] = f"{float(delta):.2f}"
    assert expected_gate_delta_percentage_points == {
        "claim_support_precision": "0.00",
        "citation_precision": "0.00",
        "citation_coverage": "0.00",
    }


def test_grounded_run_is_invalid_when_a_verification_case_is_missing() -> None:
    grounded_run = grounded_run_module()
    dataset = grounded_run.load_grounded_dataset(DATASET_PATH)
    observations = grounded_run.load_grounded_observations(OBSERVATIONS_PATH)
    incomplete = observations.model_copy(update={"observations": observations.observations[:-1]})

    result = grounded_run.execute_grounded_fixture(dataset, incomplete)

    assert result.state == "INVALID"
    assert result.aggregate is None
    assert "SYS-GROUNDED-COVERAGE-INVALID" in result.failure_codes


def test_grounded_run_records_all_compatibility_versions() -> None:
    grounded_run = grounded_run_module()
    dataset = grounded_run.load_grounded_dataset(DATASET_PATH)
    observations = grounded_run.load_grounded_observations(OBSERVATIONS_PATH)

    result = grounded_run.execute_grounded_fixture(dataset, observations)

    assert result.evaluator_version == "grounded-answer-v1"
    assert result.proposition_contract_version == "claim-proposition-v1"
    assert result.traversal_contract_version == "claim-traversal-v1"
    assert result.normalizer_version == "claim-normalizer-v1"
    assert result.source_resolution_version == "source-text-resolution-v1"
    assert result.guard_version == "high-risk-guard-v1"


def test_grounded_source_text_resolution_uses_the_ax_sut_adapter() -> None:
    grounded_run = grounded_run_module()
    text = "제15조: 즉시 해고는 금지됩니다."
    source_digest = f"sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        return httpx.Response(
            200,
            json={
                "record_kind": "company_rule",
                "record_id": "rule-15",
                "text": text,
                "provenance": {"source_text_digest": source_digest},
                "correlation_id": "source:ga-001",
            },
        )

    adapter = AxHttpAdapter(
        AxHttpAdapterConfig(
            base_url="https://ax.example.test",
            sut_commit_sha=PINNED_AX_SHA,
            tenant_id="11111111-1111-1111-1111-111111111111",
            user_id="evaluation-plane",
            roles=("Executive",),
        ),
        transport=httpx.MockTransport(handler),
    )
    citation = GroundedCitation(
        record_kind="company_rule",
        record_id="rule-15",
        evidence_span_id="span-rule-15",
        source_text_digest=source_digest,
        claim_paths=("summary",),
    )

    resolutions = grounded_run.resolve_cited_source_texts(
        adapter=adapter,
        context=AxRequestContext(
            run_id="grounded-live-seam",
            case_id="GA-001",
            eval_correlation_id="eval:grounded-live-seam:GA-001",
        ),
        citations=(citation, citation),
    )

    assert requested_paths == ["/v1/retrieval/source-text/company_rule/rule-15"]
    assert resolutions[0].source_text_digest == source_digest
    assert resolutions[0].text == text


def test_grounded_run_is_invalid_when_a_metric_has_zero_applicable_cases() -> None:
    grounded_run = grounded_run_module()
    dataset = grounded_run.load_grounded_dataset(DATASET_PATH)
    observations = grounded_run.load_grounded_observations(OBSERVATIONS_PATH)
    no_coverage_cases = tuple(
        case.model_copy(
            update={
                "applicability": case.applicability.model_copy(update={"citation_coverage": False})
            }
        )
        for case in dataset.cases
    )
    no_coverage_dataset = dataset.model_copy(update={"cases": no_coverage_cases})

    result = grounded_run.execute_grounded_fixture(no_coverage_dataset, observations)

    assert result.state == "INVALID"
    assert result.aggregate is None
    assert "SYS-GROUNDED-COVERAGE-INVALID" in result.failure_codes
