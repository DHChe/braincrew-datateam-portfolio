import json
from pathlib import Path
from typing import Any, TypedDict, cast

import pytest
from pydantic import ValidationError

from braincrew import live_preflight
from braincrew.grounded_contracts import (
    AnswerPathHealth,
    GroundedObservation,
    GroundedObservationBatch,
)

OBSERVATIONS_PATH = Path("tests/fixtures/grounded_observations_v1.json")
AX_ANSWER_PATH_CENSUS_PATH = Path("tests/fixtures/ax_answer_path_emission_states_v1.json")


class _AxAnswerPathEmissionShape(TypedDict):
    id: str
    source_sites: list[int]
    llm_call_performed: bool
    llm_call_succeeded: bool | None
    failure_reason_example: str | None
    answer_quality_available: bool


def _answer_path_census() -> dict[str, Any]:
    return cast(
        dict[str, Any],
        json.loads(AX_ANSWER_PATH_CENSUS_PATH.read_text(encoding="utf-8")),
    )


AX_ANSWER_PATH_EMISSION_SHAPES = cast(
    list[_AxAnswerPathEmissionShape],
    _answer_path_census()["distinct_emission_shapes"],
)


def _fixture_batch() -> GroundedObservationBatch:
    return GroundedObservationBatch.model_validate_json(
        OBSERVATIONS_PATH.read_text(encoding="utf-8")
    )


def _observation_payload(**overrides: Any) -> dict[str, Any]:
    payload = _fixture_batch().observations[0].model_dump(mode="python")
    payload.update(overrides)
    return payload


def test_ax_answer_path_emission_census_pins_every_source_call_site() -> None:
    census = _answer_path_census()
    source = cast(dict[str, Any], census["source"])
    assert all("failure_reason_example" in shape for shape in AX_ANSWER_PATH_EMISSION_SHAPES)
    assert all("failure_reason" not in shape for shape in AX_ANSWER_PATH_EMISSION_SHAPES)
    distinct_shapes = {
        (
            shape["llm_call_performed"],
            shape["llm_call_succeeded"],
            shape["failure_reason_example"] is not None,
        )
        for shape in AX_ANSWER_PATH_EMISSION_SHAPES
    }

    assert census["schema_version"] == "ax-answer-path-emission-state-census-v1"
    assert census["enumerated_at"] == "2026-07-31"
    assert source["commit_sha"] == "1ead1331166538e417027a7064179f15c5cfbf61"
    assert source["sha256"] == "681956917adb17453b8ace3e03dc6da9422177850286be2582f9ff3bacf2c702"
    assert source["provider_metadata_call_sites"] == [217, 541, 595, 676]
    assert source["template_result_call_sites"] == [71, 87, 111, 157, 187]
    assert distinct_shapes == {
        (True, True, False),
        (True, False, True),
        (False, None, True),
        (False, None, False),
    }


def test_ax_answer_path_census_matches_commit_under_test() -> None:
    source = cast(dict[str, Any], _answer_path_census()["source"])
    census_sha = cast(str, source["commit_sha"])

    if census_sha != live_preflight.PINNED_AX_SHA:
        pytest.fail(
            "AX answer-path census commit must match the AX commit under test; "
            f"re-enumerate the census (census={census_sha}, "
            f"PINNED_AX_SHA={live_preflight.PINNED_AX_SHA})"
        )


