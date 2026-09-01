from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.ingestion.connectors import (
    ConnectorStatus,
    create_connector,
)
from backend.app.services.intelligence.methane.ingestion.models import (
    IngestionMetadata,
    IngestionSourceType,
)
from backend.app.services.intelligence.methane.ingestion.registry import (
    IngestionRegistry,
    RegisteredSource,
    RegistryError,
    create_registry,
)


def make_source(
    source_id: str = "source-1",
    source_type: IngestionSourceType = IngestionSourceType.API,
) -> RegisteredSource:
    metadata = IngestionMetadata(
        source_id=source_id,
        source_type=source_type,
        source_name="Test Source",
        acquired_at=datetime.now(timezone.utc),
    )

    connector = create_connector(
        source_id=source_id,
        source_type=source_type,
    )

    return RegisteredSource(
        metadata=metadata,
        connector=connector,
    )


def test_register_and_get():
    registry = IngestionRegistry()
    source = make_source()

    registry.register(source)

    assert registry.get("source-1") is source
    assert registry.contains("source-1")
    assert registry.count() == 1


def test_duplicate_registration_rejected():
    registry = IngestionRegistry()
    source = make_source()

    registry.register(source)

    with pytest.raises(RegistryError):
        registry.register(source)


def test_unknown_source_rejected():
    registry = IngestionRegistry()

    with pytest.raises(RegistryError):
        registry.get("missing")


def test_unregister():
    registry = IngestionRegistry()
    source = make_source()

    registry.register(source)

    removed = registry.unregister("source-1")

    assert removed is source
    assert not registry.contains("source-1")
    assert registry.count() == 0


def test_list_sources():
    registry = IngestionRegistry(
        [
            make_source("a"),
            make_source("b"),
        ]
    )

    sources = registry.list_sources()

    assert len(sources) == 2
    assert sources[0].source_id == "a"
    assert sources[1].source_id == "b"


def test_by_type():
    registry = IngestionRegistry(
        [
            make_source("api-1", IngestionSourceType.API),
            make_source("api-2", IngestionSourceType.API),
            make_source("sensor-1", IngestionSourceType.SENSOR),
        ]
    )

    results = registry.by_type(IngestionSourceType.API)

    assert len(results) == 2
    assert all(
        item.source_type == IngestionSourceType.API
        for item in results
    )


def test_connect_and_disconnect():
    registry = IngestionRegistry()
    registry.register(make_source())

    assert registry.connect("source-1") == ConnectorStatus.CONNECTED
    assert registry.status("source-1") == ConnectorStatus.CONNECTED

    assert registry.disconnect("source-1") == ConnectorStatus.DISCONNECTED
    assert registry.status("source-1") == ConnectorStatus.DISCONNECTED


def test_source_type_mismatch_rejected():
    metadata = IngestionMetadata(
        source_id="source-1",
        source_type=IngestionSourceType.API,
        source_name="Test Source",
        acquired_at=datetime.now(timezone.utc),
    )

    connector = create_connector(
        source_id="source-1",
        source_type=IngestionSourceType.SENSOR,
    )

    source = RegisteredSource(
        metadata=metadata,
        connector=connector,
    )

    with pytest.raises(RegistryError):
        IngestionRegistry().register(source)


def test_create_registry():
    source = make_source()

    registry = create_registry([source])

    assert registry.count() == 1
    assert registry.get("source-1") is source
