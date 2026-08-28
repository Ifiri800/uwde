from dataclasses import dataclass, field
from enum import Enum


class LeadSignalType(str, Enum):
    BUYER_INTENT = "buyer_intent"
    HIRING = "hiring"
    PROCUREMENT = "procurement"
    EXPANSION = "expansion"
    FUNDING = "funding"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    NEW_PROJECT = "new_project"
    PARTNERSHIP = "partnership"
    EXECUTIVE_CHANGE = "executive_change"
    GROWTH = "growth"


@dataclass
class LeadSignal:
    signal_id: str
    signal_type: LeadSignalType
    company_id: str
    confidence: float = 0.0
    strength: float = 0.0
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.signal_id:
            raise ValueError("signal_id is required")

        if not self.company_id:
            raise ValueError("company_id is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.strength <= 1.0:
            raise ValueError(
                "strength must be between 0.0 and 1.0"
            )

        if not isinstance(self.evidence_ids, list):
            raise TypeError(
                "evidence_ids must be a list"
            )

    @property
    def is_supported(self) -> bool:
        return bool(self.evidence_ids)

    @property
    def commercial_strength(self) -> float:
        return round(
            (self.confidence + self.strength) / 2,
            4,
        )
