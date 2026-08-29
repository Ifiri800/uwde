from __future__ import annotations

from typing import Any

import httpx

from backend.app.services.api.errors import (
    APIAuthenticationError,
    APIRateLimitError,
    APIRequestError,
    APIResponseError,
)
from backend.app.services.api.models import (
    APIRequest,
    APIResponse,
)


MAX_RESPONSE_SIZE = 10 * 1024 * 1024


def execute_api_request(
    request: APIRequest,
    *,
    max_response_size: int = MAX_RESPONSE_SIZE,
) -> APIResponse:
    """
    Execute one API request and return a normalized API response.

    Security and reliability controls:
    - HTTP/HTTPS only
    - bounded timeout
    - bounded response size
    - explicit redirect handling
    - authentication failure classification
    - rate-limit classification
    - HTTP error classification
    """

    method = request.method.upper()

    timeout = httpx.Timeout(
        request.timeout_seconds,
        connect=request.timeout_seconds,
        read=request.timeout_seconds,
        write=request.timeout_seconds,
        pool=request.timeout_seconds,
    )

    headers = {
        "Accept": (
            "application/json,"
            "application/problem+json,"
            "application/xml,"
            "text/xml,"
            "text/plain;q=0.8"
        ),
        "User-Agent": (
            "UWDE/0.1 "
            "(+https://github.com/Ifiri800/uwde; "
            "Universal Web Data Extractor)"
        ),
    }

    headers.update(request.headers)

    try:
        with httpx.Client(
            timeout=timeout,
            headers=headers,
            follow_redirects=False,
            http2=False,
        ) as client:

            response = client.request(
                method=method,
                url=request.url,
                params=request.params,
                json=request.body
                if request.body is not None
                and method in {"POST", "PUT", "PATCH"}
                else None,
            )

    except httpx.TimeoutException as exc:
        raise APIRequestError(
            "The API request timed out."
        ) from exc

    except httpx.RequestError as exc:
        raise APIRequestError(
            f"Unable to connect to API: {exc}"
        ) from exc

    if response.status_code in {401, 403}:
        raise APIAuthenticationError(
            f"API authentication failed with HTTP "
            f"{response.status_code}."
        )

    if response.status_code == 429:
        retry_after = response.headers.get(
            "retry-after"
        )

        if retry_after:
            raise APIRateLimitError(
                f"API rate limit exceeded. "
                f"Retry-After: {retry_after}"
            )

        raise APIRateLimitError(
            "API rate limit exceeded."
        )

    if 300 <= response.status_code < 400:
        location = response.headers.get("location")

        if not location:
            raise APIResponseError(
                "API returned a redirect without a destination."
            )

        raise APIResponseError(
            "API redirects are not followed automatically."
        )

    if response.status_code >= 400:
        raise APIResponseError(
            f"API returned HTTP {response.status_code}."
        )

    content_length = response.headers.get(
        "content-length"
    )

    if content_length:
        try:
            if int(content_length) > max_response_size:
                raise APIResponseError(
                    "API response exceeds the maximum "
                    "allowed response size."
                )
        except ValueError:
            pass

    body = response.content

    if len(body) > max_response_size:
        raise APIResponseError(
            "API response exceeds the maximum "
            "allowed response size."
        )

    content_type = response.headers.get(
        "content-type",
        "",
    ).lower()

    return APIResponse(
        url=request.url,
        final_url=str(response.url),
        status_code=response.status_code,
        content_type=content_type,
        headers=dict(response.headers),
        body=body,
    )


__all__ = [
    "MAX_RESPONSE_SIZE",
    "execute_api_request",
]
