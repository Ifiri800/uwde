import pytest

from backend.app.services.intelligence.methane.ingestion.connectors import (
    ConnectorStatus,
    create_connector,
    supported_source_types,
)
from backend.app.services.intelligence.methane.ingestion.models import (
    IngestionSourceType,
)


def test_create_api_connector():
    connector = create_connector(
        "SRC-001",
        IngestionSourceType.API,
    )

    assert connector.source_id == "SRC-001"
    assert connector.source_type == IngestionSourceType.API


def test_connector_starts_disconnected():
    connector = create_connector(
        "SRC-001",
        IngestionSourceType.FILE,
    )

    assert connector.connected is False


def test_connect():
    connector = create_connector(
        "SRC-001",
        IngestionSourceType.SENSOR,
    )

    assert connector.connect() == ConnectorStatus.CONNECTED
    assert connector.connected is True


def test_disconnect():
    connector = create_connector(
        "SRC-001",
        IngestionSourceType.SATELLITE,
    )

    connector.connect()

    assert connector.disconnect() == ConnectorStatus.DISCONNECTED
    assert connector.connected is False


def test_fetch_requires_connection():
    connector = create_connector(
        "SRC-001",
        IngestionSourceType.GIS,
    )

    with pytest.raises(RuntimeError):
        connector.fetch()


def test_fetch_returns_records():
    records = (
        {"facility_id": "FAC-001", "methane_kg": 12.5},
        {"facility_id": "FAC-002", "methane_kg": 8.2},
    )

    connector = create_connector(
        "SRC-001",
        IngestionSourceType.API,
        records,
    )

    connector.connect()

    result = connector.fetch()

    assert result.record_count == 2
    assert result.records[0]["facility_id"] == "FAC-001"


def test_fetch_preserves_source_type():
    connector = create_connector(
        "SRC-001",
        IngestionSourceType.SATELLITE,
        ({"plume": True},),
    )

    connector.connect()

    result = connector.fetch()

    assert result.source_type == IngestionSourceType.SATELLITE


def test_supported_source_types_include_required_sources():
    supported = supported_source_types()

    assert IngestionSourceType.API in supported
    assert IngestionSourceType.FILE in supported
    assert IngestionSourceType.SENSOR in supported
    assert IngestionSourceType.SATELLITE in supported
    assert IngestionSourceType.GIS in supported
    assert IngestionSourceType.MANUAL in supported
    assert IngestionSourceType.DATABASE in supported


def test_empty_connector_returns_zero_records():
    connector = create_connector(
        "SRC-001",
        IngestionSourceType.MANUAL,
    )

    connector.connect()

    result = connector.fetch()

    assert result.record_count == 0
