from __future__ import annotations

from .hierarchy import validate_hierarchy
from .models import EmissionSource, InventoryEntity, MethaneInventory


class InventoryRegistry:
    def __init__(self) -> None:
        self.inventory = MethaneInventory()

    def register_entity(self, entity: InventoryEntity) -> None:
        self.inventory.add_entity(entity)

    def register_source(self, source: EmissionSource) -> None:
        if source.component_id not in self.inventory.entities:
            raise ValueError(
                f"component not found: {source.component_id}"
            )

        self.inventory.add_source(source)

    def validate(self) -> list[str]:
        return validate_hierarchy(
            list(self.inventory.entities.values())
        )

    def get_entity(self, entity_id: str) -> InventoryEntity | None:
        return self.inventory.entities.get(entity_id)

    def get_source(self, source_id: str) -> EmissionSource | None:
        return self.inventory.emission_sources.get(source_id)

    def sources_for_component(
        self,
        component_id: str,
    ) -> list[EmissionSource]:
        return [
            source
            for source in self.inventory.emission_sources.values()
            if source.component_id == component_id
        ]
