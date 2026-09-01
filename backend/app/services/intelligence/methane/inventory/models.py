from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class InventoryEntityType(str, Enum):
    OPERATOR = "operator"
    ASSET = "asset"
    FIELD = "field"
    FACILITY = "facility"
    EQUIPMENT = "equipment"
    COMPONENT = "component"


class EmissionSourceType(str, Enum):
    FUGITIVE = "fugitive"
    VENTING = "venting"
    FLARING = "flaring"
    COMBUSTION = "combustion"
    PROCESS = "process"
    OTHER_METHANE = "other_methane"


@dataclass(frozen=True)
class InventoryEntity:
    id: str
    name: str
    entity_type: InventoryEntityType
    parent_id: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id is required")
        if not self.name.strip():
            raise ValueError("name is required")


@dataclass(frozen=True)
class EmissionSource:
    id: str
    name: str
    source_type: EmissionSourceType
    component_id: str
    methane_relevant: bool = True
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("id is required")
        if not self.name.strip():
            raise ValueError("name is required")
        if not self.component_id.strip():
            raise ValueError("component_id is required")


@dataclass
class MethaneInventory:
    entities: dict[str, InventoryEntity] = field(default_factory=dict)
    emission_sources: dict[str, EmissionSource] = field(default_factory=dict)

    def add_entity(self, entity: InventoryEntity) -> None:
        if entity.id in self.entities:
            raise ValueError(f"duplicate inventory entity: {entity.id}")
        self.entities[entity.id] = entity

    def add_source(self, source: EmissionSource) -> None:
        if source.id in self.emission_sources:
            raise ValueError(f"duplicate emission source: {source.id}")
        self.emission_sources[source.id] = source
