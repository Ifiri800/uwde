from __future__ import annotations

from .models import ReconciledEstimate, ReconciliationResult


class ReconciliationRegistry:
    """In-memory registry for reconciliation results."""

    def __init__(self) -> None:
        self._results: dict[str, ReconciliationResult] = {}

    def register(
        self,
        result: ReconciliationResult,
    ) -> None:
        reconciliation_id = result.estimate.reconciliation_id

        if reconciliation_id in self._results:
            raise ValueError(
                f"duplicate reconciliation ID: {reconciliation_id}"
            )

        self._results[reconciliation_id] = result

    def get(
        self,
        reconciliation_id: str,
    ) -> ReconciliationResult | None:
        return self._results.get(reconciliation_id)

    def get_estimate(
        self,
        reconciliation_id: str,
    ) -> ReconciledEstimate | None:
        result = self.get(reconciliation_id)

        if result is None:
            return None

        return result.estimate

    def all_results(self) -> tuple[ReconciliationResult, ...]:
        return tuple(self._results.values())
