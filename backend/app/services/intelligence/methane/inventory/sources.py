from __future__ import annotations

from .models import EmissionSource, EmissionSourceType


def create_emission_source(
    source_id: str,
    name: str,
    source_type: EmissionSourceType,
    component_id: str,
    *,
    methane_relevant: bool = True,
    metadata: dict[str, object] | None = None,
) -> EmissionSource:
    return EmissionSource(
        id=source_id,
        name=name,
        source_type=source_type,
        component_id=component_id,
        methane_relevant=methane_relevant,
        metadata=metadata or {},
    )
