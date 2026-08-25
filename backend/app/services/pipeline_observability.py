from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


PIPELINE_STAGES = (
    "validation",
    "planning",
    "fetching",
    "decoding",
    "extraction",
    "quality_validation",
    "completed",
)


@dataclass
class PipelineStage:
    name: str
    status: str = "pending"
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PipelineExecutionMetadata:
    run_id: str
    started_at: str
    completed_at: str | None = None
    duration_ms: float | None = None
    status: str = "running"
    failure_stage: str | None = None
    failure_type: str | None = None
    stages: list[PipelineStage] = field(
        default_factory=list
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "failure_stage": self.failure_stage,
            "failure_type": self.failure_type,
            "stages": [
                stage.to_dict()
                for stage in self.stages
            ],
        }


class PipelineExecutionTracker:
    """
    Tracks execution metadata for a single UWDE pipeline run.
    """

    def __init__(self) -> None:
        now = datetime.now(timezone.utc)

        self._started = now

        self.metadata = PipelineExecutionMetadata(
            run_id=str(uuid4()),
            started_at=now.isoformat(),
            stages=[
                PipelineStage(name=name)
                for name in PIPELINE_STAGES
            ],
        )

    def start_stage(self, stage_name: str) -> None:
        stage = self._get_stage(stage_name)

        now = datetime.now(timezone.utc)

        stage.status = "running"
        stage.started_at = now.isoformat()
        stage.completed_at = None
        stage.duration_ms = None
        stage.error = None

    def complete_stage(self, stage_name: str) -> None:
        stage = self._get_stage(stage_name)

        now = datetime.now(timezone.utc)

        stage.status = "completed"
        stage.completed_at = now.isoformat()

        if stage.started_at:
            started = datetime.fromisoformat(
                stage.started_at
            )

            stage.duration_ms = (
                now - started
            ).total_seconds() * 1000

    def fail_stage(
        self,
        stage_name: str,
        error: Exception | str,
        failure_type: str | None = None,
    ) -> None:
        stage = self._get_stage(stage_name)

        now = datetime.now(timezone.utc)

        stage.status = "failed"
        stage.completed_at = now.isoformat()
        stage.error = str(error)

        if stage.started_at:
            started = datetime.fromisoformat(
                stage.started_at
            )

            stage.duration_ms = (
                now - started
            ).total_seconds() * 1000

        self.metadata.status = "failed"
        self.metadata.failure_stage = stage_name
        self.metadata.failure_type = (
            failure_type
            or (
                error.__class__.__name__
                if isinstance(error, Exception)
                else "PipelineError"
            )
        )

    def complete(
        self,
        status: str = "success",
    ) -> PipelineExecutionMetadata:
        now = datetime.now(timezone.utc)

        self.metadata.completed_at = now.isoformat()
        self.metadata.status = status

        self.metadata.duration_ms = (
            now - self._started
        ).total_seconds() * 1000

        return self.metadata

    def fail(
        self,
        stage_name: str,
        error: Exception | str,
        failure_type: str | None = None,
    ) -> PipelineExecutionMetadata:
        self.fail_stage(
            stage_name=stage_name,
            error=error,
            failure_type=failure_type,
        )

        now = datetime.now(timezone.utc)

        self.metadata.completed_at = now.isoformat()

        self.metadata.duration_ms = (
            now - self._started
        ).total_seconds() * 1000

        return self.metadata

    def to_dict(self) -> dict[str, Any]:
        return self.metadata.to_dict()

    def _get_stage(
        self,
        stage_name: str,
    ) -> PipelineStage:
        for stage in self.metadata.stages:
            if stage.name == stage_name:
                return stage

        raise ValueError(
            f"Unknown pipeline stage: {stage_name}"
        )