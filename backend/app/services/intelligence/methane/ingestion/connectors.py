from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol

from .models import IngestionSourceType


class ConnectorStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


@dataclass(frozen=True)
class ConnectorResult:
    source_id: str
    source_type: IngestionSourceType
    records: tuple[Mapping[str, Any], ...]
    status: ConnectorStatus = ConnectorStatus.CONNECTED
    message: str | None = None

    @property
    def record_count(self) -> int:
        return len(self.records)


class IngestionConnector(Protocol):
    source_type: IngestionSourceType

    def connect(self) -> ConnectorStatus:
        ...

    def disconnect(self) -> ConnectorStatus:
        ...

    def fetch(self) -> ConnectorResult:
        ...


@dataclass
class MemoryConnector:
    source_id: str
    source_type: IngestionSourceType
    records: tuple[Mapping[str, Any], ...] = ()
    connected: bool = False

    def connect(self) -> ConnectorStatus:
        self.connected = True
        return ConnectorStatus.CONNECTED

    def disconnect(self) -> ConnectorStatus:
        self.connected = False
        return ConnectorStatus.DISCONNECTED

    def fetch(self) -> ConnectorResult:
        if not self.connected:
            raise RuntimeError("connector is not connected")

        return ConnectorResult(
            source_id=self.source_id,
            source_type=self.source_type,
            records=self.records,
        )


def create_connector(
    source_id: str,
    source_type: IngestionSourceType,
    records: tuple[Mapping[str, Any], ...] = (),
) -> MemoryConnector:
    return MemoryConnector(
        source_id=source_id,
        source_type=source_type,
        records=records,
    )


def supported_source_types() -> frozenset[IngestionSourceType]:
    return frozenset(IngestionSourceType)
