from __future__ import annotations

import json

import pytest

from backend.app.services.pipeline_orchestrator import (
    PipelineResult,
    run_extraction_pipeline,
)


def test_pipeline_returns_structured_records(
    monkeypatch,
):
    class FakeResponse:
        url = "https://example.com"
        final_url = "https://example.com/jobs"
        status_code = 200
        content_type = "text/html"
        body = b"""
        <html>
            <body>
                <article class="job">
                    <h2 class="title">Environmental Consultant</h2>
                </article>
                <article class="job">
                    <h2 class="title">WASH Specialist</h2>
                </article>
            </body>
        </html>
        """

    monkeypatch.setattr(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        lambda url: FakeResponse(),
    )

    result = run_extraction_pipeline(
        "https://example.com",
        "Extract the job title",
    )

    assert isinstance(result, PipelineResult)
    assert result.status == "success"
    assert result.record_count == 2

    assert result.records[0]["title"] == (
        "Environmental Consultant"
    )

    assert result.records[1]["title"] == (
        "WASH Specialist"
    )


def test_pipeline_normalizes_instruction(
    monkeypatch,
):
    class FakeResponse:
        url = "https://example.com"
        final_url = "https://example.com"
        status_code = 200
        content_type = "text/html"
        body = b"""
        <html>
            <article class="job">
                <h2 class="title">Consultant</h2>
            </article>
        </html>
        """

    monkeypatch.setattr(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        lambda url: FakeResponse(),
    )

    result = run_extraction_pipeline(
        "  https://example.com  ",
        "  Extract the job title  ",
    )

    assert result.url == "https://example.com"
    assert result.instruction == (
        "Extract the job title"
    )


def test_pipeline_rejects_empty_url():
    with pytest.raises(
        ValueError,
        match="URL is required",
    ):
        run_extraction_pipeline(
            "",
            "Extract the title",
        )


def test_pipeline_rejects_empty_instruction():
    with pytest.raises(
        ValueError,
        match="Instruction is required",
    ):
        run_extraction_pipeline(
            "https://example.com",
            "",
        )


def test_pipeline_result_is_serializable(
    monkeypatch,
):
    class FakeResponse:
        url = "https://example.com"
        final_url = "https://example.com"
        status_code = 200
        content_type = "text/html"
        body = b"""
        <html>
            <article class="job">
                <h2 class="title">Consultant</h2>
            </article>
        </html>
        """

    monkeypatch.setattr(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        lambda url: FakeResponse(),
    )

    result = run_extraction_pipeline(
        "https://example.com",
        "Extract the job title",
    )

    serialized = result.to_dict()

    json.dumps(serialized)

    assert serialized["validation"] is not None
    assert serialized["validation"]["valid"] is True
    assert serialized["validation"]["record_count"] == 1


def test_pipeline_reports_validation_warning_for_no_records(
    monkeypatch,
):
    class FakeResponse:
        url = "https://example.com"
        final_url = "https://example.com"
        status_code = 200
        content_type = "text/html"
        body = b"""
        <html>
            <body>
                <h1>Nothing to extract</h1>
            </body>
        </html>
        """

    monkeypatch.setattr(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        lambda url: FakeResponse(),
    )

    result = run_extraction_pipeline(
        "https://example.com",
        "Extract the job title",
    )

    assert result.status == "success"
    assert result.record_count == 0
    assert result.validation is not None
    assert result.validation.valid is True

    warning_codes = {
        issue.code
        for issue in result.validation.warnings
    }

    assert "NO_RECORDS" in warning_codes


