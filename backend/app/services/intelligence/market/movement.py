from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from backend.app.services.intelligence.domain.signals import SignalType
from .temporal import TemporalSignalHistory


class MovementType(StrEnum):
    EXPANSION = "expansion"
    CONTRACTION = "contraction"
    PRICING = "pricing"
    PRODUCT = "product"
    GEOGRAPHIC = "geographic"
    HIRING = "hiring"
    FUNDING = "funding"
    TECHNOLOGY = "technology"
    CAPACITY = "capacity"
    DEMAND = "demand"


class MovementDirection(StrEnum):
    INCREASE = "increase"
    DECREASE = "decrease"
    STABLE = "stable"


@dataclass(frozen=True)
class CompetitiveMovement:
    """
    Explainable movement detected from the historical activity of
    a market participant.

    A movement describes what changed over time. It does not itself
    determine whether that movement is a competitive threat.
    """

    entity_id: str
    movement_type: MovementType
    direction: MovementDirection
    signal_type: SignalType
    signal_count: int
    intensity: float
    confidence: float
    first_observed_at: object
    latest_observed_at: object
    evidence_ids: tuple[str, ...]
    explanation: str

    def __post_init__(self) -> None:
        if not self.entity_id.strip():
            raise ValueError("entity_id is required")

        if self.signal_count < 1:
            raise ValueError("signal_count must be at least 1")

        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("intensity must be between 0.0 and 1.0")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if not self.explanation.strip():
            raise ValueError("explanation is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "movement_type": self.movement_type.value,
            "direction": self.direction.value,
            "signal_type": self.signal_type.value,
            "signal_count": self.signal_count,
            "intensity": self.intensity,
            "confidence": self.confidence,
            "first_observed_at": self.first_observed_at.isoformat(),
            "latest_observed_at": self.latest_observed_at.isoformat(),
            "evidence_ids": list(self.evidence_ids),
            "explanation": self.explanation,
        }


