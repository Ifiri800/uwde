from __future__ import annotations

from .models import AcquisitionCategory, AcquisitionObservation, AcquisitionRegistry


class AcquisitionObservationRegistry:
    def __init__(self) -> None:
        self.registry = AcquisitionRegistry()

    def register(self, observation: AcquisitionObservation) -> None:
        self.registry.add(observation)

    def get(self, observation_id: str) -> AcquisitionObservation | None:
        return self.registry.get(observation_id)

    def by_category(
        self,
        category: AcquisitionCategory,
    ) -> list[AcquisitionObservation]:
        return self.registry.by_category(category)

    def count(self) -> int:
        return len(self.registry.observations)
