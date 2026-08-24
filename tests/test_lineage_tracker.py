from datetime import datetime, timezone

import pytest

from backend.app.services.lineage.tracker import (
    LineageRecord,
    LineageStep,
    build_lineage,
    create_lineage,
    record_lineage_step,
)


def test_lineage_step_stores_operation_and_values():
    step = LineageStep(
        operation="clean",
        input_value="  Nigeria  ",
        output_value="Nigeria",
    )

    assert step.operation == "clean"
    assert step.input_value == "  Nigeria  "
    assert step.output_value == "Nigeria"


def test_lineage_step_default_timestamp_is_utc():
    step = LineageStep(
        operation="normalize",
        input_value="125000",
        output_value=125000,
    )

    assert step.timestamp.tzinfo is not None
    assert step.is_utc is True


def test_lineage_step_stores_metadata():
    step = LineageStep(
        operation="normalize",
        input_value="125000",
        output_value=125000,
        metadata={
            "type": "number",
            "source": "normalizer",
        },
    )

    assert step.metadata["type"] == "number"
    assert step.metadata["source"] == "normalizer"


def test_lineage_step_requires_operation():
    with pytest.raises(ValueError):
        LineageStep(
            operation="",
            input_value="raw",
            output_value="clean",
        )


def test_lineage_step_requires_timezone_aware_timestamp():
    naive_timestamp = datetime(2026, 8, 24, 10, 0, 0)

    with pytest.raises(ValueError):
        LineageStep(
            operation="clean",
            input_value="raw",
            output_value="clean",
            timestamp=naive_timestamp,
        )


def test_create_lineage_stores_raw_and_final_value():
    lineage = create_lineage(
        field_name="title",
        source_url="https://example.com/jobs",
        raw_value="  Environmental Consultant  ",
    )

    assert isinstance(lineage, LineageRecord)
    assert lineage.field_name == "title"
    assert lineage.source_url == "https://example.com/jobs"
    assert lineage.raw_value == "  Environmental Consultant  "
    assert lineage.final_value == "  Environmental Consultant  "
    assert lineage.step_count == 0


def test_create_lineage_timestamp_is_utc():
    lineage = create_lineage(
        field_name="title",
        source_url="https://example.com/jobs",
        raw_value="Environmental Consultant",
    )

    assert lineage.created_at.tzinfo is not None
    assert (
        lineage.created_at.utcoffset()
        == timezone.utc.utcoffset(lineage.created_at)
    )


def test_create_lineage_stores_metadata():
    lineage = create_lineage(
        field_name="salary",
        source_url="https://example.com/jobs",
        raw_value="125000",
        metadata={
            "page": 2,
            "selector": ".salary",
        },
    )

    assert lineage.metadata["page"] == 2
    assert lineage.metadata["selector"] == ".salary"


def test_create_lineage_requires_field_name():
    with pytest.raises(ValueError):
        create_lineage(
            field_name="",
            source_url="https://example.com",
            raw_value="value",
        )


def test_create_lineage_requires_source_url():
    with pytest.raises(ValueError):
        create_lineage(
            field_name="title",
            source_url="",
            raw_value="value",
        )


def test_add_step_updates_final_value():
    lineage = create_lineage(
        field_name="title",
        source_url="https://example.com",
        raw_value="  Environmental Consultant  ",
    )

    step = lineage.add_step(
        operation="clean",
        input_value="  Environmental Consultant  ",
        output_value="Environmental Consultant",
    )

    assert isinstance(step, LineageStep)
    assert lineage.final_value == "Environmental Consultant"
    assert lineage.step_count == 1


def test_record_lineage_step_adds_step():
    lineage = create_lineage(
        field_name="salary",
        source_url="https://example.com",
        raw_value="125000",
    )

    step = record_lineage_step(
        lineage,
        operation="normalize",
        input_value="125000",
        output_value=125000,
    )

    assert step.operation == "normalize"
    assert lineage.final_value == 125000
    assert lineage.step_count == 1


