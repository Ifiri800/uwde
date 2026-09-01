from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.quantification.bottom_up.activity import (
    ActivityData,
    validate_activity_data,
)


def test_valid_activity_data():
    activity = ActivityData(
        activity_id="ACT-001",
        source_id="SRC-001",
        quantity=100.0,
        unit="m3",
        period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 1, 31, tzinfo=timezone.utc),
    )

    validate_activity_data(activity)


def test_activity_data_rejects_negative_quantity():
    activity = ActivityData(
        activity_id="ACT-001",
        source_id="SRC-001",
        quantity=-1.0,
        unit="m3",
        period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 1, 31, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError):
        validate_activity_data(activity)


def test_activity_data_rejects_zero_or_empty_unit():
    activity = ActivityData(
        activity_id="ACT-001",
        source_id="SRC-001",
        quantity=100.0,
        unit="",
        period_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 1, 31, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError):
        validate_activity_data(activity)


def test_activity_data_requires_timezone_aware_dates():
    activity = ActivityData(
        activity_id="ACT-001",
        source_id="SRC-001",
        quantity=100.0,
        unit="m3",
        period_start=datetime(2026, 1, 1),
        period_end=datetime(2026, 1, 31),
    )

    with pytest.raises(ValueError):
        validate_activity_data(activity)


def test_activity_period_must_be_ordered():
    activity = ActivityData(
        activity_id="ACT-001",
        source_id="SRC-001",
        quantity=100.0,
        unit="m3",
        period_start=datetime(2026, 2, 1, tzinfo=timezone.utc),
        period_end=datetime(2026, 1, 31, tzinfo=timezone.utc),
    )

    with pytest.raises(ValueError):
        validate_activity_data(activity)
