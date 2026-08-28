from __future__ import annotations

from dataclasses import dataclass

from backend.app.services.intelligence.domain.signals import Signal


@dataclass(frozen=True)
class SignalDeduplicationResult:
    """
    Explainable result of signal deduplication.
    """

    signals: tuple[Signal, ...]
    duplicates_removed: int
    groups_merged: int

    def __post_init__(self) -> None:
        if self.duplicates_removed < 0:
            raise ValueError("duplicates_removed cannot be negative")

        if self.groups_merged < 0:
            raise ValueError("groups_merged cannot be negative")

    def to_dict(self) -> dict:
        return {
            "signals": [
                signal.model_dump(mode="json")
                for signal in self.signals
            ],
            "duplicates_removed": self.duplicates_removed,
            "groups_merged": self.groups_merged,
        }


class SignalDeduplicator:
    """
    Deterministically suppresses duplicate intelligence signals.

    Signals are considered duplicates when they describe the same
    signal type, entity, previous value, and current value.
    """

    def deduplicate(
        self,
        signals: list[Signal],
    ) -> SignalDeduplicationResult:
        if not isinstance(signals, list):
            raise TypeError("signals must be a list")

        if any(
            not isinstance(signal, Signal)
            for signal in signals
        ):
            raise TypeError(
                "signals must contain only Signal objects"
            )

        groups: dict[tuple[object, ...], list[Signal]] = {}

        for signal in signals:
            key = self._fingerprint(signal)
            groups.setdefault(key, []).append(signal)

        deduplicated: list[Signal] = []
        duplicates_removed = 0
        groups_merged = 0

        for group in groups.values():
            if len(group) == 1:
                deduplicated.append(group[0])
                continue

            merged = self._merge_group(group)

            deduplicated.append(merged)
            duplicates_removed += len(group) - 1
            groups_merged += 1

        return SignalDeduplicationResult(
            signals=tuple(deduplicated),
            duplicates_removed=duplicates_removed,
            groups_merged=groups_merged,
        )

    @staticmethod
    def _fingerprint(
        signal: Signal,
    ) -> tuple[object, ...]:
        """
        Build a deterministic identity for the underlying event.

        Signal ID is intentionally excluded because duplicate signals
        can originate from different observations and therefore have
        different generated IDs.
        """
        return (
            signal.signal_type,
            signal.entity_id,
            SignalDeduplicator._freeze_value(signal.previous_value),
            SignalDeduplicator._freeze_value(signal.current_value),
        )

    @staticmethod
    def _freeze_value(value: object) -> object:
        """
        Convert common nested values into deterministic hashable forms.
        """
        if isinstance(value, dict):
            return tuple(
                sorted(
                    (
                        str(key),
                        SignalDeduplicator._freeze_value(item),
                    )
                    for key, item in value.items()
                )
            )

        if isinstance(value, (list, tuple)):
            return tuple(
                SignalDeduplicator._freeze_value(item)
                for item in value
            )

        if isinstance(value, set):
            return tuple(
                sorted(
                    SignalDeduplicator._freeze_value(item)
                    for item in value
                )
            )

        return value

    @staticmethod
    def _merge_group(
        group: list[Signal],
    ) -> Signal:
        """
        Merge a group of duplicate signals into one representative.

        The first signal provides the stable identity and temporal
        position. Confidence and strength use the strongest observed
        values, while evidence is consolidated across all duplicates.
        """
        representative = group[0]

        evidence_ids: list[str] = []

        for signal in group:
            for evidence_id in signal.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)

        strongest_confidence = max(
            signal.confidence
            for signal in group
        )

        strongest_strength = max(
            signal.strength
            for signal in group
        )

        merged_signal = representative.model_copy(
            update={
                "confidence": strongest_confidence,
                "strength": strongest_strength,
                "evidence_ids": evidence_ids,
                "metadata": {
                    **representative.metadata,
                    "deduplicated": True,
                    "merged_signal_ids": [
                        signal.signal_id
                        for signal in group
                    ],
                    "duplicate_count": len(group) - 1,
                },
            }
        )

        return merged_signal


def deduplicate_signals(
    signals: list[Signal],
) -> SignalDeduplicationResult:
    """
    Convenience function using the default deduplicator.
    """
    return SignalDeduplicator().deduplicate(signals)
