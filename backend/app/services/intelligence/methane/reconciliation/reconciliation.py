from __future__ import annotations

from collections.abc import Iterable
from uuid import uuid4

from .confidence import calculate_reconciliation_confidence
from .discrepancy import calculate_pairwise_discrepancies
from .fusion import fused_uncertainty, weighted_fusion
from .models import (
    ConfidenceAssessment,
    FusionResult,
    ReconciledEstimate,
    ReconciliationInput,
    ReconciliationMethod,
    ReconciliationResult,
    ReconciliationStatus,
)
from .validation import validate_reconciliation_inputs


def reconcile(
    inputs: Iterable[ReconciliationInput],
    *,
    tolerance: float = 0.10,
    reconciliation_id: str | None = None,
) -> ReconciliationResult:
    """Fuse compatible methane emission estimates."""

    values = tuple(inputs)

    errors = validate_reconciliation_inputs(values)

    result_id = reconciliation_id or f"rec-{uuid4().hex}"

    if errors:
        estimate = ReconciledEstimate(
            reconciliation_id=result_id,
            value=0.0,
            unit=values[0].unit if values else "",
            status=ReconciliationStatus.REJECTED,
            inputs=values,
        )

        fusion = FusionResult(
            value=0.0,
            unit=values[0].unit if values else "",
            method=ReconciliationMethod.WEIGHTED,
            inputs=values,
            total_weight=0.0,
        )

        return ReconciliationResult(
            estimate=estimate,
            fusion=fusion,
            warnings=tuple(errors),
        )

    value = weighted_fusion(values)
    uncertainty = fused_uncertainty(values)

    confidence_score = calculate_reconciliation_confidence(values)

    confidence = ConfidenceAssessment(
        score=confidence_score,
        level=(
            "high"
            if confidence_score >= 0.75
            else "medium"
            if confidence_score >= 0.50
            else "low"
        ),
        uncertainty=uncertainty,
    )

    discrepancies = calculate_pairwise_discrepancies(
        values,
        tolerance=tolerance,
    )

    significant_discrepancies = tuple(
        item
        for item in discrepancies
        if not item.within_tolerance
    )

    if significant_discrepancies:
        largest_discrepancy = max(
            significant_discrepancies,
            key=lambda item: item.relative_difference,
        )

        warnings = (
            (
                f"{largest_discrepancy.input_id}: "
                f"{largest_discrepancy.relative_difference * 100.0:.2f}% discrepancy"
            ),
        )
    else:
        warnings = ()
    fusion = FusionResult(
        value=value,
        unit=values[0].unit,
        method=ReconciliationMethod.WEIGHTED,
        inputs=values,
        total_weight=sum(
            item.weight for item in values
        ),
    )

    estimate = ReconciledEstimate(
        reconciliation_id=result_id,
        value=value,
        unit=values[0].unit,
        status=ReconciliationStatus.RECONCILED,
        inputs=values,
        discrepancies=discrepancies,
        confidence_level=confidence_score,
        uncertainty=uncertainty,
    )

    return ReconciliationResult(
        estimate=estimate,
        fusion=fusion,
        discrepancies=discrepancies,
        confidence=confidence,
        warnings=warnings,
    )
