from __future__ import annotations

from .models import (
    ApplicabilityRule,
    MethodologyReference,
    RegulatoryFramework,
    RegulatoryRequirement,
)


class FoundationRegistry:
    """In-memory canonical registry for methane MRV foundations."""

    def __init__(self) -> None:
        self._frameworks: dict[str, RegulatoryFramework] = {}
        self._requirements: dict[str, RegulatoryRequirement] = {}
        self._methodologies: dict[str, MethodologyReference] = {}
        self._rules: dict[str, ApplicabilityRule] = {}

    def register_framework(
        self,
        framework: RegulatoryFramework,
    ) -> None:
        if not isinstance(framework, RegulatoryFramework):
            raise TypeError("framework must be a RegulatoryFramework")

        if framework.framework_id in self._frameworks:
            raise ValueError(
                f"framework already registered: {framework.framework_id}"
            )

        self._frameworks[framework.framework_id] = framework

    def register_requirement(
        self,
        requirement: RegulatoryRequirement,
    ) -> None:
        if not isinstance(requirement, RegulatoryRequirement):
            raise TypeError(
                "requirement must be a RegulatoryRequirement"
            )

        if requirement.framework_id not in self._frameworks:
            raise ValueError(
                f"unknown framework: {requirement.framework_id}"
            )

        if requirement.requirement_id in self._requirements:
            raise ValueError(
                f"requirement already registered: "
                f"{requirement.requirement_id}"
            )

        self._requirements[requirement.requirement_id] = requirement

    def register_methodology(
        self,
        methodology: MethodologyReference,
    ) -> None:
        if not isinstance(methodology, MethodologyReference):
            raise TypeError(
                "methodology must be a MethodologyReference"
            )

        if methodology.methodology_id in self._methodologies:
            raise ValueError(
                f"methodology already registered: "
                f"{methodology.methodology_id}"
            )

        self._methodologies[methodology.methodology_id] = methodology

    def register_rule(
        self,
        rule: ApplicabilityRule,
    ) -> None:
        if not isinstance(rule, ApplicabilityRule):
            raise TypeError(
                "rule must be an ApplicabilityRule"
            )

        if rule.framework_id not in self._frameworks:
            raise ValueError(
                f"unknown framework: {rule.framework_id}"
            )

        if rule.rule_id in self._rules:
            raise ValueError(
                f"rule already registered: {rule.rule_id}"
            )

        self._rules[rule.rule_id] = rule

    def get_framework(
        self,
        framework_id: str,
    ) -> RegulatoryFramework | None:
        return self._frameworks.get(framework_id)

    def get_requirement(
        self,
        requirement_id: str,
    ) -> RegulatoryRequirement | None:
        return self._requirements.get(requirement_id)

    def get_methodology(
        self,
        methodology_id: str,
    ) -> MethodologyReference | None:
        return self._methodologies.get(methodology_id)

    def get_rule(
        self,
        rule_id: str,
    ) -> ApplicabilityRule | None:
        return self._rules.get(rule_id)

    @property
    def frameworks(self) -> tuple[RegulatoryFramework, ...]:
        return tuple(self._frameworks.values())

    @property
    def requirements(self) -> tuple[RegulatoryRequirement, ...]:
        return tuple(self._requirements.values())

    @property
    def methodologies(self) -> tuple[MethodologyReference, ...]:
        return tuple(self._methodologies.values())

    @property
    def rules(self) -> tuple[ApplicabilityRule, ...]:
        return tuple(self._rules.values())
