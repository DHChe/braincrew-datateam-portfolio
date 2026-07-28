from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError


def test_latency_definition_names_retries_without_claiming_nonexistent_backoff() -> None:
    from braincrew.operational_evaluator import CLIENT_TOTAL_LATENCY_DEFINITION

    if "including retries;" not in CLIENT_TOTAL_LATENCY_DEFINITION:
        pytest.fail(f"latency definition lost retry coverage: {CLIENT_TOTAL_LATENCY_DEFINITION}")
    if "backoff" in CLIENT_TOTAL_LATENCY_DEFINITION:
        pytest.fail(
            "latency definition claims nonexistent retry backoff: "
            f"{CLIENT_TOTAL_LATENCY_DEFINITION}"
        )


def test_operational_evaluator_preserves_measured_latency_and_explicit_unmeasured_cost() -> None:
    from braincrew.operational_evaluator import (
        CLIENT_TOTAL_LATENCY_DEFINITION,
        OPERATIONAL_EVALUATOR_VERSION,
        OperationalMeasurement,
        evaluate_operational_measurement,
    )

    measurement = OperationalMeasurement(
        latency_ms=Decimal("12.5"),
        latency_definition=CLIENT_TOTAL_LATENCY_DEFINITION,
        cost_usd=None,
        cost_status="unmeasured",
    )

    result = evaluate_operational_measurement(measurement)

    assert result.evaluator_version == OPERATIONAL_EVALUATOR_VERSION
    assert result.latency_ms == Decimal("12.5")
    assert result.latency_definition == CLIENT_TOTAL_LATENCY_DEFINITION
    assert result.cost_usd is None
    assert result.cost_status == "unmeasured"


def test_operational_measurement_refuses_zero_as_a_substitute_for_unmeasured_cost() -> None:
    from braincrew.operational_evaluator import (
        CLIENT_TOTAL_LATENCY_DEFINITION,
        OperationalMeasurement,
    )

    with pytest.raises(
        ValidationError,
        match="unmeasured operational cost must be null",
    ):
        OperationalMeasurement(
            latency_ms=Decimal("1"),
            latency_definition=CLIENT_TOTAL_LATENCY_DEFINITION,
            cost_usd=Decimal("0"),
            cost_status="unmeasured",
        )


def test_operational_measurement_refuses_a_measured_cost_without_a_value() -> None:
    from braincrew.operational_evaluator import (
        CLIENT_TOTAL_LATENCY_DEFINITION,
        OperationalMeasurement,
    )

    with pytest.raises(
        ValidationError,
        match="measured operational cost requires a value",
    ):
        OperationalMeasurement(
            latency_ms=Decimal("1"),
            latency_definition=CLIENT_TOTAL_LATENCY_DEFINITION,
            cost_usd=None,
            cost_status="measured",
        )