@pytest.mark.parametrize(
    "shape",
    AX_ANSWER_PATH_EMISSION_SHAPES,
    ids=[shape["id"] for shape in AX_ANSWER_PATH_EMISSION_SHAPES],
)
def test_answer_path_health_represents_every_ax_emission_shape(
    shape: _AxAnswerPathEmissionShape,
) -> None:
    health = AnswerPathHealth(
        llm_call_performed=shape["llm_call_performed"],
        llm_call_succeeded=shape["llm_call_succeeded"],
        failure_reason=shape["failure_reason_example"],
    )

    assert health.llm_call_performed is shape["llm_call_performed"]
    assert health.llm_call_succeeded is shape["llm_call_succeeded"]
    assert health.failure_reason == shape["failure_reason_example"]
    assert health.answer_quality_available is shape["answer_quality_available"]


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        (
            {
                "llm_call_performed": True,
                "llm_call_succeeded": False,
                "failure_reason": None,
            },
            "failed LLM call requires a failure reason",
        ),
        (
            {
                "llm_call_performed": True,
                "llm_call_succeeded": True,
                "failure_reason": "provider_error",
            },
            "successful LLM call cannot carry a failure reason",
        ),
        (
            {
                "llm_call_performed": False,
                "llm_call_succeeded": True,
                "failure_reason": None,
            },
            "unperformed LLM call cannot report success",
        ),
        (
            {
                "llm_call_performed": False,
                "llm_call_succeeded": False,
                "failure_reason": "provider_error",
            },
            "unperformed LLM call cannot report success",
        ),
        (
            {
                "llm_call_performed": True,
                "llm_call_succeeded": None,
                "failure_reason": "provider_error",
            },
            "performed LLM call must report success or failure",
        ),
    ],
    ids=[
        "performed-failure-without-reason",
        "success-with-reason",
        "unperformed-with-success",
        "unperformed-with-failure-outcome",
        "performed-without-outcome",
    ],
)
def test_answer_path_health_refuses_contradictory_call_states(
    payload: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        AnswerPathHealth.model_validate(payload)


@pytest.mark.parametrize(
    "payload",
    [
        {
            "llm_call_performed": 1,
            "llm_call_succeeded": True,
            "failure_reason": None,
        },
        {
            "llm_call_performed": "true",
            "llm_call_succeeded": True,
            "failure_reason": None,
        },
        {
            "llm_call_performed": True,
            "llm_call_succeeded": 1,
            "failure_reason": None,
        },
        {
            "llm_call_performed": True,
            "llm_call_succeeded": "true",
            "failure_reason": None,
        },
        {
            "llm_call_performed": True,
            "llm_call_succeeded": "false",
            "failure_reason": "provider_error",
        },
    ],
    ids=[
        "performed-int",
        "performed-string",
        "succeeded-int",
        "succeeded-true-string",
        "succeeded-false-string",
    ],
)
def test_answer_path_health_refuses_coerced_booleans(
    payload: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        AnswerPathHealth.model_validate(payload)


def test_answer_path_health_requires_performed_state() -> None:
    with pytest.raises(ValidationError, match="llm_call_performed"):
        AnswerPathHealth.model_validate(
            {
                "llm_call_succeeded": True,
                "failure_reason": None,
            }
        )


@pytest.mark.parametrize(
    ("available", "error", "message"),
    [
        (True, None, "error must match answer-path failure reason"),
        (False, "different_error", "error must match answer-path failure reason"),
    ],
    ids=["availability", "error"],
)
def test_grounded_observation_binds_state_to_answer_path_health(
    available: bool,
    error: str | None,
    message: str,
) -> None:
    with pytest.raises(ValidationError, match=message):
        GroundedObservation.model_validate(
            _observation_payload(
                available=available,
                error=error,
                answer_path={
                    "llm_call_performed": True,
                    "llm_call_succeeded": False,
                    "failure_reason": "provider_error",
                },
            )
        )


def test_live_grounded_observation_batch_requires_answer_path_health() -> None:
    fixture_batch = _fixture_batch()

    with pytest.raises(
        ValidationError,
        match="live grounded observations require answer-path health",
    ):
        GroundedObservationBatch.model_validate(
            {
                **fixture_batch.model_dump(mode="python"),
                "adapter_version": "ax-sut-http-v1",
                "observations": [fixture_batch.observations[0].model_dump(mode="python")],
            }
        )
