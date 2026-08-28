from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.services.intelligence.domain.signals import SignalType


@dataclass(frozen=True)
class DetectionContext:
    """
    Context describing what is being observed.
    """

    entity_type: str
    field_name: str | None = None


@dataclass(frozen=True)
class DetectionRule:
    """
    Defines a context-aware rule for detecting an intelligence signal.
    """

    name: str
    signal_type: SignalType
    description: str

    def matches(
        self,
        *,
        context: DetectionContext,
        previous_value: Any,
        current_value: Any,
    ) -> bool:
        raise NotImplementedError


@dataclass(frozen=True)
class ValueChangedRule(DetectionRule):
    """
    Detects a meaningful change in a specific field.
    """

    allowed_entity_types: frozenset[str] = frozenset()
    allowed_fields: frozenset[str] = frozenset()

    def matches(
        self,
        *,
        context: DetectionContext,
        previous_value: Any,
        current_value: Any,
    ) -> bool:
        if (
            self.allowed_entity_types
            and context.entity_type not in self.allowed_entity_types
        ):
            return False

        if (
            self.allowed_fields
            and context.field_name not in self.allowed_fields
        ):
            return False

        return (
            previous_value is not None
            and current_value is not None
            and previous_value != current_value
        )


@dataclass(frozen=True)
class ValueAppearedRule(DetectionRule):
    """
    Detects the appearance of a previously absent value
    for a specific entity type.
    """

    allowed_entity_types: frozenset[str] = frozenset()
    allowed_fields: frozenset[str] = frozenset()

    def matches(
        self,
        *,
        context: DetectionContext,
        previous_value: Any,
        current_value: Any,
    ) -> bool:
        if (
            self.allowed_entity_types
            and context.entity_type not in self.allowed_entity_types
        ):
            return False

        if (
            self.allowed_fields
            and context.field_name not in self.allowed_fields
        ):
            return False

        return (
            previous_value is None
            and current_value is not None
        )


PRICE_CHANGE_RULE = ValueChangedRule(
    name="price_change",
    signal_type=SignalType.PRICE_CHANGE,
    description="Detects a change in an observed product price.",
    allowed_entity_types=frozenset({"product"}),
    allowed_fields=frozenset({"price"}),
)


NEW_PRODUCT_RULE = ValueAppearedRule(
    name="new_product",
    signal_type=SignalType.NEW_PRODUCT,
    description="Detects a newly observed product.",
    allowed_entity_types=frozenset({"product"}),
    allowed_fields=frozenset({"existence"}),
)


NEW_COMPANY_RULE = ValueAppearedRule(
    name="new_company",
    signal_type=SignalType.NEW_COMPANY,
    description="Detects a newly observed company.",
    allowed_entity_types=frozenset({"company"}),
    allowed_fields=frozenset({"existence"}),
)


DEFAULT_RULES: tuple[DetectionRule, ...] = (
    PRICE_CHANGE_RULE,
    NEW_PRODUCT_RULE,
    NEW_COMPANY_RULE,
)
