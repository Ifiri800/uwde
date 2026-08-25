from __future__ import annotations

from datetime import datetime

from backend.app.services.pipeline_observability import (
    PIPELINE_STAGES,
    PipelineExecutionTracker,
)


def test_tracker_creates_run_metadata():
    tracker = PipelineExecutionTracker()

    assert tracker.metadata.run_id
    assert tracker.metadata.status == "running"
    assert tracker.metadata.completed_at is None
    assert len(tracker.metadata.stages) == len(PIPELINE_STAGES)


def test_tracker_contains_expected_stages():
    tracker = PipelineExecutionTracker()

    stage_names = [
        stage.name
        for stage in tracker.metadata.stages
    ]

    assert stage_names == list(PIPELINE_STAGES)


def test_stage_lifecycle_records_timing():
    tracker = PipelineExecutionTracker()

    tracker.start_stage("fetching")
    tracker.complete_stage("fetching")

    stage = next(
        stage
        for stage in tracker.metadata.stages
        if stage.name == "fetching"
    )

    assert stage.status == "completed"
    assert stage.started_at is not None
    assert stage.completed_at is not None
    assert stage.duration_ms is not None
    assert stage.duration_ms >= 0


def test_failed_stage_records_error():
    tracker = PipelineExecutionTracker()

    tracker.start_stage("extraction")
    metadata = tracker.fail(
        "extraction",
        ValueError("Extraction failed"),
    )

    stage = next(
        stage
        for stage in metadata.stages
        if stage.name == "extraction"
    )

    assert metadata.status == "failed"
    assert metadata.failure_stage == "extraction"
    assert metadata.failure_type == "ValueError"
    assert stage.status == "failed"
    assert stage.error == "Extraction failed"
    assert stage.duration_ms is not None


def test_successful_completion_records_metadata():
    tracker = PipelineExecutionTracker()

    tracker.start_stage("validation")
    tracker.complete_stage("validation")

    tracker.start_stage("planning")
    tracker.complete_stage("planning")

    metadata = tracker.complete()

    assert metadata.status == "success"
    assert metadata.completed_at is not None
    assert metadata.duration_ms is not None
    assert metadata.duration_ms >= 0


def test_unknown_stage_is_rejected():
    tracker = PipelineExecutionTracker()

    try:
        tracker.start_stage("unknown")
    except ValueError as exc:
        assert "Unknown pipeline stage" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def test_metadata_is_serializable():
    tracker = PipelineExecutionTracker()

    tracker.start_stage("decoding")
    tracker.complete_stage("decoding")

    metadata = tracker.complete()
    payload = metadata.to_dict()

    assert isinstance(payload, dict)
    assert isinstance(payload["run_id"], str)
    assert payload["status"] == "success"
    assert isinstance(payload["stages"], list)


def test_timestamps_are_iso8601():
    tracker = PipelineExecutionTracker()

    tracker.start_stage("decoding")
    tracker.complete_stage("decoding")

    metadata = tracker.complete()

    datetime.fromisoformat(metadata.started_at)
    datetime.fromisoformat(metadata.completed_at)

    stage = next(
        stage
        for stage in metadata.stages
        if stage.name == "decoding"
    )

    datetime.fromisoformat(stage.started_at)
    datetime.fromisoformat(stage.completed_at)
