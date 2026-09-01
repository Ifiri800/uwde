from __future__ import annotations

from .models import IntelligenceTrend


def analyze_trend(
    entity_id: str,
    baseline: float,
    current: float,
    *,
    confidence: float = 1.0,
) -> IntelligenceTrend:

    if baseline < 0 or current < 0:
        raise ValueError("trend values cannot be negative")

    magnitude = (
        0.0
        if baseline == 0
        else (current - baseline) / baseline
    )

    if magnitude > 0.05:
        direction = "increasing"
    elif magnitude < -0.05:
        direction = "decreasing"
    else:
        direction = "stable"

    return IntelligenceTrend(
        entity_id=entity_id,
        direction=direction,
        magnitude=magnitude,
        baseline=baseline,
        current=current,
        confidence=max(0.0, min(1.0, confidence)),
    )
