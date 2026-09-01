from __future__ import annotations


class GEEError(Exception):
    """Base exception for Google Earth Engine integration."""


class GEEAuthenticationError(GEEError):
    """Raised when Earth Engine authentication or initialization fails."""


class GEEConfigurationError(GEEError):
    """Raised when Earth Engine configuration is invalid."""


class GEEDatasetError(GEEError):
    """Raised when an Earth Engine dataset cannot be accessed."""


class GEEExtractionError(GEEError):
    """Raised when Earth Engine data extraction fails."""
