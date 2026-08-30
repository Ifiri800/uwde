from __future__ import annotations

from typing import Any, Iterable, Mapping

from .context import build_ai_context, observation_from_mapping
from .orchestrator import AIOrchestrationResult
from .orchestrator import orchestrate_context


def build_pipeline_ai_context(
    records: Iterable[Mapping[str, Any]],
    *,
    instruction: str = "",
):
    """
    Convert validated extraction records into AI intelligence context.

    The adapter keeps the AI layer independent from the extraction
    pipeline's internal record implementation.
    """

    if not isinstance(instruction, str):
        raise TypeError("instruction must be a string")

    observations = []

    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise TypeError(
                f"record at index {index} must be a mapping"
            )

        normalized_record = dict(record)

        if not any(
            normalized_record.get(key)
            for key in (
                "statement",
                "description",
                "conclusion",
                "message",
                "name",
            )
        ):
            parts = [
                str(value).strip()
                for value in normalized_record.values()
                if value is not None and str(value).strip()
            ]

            normalized_record["statement"] = " | ".join(parts)

        observations.append(
            observation_from_mapping(
                normalized_record,
                source="extraction",
                category="record",
            )
        )

    return build_ai_context(
        observations,
        metadata={
            "instruction": instruction.strip(),
            "record_count": len(observations),
        },
    )


def orchestrate_pipeline_records(
    records: Iterable[Mapping[str, Any]],
    *,
    instruction: str = "",
) -> AIOrchestrationResult:
    """
    Run the existing AI intelligence pipeline against extracted records.
    """

    context = build_pipeline_ai_context(
        records,
        instruction=instruction,
    )

    return orchestrate_context(context)