def test_pipeline_records_observability_metadata(
    monkeypatch,
):
    class FakeResponse:
        url = "https://example.com"
        final_url = "https://example.com/jobs"
        status_code = 200
        content_type = "text/html"
        body = b"""
        <html>
            <body>
                <article class="job">
                    <h2 class="title">Environmental Consultant</h2>
                </article>
            </body>
        </html>
        """

    monkeypatch.setattr(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        lambda url: FakeResponse(),
    )

    result = run_extraction_pipeline(
        "https://example.com",
        "Extract the job title",
    )

    assert result.observability is not None

    metadata = result.observability

    assert metadata.run_id
    assert metadata.started_at
    assert metadata.completed_at
    assert metadata.duration_ms is not None
    assert metadata.status == "success"

    stage_names = [
        stage.name
        for stage in metadata.stages
    ]

    assert stage_names == [
        "validation",
        "planning",
        "fetching",
        "decoding",
        "extraction",
        "quality_validation",
        "ai_intelligence",
        "completed",
    ]


def test_pipeline_observability_records_stage_timings(
    monkeypatch,
):
    class FakeResponse:
        url = "https://example.com"
        final_url = "https://example.com"
        status_code = 200
        content_type = "text/html"
        body = b"""
        <html>
            <article class="job">
                <h2 class="title">Consultant</h2>
            </article>
        </html>
        """

    monkeypatch.setattr(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        lambda url: FakeResponse(),
    )

    result = run_extraction_pipeline(
        "https://example.com",
        "Extract the job title",
    )

    assert result.observability is not None

    stages = {
        stage.name: stage
        for stage in result.observability.stages
    }

    for stage_name in (
        "validation",
        "planning",
        "fetching",
        "decoding",
        "extraction",
        "quality_validation",
        "completed",
    ):
        assert stage_name in stages

        stage = stages[stage_name]

        assert stage.started_at
        assert stage.completed_at
        assert stage.duration_ms is not None
        assert stage.duration_ms >= 0
def test_pipeline_result_serializes_ai_output(
    monkeypatch,
):
    class FakeResponse:
        url = "https://example.com"
        final_url = "https://example.com/jobs"
        status_code = 200
        content_type = "text/html"
        body = b"""
        <html>
            <body>
                <article class="job">
                    <h2 class="title">Environmental Consultant</h2>
                </article>
            </body>
        </html>
        """

    monkeypatch.setattr(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        lambda url: FakeResponse(),
    )

    result = run_extraction_pipeline(
        "https://example.com",
        "Extract the job title",
    )

    data = result.to_dict()

    assert "ai" in data
    assert data["ai"] is not None
    assert "context" in data["ai"]
    assert "reasoning" in data["ai"]
    assert "synthesis" in data["ai"]
    assert "recommendation" in data["ai"]

    serialized = json.dumps(data)

    assert serialized

def test_pipeline_runs_complete_ai_intelligence_flow(
    monkeypatch,
):
    class FakeResponse:
        url = "https://example.com"
        final_url = "https://example.com/jobs"
        status_code = 200
        content_type = "text/html"
        body = b"""
        <html>
            <body>
                <article class="job">
                    <h2 class="title">Environmental Consultant</h2>
                    <p class="location">Kano, Nigeria</p>
                </article>
                <article class="job">
                    <h2 class="title">WASH Specialist</h2>
                    <p class="location">Abuja, Nigeria</p>
                </article>
            </body>
        </html>
        """

    monkeypatch.setattr(
        "backend.app.services.pipeline_orchestrator.fetch_url",
        lambda url: FakeResponse(),
    )

    result = run_extraction_pipeline(
        "https://example.com",
        "Extract the job title and location",
    )

    assert result.status == "success"
    assert result.record_count == 2

    assert result.ai is not None

    assert result.ai.context.observation_count == 2

    assert result.ai.reasoning is not None
    assert result.ai.reasoning.conclusion

    assert result.ai.synthesis is not None
    assert result.ai.synthesis.summary

    assert result.ai.recommendation is not None
    assert result.ai.recommendation.recommendation

    assert result.ai.evaluation is not None
    assert result.ai.evaluation.guardrails.passed

    assert result.observability is not None

    stage_names = [
        stage.name
        for stage in result.observability.stages
    ]

    assert stage_names == [
        "validation",
        "planning",
        "fetching",
        "decoding",
        "extraction",
        "quality_validation",
        "ai_intelligence",
        "completed",
    ]
