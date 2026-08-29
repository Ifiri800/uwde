from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from backend.app.services.api.authentication import APIAuthentication
from backend.app.services.api.client import execute_api_request
from backend.app.services.api.errors import (
    APIAcquisitionError,
    APIPaginationError,
)
from backend.app.services.api.models import (
    APIAcquisitionResult,
    APIRequest,
)
from backend.app.services.api.pagination import (
    APIPaginationConfig,
    APIPaginationState,
    build_cursor_url,
    build_next_token_url,
    build_offset_url,
    build_page_url,
    detect_api_pagination,
)
from backend.app.services.api.parser import parse_api_response


def _extract_records(data: Any) -> list[dict[str, Any]]:
    """Normalize common API payload shapes into records."""

    if isinstance(data, list):
        return [
            item for item in data
            if isinstance(item, dict)
        ]

    if not isinstance(data, dict):
        return []

    for key in (
        "data",
        "results",
        "items",
        "records",
    ):
        value = data.get(key)

        if isinstance(value, list):
            return [
                item for item in value
                if isinstance(item, dict)
            ]

    return [data]


def _build_next_request_url(
    current_url: str,
    config: APIPaginationConfig,
    state: APIPaginationState,
    pagination,
) -> str | None:
    """Build the next request URL from detected pagination."""

    if config.strategy == "page":
        return build_page_url(
            current_url,
            config,
            state.pages_crawled + 1,
        )

    if config.strategy == "offset":
        return build_offset_url(
            current_url,
            config,
            state.offset + config.page_size,
        )

    if config.strategy == "cursor" and pagination.cursor:
        return build_cursor_url(
            current_url,
            config,
            pagination.cursor,
        )

    if config.strategy == "next_token" and pagination.next_token:
        return build_next_token_url(
            current_url,
            token_parameter=config.cursor_parameter,
            token=pagination.next_token,
        )

    if pagination.next_url:
        return urljoin(
            current_url,
            pagination.next_url,
        )

    return None


def acquire_api(
    request: APIRequest,
    *,
    authentication: APIAuthentication | None = None,
    pagination: APIPaginationConfig | None = None,
) -> APIAcquisitionResult:
    """
    Execute an API acquisition sequence with bounded pagination.
    """

    config = pagination or APIPaginationConfig()

    state = APIPaginationState()

    records: list[dict[str, Any]] = []
    current_url = request.url
    current_request = request
    first_response = None

    try:
        while state.can_continue(config):
            response = execute_api_request(
                current_request,
                authentication=authentication,
            )

            if first_response is None:
                first_response = response

            data = parse_api_response(response)

            page_records = _extract_records(data)

            remaining = max(
                0,
                config.max_records - len(records),
            )

            records.extend(
                page_records[:remaining]
            )

            state = APIPaginationState(
                page=state.page,
                offset=state.offset + config.page_size,
                cursor=None,
                next_token=None,
                pages_crawled=state.pages_crawled + 1,
                records_collected=len(records),
            )

            if len(records) >= config.max_records:
                break

            pagination_result = detect_api_pagination(
                data,
                current_url=response.final_url,
                headers=response.headers,
            )

            if not pagination_result.has_next:
                break

            next_url = _build_next_request_url(
                response.final_url,
                config,
                state,
                pagination_result,
            )

            if not next_url:
                break

            current_url = next_url

            current_request = APIRequest(
                url=current_url,
                method=request.method,
                headers=request.headers,
                params={},
                body=request.body,
                timeout_seconds=request.timeout_seconds,
            )

        if first_response is None:
            raise APIAcquisitionError(
                "API acquisition produced no response."
            )

        return APIAcquisitionResult(
            status="success",
            url=request.url,
            final_url=first_response.final_url,
            status_code=first_response.status_code,
            content_type=first_response.content_type,
            records=records,
            data=None,
            pages_crawled=state.pages_crawled,
        )

    except APIPaginationError:
        raise

    except APIAcquisitionError:
        raise

    except Exception as exc:
        raise APIAcquisitionError(
            f"API acquisition failed: {exc}"
        ) from exc


__all__ = [
    "acquire_api",
]




