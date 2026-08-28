from __future__ import annotations

from typing import Any

from backend.app.services.intelligence.detection.rules import (
    DEFAULT_RULES,
    DetectionContext,
    DetectionRule,
)
from backend.app.services.intelligence.domain.signals import Signal


class SignalDetectionEngine:
    """
    Domain-neutral engine for converting contextual observations
    into intelligence signals.
    """

    def __init__(
        self,
        rules: tuple[DetectionRule, ...] = DEFAULT_RULES,
    ) -> None:
        self.rules = rules

    def detect(
        self,
        *,
        entity_id: str,
        entity_type: str,
        field_name: str | None,
        previous_value: Any,
        current_value: Any,
        evidence_ids: list[str] | None = None,
    ) -> list[Signal]:
        """
        Evaluate registered rules against a contextual observation.
        """

        context = DetectionContext(
            entity_type=entity_type,
            field_name=field_name,
        )

        signals: list[Signal] = []

        for rule in self.rules:
            if not rule.matches(
                context=context,
                previous_value=previous_value,
                current_value=current_value,
            ):
                continue

            signals.append(
                Signal(
                    signal_id=f"{entity_id}:{rule.name}",
                    signal_type=rule.signal_type,
                    entity_id=entity_id,
                    confidence=1.0,
                    strength=1.0,
                    evidence_ids=evidence_ids or [],
                    previous_value=previous_value,
                    current_value=current_value,
                )
            )

        return signals


def detect_signals(
    *,
    entity_id: str,
    entity_type: str,
    field_name: str | None,
    previous_value: Any,
    current_value: Any,
    evidence_ids: list[str] | None = None,
) -> list[Signal]:
    """
    Convenience function using the default detection engine.
    """

    return SignalDetectionEngine().detect(
        entity_id=entity_id,
        entity_type=entity_type,
        field_name=field_name,
        previous_value=previous_value,
        current_value=current_value,
        evidence_ids=evidence_ids,
    )
