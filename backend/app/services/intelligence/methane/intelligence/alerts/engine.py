from __future__ import annotations

from .models import DecisionPriority, IntelligenceAlert


def generate_alert(
    entity_id: str,
    *,
    alert_type: str,
    score: float,
    message: str,
    evidence_ids: tuple[str, ...] = (),
) -> IntelligenceAlert:

    score = max(0.0, min(1.0, score))

    if score >= 0.90:
        priority = DecisionPriority.CRITICAL
    elif score >= 0.75:
        priority = DecisionPriority.HIGH
    elif score >= 0.50:
        priority = DecisionPriority.MEDIUM
    else:
        priority = DecisionPriority.LOW

    return IntelligenceAlert(
        alert_id=f"alert-{entity_id}-{alert_type}",
        entity_id=entity_id,
        alert_type=alert_type,
        priority=priority,
        score=score,
        message=message,
        evidence_ids=evidence_ids,
    )
