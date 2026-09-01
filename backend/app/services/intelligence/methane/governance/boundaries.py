from __future__ import annotations

from collections.abc import Iterable

from .models import AssetBoundary, BoundaryType


def build_boundary(
    assets: Iterable[AssetBoundary],
    boundary_type: BoundaryType,
) -> tuple[AssetBoundary, ...]:
    """Build a normalized immutable boundary collection."""

    if not isinstance(boundary_type, BoundaryType):
        raise TypeError("boundary_type must be a BoundaryType")

    result = []

    for asset in assets:
        if not isinstance(asset, AssetBoundary):
            raise TypeError("all assets must be AssetBoundary instances")

        if asset.boundary_type != boundary_type:
            raise ValueError(
                f"asset {asset.asset_id} has boundary type "
                f"{asset.boundary_type.value}, expected "
                f"{boundary_type.value}"
            )

        if asset.included:
            result.append(asset)

    return tuple(result)


def validate_boundary(
    assets: Iterable[AssetBoundary],
) -> tuple[str, ...]:
    """Return deterministic boundary validation errors."""

    errors: list[str] = []
    seen: set[str] = set()

    for asset in assets:
        if not isinstance(asset, AssetBoundary):
            errors.append("invalid asset boundary type")
            continue

        if asset.asset_id in seen:
            errors.append(f"duplicate asset_id: {asset.asset_id}")

        seen.add(asset.asset_id)

    return tuple(errors)
