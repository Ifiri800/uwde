from __future__ import annotations

from collections.abc import Iterable

from .models import DataGovernanceRule


def validate_data_rules(
    rules: Iterable[DataGovernanceRule],
) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()

    for rule in rules:
        if not isinstance(rule, DataGovernanceRule):
            errors.append("invalid data governance rule")
            continue

        if rule.data_domain in seen:
            errors.append(
                f"duplicate data domain: {rule.data_domain}"
            )

        seen.add(rule.data_domain)

    return tuple(errors)


def build_data_governance_rules(
    rules: Iterable[DataGovernanceRule],
) -> tuple[DataGovernanceRule, ...]:
    result = tuple(rules)

    errors = validate_data_rules(result)

    if errors:
        raise ValueError("; ".join(errors))

    return result


def audit_requirements(
    rules: Iterable[DataGovernanceRule],
) -> dict[str, int]:
    rules = tuple(rules)

    return {
        "total_rules": len(rules),
        "version_controlled": sum(
            rule.version_controlled
            for rule in rules
        ),
        "audit_required": sum(
            rule.audit_required
            for rule in rules
        ),
    }
