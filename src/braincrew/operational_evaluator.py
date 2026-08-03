"""Operational measurements with explicit latency and cost semantics."""

from __future__ import annotations

from decimal import Decimal
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

type LatencyDefinition = Literal[
    "client wall-clock from adapter call start through terminal response validation, "
    "including retries; excludes corpus identity and evaluator time"
]

OPERATIONAL_EVALUATOR_VERSION: Final[Literal["operational-v1"]] = "operational-v1"
CLIENT_TOTAL_LATENCY_DEFINITION: Final[LatencyDefinition] = (
    "client wall-clock from adapter call start through terminal response validation, "
    "including retries; excludes corpus identity and evaluator time"
)


class OperationalMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    latency_ms: Decimal = Field(ge=0)
    latency_definition: LatencyDefinition
    cost_usd: Decimal | None
    cost_status: Literal["measured", "unmeasured"]

    @model_validator(mode="after")
    def bind_cost_status(self) -> OperationalMeasurement:
        if self.cost_status == "unmeasured" and self.cost_usd is not None:
            raise ValueError("unmeasured operational cost must be null")
        if self.cost_status == "measured" and self.cost_usd is None:
            raise ValueError("measured operational cost requires a value")
        if self.cost_usd is not None and self.cost_usd < 0:
            raise ValueError("measured operational cost must be non-negative")
        return self


class OperationalCaseEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    evaluator_version: Literal["operational-v1"]
    latency_ms: Decimal
    latency_definition: LatencyDefinition
    cost_usd: Decimal | None
    cost_status: Literal["measured", "unmeasured"]


def evaluate_operational_measurement(
    measurement: OperationalMeasurement,
) -> OperationalCaseEvaluation:
    """Preserve a validated measurement under the versioned operational contract."""
    return OperationalCaseEvaluation(
        evaluator_version=OPERATIONAL_EVALUATOR_VERSION,
        latency_ms=measurement.latency_ms,
        latency_definition=measurement.latency_definition,
        cost_usd=measurement.cost_usd,
        cost_status=measurement.cost_status,
    )
