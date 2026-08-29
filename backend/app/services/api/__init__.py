from .authentication import (
    APIAuthentication,
    APIAuthType,
)

from .client import (
    MAX_RESPONSE_SIZE,
    execute_api_request,
)

from .errors import (
    APIAcquisitionError,
    APIAuthenticationError,
    APIPaginationError,
    APIRequestError,
    APIResponseError,
    APIRateLimitError,
)

from .models import (
    APIAcquisitionResult,
    APIRequest,
    APIResponse,
)

from .parser import parse_api_response

from .pagination import (
    APIPaginationConfig,
    APIPaginationState,
    APIPaginationResult,
    detect_api_pagination,
    build_page_url,
    build_offset_url,
    build_cursor_url,
    build_next_token_url,
)

from .acquisition import (
    acquire_api,
)

__all__ = [
    "APIAuthentication",
    "APIAuthType",
    "MAX_RESPONSE_SIZE",
    "execute_api_request",
    "APIAcquisitionError",
    "APIAuthenticationError",
    "APIPaginationError",
    "APIRequestError",
    "APIResponseError",
    "APIRateLimitError",
    "APIAcquisitionResult",
    "APIRequest",
    "APIResponse",
    "parse_api_response",
    "APIPaginationConfig",
    "APIPaginationState",
    "APIPaginationResult",
    "detect_api_pagination",
    "build_page_url",
    "build_offset_url",
    "build_cursor_url",
    "build_next_token_url",
    "acquire_api",
]
