from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SignalType(StrEnum):
    NEW_COMPANY = "new_company"
    NEW_PRODUCT = "new_product"
    PRICE_CHANGE = "price_change"
    PRODUCT_LAUNCH = "product_launch"
    COMPANY_EXPANSION = "company_expansion"
    HIRING_SIGNAL = "hiring_signal"
    PROCUREMENT_SIGNAL = "procurement_signal"
    FUNDING_SIGNAL = "funding_signal"
    MARKET_GROWTH = "market_growth"
    COMPETITOR_CHANGE = "competitor_change"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    TENDER_OPPORTUNITY = "tender_opportunity"
    BUYER_INTENT = "buyer_intent"


class SignalStatus(StrEnum):
    DETECTED = "detected"
    VALIDATED = "validated"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class Signal(BaseModel):
    """
    Represents an interpreted intelligence signal derived from
    one or more observations/evidence records.
    """

    model_config = ConfigDict(extra="forbid")

    signal_id: str = Field(
        min_length=1,
        max_length=200,
    )

    signal_type: SignalType

    entity_id: str = Field(
        min_length=1,
        max_length=200,
    )

    detected_at: datetime = Field(
        default_factory=utc_now,
    )

    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
    )

    strength: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
    )

    previous_value: object | None = None

    current_value: object | None = None

    status: SignalStatus = SignalStatus.DETECTED

    metadata: dict[str, object] = Field(
        default_factory=dict,
    )

    @property
    def is_supported(self) -> bool:
        """Return whether the signal has supporting evidence."""
        return bool(self.evidence_ids)

    @property
    def is_actionable(self) -> bool:
        """
        Return whether the signal has enough evidence, validation,
        confidence, and strength to be considered actionable.
        """
        return (
            self.is_supported
            and self.status == SignalStatus.VALIDATED
            and self.confidence >= 0.70
            and self.strength >= 0.50
        )
