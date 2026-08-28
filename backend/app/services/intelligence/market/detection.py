from __future__ import annotations

from backend.app.services.intelligence.domain.signals import Signal
from .entities import MarketObservation
from .signals import generate_market_signal


class MarketDetectionEngine:
    """
    Domain-specific detection adapter for market observations.

    Converts validated MarketObservation records into common
    intelligence Signals while preserving observation timestamps,
    confidence, values, evidence, and source metadata.
    """

    def detect(
        self,
        observation: MarketObservation,
    ) -> list[Signal]:
        if not isinstance(observation, MarketObservation):
            raise TypeError(
                "observation must be a MarketObservation"
            )

        return [generate_market_signal(observation)]

    def detect_many(
        self,
        observations: list[MarketObservation],
    ) -> list[Signal]:
        if not isinstance(observations, list):
            raise TypeError(
                "observations must be a list"
            )

        signals: list[Signal] = []
        seen_observation_ids: set[str] = set()

        for observation in observations:
            if not isinstance(
                observation,
                MarketObservation,
            ):
                raise TypeError(
                    "observations must contain only "
                    "MarketObservation objects"
                )

            if observation.observation_id in seen_observation_ids:
                continue

            seen_observation_ids.add(
                observation.observation_id
            )

            signals.extend(
                self.detect(observation)
            )

        return signals


def detect_market_signal(
    observation: MarketObservation,
) -> list[Signal]:
    return MarketDetectionEngine().detect(observation)


def detect_market_signals(
    observations: list[MarketObservation],
) -> list[Signal]:
    return MarketDetectionEngine().detect_many(observations)
