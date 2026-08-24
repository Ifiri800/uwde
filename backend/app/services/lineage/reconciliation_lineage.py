from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.app.services.lineage.tracker import (
    LineageRecord,
    create_lineage,
    record_lineage_step,
)
from backend.app.services.reconciliation.pipeline import (
    ReconciliationResult,
)


@dataclass(frozen=True)
class ReconciliationLineage:
    """
    Links a reconciliation result to the lineage records of the
    observations that produced it.
    """

    field_name: str
    source_lineages: tuple[LineageRecord, ...]
    final_lineage: LineageRecord

    @property
    def source_count(self) -> int:
        """Return the number of source lineage records."""
        return len(self.source_lineages)

    @property
    def has_conflict(self) -> bool:
        """Return whether the reconciliation involved a conflict."""
        return self.field_name in {
            conflict.field_name
            for conflict in self._conflicts
        }

    @property
    def _conflicts(self) -> list[Any]:
        """
        Internal compatibility property.

        The final lineage stores reconciliation metadata so the
        lineage object remains self-contained.
        """
        conflicts = self.final_lineage.metadata.get(
            "conflicts",
            [],
        )

        return list(conflicts)

    @property
    def final_value(self) -> Any:
        """Return the final reconciled value."""
        return self.final_lineage.final_value


def create_reconciliation_lineage(
    field_name: str,
    source_lineages: list[LineageRecord],
    final_value: Any,
    *,
    reconciliation_result: ReconciliationResult | None = None,
    metadata: dict[str, Any] | None = None,
) -> ReconciliationLineage:
    """
    Create lineage for a reconciled field.

    Source lineage records are preserved unchanged. A separate
    final lineage record is created to represent the reconciled
    result.
    """

    if not field_name or not field_name.strip():
        raise ValueError("field_name is required")

    if not source_lineages:
        raise ValueError(
            "at least one source lineage is required"
        )

    first_source = source_lineages[0]

    lineage_metadata: dict[str, Any] = {
        "lineage_type": "reconciliation",
        "source_count": len(source_lineages),
    }

    if reconciliation_result is not None:
        lineage_metadata.update(
            {
                "conflict_count": (
                    reconciliation_result.conflict_count
                ),
                "requires_review": (
                    reconciliation_result.requires_review
                ),
                "conflicts": list(
                    reconciliation_result.conflicts
                ),
            }
        )

    if metadata:
        lineage_metadata.update(metadata)

    final_lineage = create_lineage(
        field_name=field_name,
        source_url=first_source.source_url,
        raw_value=first_source.raw_value,
        metadata=lineage_metadata,
    )

    record_lineage_step(
        final_lineage,
        operation="reconcile",
        input_value=[
            source.final_value
            for source in source_lineages
        ],
        output_value=final_value,
        metadata={
            "source_count": len(source_lineages),
            "strategy": (
                reconciliation_result.resolutions[0].strategy
                if reconciliation_result is not None
                and reconciliation_result.resolutions
                else None
            ),
        },
    )

    return ReconciliationLineage(
        field_name=field_name,
        source_lineages=tuple(source_lineages),
        final_lineage=final_lineage,
    )


def attach_reconciliation_lineage(
    lineage: LineageRecord,
    reconciliation_result: ReconciliationResult,
) -> LineageRecord:
    """
    Append a reconciliation step to an existing lineage record.

    This is useful when the same lineage object should continue
    through reconciliation instead of creating a separate record.
    """

    if not isinstance(lineage, LineageRecord):
        raise TypeError(
            "lineage must be a LineageRecord"
        )

    if not isinstance(
        reconciliation_result,
        ReconciliationResult,
    ):
        raise TypeError(
            "reconciliation_result must be a ReconciliationResult"
        )

    final_value = reconciliation_result.values.get(
        lineage.field_name,
        lineage.final_value,
    )

    record_lineage_step(
        lineage,
        operation="reconcile",
        input_value=lineage.final_value,
        output_value=final_value,
        metadata={
            "conflict_count": (
                reconciliation_result.conflict_count
            ),
            "requires_review": (
                reconciliation_result.requires_review
            ),
        },
    )

    lineage.metadata["reconciliation"] = {
        "conflict_count": (
            reconciliation_result.conflict_count
        ),
        "requires_review": (
            reconciliation_result.requires_review
        ),
    }

    return lineage


def build_reconciliation_lineages(
    source_lineages: dict[
        str,
        list[LineageRecord],
    ],
    reconciliation_result: ReconciliationResult,
) -> dict[str, ReconciliationLineage]:
    """
    Build reconciliation lineage records for every reconciled field.

    Fields without a final reconciled value are still represented
    when they have source lineage records.
    """

    results: dict[str, ReconciliationLineage] = {}

    for field_name, lineages in source_lineages.items():
        if not lineages:
            continue

        final_value = reconciliation_result.values.get(
            field_name,
            lineages[0].final_value,
        )

        results[field_name] = (
            create_reconciliation_lineage(
                field_name=field_name,
                source_lineages=lineages,
                final_value=final_value,
                reconciliation_result=reconciliation_result,
            )
        )

    return results