import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.extraction_engine import build_extraction_plan
from app.services.extraction_executor import execute_extraction


HTML = """
<html>
<head>
    <title>Jobs</title>
</head>
<body>

<article class="job-card">
    <h2 class="job-title">Environmental Consultant</h2>
    <div class="company">Green Solutions Ltd</div>
    <div class="location">Abuja, Nigeria</div>
    <div class="salary">$2,500</div>
    <div class="description">
        Environmental assessment and sustainability consulting.
    </div>
    <time class="posted-date">2026-08-20</time>
    <a class="apply" href="/jobs/123/apply">Apply</a>
</article>

<article class="job-card">
    <h2 class="job-title">WASH Specialist</h2>
    <div class="company">Water Partners</div>
    <div class="location">Lagos, Nigeria</div>
    <div class="salary">$3,000</div>
    <div class="description">
        WASH programme implementation and monitoring.
    </div>
    <time class="posted-date">2026-08-21</time>
    <a class="apply" href="https://example.com/jobs/456/apply">Apply</a>
</article>

</body>
</html>
"""


def test_extracts_multiple_records():
    plan = build_extraction_plan(
        "Extract the job title, company, location, salary, and application URL."
    )

    result = execute_extraction(
        HTML,
        plan,
        "https://example.com/jobs",
    )

    assert len(result.records) == 2

    assert result.records[0]["title"] == "Environmental Consultant"
    assert result.records[0]["company"] == "Green Solutions Ltd"
    assert result.records[0]["location"] == "Abuja, Nigeria"
    assert result.records[0]["salary"] == "$2,500"
    assert result.records[0]["application_url"] == (
        "https://example.com/jobs/123/apply"
    )


def test_resolves_relative_application_urls():
    plan = build_extraction_plan(
        "Extract the job title and application URL."
    )

    result = execute_extraction(
        HTML,
        plan,
        "https://example.com/jobs",
    )

    assert result.records[0]["application_url"] == (
        "https://example.com/jobs/123/apply"
    )


def test_preserves_absolute_application_urls():
    plan = build_extraction_plan(
        "Extract the job title and application URL."
    )

    result = execute_extraction(
        HTML,
        plan,
        "https://example.com/jobs",
    )

    assert result.records[1]["application_url"] == (
        "https://example.com/jobs/456/apply"
    )


def test_extracts_description_and_posted_date():
    plan = build_extraction_plan(
        "Extract the job title, description, and posted date."
    )

    result = execute_extraction(
        HTML,
        plan,
        "https://example.com/jobs",
    )

    assert result.records[0]["title"] == "Environmental Consultant"
    assert result.records[0]["description"] == (
        "Environmental assessment and sustainability consulting."
    )
    assert result.records[0]["posted_date"] == "2026-08-20"


def test_returns_empty_records_for_empty_html():
    plan = build_extraction_plan(
        "Extract the job title."
    )

    result = execute_extraction(
        "",
        plan,
        "https://example.com/",
    )

    assert result.records == []


def test_ignores_records_without_extractable_fields():
    html = """
    <html>
        <body>
            <article class="job-card">
                <p>Some unrelated content.</p>
            </article>
        </body>
    </html>
    """

    plan = build_extraction_plan(
        "Extract the job title."
    )

    result = execute_extraction(
        html,
        plan,
        "https://example.com/",
    )

    assert result.records == []


def test_result_can_be_serialized():
    plan = build_extraction_plan(
        "Extract the job title and company."
    )

    result = execute_extraction(
        HTML,
        plan,
        "https://example.com/jobs",
    )

    payload = result.model_dump()

    assert "records" in payload
    assert isinstance(payload["records"], list)
    assert payload["records"][0]["title"] == "Environmental Consultant"
