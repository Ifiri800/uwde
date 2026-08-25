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


@dataclass
class PipelineResult:
    """
    Result returned by the UWDE extraction pipeline.

    The orchestrator is intentionally lightweight:
    it coordinates existing services rather than reimplementing
    fetching, planning, or extraction logic.
    """

    status: str
    url: str
    final_url: str
    status_code: int
    content_type: str
    instruction: str
    plan: ExtractionPlan | None = None
    records: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def record_count(self) -> int:
        return len(self.records)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "url": self.url,
            "final_url": self.final_url,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "instruction": self.instruction,
            "plan": self.plan.to_dict() if self.plan else None,
            "records": self.records,
            "record_count": self.record_count,
            "errors": self.errors,
        }


def run_extraction_pipeline(
    url: str,
    instruction: str,
) -> PipelineResult:
    """
    Execute the core UWDE extraction pipeline.

    Pipeline:

        URL
          ↓
        Extraction plan
          ↓
        HTTP fetch
          ↓
        HTML decoding
          ↓
        Extraction
          ↓
        Structured result

    Existing services remain responsible for their own concerns:

        extraction_engine  -> planning
        http_fetcher       -> HTTP retrieval
        extraction_executor -> structured extraction
    """

    normalized_url = str(url).strip()
    normalized_instruction = str(instruction).strip()

    if not normalized_url:
        raise ValueError("URL is required.")

    if not normalized_instruction:
        raise ValueError("Instruction is required.")

    # ---------------------------------------------------------------
    # 1. Build extraction plan
    # ---------------------------------------------------------------

    plan = build_extraction_plan(
        normalized_instruction
    )

    # ---------------------------------------------------------------
    # 2. Fetch website
    # ---------------------------------------------------------------

    try:
        fetched = fetch_url(
            normalized_url
        )
    except FetchError:
        raise

    # ---------------------------------------------------------------
    # 3. Decode response body
    # ---------------------------------------------------------------

    html = fetched.body.decode(
        "utf-8",
        errors="replace",
    )

    # ---------------------------------------------------------------
    # 4. Execute extraction
    # ---------------------------------------------------------------

    result: ExtractionResult = execute_extraction(
        html=html,
        plan=plan,
        base_url=fetched.final_url,
    )

    # ---------------------------------------------------------------
    # 5. Return normalized pipeline result
    # ---------------------------------------------------------------

    return PipelineResult(
        status="success",
        url=fetched.url,
        final_url=fetched.final_url,
        status_code=fetched.status_code,
        content_type=fetched.content_type,
        instruction=normalized_instruction,
        plan=plan,
        records=result.records,
    )