from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .observations import MarketObservationType


@dataclass(frozen=True)
class Market:
    market_id: str
    name: str
    industry: str
    geography: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.market_id.strip():
            raise ValueError("market_id is required")

        if not self.name.strip():
            raise ValueError("name is required")

        if not self.industry.strip():
            raise ValueError("industry is required")

        if self.geography is not None and not self.geography.strip():
            raise ValueError("geography cannot be empty")

    def to_dict(self) -> dict:
        return {
            "market_id": self.market_id,
            "name": self.name,
            "industry": self.industry,
            "geography": self.geography,
            "description": self.description,
        }


@dataclass(frozen=True)
class MarketSegment:
    segment_id: str
    market_id: str
    name: str
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.segment_id.strip():
            raise ValueError("segment_id is required")

        if not self.market_id.strip():
            raise ValueError("market_id is required")

        if not self.name.strip():
            raise ValueError("name is required")

    def to_dict(self) -> dict:
        return {
            "segment_id": self.segment_id,
            "market_id": self.market_id,
            "name": self.name,
            "description": self.description,
        }


@dataclass(frozen=True)
class MarketObservation:
    observation_id: str
    market_id: str
    observation_type: MarketObservationType | str
    value: object
    source_url: str
    observed_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    confidence: float = 0.0
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.observation_id.strip():
            raise ValueError("observation_id is required")

        if not self.market_id.strip():
            raise ValueError("market_id is required")

        try:
            normalized_type = MarketObservationType(
                self.observation_type
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "observation_type must be a valid "
                "MarketObservationType"
            ) from exc

        object.__setattr__(
            self,
            "observation_type",
            normalized_type,
        )

        if not self.source_url.strip():
            raise ValueError("source_url is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

        if self.observed_at.tzinfo is None:
            raise ValueError(
                "observed_at must be timezone-aware"
            )

    def to_dict(self) -> dict:
        return {
            "observation_id": self.observation_id,
            "market_id": self.market_id,
            "observation_type": self.observation_type.value,
            "value": self.value,
            "source_url": self.source_url,
            "observed_at": self.observed_at.isoformat(),
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
        }
