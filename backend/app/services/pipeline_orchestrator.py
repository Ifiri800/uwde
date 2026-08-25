from __future__ import annotations

from dataclasses import dataclass, field
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
          ↓
        Input validation
          ↓
        Extraction plan
          ↓
        HTTP fetch
          ↓
        HTML decoding
          ↓
        Structured extraction
          ↓
        Output validation
          ↓
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

    @property
    def record_count(self) -> int:
        return len(self.records)

    def to_dict(self) -> dict[str, Any]:
        validation_data = (
            self.validation.to_dict()
            if self.validation
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
        }


def run_extraction_pipeline(
    url: str,
    instruction: str,
) -> PipelineResult:
    """
    Execute the complete UWDE extraction pipeline.
    """

    normalized_url = str(url).strip()
    normalized_instruction = str(
        instruction
    ).strip()

    # ---------------------------------------------------------------
    # 1. Validate pipeline input
    # ---------------------------------------------------------------

    input_validation = validate_pipeline_input(
        url=normalized_url,
        instruction=normalized_instruction,
    )

    if not input_validation.valid:
        errors = [
            issue.message
            for issue in input_validation.errors
        ]

        raise ValueError(
            "; ".join(errors)
        )

    # ---------------------------------------------------------------
    # 2. Build extraction plan
    # ---------------------------------------------------------------

    plan = build_extraction_plan(
        normalized_instruction
    )

    # ---------------------------------------------------------------
    # 3. Fetch website
    # ---------------------------------------------------------------

    try:
        fetched = fetch_url(
            normalized_url
        )
    except FetchError:
        raise

    # ---------------------------------------------------------------
    # 4. Decode response body
    # ---------------------------------------------------------------

    html = fetched.body.decode(
        "utf-8",
        errors="replace",
    )

    # ---------------------------------------------------------------
    # 5. Execute extraction
    # ---------------------------------------------------------------

    result: ExtractionResult = execute_extraction(
        html=html,
        plan=plan,
        base_url=fetched.final_url,
    )

    records = result.records

    # ---------------------------------------------------------------
    # 6. Validate pipeline output
    #
    # We deliberately do not require every extracted field here.
    # The extraction plan determines which fields are requested,
    # while the validator checks structural integrity and empty
    # output.
    # ---------------------------------------------------------------

    validation = validate_pipeline_output(
        records=records,
    )

    # ---------------------------------------------------------------
    # 7. Convert validation errors into pipeline errors
    # ---------------------------------------------------------------

    errors = [
        issue.message
        for issue in validation.errors
    ]

    # Warnings do not fail the pipeline.
    #
    # Example:
    # NO_RECORDS is currently a warning.
    #
    # Therefore a technically valid pipeline may still contain
    # validation warnings.
    status = (
        "success"
        if validation.valid
        else "validation_failed"
    )

    # ---------------------------------------------------------------
    # 8. Return validated pipeline result
    # ---------------------------------------------------------------

    return PipelineResult(
        status=status,
        url=fetched.url,
        final_url=fetched.final_url,
        status_code=fetched.status_code,
        content_type=fetched.content_type,
        instruction=normalized_instruction,
        plan=plan,
        records=records,
        errors=errors,
        validation=validation,
    )