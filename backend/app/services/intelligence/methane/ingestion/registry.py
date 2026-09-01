from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .connectors import (
    ConnectorStatus,
    IngestionConnector,
)
from .models import (
    IngestionMetadata,
    IngestionSourceType,
)


class RegistryError(ValueError):
    """Raised when ingestion registry rules are violated."""


@dataclass(frozen=True)
class RegisteredSource:
    """Immutable registration record for an ingestion source."""

    metadata: IngestionMetadata
    connector: IngestionConnector

    @property
    def source_id(self) -> str:
        return self.metadata.source_id

    @property
    def source_type(self) -> IngestionSourceType:
        return self.metadata.source_type


class IngestionRegistry:
    """Registry for methane ingestion sources and their connectors."""

    def __init__(
        self,
        sources: Iterable[RegisteredSource] = (),
    ) -> None:
        self._sources: dict[str, RegisteredSource] = {}

        for source in sources:
            self.register(source)

    def register(self, source: RegisteredSource) -> RegisteredSource:
        if not isinstance(source, RegisteredSource):
            raise TypeError("source must be RegisteredSource")

        source_id = source.source_id

        if not source_id.strip():
            raise RegistryError("source_id is required")

        if source_id in self._sources:
            raise RegistryError(
                f"source already registered: {source_id}"
            )

        if source.connector.source_type != source.source_type:
            raise RegistryError(
                "connector source_type does not match metadata"
            )

        self._sources[source_id] = source
        return source

    def unregister(self, source_id: str) -> RegisteredSource:
        if not isinstance(source_id, str):
            raise TypeError("source_id must be a string")

        if source_id not in self._sources:
            raise RegistryError(
                f"source not registered: {source_id}"
            )

        return self._sources.pop(source_id)

    def get(self, source_id: str) -> RegisteredSource:
        if not isinstance(source_id, str):
            raise TypeError("source_id must be a string")

        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise RegistryError(
                f"source not registered: {source_id}"
            ) from exc

    def contains(self, source_id: str) -> bool:
        return source_id in self._sources

    def list_sources(self) -> tuple[RegisteredSource, ...]:
        return tuple(self._sources.values())

    def by_type(
        self,
        source_type: IngestionSourceType,
    ) -> tuple[RegisteredSource, ...]:
        if not isinstance(source_type, IngestionSourceType):
            raise TypeError(
                "source_type must be IngestionSourceType"
            )

        return tuple(
            source
            for source in self._sources.values()
            if source.source_type == source_type
        )

    def connect(self, source_id: str) -> ConnectorStatus:
        source = self.get(source_id)
        return source.connector.connect()

    def disconnect(self, source_id: str) -> ConnectorStatus:
        source = self.get(source_id)
        return source.connector.disconnect()

    def status(self, source_id: str) -> ConnectorStatus:
        source = self.get(source_id)

        connector = source.connector

        if hasattr(connector, "connected"):
            return (
                ConnectorStatus.CONNECTED
                if getattr(connector, "connected")
                else ConnectorStatus.DISCONNECTED
            )

        return ConnectorStatus.AVAILABLE

    def count(self) -> int:
        return len(self._sources)


def create_registry(
    sources: Iterable[RegisteredSource] = (),
) -> IngestionRegistry:
    """Create an ingestion registry."""
    return IngestionRegistry(sources)
