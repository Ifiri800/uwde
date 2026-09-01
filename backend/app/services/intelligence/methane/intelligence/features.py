from __future__ import annotations

from collections.abc import Iterable

from backend.app.services.intelligence.methane.intelligence.models import (
    IntelligenceFeature,
)


def normalize_features(
    features: Iterable[IntelligenceFeature],
) -> tuple[IntelligenceFeature, ...]:
    """Validate and deterministically order Layer 10 features."""

    values = tuple(features)

    if any(
        not isinstance(feature, IntelligenceFeature)
        for feature in values
    ):
        raise TypeError(
            "features must contain only IntelligenceFeature objects"
        )

    return tuple(
        sorted(
            values,
            key=lambda feature: feature.name,
        )
    )


def feature_map(
    features: Iterable[IntelligenceFeature],
) -> dict[str, float]:
    """Return a deterministic feature-name/value mapping."""

    normalized = normalize_features(features)

    return {
        feature.name: feature.value
        for feature in normalized
    }
