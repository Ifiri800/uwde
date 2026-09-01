from datetime import datetime, timezone

from backend.app.services.intelligence.methane.quantification.models import (
    ActivityData,
    EmissionEstimate,
    EmissionFactor,
    EstimateStatus,
    Measurement,
    QuantificationInput,
    QuantificationLevel,
    QuantificationMethod,
    QuantificationResult,
    RemoteObservation,
)


def test_quantification_input():
    value = QuantificationInput(
        input_id="i-1",
        method=QuantificationMethod.BOTTOM_UP,
        level=QuantificationLevel.FACILITY,
        value=10.0,
        unit="kg_ch4",
    )

    assert value.value == 10.0
    assert value.method == QuantificationMethod.BOTTOM_UP


def test_emission_estimate():
    estimate = EmissionEstimate(
        estimate_id="e-1",
        method=QuantificationMethod.BOTTOM_UP,
        level=QuantificationLevel.FACILITY,
        value=25.0,
        unit="kg_ch4",
    )

    assert estimate.status == EstimateStatus.ESTIMATED
    assert not estimate.has_uncertainty


def test_emission_estimate_uncertainty():
    estimate = EmissionEstimate(
        estimate_id="e-2",
        method=QuantificationMethod.MEASUREMENT,
        level=QuantificationLevel.SOURCE,
        value=25.0,
        unit="kg_ch4",
        uncertainty=2.5,
    )

    assert estimate.has_uncertainty


def test_quantification_result():
    estimate = EmissionEstimate(
        estimate_id="e-3",
        method=QuantificationMethod.TOP_DOWN,
        level=QuantificationLevel.SITE,
        value=50.0,
        unit="kg_ch4",
    )

    result = QuantificationResult(
        estimate=estimate,
        warnings=("low confidence",),
    )

    assert result.value == 50.0
    assert result.has_warnings
    assert result.input_count == 0


def test_emission_factor():
    factor = EmissionFactor(
        factor_id="ef-1",
        value=0.5,
        unit="kg_ch4/unit",
        source="test",
        tier="Tier 1",
    )

    assert factor.value == 0.5
    assert factor.tier == "Tier 1"


def test_activity_data():
    activity = ActivityData(
        activity_id="a-1",
        value=100.0,
        unit="units",
        activity_type="throughput",
    )

    assert activity.value == 100.0


def test_measurement():
    measurement = Measurement(
        measurement_id="m-1",
        value=5.0,
        unit="kg_ch4/hour",
        measurement_type="source",
    )

    assert measurement.value == 5.0


def test_remote_observation():
    observation = RemoteObservation(
        observation_id="r-1",
        value=12.0,
        unit="kg_ch4/hour",
        observation_type="satellite",
        latitude=5.5,
        longitude=6.5,
    )

    assert observation.observation_type == "satellite"
    assert observation.latitude == 5.5


def test_timestamp_support():
    timestamp = datetime.now(timezone.utc)

    activity = ActivityData(
        activity_id="a-2",
        value=1.0,
        unit="unit",
        activity_type="production",
        timestamp=timestamp,
    )

    assert activity.timestamp == timestamp
