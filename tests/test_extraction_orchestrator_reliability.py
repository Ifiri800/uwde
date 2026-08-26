from __future__ import annotations

from unittest.mock import patch

import pytest

from backend.app.services.extraction_engine import (
    ExtractionField,
    ExtractionPlan,
)
from backend.app.services.extraction_executor import (
    ExtractionResult,
)
from backend.app.services.http_fetcher import (
    FetchResult,
)
from backend.app.services.pipeline_orchestrator import (
    PipelineResult,
    run_extraction_pipeline,
)


def _mock_fetch_result() -> FetchResult:
    return FetchResult(
        url="https://example.com",
        final_url="https://example.com",
        status_code=200,
        content_type="text/html",
        body=(
            b"<article class='job'>"
            b"<h2 class='title'>Environmental Consultant</h2>"
            b"</article>"
        ),
    )


def _mock_plan() -> ExtractionPlan:
    return ExtractionPlan(
        instruction="Extract the job title.",
        fields=[
            ExtractionField(
                name="title",
                description="The job title",
            )
        ],
    )


def _successful_extraction() -> ExtractionResult:
    return ExtractionResult(
        records=[
            {
                "title": "Environmental Consultant"
            }
        ]
    )


def test_pipeline_result_contains_reliability_metadata():
    with (
        patch(
            "backend.app.services.pipeline_orchestrator.fetch_url",
            return_value=_mock_fetch_result(),
        ),
        patch(
            "backend.app.services.pipeline_orchestrator.build_extraction_plan",
            return_value=_mock_plan(),
        ),
        patch(
            "backend.app.services.pipeline_orchestrator.execute_extraction",
            return_value=_successful_extraction(),
        ),
    ):
        result = run_extraction_pipeline(
            "https://example.com",
            "Extract the job title.",
        )

    assert isinstance(result, PipelineResult)
    assert result.reliability is not None
    assert result.reliability.status == "success"
    assert result.reliability.attempt_count == 0
    assert result.reliability.retry_count == 0
    assert result.reliability.recovered is False


def test_pipeline_result_serializes_reliability_metadata():
    with (
        patch(
            "backend.app.services.pipeline_orchestrator.fetch_url",
            return_value=_mock_fetch_result(),
        ),
        patch(
            "backend.app.services.pipeline_orchestrator.build_extraction_plan",
            return_value=_mock_plan(),
        ),
        patch(
            "backend.app.services.pipeline_orchestrator.execute_extraction",
            return_value=_successful_extraction(),
        ),
    ):
        result = run_extraction_pipeline(
            "https://example.com",
            "Extract the job title.",
        )

    serialized = result.to_dict()

    assert "reliability" in serialized
    assert serialized["reliability"] is not None
    assert serialized["reliability"]["status"] == "success"
    assert serialized["reliability"]["attempt_count"] == 0
    assert serialized["reliability"]["retry_count"] == 0
    assert serialized["reliability"]["recovered"] is False


def test_pipeline_retries_failed_extraction_and_recovers():
    failures = [
        RuntimeError("Temporary extraction failure"),
        _successful_extraction(),
    ]

    def execute_with_one_failure(**_: object) -> ExtractionResult:
        outcome = failures.pop(0)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome

    with (
        patch(
            "backend.app.services.pipeline_orchestrator.fetch_url",
            return_value=_mock_fetch_result(),
        ),
        patch(
            "backend.app.services.pipeline_orchestrator.build_extraction_plan",
            return_value=_mock_plan(),
        ),
        patch(
            "backend.app.services.pipeline_orchestrator.execute_extraction",
            side_effect=execute_with_one_failure,
        ) as execute_mock,
    ):
        result = run_extraction_pipeline(
            "https://example.com",
            "Extract the job title.",
        )

    assert isinstance(result, PipelineResult)
    assert result.status == "success"
    assert result.records == [
        {
            "title": "Environmental Consultant"
        }
    ]

    assert execute_mock.call_count == 2

    assert result.reliability is not None
    assert result.reliability.status == "success"
    assert result.reliability.attempt_count == 2
    assert result.reliability.retry_count == 1
    assert result.reliability.recovered is True

    assert len(result.reliability.attempts) == 2
    assert result.reliability.attempts[0].status == "failed"
    assert result.reliability.attempts[0].error == (
        "Temporary extraction failure"
    )
    assert result.reliability.attempts[0].error_type == (
        "RuntimeError"
    )
    assert result.reliability.attempts[1].status == "success"


def test_pipeline_reliability_serializes_retry_recovery():
    failures = [
        RuntimeError("Temporary extraction failure"),
        _successful_extraction(),
    ]

    def execute_with_one_failure(**_: object) -> ExtractionResult:
        outcome = failures.pop(0)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome

    with (
        patch(
            "backend.app.services.pipeline_orchestrator.fetch_url",
            return_value=_mock_fetch_result(),
        ),
        patch(
            "backend.app.services.pipeline_orchestrator.build_extraction_plan",
            return_value=_mock_plan(),
        ),
        patch(
            "backend.app.services.pipeline_orchestrator.execute_extraction",
            side_effect=execute_with_one_failure,
        ),
    ):
        result = run_extraction_pipeline(
            "https://example.com",
            "Extract the job title.",
        )

    serialized = result.to_dict()
    reliability = serialized["reliability"]

    assert reliability["status"] == "success"
    assert reliability["attempt_count"] == 2
    assert reliability["retry_count"] == 1
    assert reliability["recovered"] is True
    assert len(reliability["attempts"]) == 2
    assert reliability["attempts"][0]["status"] == "failed"
    assert reliability["attempts"][1]["status"] == "success"
