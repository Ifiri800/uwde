from __future__ import annotations


class APIAcquisitionError(RuntimeError):
    """Base exception for API acquisition failures."""


class APIRequestError(APIAcquisitionError):
    """Raised when an API request cannot be completed."""


class APIResponseError(APIAcquisitionError):
    """Raised when an API returns an unusable response."""


class APIAuthenticationError(APIAcquisitionError):
    """Raised when API authentication fails."""


class APIRateLimitError(APIAcquisitionError):
    """Raised when an API rate limit is encountered."""


class APIPaginationError(APIAcquisitionError):
    """Raised when API pagination cannot be processed."""
