from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.services.extraction_engine import ExtractionPlan
from app.services.pagination import (
    PaginationConfig,
    PaginationStrategy,
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


def _get_records(extraction_result: Any) -> list[dict[str, Any]]:
    """
    Convert an extraction result into a list of dictionaries.

    Supports:
    - ExtractionResult
    - dictionaries containing "records"
    - direct lists
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

    if isinstance(extraction_result, dict):
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

    if isinstance(extraction_result, list):
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
    Find the next page URL.
    """

    if not html:
        return None

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # rel="next"
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

    # Common selectors
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
        link = soup.select_one(selector)

        if link is None:
            continue

        href = link.get("href")

        if href:
            return urljoin(
                current_url,
                str(href),
            )

    # Common next-page text
    next_texts = {
        "next",
        "next page",
        "older",
        "older posts",
        "›",
        "next",
        "?",
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


def _is_retryable_fetch_error(exc: Exception) -> bool:
    """
    Determine whether a fetch exception is transient.

    Retryable:
    - TimeoutError
    - ConnectionError

    Permanent/unclassified errors are not retried.
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
    Fetch a URL with bounded retries.

    max_retries means retries AFTER the initial request.

    Therefore:
        max_retries=2
        -> maximum 3 total attempts
    """

    attempts = 0

    while True:
        attempts += 1

        try:
            return True, fetch_fn(url), None

        except Exception as exc:
            if not _is_retryable_fetch_error(exc):
                return False, None, exc

            if attempts > max_retries:
                return False, None, exc


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
    Crawl pages and extract records.

    Reliability guarantees:
    - transient fetch errors are retried
    - permanent fetch errors are not retried
    - retry exhaustion does not crash the crawl
    - extraction errors are isolated
    - page and record limits are preserved
    """

    # ---------------------------------------------------------------
    # Validate URL
    # ---------------------------------------------------------------

    if not start_url:
        raise ValueError(
            "start_url must not be empty"
        )

    # ---------------------------------------------------------------
    # Validate retry configuration
    # ---------------------------------------------------------------

    if max_retries < 0:
        raise ValueError(
            "max_retries must not be negative"
        )

    # ---------------------------------------------------------------
    # Validate rate limit
    # ---------------------------------------------------------------

    if rate_limit_seconds is not None:
        if rate_limit_seconds < 0:
            raise ValueError(
                "rate_limit_seconds must not be negative"
            )

    # ---------------------------------------------------------------
    # Default configuration
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

    # If no explicit rate limit was supplied, use the config value.
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

    stopped_reason = ""

    # ---------------------------------------------------------------
    # Main loop
    # ---------------------------------------------------------------

    while current_url:

        # -----------------------------------------------------------
        # Duplicate URL protection
        # -----------------------------------------------------------

        if current_url in visited_urls:
            stopped_reason = "duplicate_url"
            break

        # -----------------------------------------------------------
        # Maximum page protection
        # -----------------------------------------------------------

        if len(urls_crawled) >= max_pages:
            stopped_reason = "max_pages"
            break

        # -----------------------------------------------------------
        # Maximum record protection
        # -----------------------------------------------------------

        if len(records) >= max_records:
            stopped_reason = "max_records"
            break

        # -----------------------------------------------------------
        # Register page BEFORE fetching.
        #
        # This preserves crawler state even when fetch fails.
        # -----------------------------------------------------------

        visited_urls.add(current_url)
        urls_crawled.append(current_url)

        # -----------------------------------------------------------
        # Fetch with bounded retry policy
        # -----------------------------------------------------------

        fetch_success, html, fetch_error = _fetch_with_retry(
            fetch_fn,
            current_url,
            max_retries=max_retries,
        )

        if not fetch_success:
            stopped_reason = "fetch_error"
            break

        if html is None:
            stopped_reason = "fetch_error"
            break

        # -----------------------------------------------------------
        # Normalize fetch result.
        # -----------------------------------------------------------

        if not isinstance(
            html,
            str,
        ):
            if hasattr(
                html,
                "html",
            ):
                html = html.html

            elif hasattr(
                html,
                "text",
            ):
                html = html.text

            else:
                html = str(html)

        # -----------------------------------------------------------
        # Execute extraction.
        #
        # Extraction failures must not escape the crawler.
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
        # Add extracted records.
        #
        # Respect max_records exactly.
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
        # Stop when record limit is reached.
        # -----------------------------------------------------------

        if len(records) >= max_records:
            stopped_reason = "max_records"
            break

        # -----------------------------------------------------------
        # Stop when maximum page count has been reached.
        # -----------------------------------------------------------

        if len(urls_crawled) >= max_pages:
            stopped_reason = "max_pages"
            break

        # -----------------------------------------------------------
        # Pagination strategy.
        # -----------------------------------------------------------

        strategy = getattr(
            config,
            "strategy",
            PaginationStrategy.NEXT_LINK,
        )

        if strategy != PaginationStrategy.NEXT_LINK:
            pass

        next_url = _find_next_url(
            html,
            current_url,
        )

        # -----------------------------------------------------------
        # No next page
        # -----------------------------------------------------------

        if not next_url:
            stopped_reason = "no_next_page"
            break

        # -----------------------------------------------------------
        # Duplicate next page
        # -----------------------------------------------------------

        if next_url in visited_urls:
            stopped_reason = "duplicate_url"
            break

        current_url = next_url

    return CrawlResult(
        records=records,
        pages_crawled=len(urls_crawled),
        urls_crawled=urls_crawled,
        stopped_reason=stopped_reason,
    )


__all__ = [
    "CrawlResult",
    "crawl",
]


