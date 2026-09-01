from datetime import date

import pytest

from backend.app.services.intelligence.methane.foundation import (
    ApplicabilityRule,
    FoundationRegistry,
    FrameworkStatus,
    MethodologyReference,
    RegulatoryFramework,
    RegulatoryRequirement,
    validate_framework,
    validate_requirement,
)


def make_framework() -> RegulatoryFramework:
    return RegulatoryFramework(
        framework_id="test.framework",
        name="Test Methane Framework",
        jurisdiction="Nigeria",
        authority="Test Authority",
        version="1.0",
        effective_date=date(2026, 1, 1),
        status=FrameworkStatus.ACTIVE,
    )


def test_framework_creation() -> None:
    framework = make_framework()

    assert framework.framework_id == "test.framework"
    assert framework.jurisdiction == "Nigeria"
    assert framework.status is FrameworkStatus.ACTIVE


def test_framework_requires_id() -> None:
    with pytest.raises(ValueError):
        RegulatoryFramework(
            framework_id="",
            name="Framework",
            jurisdiction="Nigeria",
            authority="Authority",
        )


def test_requirement_creation() -> None:
    requirement = RegulatoryRequirement(
        requirement_id="req.001",
        framework_id="test.framework",
        title="Maintain emissions records",
        description="Records must be maintained.",
    )

    assert requirement.mandatory is True


def test_registry_registers_framework() -> None:
    registry = FoundationRegistry()
    framework = make_framework()

    registry.register_framework(framework)

    assert registry.get_framework("test.framework") == framework


def test_registry_rejects_duplicate_framework() -> None:
    registry = FoundationRegistry()
    framework = make_framework()

    registry.register_framework(framework)

    with pytest.raises(ValueError):
        registry.register_framework(framework)


def test_requirement_requires_known_framework() -> None:
    registry = FoundationRegistry()

    requirement = RegulatoryRequirement(
        requirement_id="req.001",
        framework_id="missing",
        title="Requirement",
        description="Description",
    )

    with pytest.raises(ValueError):
        registry.register_requirement(requirement)


def test_registry_registers_requirement() -> None:
    registry = FoundationRegistry()
    registry.register_framework(make_framework())

    requirement = RegulatoryRequirement(
        requirement_id="req.001",
        framework_id="test.framework",
        title="Requirement",
        description="Description",
    )

    registry.register_requirement(requirement)

    assert registry.get_requirement("req.001") == requirement


def test_methodology_and_rule_registration() -> None:
    registry = FoundationRegistry()
    registry.register_framework(make_framework())

    methodology = MethodologyReference(
        methodology_id="ipcc.2006",
        name="IPCC Guidelines",
        publisher="IPCC",
    )

    rule = ApplicabilityRule(
        rule_id="rule.001",
        framework_id="test.framework",
        condition="Applicable to covered facilities",
    )

    registry.register_methodology(methodology)
    registry.register_rule(rule)

    assert registry.get_methodology("ipcc.2006") == methodology
    assert registry.get_rule("rule.001") == rule


def test_validation_success() -> None:
    result = validate_framework(make_framework())

    assert result.valid is True
    assert result.errors == ()


def test_validation_requirement_success() -> None:
    requirement = RegulatoryRequirement(
        requirement_id="req.001",
        framework_id="test.framework",
        title="Requirement",
        description="Description",
    )

    result = validate_requirement(requirement)

    assert result.valid is True
