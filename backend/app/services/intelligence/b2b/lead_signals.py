from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LeadSignalType(str, Enum):
    BUYER_INTENT = "buyer_intent"
    HIRING = "hiring"
    EXPANSION = "expansion"
    PROCUREMENT = "procurement"
    TECHNOLOGY_CHANGE = "technology_change"
    FUNDING = "funding"
    PARTNERSHIP = "partnership"


@dataclass(frozen=True)
class LeadSignal:
    signal_id: str
    company_id: str
    signal_type: LeadSignalType
    confidence: float = 1.0
    strength: float = 1.0
    evidence_ids: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.signal_id:
            raise ValueError("signal_id is required.")

        if not self.company_id:
            raise ValueError("company_id is required.")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1."
            )

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(
                "strength must be between 0 and 1."
            )

    @property
    def is_supported(self) -> bool:
        return bool(self.evidence_ids)

    @property
    def commercial_strength(self) -> float:
        return self.confidence * self.strength
