from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime

from .errors import QuantificationValidationError
from .models import (
    ActivityData,
    EmissionEstimate,
    EmissionFactor,
    Measurement,
    QuantificationInput,
    QuantificationResult,
    RemoteObservation,
)


def validate_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise QuantificationValidationError(
            f"{field_name} is required"
        )


def validate_non_negative(
    value: float,
    field_name: str,
) -> None:
    if not isinstance(value, (int, float)):
        raise QuantificationValidationError(
            f"{field_name} must be numeric"
        )

    if not math.isfinite(float(value)):
        raise QuantificationValidationError(
            f"{field_name} must be finite"
        )

    if value < 0:
        raise QuantificationValidationError(
            f"{field_name} cannot be negative"
        )


def validate_timezone_aware(
    value: datetime | None,
    field_name: str,
) -> None:
    if value is not None and value.tzinfo is None:
        raise QuantificationValidationError(
            f"{field_name} must be timezone-aware"
        )


def validate_mapping(
    value: Mapping,
    field_name: str = "metadata",
) -> None:
    if not isinstance(value, Mapping):
        raise QuantificationValidationError(
            f"{field_name} must be a mapping"
        )


def validate_quantification_input(
    value: QuantificationInput,
) -> QuantificationInput:
    if not isinstance(value, QuantificationInput):
        raise QuantificationValidationError(
            "value must be a QuantificationInput instance"
        )

    validate_non_empty(value.input_id, "input_id")
    validate_non_negative(value.value, "value")
    validate_non_empty(value.unit, "unit")
    validate_mapping(value.metadata)

    validate_timezone_aware(
        value.timestamp,
        "timestamp",
    )

    return value


def validate_emission_factor(
    value: EmissionFactor,
) -> EmissionFactor:
    if not isinstance(value, EmissionFactor):
        raise QuantificationValidationError(
            "value must be an EmissionFactor instance"
        )

    validate_non_empty(value.factor_id, "factor_id")
    validate_non_negative(value.value, "value")
    validate_non_empty(value.unit, "unit")
    validate_non_empty(value.source, "source")

    if value.uncertainty is not None:
        validate_non_negative(
            value.uncertainty,
            "uncertainty",
        )

    validate_mapping(value.metadata)

    return value


def validate_activity_data(
    value: ActivityData,
) -> ActivityData:
    if not isinstance(value, ActivityData):
        raise QuantificationValidationError(
            "value must be an ActivityData instance"
        )

    validate_non_empty(value.activity_id, "activity_id")
    validate_non_negative(value.value, "value")
    validate_non_empty(value.unit, "unit")
    validate_non_empty(value.activity_type, "activity_type")

    validate_timezone_aware(
        value.timestamp,
        "timestamp",
    )

    validate_mapping(value.metadata)

    return value


def validate_measurement(
    value: Measurement,
) -> Measurement:
    if not isinstance(value, Measurement):
        raise QuantificationValidationError(
            "value must be a Measurement instance"
        )

    validate_non_empty(
        value.measurement_id,
        "measurement_id",
    )
    validate_non_negative(value.value, "value")
    validate_non_empty(value.unit, "unit")
    validate_non_empty(
        value.measurement_type,
        "measurement_type",
    )

    validate_timezone_aware(
        value.timestamp,
        "timestamp",
    )

    if value.uncertainty is not None:
        validate_non_negative(
            value.uncertainty,
            "uncertainty",
        )

    validate_mapping(value.metadata)

    return value


def validate_remote_observation(
    value: RemoteObservation,
) -> RemoteObservation:
    if not isinstance(value, RemoteObservation):
        raise QuantificationValidationError(
            "value must be a RemoteObservation instance"
        )

    validate_non_empty(
        value.observation_id,
        "observation_id",
    )
    validate_non_negative(value.value, "value")
    validate_non_empty(value.unit, "unit")
    validate_non_empty(
        value.observation_type,
        "observation_type",
    )

    validate_timezone_aware(
        value.timestamp,
        "timestamp",
    )

    if value.latitude is not None:
        if not -90.0 <= value.latitude <= 90.0:
            raise QuantificationValidationError(
                "latitude must be between -90 and 90"
            )

    if value.longitude is not None:
        if not -180.0 <= value.longitude <= 180.0:
            raise QuantificationValidationError(
                "longitude must be between -180 and 180"
            )

    if value.uncertainty is not None:
        validate_non_negative(
            value.uncertainty,
            "uncertainty",
        )

    validate_mapping(value.metadata)

    return value


def validate_emission_estimate(
    value: EmissionEstimate,
) -> EmissionEstimate:
    if not isinstance(value, EmissionEstimate):
        raise QuantificationValidationError(
            "value must be an EmissionEstimate instance"
        )

    validate_non_empty(
        value.estimate_id,
        "estimate_id",
    )
    validate_non_negative(value.value, "value")
    validate_non_empty(value.unit, "unit")

    validate_timezone_aware(
        value.timestamp,
        "timestamp",
    )

    if value.uncertainty is not None:
        validate_non_negative(
            value.uncertainty,
            "uncertainty",
        )

    validate_mapping(value.metadata)

    return value


def validate_quantification_result(
    value: QuantificationResult,
) -> QuantificationResult:
    if not isinstance(value, QuantificationResult):
        raise QuantificationValidationError(
            "value must be a QuantificationResult instance"
        )

    validate_emission_estimate(value.estimate)

    for item in value.inputs:
        validate_quantification_input(item)

    return value
