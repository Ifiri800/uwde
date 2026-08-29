from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup

from app.services.extraction_engine import ExtractionPlan
from app.services.pagination import (
    PaginationConfig,
    PaginationStrategy,
    build_next_url,
)


@dataclass
class CrawlResult:
    records: list[dict[str, Any]] = field(default_factory=list)
    pages_crawled: int = 0
    urls_crawled: list[str] = field(default_factory=list)
    stopped_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "records": self.records,
            "pages_crawled": self.pages_crawled,
            "urls_crawled": self.urls_crawled,
            "stopped_reason": self.stopped_reason,
        }


def _get_records(
    extraction_result: Any,
) -> list[dict[str, Any]]:
    """
    Normalize supported extraction result shapes.

    Supported:
    - ExtractionResult-like objects
    - dictionaries containing "records"
    - direct lists of dictionaries
    """

    if extraction_result is None:
        return []

    records = getattr(
        extraction_result,
        "records",
        None,
    )

    if records is not None:
        if isinstance(records, list):
            return [
                record
                for record in records
                if isinstance(record, dict)
            ]

        return []

    if isinstance(
        extraction_result,
        dict,
    ):
        records = extraction_result.get(
            "records",
            [],
        )

        if isinstance(records, list):
            return [
                record
                for record in records
                if isinstance(record, dict)
            ]

        return []

    if isinstance(
        extraction_result,
        list,
    ):
        return [
            record
            for record in extraction_result
            if isinstance(record, dict)
        ]

    return []


def _find_next_url(
    html: str,
    current_url: str,
) -> str | None:
    """
    Discover a next-page URL from HTML.
    """

    if not html:
        return None

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # Explicit rel="next".
    for link in soup.find_all(
        "a",
        href=True,
    ):
        rel = link.get("rel")

        if isinstance(rel, list):
            rel_values = [
                str(value).lower()
                for value in rel
            ]
        else:
            rel_values = str(
                rel or ""
            ).lower().split()

        if "next" in rel_values:
            return urljoin(
                current_url,
                str(link.get("href")),
            )

    # Common next-page selectors.
    selectors = [
        "a.next",
        "a.next-page",
        ".next a",
        ".next-page a",
        "[aria-label='Next']",
        "[aria-label='Next page']",
        "[title='Next']",
        "[title='Next page']",
    ]

    for selector in selectors:
        link = soup.select_one(
            selector
        )

        if link is None:
            continue

        href = link.get("href")

        if href:
            return urljoin(
                current_url,
                str(href),
            )

    # Common next-page link text.
    next_texts = {
        "next",
        "next page",
        "older",
        "older posts",
        "›",
    }

    for link in soup.find_all(
        "a",
        href=True,
    ):
        text = link.get_text(
            " ",
            strip=True,
        ).lower()

        if text in next_texts:
            return urljoin(
                current_url,
                str(link.get("href")),
            )

    return None


def _is_retryable_fetch_error(
    exc: Exception,
) -> bool:
    """
    Determine whether a fetch failure is transient.
    """

    return isinstance(
        exc,
        (
            TimeoutError,
            ConnectionError,
        ),
    )


def _fetch_with_retry(
    fetch_fn: Callable[..., Any],
    url: str,
    max_retries: int = 2,
) -> tuple[bool, Any, Exception | None]:
    """
    Execute bounded fetch retries.

    max_retries represents retries after the initial attempt.

    Example:
        max_retries=2
        -> maximum 3 total attempts.
    """

    attempts = 0

    while True:
        attempts += 1

        try:
            return (
                True,
                fetch_fn(url),
                None,
            )

        except Exception as exc:
            if not _is_retryable_fetch_error(
                exc
            ):
                return (
                    False,
                    None,
                    exc,
                )

            if attempts > max_retries:
                return (
                    False,
                    None,
                    exc,
                )