def test_multiple_lineage_steps_preserve_order():
    lineage = create_lineage(
        field_name="title",
        source_url="https://example.com",
        raw_value="  Environmental Consultant  ",
    )

    record_lineage_step(
        lineage,
        operation="clean",
        input_value="  Environmental Consultant  ",
        output_value="Environmental Consultant",
    )

    record_lineage_step(
        lineage,
        operation="normalize",
        input_value="Environmental Consultant",
        output_value="Environmental Consultant",
    )

    record_lineage_step(
        lineage,
        operation="validate",
        input_value="Environmental Consultant",
        output_value="Environmental Consultant",
    )

    assert lineage.step_count == 3
    assert lineage.operations == [
        "clean",
        "normalize",
        "validate",
    ]


def test_get_step_returns_matching_operation():
    lineage = create_lineage(
        field_name="title",
        source_url="https://example.com",
        raw_value=" raw ",
    )

    record_lineage_step(
        lineage,
        operation="clean",
        input_value=" raw ",
        output_value="raw",
    )

    step = lineage.get_step("clean")

    assert step is not None
    assert step.operation == "clean"
    assert step.output_value == "raw"


def test_get_step_returns_none_when_operation_is_missing():
    lineage = create_lineage(
        field_name="title",
        source_url="https://example.com",
        raw_value="raw",
    )

    assert lineage.get_step("normalize") is None


def test_build_lineage_creates_complete_history():
    steps = [
        {
            "operation": "clean",
            "input_value": " 125000 ",
            "output_value": "125000",
        },
        {
            "operation": "normalize",
            "input_value": "125000",
            "output_value": 125000,
        },
        {
            "operation": "validate",
            "input_value": 125000,
            "output_value": 125000,
        },
    ]

    lineage = build_lineage(
        field_name="salary",
        source_url="https://example.com/jobs",
        raw_value=" 125000 ",
        steps=steps,
    )

    assert lineage.raw_value == " 125000 "
    assert lineage.final_value == 125000
    assert lineage.step_count == 3
    assert lineage.operations == [
        "clean",
        "normalize",
        "validate",
    ]


def test_build_lineage_preserves_step_metadata():
    steps = [
        {
            "operation": "normalize",
            "input_value": "125000",
            "output_value": 125000,
            "metadata": {
                "target_type": "number",
            },
        }
    ]

    lineage = build_lineage(
        field_name="salary",
        source_url="https://example.com",
        raw_value="125000",
        steps=steps,
    )

    assert lineage.steps[0].metadata["target_type"] == "number"


def test_build_lineage_accepts_explicit_timestamp():
    timestamp = datetime(
        2026,
        8,
        24,
        12,
        0,
        0,
        tzinfo=timezone.utc,
    )

    steps = [
        {
            "operation": "clean",
            "input_value": " raw ",
            "output_value": "raw",
            "timestamp": timestamp,
        }
    ]

    lineage = build_lineage(
        field_name="title",
        source_url="https://example.com",
        raw_value=" raw ",
        steps=steps,
    )

    assert lineage.steps[0].timestamp == timestamp


def test_lineage_preserves_complex_values():
    raw_value = {
        "name": "Environmental Consultant",
        "salary": [100000, 125000],
    }

    lineage = create_lineage(
        field_name="job",
        source_url="https://example.com",
        raw_value=raw_value,
    )

    cleaned_value = {
        "name": "Environmental Consultant",
        "salary": [100000, 125000],
    }

    record_lineage_step(
        lineage,
        operation="clean",
        input_value=raw_value,
        output_value=cleaned_value,
    )

    assert lineage.raw_value == raw_value
    assert lineage.final_value == cleaned_value


def test_lineage_tracks_complete_extraction_lifecycle():
    lineage = create_lineage(
        field_name="title",
        source_url="https://example.com/jobs/123",
        raw_value="  Environmental Consultant  ",
    )

    record_lineage_step(
        lineage,
        operation="clean",
        input_value="  Environmental Consultant  ",
        output_value="Environmental Consultant",
    )

    record_lineage_step(
        lineage,
        operation="normalize",
        input_value="Environmental Consultant",
        output_value="Environmental Consultant",
    )

    record_lineage_step(
        lineage,
        operation="validate",
        input_value="Environmental Consultant",
        output_value="Environmental Consultant",
    )

    record_lineage_step(
        lineage,
        operation="reconcile",
        input_value="Environmental Consultant",
        output_value="Environmental Consultant",
    )

    assert lineage.raw_value == "  Environmental Consultant  "
    assert lineage.final_value == "Environmental Consultant"
    assert lineage.step_count == 4
    assert lineage.operations == [
        "clean",
        "normalize",
        "validate",
        "reconcile",
    ]