from __future__ import annotations

from typing import Any

from .conflicts import (
    Conflict,
    detect_conflicts,
)
from .models import ReconciliationResult
from .provenance import SourcedValue
from .resolver import (
    ResolutionStrategy,
    resolve_conflicts,
)
from .uncertainty import (
    Uncertainty,
    calculate_conflict_uncertainty,
)


def reconcile(
    observations_by_field: dict[
        str,
        list[SourcedValue],
    ],
    strategy: ResolutionStrategy | str = (
        ResolutionStrategy.HIGHEST_CONFIDENCE
    ),
) -> ReconciliationResult:
    """
    Reconcile observations grouped by field.

    Process:

    1. Detect conflicts.
    2. Resolve conflicts.
    3. Calculate uncertainty.
    4. Preserve non-conflicting values.
    5. Determine whether human review is required.
    """

    conflicts = detect_conflicts(
        observations_by_field
    )

    resolutions = resolve_conflicts(
        conflicts,
        strategy,
    )

    values: dict[str, Any] = {}

    conflict_fields = {
        conflict.field_name
        for conflict in conflicts
    }

    # Preserve values that do not have conflicts.
    for (
        field_name,
        observations,
    ) in observations_by_field.items():

        if not observations:
            continue

        if field_name not in conflict_fields:
            values[field_name] = (
                observations[0].value
            )

    # Add successfully resolved values.
    for resolution in resolutions:

        if resolution.resolved:
            values[
                resolution.field_name
            ] = resolution.value

    # Calculate uncertainty for each conflict.
    uncertainties: dict[
        str,
        Uncertainty,
    ] = {}

    for conflict in conflicts:

        uncertainties[
            conflict.field_name
        ] = calculate_conflict_uncertainty(
            conflict
        )

    requires_review = (
        any(
            resolution.requires_review
            for resolution in resolutions
        )
        or any(
            uncertainty.requires_review
            for uncertainty
            in uncertainties.values()
        )
    )

    return ReconciliationResult(
        values=values,
        conflicts=conflicts,
        resolutions=resolutions,
        requires_review=requires_review,
        uncertainties=uncertainties,
    )


def reconcile_records(
    records: list[
        dict[
            str,
            list[SourcedValue],
        ]
    ],
    strategy: ResolutionStrategy | str = (
        ResolutionStrategy.HIGHEST_CONFIDENCE
    ),
) -> list[ReconciliationResult]:
    """
    Reconcile multiple independent records.

    Each record is processed independently so
    that conflicts cannot contaminate other records.
    """

    return [
        reconcile(
            observations_by_field=record,
            strategy=strategy,
        )
        for record in records
    ]