def _get_current_page_number(
    current_url: str,
    config: PaginationConfig,
) -> int:
    """
    Determine the current page number.

    Missing or invalid values default to page 1.
    """

    parts = urlsplit(
        current_url
    )

    query = parse_qs(
        parts.query,
        keep_blank_values=True,
    )

    values = query.get(
        config.parameter
    )

    if not values:
        return 1

    try:
        page_number = int(
            values[0]
        )
    except (
        TypeError,
        ValueError,
    ):
        return 1

    return max(
        page_number,
        1,
    )


def _get_next_url(
    html: str,
    current_url: str,
    config: PaginationConfig,
    current_page_number: int,
) -> tuple[str | None, str]:
    """
    Resolve the next page according to the configured strategy.

    Returns:
        (next_url, stop_reason)
    """

    strategy = config.strategy

    if strategy == PaginationStrategy.NONE:
        return (
            None,
            "no_pagination",
        )

    if strategy == PaginationStrategy.NEXT_LINK:
        next_url = _find_next_url(
            html,
            current_url,
        )

        if not next_url:
            return (
                None,
                "no_next_page",
            )

        return (
            next_url,
            "",
        )

    if strategy == PaginationStrategy.URL:
        next_page_number = (
            current_page_number + 1
        )

        next_url = build_next_url(
            current_url,
            config,
            next_page_number,
        )

        if next_url == current_url:
            return (
                None,
                "duplicate_url",
            )

        return (
            next_url,
            "",
        )

    if strategy == PaginationStrategy.LOAD_MORE:
        return (
            None,
            "browser_required",
        )

    if strategy == PaginationStrategy.INFINITE_SCROLL:
        return (
            None,
            "browser_required",
        )

    return (
        None,
        "unsupported_pagination_strategy",
    )


def _normalize_html(
    value: Any,
) -> str | None:
    """
    Normalize supported fetch response shapes to HTML text.
    """

    if value is None:
        return None

    if isinstance(
        value,
        str,
    ):
        return value

    if hasattr(
        value,
        "html",
    ):
        html = value.html

        if html is None:
            return None

        return str(html)

    if hasattr(
        value,
        "text",
    ):
        text = value.text

        if text is None:
            return None

        return str(text)

    return str(value)


