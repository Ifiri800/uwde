from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit


@dataclass(frozen=True)
class APIPaginationConfig:
    """Configuration for bounded API pagination."""

    strategy: str = "next_url"
    page_parameter: str = "page"
    offset_parameter: str = "offset"
    limit_parameter: str = "limit"
    cursor_parameter: str = "cursor"
    page_size: int = 100
    max_pages: int = 10
    max_records: int = 1000

    def __post_init__(self) -> None:
        if self.strategy not in {
            "next_url",
            "page",
            "offset",
            "cursor",
            "next_token",
        }:
            raise ValueError(
                f"Unsupported API pagination strategy: {self.strategy}"
            )

        if self.page_size <= 0:
            raise ValueError("page_size must be greater than zero")

        if self.max_pages <= 0:
            raise ValueError("max_pages must be greater than zero")

        if self.max_records <= 0:
            raise ValueError("max_records must be greater than zero")

        for name in (
            "page_parameter",
            "offset_parameter",
            "limit_parameter",
            "cursor_parameter",
        ):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True)
class APIPaginationState:
    """State for one API pagination sequence."""

    page: int = 1
    offset: int = 0
    cursor: str | None = None
    next_token: str | None = None
    pages_crawled: int = 0
    records_collected: int = 0

    def can_continue(
        self,
        config: APIPaginationConfig,
    ) -> bool:
        return (
            self.pages_crawled < config.max_pages
            and self.records_collected < config.max_records
        )


@dataclass(frozen=True)
class APIPaginationResult:
    """Pagination information extracted from one API response."""

    next_url: str | None = None
    cursor: str | None = None
    next_token: str | None = None

    @property
    def has_next(self) -> bool:
        return bool(
            self.next_url
            or self.cursor
            or self.next_token
        )


def _nested_get(
    data: Any,
    paths: tuple[str, ...],
) -> Any:
    """Find the first non-empty value from candidate nested paths."""

    for path in paths:
        current = data

        for part in path.split("."):
            if not isinstance(current, dict):
                current = None
                break

            current = current.get(part)

        if current not in (None, ""):
            return current

    return None


def detect_api_pagination(
    data: Any,
    *,
    current_url: str,
    headers: dict[str, str] | None = None,
) -> APIPaginationResult:
    """
    Detect common API pagination signals.

    Supported response signals:
    - next URL
    - cursor
    - next_token
    - continuation_token
    - HTTP Link header with rel="next"
    """

    headers = headers or {}

    link_header = headers.get("link") or headers.get("Link")

    if link_header:
        for part in link_header.split(","):
            section = part.strip()

            if 'rel="next"' not in section.lower():
                continue

            start = section.find("<")
            end = section.find(">")

            if start >= 0 and end > start:
                return APIPaginationResult(
                    next_url=section[start + 1:end]
                )

    if not isinstance(data, dict):
        return APIPaginationResult()

    next_url = _nested_get(
        data,
        (
            "next",
            "next_url",
            "nextUrl",
            "pagination.next",
            "pagination.next_url",
            "links.next",
            "links.next_url",
            "meta.next",
        ),
    )

    cursor = _nested_get(
        data,
        (
            "next_cursor",
            "nextCursor",
            "cursor",
            "pagination.next_cursor",
            "pagination.nextCursor",
            "meta.next_cursor",
        ),
    )

    next_token = _nested_get(
        data,
        (
            "next_token",
            "nextToken",
            "continuation_token",
            "continuationToken",
            "pagination.next_token",
            "pagination.nextToken",
            "meta.next_token",
        ),
    )

    return APIPaginationResult(
        next_url=str(next_url) if next_url else None,
        cursor=str(cursor) if cursor else None,
        next_token=str(next_token) if next_token else None,
    )


def build_page_url(
    current_url: str,
    config: APIPaginationConfig,
    page: int,
) -> str:
    """Build the URL for numbered page pagination."""

    if page <= 0:
        raise ValueError("page must be greater than zero")

    parts = urlsplit(current_url)
    query = parse_qs(
        parts.query,
        keep_blank_values=True,
    )

    query[config.page_parameter] = [str(page)]
    query[config.limit_parameter] = [str(config.page_size)]

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query, doseq=True),
            parts.fragment,
        )
    )


def build_offset_url(
    current_url: str,
    config: APIPaginationConfig,
    offset: int,
) -> str:
    """Build the URL for offset/limit pagination."""

    if offset < 0:
        raise ValueError("offset must not be negative")

    parts = urlsplit(current_url)
    query = parse_qs(
        parts.query,
        keep_blank_values=True,
    )

    query[config.offset_parameter] = [str(offset)]
    query[config.limit_parameter] = [str(config.page_size)]

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query, doseq=True),
            parts.fragment,
        )
    )


def build_cursor_url(
    current_url: str,
    config: APIPaginationConfig,
    cursor: str,
) -> str:
    """Build the URL for cursor pagination."""

    if not cursor.strip():
        raise ValueError("cursor must not be empty")

    parts = urlsplit(current_url)
    query = parse_qs(
        parts.query,
        keep_blank_values=True,
    )

    query[config.cursor_parameter] = [cursor]
    query[config.limit_parameter] = [str(config.page_size)]

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query, doseq=True),
            parts.fragment,
        )
    )


def build_next_token_url(
    current_url: str,
    *,
    token_parameter: str = "next_token",
    token: str,
) -> str:
    """Build the URL for token-based pagination."""

    if not token_parameter.strip():
        raise ValueError(
            "token_parameter must not be empty"
        )

    if not token.strip():
        raise ValueError(
            "token must not be empty"
        )

    parts = urlsplit(current_url)
    query = parse_qs(
        parts.query,
        keep_blank_values=True,
    )

    query[token_parameter] = [token]

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            urlencode(query, doseq=True),
            parts.fragment,
        )
    )


__all__ = [
    "APIPaginationConfig",
    "APIPaginationState",
    "APIPaginationResult",
    "detect_api_pagination",
    "build_page_url",
    "build_offset_url",
    "build_cursor_url",
    "build_next_token_url",
]
