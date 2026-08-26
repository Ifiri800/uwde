from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any

from backend.app.services.extraction_engine import (
    ExtractionPlan,
    build_extraction_plan,
)
from backend.app.services.extraction_executor import (
    ExtractionResult,
    execute_extraction,
)
from backend.app.services.http_fetcher import (
    FetchError,
    fetch_url,
)
from backend.app.services.pipeline_observability import (
    PipelineExecutionMetadata,
    PipelineExecutionTracker,
)
from backend.app.services.pipeline_reliability import (
    PipelineReliabilityMetadata,
    PipelineReliabilityTracker,
)
from backend.app.services.pipeline_validator import (
    PipelineValidationResult,
    validate_pipeline_input,
    validate_pipeline_output,
)


@dataclass
class PipelineResult:
    """
    Result returned by the complete UWDE extraction pipeline.

    Pipeline:

        URL
          â†“
        Input validation
          â†“
        Extraction plan
          â†“
        HTTP fetch
          â†“
        HTML decoding
          â†“
        Structured extraction
          â†“
        Output validation
          â†“
        Validated pipeline result
    """

    status: str
    url: str
    final_url: str
    status_code: int
    content_type: str
    instruction: str
    plan: ExtractionPlan | None = None
    records: list[dict[str, Any]] = field(
        default_factory=list
    )
    errors: list[str] = field(
        default_factory=list
    )
    validation: PipelineValidationResult | None = None
    observability: PipelineExecutionMetadata | None = None
    reliability: PipelineReliabilityMetadata | None = None

    @property
    def record_count(self) -> int:
        return len(self.records)

    def to_dict(self) -> dict[str, Any]:
        validation_data = (
            self.validation.to_dict()
            if self.validation
            else None
        )

        observability_data = (
            self.observability.to_dict()
            if self.observability
            else None
        )

        reliability_data = (
            self.reliability.to_dict()
            if self.reliability
            else None
        )

        return {
            "status": self.status,
            "url": self.url,
            "final_url": self.final_url,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "instruction": self.instruction,
            "plan": (
                self.plan.to_dict()
                if self.plan
                else None
            ),
            "records": self.records,
            "record_count": self.record_count,
            "errors": self.errors,
            "validation": validation_data,
            "observability": observability_data,
            "reliability": reliability_data,
        }