def crawl(
    start_url: str,
    plan: ExtractionPlan,
    fetch_fn: Callable[..., Any],
    execute_fn: Callable[..., Any],
    config: PaginationConfig | None = None,
    rate_limit_seconds: float | None = None,
    max_retries: int = 2,
) -> CrawlResult:
    """
    Crawl paginated pages and extract structured records.

    Reliability guarantees:
    - bounded transient fetch retries
    - permanent fetch failures are not retried
    - retry exhaustion stops safely
    - extraction failures do not escape the crawler
    - duplicate URLs are prevented
    - page limits are enforced
    - record limits are enforced
    - rate limiting is applied between page requests
    - all results remain serializable
    """

    # ---------------------------------------------------------------
    # Input validation
    # ---------------------------------------------------------------

    if not start_url:
        raise ValueError(
            "start_url must not be empty"
        )

    if max_retries < 0:
        raise ValueError(
            "max_retries must not be negative"
        )

    if rate_limit_seconds is not None:
        if rate_limit_seconds < 0:
            raise ValueError(
                "rate_limit_seconds must not be negative"
            )

    # ---------------------------------------------------------------
    # Pagination configuration
    # ---------------------------------------------------------------

    if config is None:
        config = PaginationConfig(
            strategy=PaginationStrategy.NEXT_LINK
        )

    max_pages = getattr(
        config,
        "max_pages",
        10,
    )

    max_records = getattr(
        config,
        "max_records",
        1000,
    )

    if max_pages is None:
        max_pages = 10

    if max_records is None:
        max_records = 1000

    if max_pages <= 0:
        raise ValueError(
            "max_pages must be greater than zero"
        )

    if max_records <= 0:
        raise ValueError(
            "max_records must be greater than zero"
        )

    # ---------------------------------------------------------------
    # Rate-limit configuration
    # ---------------------------------------------------------------

    if rate_limit_seconds is None:
        rate_limit_seconds = getattr(
            config,
            "rate_limit_seconds",
            0,
        )

    if rate_limit_seconds is None:
        rate_limit_seconds = 0

    if rate_limit_seconds < 0:
        raise ValueError(
            "rate_limit_seconds must not be negative"
        )

    # ---------------------------------------------------------------
    # Crawl state
    # ---------------------------------------------------------------

    records: list[dict[str, Any]] = []

    urls_crawled: list[str] = []

    visited_urls: set[str] = set()

    current_url = start_url

    current_page_number = _get_current_page_number(
        current_url,
        config,
    )

    stopped_reason = ""

    # ---------------------------------------------------------------
    # Main crawl loop
    # ---------------------------------------------------------------

    while current_url:

        # -----------------------------------------------------------
        # Duplicate protection
        # -----------------------------------------------------------

        if current_url in visited_urls:
            stopped_reason = "duplicate_url"
            break

        # -----------------------------------------------------------
        # Page limit
        # -----------------------------------------------------------

        if len(urls_crawled) >= max_pages:
            stopped_reason = "max_pages"
            break

        # -----------------------------------------------------------
        # Record limit
        # -----------------------------------------------------------

        if len(records) >= max_records:
            stopped_reason = "max_records"
            break

        # -----------------------------------------------------------
        # Rate limiting
        #
        # Do not delay the first request.
        # Delay only between pages.
        # -----------------------------------------------------------

        if urls_crawled and rate_limit_seconds > 0:
            time.sleep(
                rate_limit_seconds
            )

        # -----------------------------------------------------------
        # Register URL before fetching.
        #
        # This preserves crawl state even when fetching fails.
        # -----------------------------------------------------------

        visited_urls.add(
            current_url
        )

        urls_crawled.append(
            current_url
        )

        # -----------------------------------------------------------
        # Fetch with bounded retries
        # -----------------------------------------------------------

        (
            fetch_success,
            fetched,
            fetch_error,
        ) = _fetch_with_retry(
            fetch_fn,
            current_url,
            max_retries=max_retries,
        )

        if not fetch_success:
            stopped_reason = "fetch_error"
            break

        html = _normalize_html(
            fetched
        )

        if html is None:
            stopped_reason = "fetch_error"
            break

        # -----------------------------------------------------------
        # Extraction
        # -----------------------------------------------------------

        try:
            extraction_result = execute_fn(
                html,
                plan,
                current_url,
            )

        except Exception:
            stopped_reason = "extraction_error"
            break

        page_records = _get_records(
            extraction_result
        )

        # -----------------------------------------------------------
        # Respect record limit exactly
        # -----------------------------------------------------------

        remaining_records = (
            max_records
            - len(records)
        )

        if remaining_records > 0:
            records.extend(
                page_records[
                    :remaining_records
                ]
            )

        # -----------------------------------------------------------
        # Record limit reached
        # -----------------------------------------------------------

        if len(records) >= max_records:
            stopped_reason = "max_records"
            break

        # -----------------------------------------------------------
        # Page limit reached
        # -----------------------------------------------------------

        if len(urls_crawled) >= max_pages:
            stopped_reason = "max_pages"
            break

        # -----------------------------------------------------------
        # Resolve pagination
        # -----------------------------------------------------------

        (
            next_url,
            pagination_stop_reason,
        ) = _get_next_url(
            html,
            current_url,
            config,
            current_page_number,
        )

        if pagination_stop_reason:
            stopped_reason = (
                pagination_stop_reason
            )
            break

        if not next_url:
            stopped_reason = "no_next_page"
            break

        # -----------------------------------------------------------
        # Duplicate next URL protection
        # -----------------------------------------------------------

        if next_url in visited_urls:
            stopped_reason = "duplicate_url"
            break

        current_url = next_url

        if config.strategy == PaginationStrategy.URL:
            current_page_number += 1

    return CrawlResult(
        records=records,
        pages_crawled=len(
            urls_crawled
        ),
        urls_crawled=urls_crawled,
        stopped_reason=stopped_reason,
    )


__all__ = [
    "CrawlResult",
    "crawl",
]
