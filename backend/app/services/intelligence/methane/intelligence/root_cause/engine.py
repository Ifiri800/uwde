from __future__ import annotations

from collections.abc import Mapping


def identify_root_cause(
    signals: Mapping[str, float],
) -> tuple[str, ...]:

    if not signals:
        return ()

    ordered = sorted(
        signals.items(),
        key=lambda item: (-item[1], item[0]),
    )

    return tuple(
        name
        for name, value in ordered
        if value > 0
    )
