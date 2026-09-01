from datetime import date

import pytest

from backend.app.services.intelligence.methane.regulatory import (
    RegulatoryRegistry,
    RegulatorySource,
    RegulatorySourceType,
    RequirementTrace,
    SourceStatus,
)


def make_source() -> RegulatorySource:
    return RegulatorySource(
        source_id="test.source",
        title="Test Regulatory Source",
        publisher="Test Authority",
        source_type=RegulatorySourceType.REGULATION,
        jurisdiction="Nigeria",
        version="1.0",
        publication_date=date(2026, 1, 1),
        effective_date=date(2026, 2, 1),
        status=SourceStatus.ACTIVE,
    )


def test_source_creation() -> None:
    source = make_source()

    assert source.source_id == "test.source"
    assert source.jurisdiction == "Nigeria"
    assert source.status is SourceStatus.ACTIVE


def test_source_requires_id() -> None:
    with pytest.raises(ValueError):
        RegulatorySource(
            source_id="",
            title="Source",
            publisher="Authority",
            source_type=RegulatorySourceType.REGULATION,
        )


def test_registry_registers_source() -> None:
    registry = RegulatoryRegistry()
    source = make_source()

    registry.register_source(source)

    assert registry.get_source("test.source") == source


def test_registry_rejects_duplicate_source() -> None:
    registry = RegulatoryRegistry()
    source = make_source()

    registry.register_source(source)

    with pytest.raises(ValueError):
        registry.register_source(source)


def test_trace_requires_known_source() -> None:
    registry = RegulatoryRegistry()

    trace = RequirementTrace(
        trace_id="trace.001",
        requirement_id="req.001",
        source_id="missing.source",
    )

    with pytest.raises(ValueError):
        registry.register_trace(trace)


def test_trace_registration() -> None:
    registry = RegulatoryRegistry()
    registry.register_source(make_source())

    trace = RequirementTrace(
        trace_id="trace.001",
        requirement_id="req.001",
        source_id="test.source",
        reference="Section 1",
        evidence="Authoritative source reference",
    )

    registry.register_trace(trace)

    assert registry.get_trace("trace.001") == trace


def test_trace_requires_id() -> None:
    with pytest.raises(ValueError):
        RequirementTrace(
            trace_id="",
            requirement_id="req.001",
            source_id="source.001",
        )


def test_source_type_enum() -> None:
    assert RegulatorySourceType.REGULATION.value == "regulation"
    assert RegulatorySourceType.GUIDANCE.value == "guidance"
    assert RegulatorySourceType.METHODOLOGY.value == "methodology"


def test_source_status_enum() -> None:
    assert SourceStatus.ACTIVE.value == "active"
    assert SourceStatus.SUPERSEDED.value == "superseded"
