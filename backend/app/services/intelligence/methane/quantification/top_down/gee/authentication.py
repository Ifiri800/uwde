from __future__ import annotations

from .errors import GEEAuthenticationError


def initialize_earth_engine(
    project: str,
    *,
    ee_module=None,
) -> None:
    """
    Initialize the Earth Engine Python API.

    Authentication is deliberately delegated to the Earth Engine
    environment. This function does not store credentials.
    """

    if not project or not project.strip():
        raise GEEAuthenticationError(
            "Earth Engine project is required"
        )

    if ee_module is None:
        try:
            import ee
        except ImportError as exc:
            raise GEEAuthenticationError(
                "The earthengine-api package is not installed"
            ) from exc

        ee_module = ee

    try:
        ee_module.Initialize(project=project)
    except Exception as exc:
        raise GEEAuthenticationError(
            "Earth Engine initialization failed"
        ) from exc
