from __future__ import annotations

from .models import LDARStrategy


def validate_ldar_strategy(
    strategy: LDARStrategy,
) -> tuple[str, ...]:
    if not isinstance(strategy, LDARStrategy):
        raise TypeError("strategy must be an LDARStrategy")

    errors: list[str] = []

    if strategy.confirmation_required and not strategy.detection_methods:
        errors.append(
            "confirmation requires at least one detection method"
        )

    if strategy.remeasurement_required and not strategy.repair_required:
        errors.append(
            "re-measurement requires repair workflow"
        )

    if strategy.verification_required and not strategy.remeasurement_required:
        errors.append(
            "verification requires re-measurement"
        )

    return tuple(errors)


def validate_ldar_strategy_or_raise(
    strategy: LDARStrategy,
) -> LDARStrategy:
    errors = validate_ldar_strategy(strategy)

    if errors:
        raise ValueError("; ".join(errors))

    return strategy


def workflow_steps(
    strategy: LDARStrategy,
) -> tuple[str, ...]:
    steps = ["detect"]

    if strategy.confirmation_required:
        steps.append("confirm")

    if strategy.quantification_required:
        steps.append("quantify")

    steps.append("classify")
    steps.append("prioritize")

    if strategy.repair_required:
        steps.append("repair")

    if strategy.remeasurement_required:
        steps.append("re-measure")

    if strategy.verification_required:
        steps.append("verify")

    return tuple(steps)
