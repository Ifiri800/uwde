import pytest

from backend.app.services.lineage.reconciliation_lineage import (
    ReconciliationLineage,
    attach_reconciliation_lineage,
    build_reconciliation_lineages,
    create_reconciliation_lineage,
)
from backend.app.services.lineage.tracker import create_lineage
from backend.app.services.reconciliation.pipeline import ReconciliationResult


def make_lineage(
    field_name: str,
    value,
    source_url: str,
):
    return create_lineage(
        field_name=field_name,
        source_url=source_url,
        raw_value=value,
        metadata={"source": "test"},
    )


def make_result(
    values: dict,
    conflicts=None,
    requires_review=False,
):
    """
    Construct ReconciliationResult using the existing
    UWDE reconciliation model.
    """
    conflicts = conflicts or []

    return ReconciliationResult(
        values=values,
        conflicts=conflicts,
        resolutions=[],
        requires_review=requires_review,
    )


def test_create_reconciliation_lineage_stores_sources():
    source_a = make_lineage(
        "title",
        "Environmental Consultant",
        "https://example.com/a",
    )

    source_b = make_lineage(
        "title",
        "Environmental Consultant",
        "https://example.com/b",
    )

    result = make_result(
        {"title": "Environmental Consultant"}
    )

    lineage = create_reconciliation_lineage(
        field_name="title",
        source_lineages=[source_a, source_b],
        final_value="Environmental Consultant",
        reconciliation_result=result,
    )

    assert isinstance(lineage, ReconciliationLineage)
    assert lineage.field_name == "title"
    assert lineage.source_count == 2
    assert lineage.final_value == "Environmental Consultant"


def test_create_reconciliation_lineage_preserves_source_lineages():
    source = make_lineage(
        "salary",
        125000,
        "https://example.com/job",
    )

    result = make_result({"salary": 125000})

    lineage = create_reconciliation_lineage(
        field_name="salary",
        source_lineages=[source],
        final_value=125000,
        reconciliation_result=result,
    )

    assert lineage.source_lineages[0] is source
    assert lineage.source_lineages[0].raw_value == 125000


def test_reconciliation_lineage_records_reconcile_step():
    source = make_lineage(
        "title",
        "Environmental Consultant",
        "https://example.com",
    )

    result = make_result(
        {"title": "Environmental Consultant"}
    )

    lineage = create_reconciliation_lineage(
        field_name="title",
        source_lineages=[source],
        final_value="Environmental Consultant",
        reconciliation_result=result,
    )

    step = lineage.final_lineage.get_step("reconcile")

    assert step is not None
    assert step.output_value == "Environmental Consultant"


def test_reconciliation_lineage_stores_reconciliation_metadata():
    source = make_lineage(
        "title",
        "Environmental Consultant",
        "https://example.com",
    )

    result = make_result(
        {"title": "Environmental Consultant"},
        requires_review=True,
    )

    lineage = create_reconciliation_lineage(
        field_name="title",
        source_lineages=[source],
        final_value="Environmental Consultant",
        reconciliation_result=result,
        metadata={"test": "metadata"},
    )

    metadata = lineage.final_lineage.metadata

    assert metadata["lineage_type"] == "reconciliation"
    assert metadata["source_count"] == 1
    assert metadata["requires_review"] is True
    assert metadata["test"] == "metadata"


def test_create_reconciliation_lineage_requires_field_name():
    source = make_lineage(
        "title",
        "Test",
        "https://example.com",
    )

    result = make_result({"title": "Test"})

    with pytest.raises(ValueError):
        create_reconciliation_lineage(
            field_name="",
            source_lineages=[source],
            final_value="Test",
            reconciliation_result=result,
        )


def test_create_reconciliation_lineage_requires_sources():
    result = make_result({"title": "Test"})

    with pytest.raises(ValueError):
        create_reconciliation_lineage(
            field_name="title",
            source_lineages=[],
            final_value="Test",
            reconciliation_result=result,
        )


