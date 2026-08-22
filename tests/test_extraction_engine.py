import pytest

from backend.app.services.extraction_engine import build_extraction_plan


def test_builds_job_extraction_plan():
    plan = build_extraction_plan(
        "Extract the job title, company, location, salary, and application URL."
    )

    assert [field.name for field in plan.fields] == [
        "title",
        "company",
        "location",
        "salary",
        "application_url",
    ]


def test_assigns_data_types():
    plan = build_extraction_plan(
        "Extract the salary and posted date."
    )

    fields = {field.name: field.data_type for field in plan.fields}

    assert fields["salary"] == "number"
    assert fields["posted_date"] == "date"


def test_supports_common_field_aliases():
    plan = build_extraction_plan(
        "Get employer, city, pay, email address, and telephone."
    )

    assert [field.name for field in plan.fields] == [
        "company",
        "location",
        "salary",
        "email",
        "phone",
    ]


def test_removes_duplicate_fields():
    plan = build_extraction_plan(
        "Extract title, job title, company, employer."
    )

    assert [field.name for field in plan.fields] == [
        "title",
        "company",
    ]


def test_preserves_original_instruction():
    instruction = "Extract the job title and company."

    plan = build_extraction_plan(instruction)

    assert plan.instruction == instruction


def test_rejects_empty_instruction():
    with pytest.raises(ValueError):
        build_extraction_plan("")


def test_supports_custom_fields():
    plan = build_extraction_plan(
        "Extract department, experience level, and closing date."
    )

    assert [field.name for field in plan.fields] == [
        "department",
        "experience_level",
        "closing_date",
    ]


def test_plan_serialization():
    plan = build_extraction_plan(
        "Extract title and company."
    )

    data = plan.to_dict()

    assert data["instruction"] == "Extract title and company."
    assert data["fields"][0]["name"] == "title"
    assert data["fields"][1]["name"] == "company"