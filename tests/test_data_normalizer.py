from datetime import date, datetime
from decimal import Decimal

import pytest

from backend.app.services.preprocessing.normalizer import (
    normalize_boolean,
    normalize_date,
    normalize_datetime,
    normalize_number,
    normalize_record,
    normalize_text,
    normalize_url,
    normalize_value,
)


def test_normalize_text():
    assert normalize_text("  Environmental   Consultant  ") == (
        "Environmental Consultant"
    )


def test_normalize_number_integer():
    assert normalize_number("42") == 42


def test_normalize_number_decimal():
    assert normalize_number("42.50") == Decimal("42.50")


def test_normalize_number_rejects_invalid_value():
    with pytest.raises(ValueError):
        normalize_number("not-a-number")


def test_normalize_boolean_true():
    assert normalize_boolean("YES") is True


def test_normalize_boolean_false():
    assert normalize_boolean("no") is False


def test_normalize_boolean_numeric():
    assert normalize_boolean(1) is True
    assert normalize_boolean(0) is False


def test_normalize_boolean_rejects_invalid_value():
    with pytest.raises(ValueError):
        normalize_boolean("maybe")


def test_normalize_date():
    result = normalize_date("2026-08-24")

    assert result == date(2026, 8, 24)


def test_normalize_datetime():
    result = normalize_datetime("2026-08-24T04:50:00")

    assert result == datetime(2026, 8, 24, 4, 50, 0)


def test_normalize_datetime_supports_utc_z():
    result = normalize_datetime("2026-08-24T04:50:00Z")

    assert result.isoformat() == "2026-08-24T04:50:00+00:00"


def test_normalize_url():
    result = normalize_url(
        "HTTPS://Example.COM/path?b=2&a=1"
    )

    assert result == (
        "https://example.com/path?b=2&a=1"
    )


def test_normalize_url_removes_default_https_port():
    result = normalize_url(
        "https://example.com:443/path"
    )

    assert result == "https://example.com/path"


def test_normalize_url_rejects_non_http_protocol():
    with pytest.raises(ValueError):
        normalize_url("ftp://example.com/file.csv")


def test_normalize_value_with_schema():
    assert normalize_value(
        "  Environmental Consultant  ",
        value_type="text",
    ) == "Environmental Consultant"

    assert normalize_value(
        "125",
        value_type="number",
    ) == 125

    assert normalize_value(
        "yes",
        value_type="boolean",
    ) is True


def test_normalize_value_none():
    assert normalize_value(None) is None


def test_normalize_record():
    record = {
        "title": "  Environmental Consultant ",
        "salary": "125000",
        "remote": "yes",
        "published": "2026-08-24",
    }

    schema = {
        "title": "text",
        "salary": "number",
        "remote": "boolean",
        "published": "date",
    }

    result = normalize_record(record, schema)

    assert result["title"] == "Environmental Consultant"
    assert result["salary"] == 125000
    assert result["remote"] is True
    assert result["published"] == date(2026, 8, 24)