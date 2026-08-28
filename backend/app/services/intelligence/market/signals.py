from __future__ import annotations

from backend.app.services.intelligence.domain.signals import (
    Signal,
    SignalType,
)
from .entities import MarketObservation
from .observations import MarketObservationType


MARKET_SIGNAL_MAP: dict[MarketObservationType, SignalType] = {
    MarketObservationType.COMPANY_ENTRY: SignalType.NEW_COMPANY,
    MarketObservationType.COMPANY_EXIT: SignalType.COMPETITOR_CHANGE,
    MarketObservationType.PRODUCT_LAUNCH: SignalType.PRODUCT_LAUNCH,
    MarketObservationType.PRODUCT_DISCONTINUATION: SignalType.COMPETITOR_CHANGE,
    MarketObservationType.PRICE_CHANGE: SignalType.PRICE_CHANGE,
    MarketObservationType.HIRING_GROWTH: SignalType.HIRING_SIGNAL,
    MarketObservationType.FUNDING_EVENT: SignalType.FUNDING_SIGNAL,
    MarketObservationType.PARTNERSHIP: SignalType.COMPANY_EXPANSION,
    MarketObservationType.MARKET_EXPANSION: SignalType.MARKET_GROWTH,
    MarketObservationType.GEOGRAPHIC_EXPANSION: SignalType.COMPANY_EXPANSION,
    MarketObservationType.TECHNOLOGY_ADOPTION: SignalType.TECHNOLOGY_ADOPTION,
    MarketObservationType.CAPACITY_CHANGE: SignalType.COMPANY_EXPANSION,
    MarketObservationType.DEMAND_SIGNAL: SignalType.BUYER_INTENT,
}


def market_signal_type(
    observation_type: MarketObservationType | str,
) -> SignalType:
    """
    Convert a market observation type into the common intelligence
    signal vocabulary.
    """
    try:
        normalized = MarketObservationType(observation_type)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "observation_type must be a valid MarketObservationType"
        ) from exc

    try:
        return MARKET_SIGNAL_MAP[normalized]
    except KeyError as exc:
        raise ValueError(
            f"No signal mapping defined for {normalized.value}"
        ) from exc


def generate_market_signal(
    observation: MarketObservation,
) -> Signal:
    """
    Convert a validated market observation into a common
    intelligence Signal.

    The observation's confidence becomes the signal confidence.
    Evidence IDs are preserved so downstream scoring and
    validation can use the original evidence chain.
    """
    if not isinstance(observation, MarketObservation):
        raise TypeError(
            "observation must be a MarketObservation"
        )

    signal_type = market_signal_type(
        observation.observation_type
    )

    return Signal(
        signal_id=f"market-signal:{observation.observation_id}",
        signal_type=signal_type,
        entity_id=observation.market_id,
        detected_at=observation.observed_at,
        confidence=observation.confidence,
        strength=observation.confidence,
        evidence_ids=list(observation.evidence_ids),
        current_value=observation.value,
        metadata={
            "source": "market",
            "observation_id": observation.observation_id,
            "observation_type": observation.observation_type.value,
            "source_url": observation.source_url,
        },
    )


def generate_market_signals(
    observations: list[MarketObservation],
) -> list[Signal]:
    """
    Convert multiple market observations into intelligence signals.
    """
    if not isinstance(observations, list):
        raise TypeError(
            "observations must be a list"
        )

    return [
        generate_market_signal(observation)
        for observation in observations
    ]
