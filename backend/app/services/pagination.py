from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit, urlunsplit

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
    rate_limit_seconds: float = 0

    def __post_init__(self) -> None:
        if self.max_pages <= 0:
            raise ValueError(
                "max_pages must be greater than zero."
            )

        if self.max_records <= 0:
            raise ValueError(
                "max_records must be greater than zero."
            )

        if not self.parameter.strip():
            raise ValueError(
                "parameter cannot be empty."
            )

        if self.rate_limit_seconds < 0:
            raise ValueError(
                "rate_limit_seconds must not be negative."
            )


@dataclass
class PaginationDetection:
    strategy: PaginationStrategy
    next_url: Optional[str] = None


def build_next_url(
    current_url: str,
    config: PaginationConfig,
    page_number: int,
) -> str:
    """
    Build the URL for a specific page while preserving
    existing query parameters and URL fragments.
    """

    if page_number <= 0:
        raise ValueError(
            "page_number must be greater than zero."
        )

    if config.strategy != PaginationStrategy.URL:
        raise ValueError(
            "build_next_url requires URL pagination strategy."
        )

    parts = urlsplit(current_url)

    query = parse_qs(
        parts.query,
        keep_blank_values=True,
    )

    query[config.parameter] = [
        str(page_number)
    ]

    new_query = urlencode(
        query,
        doseq=True,
    )

    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            parts.path,
            new_query,
            parts.fragment,
        )
    )


def _has_next_rel(value: object) -> bool:
    """
    Safely detect rel="next" regardless of whether BeautifulSoup
    returns a list or string.
    """

    if isinstance(value, list):
        return any(
            str(item).strip().lower() == "next"
            for item in value
        )

    return "next" in str(
        value or ""
    ).lower().split()


def _detect_load_more(
    soup: BeautifulSoup,
) -> bool:
    for tag in soup.find_all(
        ["button", "a"]
    ):
        element_id = str(
            tag.get("id", "")
        ).lower()

        classes = " ".join(
            str(value).lower()
            for value in tag.get(
                "class",
                [],
            )
        )

        text = tag.get_text(
            " ",
            strip=True,
        ).lower()

        if "load-more" in element_id:
            return True

        if "load_more" in classes:
            return True

        if "load-more" in classes:
            return True

        if text in {
            "load more",
            "load more results",
            "show more",
        }:
            return True

    return False


def _detect_infinite_scroll(
    soup: BeautifulSoup,
) -> bool:
    attributes = (
        "data-infinite-scroll",
        "data-infinite-scroll-enabled",
    )

    valid_values = {
        "true",
        "1",
        "yes",
    }

    for tag in soup.find_all():
        for attribute in attributes:
            value = str(
                tag.get(
                    attribute,
                    "",
                )
            ).strip().lower()

            if value in valid_values:
                return True

    return False


def detect_pagination(
    html: str,
    current_url: str,
) -> PaginationDetection:
    """
    Detect the strongest statically observable pagination mechanism.

    Detection priority:

        rel="next"
            ↓
        load more
            ↓
        infinite scroll
            ↓
        none
    """

    if not html or not html.strip():
        return PaginationDetection(
            PaginationStrategy.NONE
        )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # ---------------------------------------------------------------
    # 1. Explicit rel="next"
    # ---------------------------------------------------------------

    next_link = soup.find(
        "a",
        attrs={
            "rel": _has_next_rel
        },
    )

    if (
        next_link is not None
        and next_link.get("href")
    ):
        return PaginationDetection(
            strategy=PaginationStrategy.NEXT_LINK,
            next_url=urljoin(
                current_url,
                str(
                    next_link.get("href")
                ),
            ),
        )

    # ---------------------------------------------------------------
    # 2. Common next-page selectors
    # ---------------------------------------------------------------

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
            return PaginationDetection(
                strategy=PaginationStrategy.NEXT_LINK,
                next_url=urljoin(
                    current_url,
                    str(href),
                ),
            )

    # ---------------------------------------------------------------
    # 3. Common next-page text
    # ---------------------------------------------------------------

    next_texts = {
        "next",
        "next page",
        "older",
        "older posts",
        "›",
        "»",
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
            return PaginationDetection(
                strategy=PaginationStrategy.NEXT_LINK,
                next_url=urljoin(
                    current_url,
                    str(
                        link.get("href")
                    ),
                ),
            )

    # ---------------------------------------------------------------
    # 4. Load More
    # ---------------------------------------------------------------

    if _detect_load_more(soup):
        return PaginationDetection(
            strategy=PaginationStrategy.LOAD_MORE
        )

    # ---------------------------------------------------------------
    # 5. Infinite scroll
    # ---------------------------------------------------------------

    if _detect_infinite_scroll(soup):
        return PaginationDetection(
            strategy=PaginationStrategy.INFINITE_SCROLL
        )

    # ---------------------------------------------------------------
    # 6. No pagination
    # ---------------------------------------------------------------

    return PaginationDetection(
        strategy=PaginationStrategy.NONE
    )


__all__ = [
    "PaginationStrategy",
    "PaginationConfig",
    "PaginationDetection",
    "build_next_url",
    "detect_pagination",
]
