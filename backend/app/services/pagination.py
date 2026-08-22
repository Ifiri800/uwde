from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup


class PaginationStrategy(str, Enum):
    NONE = "none"
    NEXT_LINK = "next_link"
    URL = "url"
    LOAD_MORE = "load_more"
    INFINITE_SCROLL = "infinite_scroll"


@dataclass
class PaginationConfig:
    strategy: PaginationStrategy
    parameter: str = "page"
    max_pages: int = 10
    max_records: int = 1000

    def __post_init__(self) -> None:
        if self.max_pages <= 0:
            raise ValueError("max_pages must be greater than zero.")

        if self.max_records <= 0:
            raise ValueError("max_records must be greater than zero.")

        if not self.parameter.strip():
            raise ValueError("parameter cannot be empty.")


@dataclass
class PaginationDetection:
    strategy: PaginationStrategy
    next_url: Optional[str] = None


def build_next_url(
    current_url: str,
    config: PaginationConfig,
    page_number: int,
) -> str:
    if page_number <= 0:
        raise ValueError("page_number must be greater than zero.")

    if config.strategy != PaginationStrategy.URL:
        raise ValueError("build_next_url requires URL pagination strategy.")

    parts = urlsplit(current_url)
    query = parse_qs(parts.query, keep_blank_values=True)

    query[config.parameter] = [str(page_number)]

    new_query = urlencode(query, doseq=True)

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            new_query,
            parts.fragment,
        )
    )


def detect_pagination(
    html: str,
    current_url: str,
) -> PaginationDetection:
    if not html.strip():
        return PaginationDetection(PaginationStrategy.NONE)

    soup = BeautifulSoup(html, "html.parser")

    # 1. Explicit rel="next" link.
    next_link = soup.find(
        "a",
        attrs={"rel": lambda value: value and "next" in value},
    )

    if next_link and next_link.get("href"):
        from urllib.parse import urljoin

        return PaginationDetection(
            strategy=PaginationStrategy.NEXT_LINK,
            next_url=urljoin(current_url, next_link["href"]),
        )

    # 2. Load More controls.
    load_more = soup.find(
        lambda tag: (
            tag.name in {"button", "a"}
            and (
                "load-more" in str(tag.get("id", "")).lower()
                or "load more" in tag.get_text(" ", strip=True).lower()
                or "load_more" in str(tag.get("class", "")).lower()
            )
        )
    )

    if load_more:
        return PaginationDetection(
            strategy=PaginationStrategy.LOAD_MORE
        )

    # 3. Infinite-scroll indicators.
    infinite_scroll = soup.find(
        lambda tag: any(
            str(tag.get(attribute, "")).lower() in {
                "true",
                "1",
                "yes",
            }
            for attribute in (
                "data-infinite-scroll",
                "data-infinite-scroll-enabled",
            )
        )
    )

    if infinite_scroll:
        return PaginationDetection(
            strategy=PaginationStrategy.INFINITE_SCROLL
        )

    # 4. No pagination detected.
    return PaginationDetection(
        strategy=PaginationStrategy.NONE,
    )