def test_attach_reconciliation_lineage_adds_step():
    lineage = make_lineage(
        "title",
        "Old Title",
        "https://example.com",
    )

    result = make_result(
        {"title": "New Title"}
    )

    returned = attach_reconciliation_lineage(
        lineage,
        result,
    )

    assert returned is lineage
    assert lineage.final_value == "New Title"

    step = lineage.get_step("reconcile")

    assert step is not None
    assert step.input_value == "Old Title"
    assert step.output_value == "New Title"


def test_attach_reconciliation_lineage_stores_metadata():
    lineage = make_lineage(
        "title",
        "Old Title",
        "https://example.com",
    )

    result = make_result(
        {"title": "New Title"},
        requires_review=True,
    )

    attach_reconciliation_lineage(
        lineage,
        result,
    )

    reconciliation = lineage.metadata["reconciliation"]

    assert reconciliation["requires_review"] is True
    assert reconciliation["conflict_count"] == 0


def test_attach_reconciliation_lineage_rejects_invalid_lineage():
    result = make_result({"title": "Test"})

    with pytest.raises(TypeError):
        attach_reconciliation_lineage(
            object(),
            result,
        )


def test_attach_reconciliation_lineage_rejects_invalid_result():
    lineage = make_lineage(
        "title",
        "Test",
        "https://example.com",
    )

    with pytest.raises(TypeError):
        attach_reconciliation_lineage(
            lineage,
            object(),
        )


def test_build_reconciliation_lineages_for_multiple_fields():
    title_a = make_lineage(
        "title",
        "Environmental Consultant",
        "https://example.com/a",
    )

    title_b = make_lineage(
        "title",
        "Environmental Consultant",
        "https://example.com/b",
    )

    salary_a = make_lineage(
        "salary",
        125000,
        "https://example.com/a",
    )

    result = make_result(
        {
            "title": "Environmental Consultant",
            "salary": 125000,
        }
    )

    lineages = build_reconciliation_lineages(
        {
            "title": [title_a, title_b],
            "salary": [salary_a],
        },
        result,
    )

    assert set(lineages.keys()) == {
        "title",
        "salary",
    }

    assert lineages["title"].source_count == 2
    assert lineages["salary"].source_count == 1


def test_build_reconciliation_lineages_skips_empty_sources():
    result = make_result(
        {"title": "Environmental Consultant"}
    )

    lineages = build_reconciliation_lineages(
        {
            "title": [],
        },
        result,
    )

    assert lineages == {}


def test_build_reconciliation_lineages_preserves_final_values():
    source = make_lineage(
        "title",
        "Old Title",
        "https://example.com",
    )

    result = make_result(
        {"title": "Environmental Consultant"}
    )

    lineages = build_reconciliation_lineages(
        {"title": [source]},
        result,
    )

    assert (
        lineages["title"].final_value
        == "Environmental Consultant"
    )


def test_reconciliation_lineage_preserves_complex_values():
    source_value = {
        "name": "Environmental Consultant",
        "salary": 125000,
        "locations": ["Lagos", "Abuja"],
    }

    final_value = {
        "name": "Environmental Consultant",
        "salary": 125000,
        "locations": ["Lagos", "Abuja"],
    }

    source = make_lineage(
        "job",
        source_value,
        "https://example.com",
    )

    result = make_result(
        {"job": final_value}
    )

    lineage = create_reconciliation_lineage(
        field_name="job",
        source_lineages=[source],
        final_value=final_value,
        reconciliation_result=result,
    )

    assert lineage.final_value == final_value
    assert lineage.final_lineage.raw_value == source_value


def test_reconciliation_lineage_preserves_timezone_aware_timestamp():
    source = make_lineage(
        "title",
        "Test",
        "https://example.com",
    )

    result = make_result({"title": "Test"})

    lineage = create_reconciliation_lineage(
        field_name="title",
        source_lineages=[source],
        final_value="Test",
        reconciliation_result=result,
    )

    assert lineage.final_lineage.created_at.tzinfo is not None
    assert (
        lineage.final_lineage.created_at.utcoffset()
        is not None
    )