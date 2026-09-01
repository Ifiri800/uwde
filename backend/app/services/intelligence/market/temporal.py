from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from backend.app.services.intelligence.domain.signals import Signal


@dataclass(frozen=True)
class TemporalSignalHistory:
    """
    Explainable chronological history of related intelligence signals.
    """

    signal_type: object
    entity_id: str
    signals: tuple[Signal, ...]
    first_observed_at: datetime
    latest_observed_at: datetime
    observation_count: int
    repeated_observation_count: int
    time_span_seconds: float

    @property
    def is_recurring(self) -> bool:
        return self.repeated_observation_count > 0

    @property
    def latest_signal(self) -> Signal:
        return self.signals[-1]

    @property
    def confidence_history(self) -> tuple[float, ...]:
        return tuple(
            signal.confidence
            for signal in self.signals
        )

    @property
    def strength_history(self) -> tuple[float, ...]:
        return tuple(
            signal.strength
            for signal in self.signals
        )

    def to_dict(self) -> dict:
        return {
            "signal_type": str(self.signal_type),
            "entity_id": self.entity_id,
            "signals": [
                signal.model_dump(mode="json")
                for signal in self.signals
            ],
            "first_observed_at": self.first_observed_at.isoformat(),
            "latest_observed_at": self.latest_observed_at.isoformat(),
            "observation_count": self.observation_count,
            "repeated_observation_count": self.repeated_observation_count,
            "time_span_seconds": self.time_span_seconds,
            "is_recurring": self.is_recurring,
            "confidence_history": list(
                self.confidence_history
            ),
            "strength_history": list(
                self.strength_history
            ),
        }


class TemporalSignalTracker:
    """
    Tracks signal evolution over time.

    Signals are grouped by signal type and entity.
    """

    def track(
        self,
        signals: list[Signal],
    ) -> list[TemporalSignalHistory]:
        if not isinstance(signals, list):
            raise TypeError("signals must be a list")

        if any(
            not isinstance(signal, Signal)
            for signal in signals
        ):
            raise TypeError(
                "signals must contain only Signal objects"
            )

        groups: dict[tuple[object, str], list[Signal]] = {}

        for signal in signals:
            key = (
                signal.signal_type,
                signal.entity_id,
            )

            groups.setdefault(key, []).append(signal)

        histories: list[TemporalSignalHistory] = []

        for group in groups.values():
            ordered = sorted(
                group,
                key=lambda signal: signal.detected_at,
            )

            first_observed_at = ordered[0].detected_at
            latest_observed_at = ordered[-1].detected_at

            time_span_seconds = (
                latest_observed_at - first_observed_at
            ).total_seconds()

            histories.append(
                TemporalSignalHistory(
                    signal_type=ordered[0].signal_type,
                    entity_id=ordered[0].entity_id,
                    signals=tuple(ordered),
                    first_observed_at=first_observed_at,
                    latest_observed_at=latest_observed_at,
                    observation_count=len(ordered),
                    repeated_observation_count=max(
                        0,
                        len(ordered) - 1,
                    ),
                    time_span_seconds=max(
                        0.0,
                        time_span_seconds,
                    ),
                )
            )

        histories.sort(
            key=lambda history: history.latest_observed_at,
        )

        return histories


def track_temporal_signals(
    signals: list[Signal],
) -> list[TemporalSignalHistory]:
    """
    Convenience function using the default temporal tracker.
    """
    return TemporalSignalTracker().track(signals)