class CompetitiveMovementDetector:
    """
    Detects competitive movement from temporal signal histories.

    The detector is deterministic and does not infer threats. It
    identifies the underlying movement first so a later threat
    assessment layer can interpret its competitive significance.
    """

    MOVEMENT_MAP: dict[SignalType, MovementType] = {
        SignalType.NEW_COMPANY: MovementType.EXPANSION,
        SignalType.NEW_PRODUCT: MovementType.PRODUCT,
        SignalType.PRODUCT_LAUNCH: MovementType.PRODUCT,
        SignalType.PRICE_CHANGE: MovementType.PRICING,
        SignalType.COMPANY_EXPANSION: MovementType.EXPANSION,
        SignalType.HIRING_SIGNAL: MovementType.HIRING,
        SignalType.PROCUREMENT_SIGNAL: MovementType.EXPANSION,
        SignalType.FUNDING_SIGNAL: MovementType.FUNDING,
        SignalType.MARKET_GROWTH: MovementType.EXPANSION,
        SignalType.COMPETITOR_CHANGE: MovementType.CONTRACTION,
        SignalType.TECHNOLOGY_ADOPTION: MovementType.TECHNOLOGY,
        SignalType.TENDER_OPPORTUNITY: MovementType.DEMAND,
        SignalType.BUYER_INTENT: MovementType.DEMAND,
    }

    INCREASE_TYPES = {
        MovementType.EXPANSION,
        MovementType.PRODUCT,
        MovementType.HIRING,
        MovementType.FUNDING,
        MovementType.TECHNOLOGY,
        MovementType.DEMAND,
    }

    def detect(
        self,
        history: TemporalSignalHistory,
    ) -> CompetitiveMovement:
        if not isinstance(history, TemporalSignalHistory):
            raise TypeError(
                "history must be a TemporalSignalHistory"
            )

        try:
            signal_type = SignalType(history.signal_type)
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "history signal_type must be a valid SignalType"
            ) from exc

        try:
            movement_type = self.MOVEMENT_MAP[signal_type]
        except KeyError as exc:
            raise ValueError(
                f"No movement mapping defined for {signal_type.value}"
            ) from exc

        direction = self._direction(
            movement_type,
            history,
        )

        intensity = self._intensity(history)

        confidence = self._confidence(history)

        evidence_ids = self._evidence_ids(history)

        explanation = self._explanation(
            history=history,
            movement_type=movement_type,
            direction=direction,
            intensity=intensity,
        )

        return CompetitiveMovement(
            entity_id=history.entity_id,
            movement_type=movement_type,
            direction=direction,
            signal_type=signal_type,
            signal_count=history.observation_count,
            intensity=intensity,
            confidence=confidence,
            first_observed_at=history.first_observed_at,
            latest_observed_at=history.latest_observed_at,
            evidence_ids=evidence_ids,
            explanation=explanation,
        )

    def detect_many(
        self,
        histories: list[TemporalSignalHistory],
    ) -> list[CompetitiveMovement]:
        if not isinstance(histories, list):
            raise TypeError("histories must be a list")

        return [
            self.detect(history)
            for history in histories
        ]

    @classmethod
    def _direction(
        cls,
        movement_type: MovementType,
        history: TemporalSignalHistory,
    ) -> MovementDirection:
        if movement_type == MovementType.CONTRACTION:
            return MovementDirection.DECREASE

        if movement_type == MovementType.PRICING:
            return cls._value_direction(history)

        if movement_type in cls.INCREASE_TYPES:
            return MovementDirection.INCREASE

        if movement_type == MovementType.CAPACITY:
            return cls._value_direction(history)

        if movement_type == MovementType.GEOGRAPHIC:
            return MovementDirection.INCREASE

        return MovementDirection.STABLE

    @staticmethod
    def _value_direction(
        history: TemporalSignalHistory,
    ) -> MovementDirection:
        if len(history.signals) < 2:
            return MovementDirection.STABLE

        previous = history.signals[-2].current_value
        current = history.signals[-1].current_value

        if isinstance(previous, (int, float)) and isinstance(
            current,
            (int, float),
        ):
            if current > previous:
                return MovementDirection.INCREASE

            if current < previous:
                return MovementDirection.DECREASE

        return MovementDirection.STABLE

    @staticmethod
    def _intensity(
        history: TemporalSignalHistory,
    ) -> float:
        """
        Estimate movement intensity from recurrence and signal
        strength.

        Repeated activity increases intensity, while the average
        signal strength determines the quality of the movement.
        """
        average_strength = sum(
            history.strength_history
        ) / len(history.strength_history)

        recurrence = min(
            1.0,
            history.observation_count / 5.0,
        )

        intensity = (
            average_strength * 0.70
            + recurrence * 0.30
        )

        return round(
            min(1.0, max(0.0, intensity)),
            6,
        )

    @staticmethod
    def _confidence(
        history: TemporalSignalHistory,
    ) -> float:
        if not history.confidence_history:
            return 0.0

        return round(
            min(
                1.0,
                max(
                    0.0,
                    sum(history.confidence_history)
                    / len(history.confidence_history),
                ),
            ),
            6,
        )

    @staticmethod
    def _evidence_ids(
        history: TemporalSignalHistory,
    ) -> tuple[str, ...]:
        evidence_ids: list[str] = []

        for signal in history.signals:
            for evidence_id in signal.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)

        return tuple(evidence_ids)

    @staticmethod
    def _explanation(
        *,
        history: TemporalSignalHistory,
        movement_type: MovementType,
        direction: MovementDirection,
        intensity: float,
    ) -> str:
        recurrence = (
            "recurring"
            if history.is_recurring
            else "single-observation"
        )

        return (
            f"{movement_type.value.capitalize()} movement detected "
            f"for entity {history.entity_id}: "
            f"{history.observation_count} {recurrence} "
            f"signal(s), direction is {direction.value}, "
            f"and movement intensity is {intensity:.3f}."
        )


def detect_competitive_movement(
    history: TemporalSignalHistory,
) -> CompetitiveMovement:
    """
    Convenience function using the default movement detector.
    """
    return CompetitiveMovementDetector().detect(history)


def detect_competitive_movements(
    histories: list[TemporalSignalHistory],
) -> list[CompetitiveMovement]:
    """
    Convenience function using the default movement detector.
    """
    return CompetitiveMovementDetector().detect_many(histories)
