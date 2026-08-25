from __future__ import annotations

from unittest.mock import patch

from backend.app.services.pipeline_orchestrator import (
    PipelineResult,
    run_extraction_pipeline,
)


def test_pipeline_returns_structured_records():
    html = """
    <html>
        <body>
            <article class="job">
                <h2 class="title">Environmental Consultant</h2>
                <div class="company">UWDE Consulting</div>
                <div class="location">Abuja</div>
            </article>

            <article class="job">
                <h2 class="title">WASH Specialist</h2>
                <div class="company">Environmental Solutions</div>
                <div class="location">Kaduna</div>
            </article>
        </body>
    </html>
    """

    class FakeResponse:
        url = "https://example.com/jobs"
        final_url = "https://example.com/jobs"
        status_code = 200
        content_type = "text/html"
        body = html.encode("utf-8")

    with patch(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        return_value=FakeResponse(),
    ):
        result = run_extraction_pipeline(
            "https://example.com/jobs",
            "Extract title, company and location",
        )

    assert isinstance(result, PipelineResult)
    assert result.status == "success"
    assert result.record_count == 2

    assert result.records[0]["title"] == (
        "Environmental Consultant"
    )
    assert result.records[0]["company"] == (
        "UWDE Consulting"
    )
    assert result.records[0]["location"] == "Abuja"


def test_pipeline_normalizes_instruction():
    html = """
    <html>
        <body>
            <article class="job">
                <h2 class="title">Environmental Consultant</h2>
            </article>
        </body>
    </html>
    """

    class FakeResponse:
        url = "https://example.com"
        final_url = "https://example.com"
        status_code = 200
        content_type = "text/html"
        body = html.encode("utf-8")

    with patch(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        return_value=FakeResponse(),
    ):
        result = run_extraction_pipeline(
            "https://example.com",
            "  Extract title  ",
        )

    assert result.instruction == "Extract title"
    assert result.record_count == 1


def test_pipeline_rejects_empty_url():
    try:
        run_extraction_pipeline(
            "",
            "Extract title",
        )
    except ValueError as exc:
        assert str(exc) == "URL is required."
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_pipeline_rejects_empty_instruction():
    try:
        run_extraction_pipeline(
            "https://example.com",
            "",
        )
    except ValueError as exc:
        assert str(exc) == "Instruction is required."
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_pipeline_result_is_serializable():
    result = PipelineResult(
        status="success",
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        content_type="text/html",
        instruction="Extract title",
        records=[
            {
                "title": "Environmental Consultant",
            }
        ],
    )

    data = result.to_dict()

    assert data["status"] == "success"
    assert data["record_count"] == 1
    assert data["records"][0]["title"] == (
        "Environmental Consultant"
    )