from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketSegment:
    name: str
    description: str
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class SegmentationResult:
    dimension: str
    segments: tuple[MarketSegment, ...]


def create_segmentation(
    dimension: str,
    segments: list[MarketSegment],
) -> SegmentationResult:

    if not dimension.strip():
        raise ValueError("dimension is required")

    names: set[str] = set()

    for segment in segments:
        if not segment.name.strip():
            raise ValueError(
                "segment name is required"
            )

        key = segment.name.casefold()

        if key in names:
            raise ValueError(
                f"Duplicate segment: {segment.name}"
            )

        names.add(key)

    return SegmentationResult(
        dimension=dimension.strip(),
        segments=tuple(segments),
    )
