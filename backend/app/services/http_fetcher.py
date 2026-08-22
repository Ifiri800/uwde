from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import httpx

from backend.app.services.url_security import URLSecurityError, validate_url


MAX_RESPONSE_SIZE = 5 * 1024 * 1024  # 5 MB

USER_AGENT = (
    "UWDE/0.1 (+https://github.com/Ifiri800/uwde; "
    "Universal Web Data Extractor)"
)


class FetchError(RuntimeError):
    """Raised when a website cannot be safely fetched."""


@dataclass
class FetchResult:
    url: str
    status_code: int
    content_type: str
    body: bytes
    final_url: str


def _validate_redirect_url(url: str) -> str:
    """Validate a redirect destination before following it."""
    try:
        return validate_url(url)
    except URLSecurityError as exc:
        raise FetchError(f"Unsafe redirect destination: {exc}") from exc


def fetch_url(
    url: str,
    *,
    timeout_seconds: float = 15.0,
    max_response_size: int = MAX_RESPONSE_SIZE,
) -> FetchResult:
    """
    Fetch a public HTTP/HTTPS URL safely.

    Security controls:
    - validates the initial URL
    - validates every redirect destination
    - limits redirects
    - enforces connection/read/write/pool timeouts
    - limits response size
    - rejects unsupported content types
    """

    try:
        validated_url = validate_url(url)
    except URLSecurityError as exc:
        raise FetchError(str(exc)) from exc

    timeout = httpx.Timeout(
        timeout_seconds,
        connect=timeout_seconds,
        read=timeout_seconds,
        write=timeout_seconds,
        pool=timeout_seconds,
    )

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,text/plain;q=0.8"
        ),
        "Accept-Encoding": "gzip, deflate",
    }

    current_url = validated_url

    try:
        with httpx.Client(
            timeout=timeout,
            headers=headers,
            follow_redirects=False,
            http2=False,
        ) as client:
            for _ in range(5):
                response = client.get(current_url)

                if 300 <= response.status_code < 400:
                    location = response.headers.get("location")

                    if not location:
                        raise FetchError(
                            "The server returned a redirect without a "
                            "destination."
                        )

                    redirect_url = urljoin(current_url, location)
                    current_url = _validate_redirect_url(redirect_url)
                    continue

                if response.status_code >= 400:
                    raise FetchError(
                        f"Website returned HTTP {response.status_code}."
                    )

                content_type = response.headers.get(
                    "content-type",
                    "",
                ).lower()

                if not (
                    content_type.startswith("text/html")
                    or content_type.startswith("application/xhtml+xml")
                    or content_type.startswith("text/plain")
                ):
                    raise FetchError(
                        f"Unsupported content type: {content_type or 'unknown'}"
                    )

                content_length = response.headers.get("content-length")

                if content_length:
                    try:
                        if int(content_length) > max_response_size:
                            raise FetchError(
                                "The website response is larger than the "
                                "allowed limit."
                            )
                    except ValueError:
                        pass

                body = response.content

                if len(body) > max_response_size:
                    raise FetchError(
                        "The website response is larger than the "
                        "allowed limit."
                    )

                return FetchResult(
                    url=validated_url,
                    status_code=response.status_code,
                    content_type=content_type,
                    body=body,
                    final_url=str(response.url),
                )

            raise FetchError("Too many redirects.")

    except FetchError:
        raise

    except httpx.TimeoutException as exc:
        raise FetchError("The website request timed out.") from exc

    except httpx.RequestError as exc:
        raise FetchError(
            f"Unable to connect to the website: {exc}"
        ) from exc