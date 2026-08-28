from __future__ import annotations

from enum import Enum


class MarketObservationType(str, Enum):
    COMPANY_ENTRY = "company_entry"
    COMPANY_EXIT = "company_exit"
    PRODUCT_LAUNCH = "product_launch"
    PRODUCT_DISCONTINUATION = "product_discontinuation"
    PRICE_CHANGE = "price_change"
    HIRING_GROWTH = "hiring_growth"
    FUNDING_EVENT = "funding_event"
    PARTNERSHIP = "partnership"
    MARKET_EXPANSION = "market_expansion"
    GEOGRAPHIC_EXPANSION = "geographic_expansion"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    CAPACITY_CHANGE = "capacity_change"
    DEMAND_SIGNAL = "demand_signal"
