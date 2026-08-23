from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable

from app.services.extraction_engine import ExtractionPlan
from app.services.extraction_executor import ExtractionResult
from app.services.pagination import (
    PaginationConfig,
    PaginationStrategy,
    detect_pagination,
)


@dataclass
class CrawlResult:
    records: list[dict] = field(default_factory=list)
    pages_crawled: int = 0
    urls_crawled: list[str] = field(default_factory=list)
    stopped_reason: str = "completed"

    def to_dict(self) -> dict:
        return {
            "records": self.records,
            "pages_crawled": self.pages_crawled,
            "urls_crawled": self.urls_crawled,
            "stopped_reason": self.stopped_reason,
        }


def crawl(
    start_url: str,
    plan: ExtractionPlan,
    fetch_page: Callable[[str], str],
    execute_page: Callable[
        [str, ExtractionPlan, str],
        ExtractionResult,
    ],
    pagination_config: PaginationConfig | None = None,
    rate_limit_seconds: float = 0.0,
) -> CrawlResult:
    """
    Crawl a sequence of pages and execute an extraction plan on each page.

    The crawler deliberately receives fetch_page and execute_page as
    dependencies. This keeps the orchestration layer independent from
    network and extraction implementation details and makes it easy to
    test safely.

    Security-sensitive URL validation remains the responsibility of the
    supplied fetch_page implementation.
    """

    if not start_url or not start_url.strip():
        raise ValueError("start_url cannot be empty.")

    if rate_limit_seconds < 0:
        raise ValueError("rate_limit_seconds cannot be negative.")

    config = pagination_config or PaginationConfig(
        strategy=PaginationStrategy.NEXT_LINK,
    )

    if config.max_pages <= 0:
        raise ValueError("max_pages must be greater than zero.")

    if config.max_records <= 0:
        raise ValueError("max_records must be greater than zero.")

    records: list[dict] = []
    urls_crawled: list[str] = []
    visited_urls: set[str] = set()

    current_url = start_url
    stopped_reason = "completed"

    while current_url:
        if len(urls_crawled) >= config.max_pages:
            stopped_reason = "max_pages"
            break

        if current_url in visited_urls:
            stopped_reason = "duplicate_url"
            break

        visited_urls.add(current_url)

        if rate_limit_seconds and urls_crawled:
            time.sleep(rate_limit_seconds)

        html = fetch_page(current_url)

        extraction_result = execute_page(
            html,
            plan,
            current_url,
        )

        remaining = config.max_records - len(records)

        if remaining <= 0:
            stopped_reason = "max_records"
            break

        records.extend(extraction_result.records[:remaining])
        urls_crawled.append(current_url)

        if len(records) >= config.max_records:
            stopped_reason = "max_records"
            break

        if config.strategy == PaginationStrategy.URL:
            next_page_number = len(urls_crawled) + 1

            from app.services.pagination import build_next_url

            next_url = build_next_url(
                current_url,
                config,
                next_page_number,
            )

        else:
            pagination = detect_pagination(
                html,
                current_url,
            )

            if pagination.strategy == PaginationStrategy.NEXT_LINK:
                next_url = pagination.next_url

            else:
                next_url = None

        if not next_url:
            stopped_reason = "no_next_page"
            break

        current_url = next_url

    return CrawlResult(
        records=records,
        pages_crawled=len(urls_crawled),
        urls_crawled=urls_crawled,
        stopped_reason=stopped_reason,
    )
