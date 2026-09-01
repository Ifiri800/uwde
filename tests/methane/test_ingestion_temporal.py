from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.intelligence.methane.ingestion.temporal import (
    TemporalNormalizationError,
    duration_seconds,
    normalize_timestamp,
    synchronize_timestamps,
    to_utc,
    validate_temporal_order,
)


def test_to_utc_converts_timezone():
    value = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=timezone(timedelta(hours=1)),
    )

    result = to_utc(value)

    assert result.hour == 11
    assert result.tzinfo == timezone.utc


def test_to_utc_rejects_naive_datetime():
    with pytest.raises(TemporalNormalizationError):
        to_utc(datetime(2026, 8, 31, 12, 0))


def test_normalize_timestamp_returns_utc():
    value = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=timezone(timedelta(hours=1)),
    )

    result = normalize_timestamp(value)

    assert result.timezone == "UTC"
    assert result.value.tzinfo == timezone.utc
    assert result.value.hour == 11


def test_synchronize_timestamps():
    values = (
        datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc),
        datetime(
            2026,
            8,
            31,
            12,
            0,
            tzinfo=timezone(timedelta(hours=1)),
        ),
    )

    result = synchronize_timestamps(values)

    assert len(result) == 2
    assert result[0].value.hour == 10
    assert result[1].value.hour == 11
    assert result[0].value.tzinfo == timezone.utc
    assert result[1].value.tzinfo == timezone.utc


def test_duration_seconds():
    start = datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 31, 11, 30, tzinfo=timezone.utc)

    assert duration_seconds(start, end) == 5400.0


def test_duration_handles_different_timezones():
    start = datetime(
        2026,
        8,
        31,
        10,
        0,
        tzinfo=timezone.utc,
    )

    end = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=timezone(timedelta(hours=2)),
    )

    assert duration_seconds(start, end) == 0.0


def test_duration_rejects_reverse_order():
    start = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
    end = datetime(2026, 8, 31, 11, 0, tzinfo=timezone.utc)

    with pytest.raises(TemporalNormalizationError):
        duration_seconds(start, end)


def test_validate_temporal_order():
    values = (
        datetime(2026, 8, 31, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 8, 31, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc),
    )

    assert validate_temporal_order(values) is True


def test_validate_temporal_order_rejects_unsorted_values():
    values = (
        datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc),
        datetime(2026, 8, 31, 11, 0, tzinfo=timezone.utc),
    )

    assert validate_temporal_order(values) is False


def test_validate_temporal_order_allows_equal_timestamps():
    value = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)

    assert validate_temporal_order((value, value)) is True