def run_extraction_pipeline(
    url: str,
    instruction: str,
) -> PipelineResult:
    """
    Execute the complete UWDE extraction pipeline
    with execution observability and reliability tracking.

    Reliability tracking is initialized here so that the
    orchestrator can record execution attempts and outcomes.

    Actual retry execution and retry classification are
    intentionally handled in the subsequent reliability
    integration steps.
    """

    tracker = PipelineExecutionTracker()
    reliability_tracker = PipelineReliabilityTracker()

    normalized_url = str(url).strip()
    normalized_instruction = str(
        instruction
    ).strip()

    # ---------------------------------------------------------------
    # 1. Validate pipeline input
    # ---------------------------------------------------------------

    tracker.start_stage("validation")

    try:
        input_validation = validate_pipeline_input(
            url=normalized_url,
            instruction=normalized_instruction,
        )

        if not input_validation.valid:
            errors = [
                issue.message
                for issue in input_validation.errors
            ]

            error = ValueError(
                "; ".join(errors)
            )

            tracker.fail(
                "validation",
                error,
                failure_type="PipelineInputValidationError",
            )

            raise error

        tracker.complete_stage("validation")

    except Exception:
        if tracker.metadata.status != "failed":
            tracker.fail(
                "validation",
                "Pipeline input validation failed",
                failure_type="PipelineInputValidationError",
            )
        raise

    # ---------------------------------------------------------------
    # 2. Build extraction plan
    # ---------------------------------------------------------------

    tracker.start_stage("planning")

    try:
        plan = build_extraction_plan(
            normalized_instruction
        )

        tracker.complete_stage("planning")

    except Exception as exc:
        tracker.fail(
            "planning",
            exc,
        )
        raise

    # ---------------------------------------------------------------
    # 3. Fetch website
    # ---------------------------------------------------------------

    tracker.start_stage("fetching")

    try:
        fetched = fetch_url(
            normalized_url
        )

        tracker.complete_stage("fetching")

    except FetchError as exc:
        tracker.fail(
            "fetching",
            exc,
        )
        raise

    except Exception as exc:
        tracker.fail(
            "fetching",
            exc,
        )
        raise

    # ---------------------------------------------------------------
    # 4. Decode response body
    # ---------------------------------------------------------------

    tracker.start_stage("decoding")

    try:
        html = fetched.body.decode(
            "utf-8",
            errors="replace",
        )

        tracker.complete_stage("decoding")

    except Exception as exc:
        tracker.fail(
            "decoding",
            exc,
        )
        raise

    # ---------------------------------------------------------------
    # 5. Execute extraction with reliability retries
    # ---------------------------------------------------------------

        # ---------------------------------------------------------------
    # 5. Execute extraction with reliability retries
    # ---------------------------------------------------------------

    tracker.start_stage("extraction")

    try:
        records = []

        try:
            result: ExtractionResult = execute_extraction(
                html=html,
                plan=plan,
                base_url=fetched.final_url,
            )

            records = result.records

        except Exception as first_exc:
            # The first execution is the normal pipeline execution.
            # Only create reliability attempt metadata when a retry
            # is actually required.
            first_attempt = reliability_tracker.start_attempt()

            reliability_tracker.fail_attempt(
                first_attempt,
                first_exc,
            )

            while reliability_tracker.can_retry():
                delay = reliability_tracker.next_retry_delay()

                if delay > 0:
                    time.sleep(delay)

                attempt = reliability_tracker.start_attempt()

                try:
                    result = execute_extraction(
                        html=html,
                        plan=plan,
                        base_url=fetched.final_url,
                    )

                    records = result.records

                    reliability_tracker.complete_attempt(
                        attempt
                    )

                    reliability_tracker.complete(
                        recovered=True
                    )

                    break

                except Exception as exc:
                    reliability_tracker.fail_attempt(
                        attempt,
                        exc,
                    )

                    if not reliability_tracker.can_retry():
                        reliability_tracker.fail(exc)

                        tracker.fail(
                            "extraction",
                            exc,
                        )

                        raise

            else:
                reliability_tracker.fail(
                    first_exc
                )

                tracker.fail(
                    "extraction",
                    first_exc,
                )

                raise

        tracker.complete_stage("extraction")

    except Exception:
        if tracker.metadata.status != "failed":
            tracker.fail(
                "extraction",
                "Extraction failed after retry attempts",
                failure_type="ExtractionRetryError",
            )
        raise
    # ---------------------------------------------------------------
    # 6. Validate pipeline output
    # ---------------------------------------------------------------

    tracker.start_stage("quality_validation")

    try:
        validation = validate_pipeline_output(
            records=records,
        )

        errors = [
            issue.message
            for issue in validation.errors
        ]

        status = (
            "success"
            if validation.valid
            else "validation_failed"
        )

        tracker.complete_stage(
            "quality_validation"
        )

    except Exception as exc:
        tracker.fail(
            "quality_validation",
            exc,
        )
        raise

    # ---------------------------------------------------------------
    # 7. Complete pipeline
    # ---------------------------------------------------------------

    tracker.start_stage("completed")
    tracker.complete_stage("completed")

    observability = tracker.complete(
        status=status
    )

    if reliability_tracker.metadata.status == "running":
        reliability = reliability_tracker.complete(
            recovered=False
        )
    else:
        reliability = reliability_tracker.metadata

    # ---------------------------------------------------------------
    # 8. Return validated pipeline result
    # ---------------------------------------------------------------

    return PipelineResult(
        status=status,
        url=normalized_url,
        final_url=fetched.final_url,
        status_code=fetched.status_code,
        content_type=fetched.content_type,
        instruction=normalized_instruction,
        plan=plan,
        records=records,
        errors=errors,
        validation=validation,
        observability=observability,
        reliability=reliability,
    )







