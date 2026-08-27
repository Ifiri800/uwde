import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "backend"),
)

from app.services.crawler import crawl
from app.services.extraction_engine import build_extraction_plan
from app.services.pagination import (
    PaginationConfig,
    PaginationStrategy,
)


PLAN = build_extraction_plan(
    "Extract the job title."
)


def test_retries_transient_fetch_failure():
    attempts = []

    def fetch(url):
        attempts.append(url)

        if len(attempts) < 3:
            raise TimeoutError("temporary timeout")

        return """
            <article>
                <h2>Environmental Consultant</h2>
            </article>
        """

    def execute(html, plan, url):
        return {
            "records": [
                {
                    "title": "Environmental Consultant",
                }
            ]
        }

    result = crawl(
        "https://example.com/jobs",
        PLAN,
        fetch,
        execute,
    )

    assert len(attempts) == 3
    assert len(result.records) == 1


def test_does_not_retry_permanent_failure():
    attempts = []

    def fetch(url):
        attempts.append(url)
        raise ValueError("permanent failure")

    def execute(html, plan, url):
        return {"records": []}

    result = crawl(
        "https://example.com/jobs",
        PLAN,
        fetch,
        execute,
    )

    assert len(attempts) == 1
    assert result.stopped_reason == "fetch_error"


def test_retry_exhaustion_stops_crawl():
    attempts = []

    def fetch(url):
        attempts.append(url)
        raise TimeoutError("persistent timeout")

    def execute(html, plan, url):
        return {"records": []}

    result = crawl(
        "https://example.com/jobs",
        PLAN,
        fetch,
        execute,
    )

    assert len(attempts) >= 1
    assert result.stopped_reason == "fetch_error"


def test_extraction_failure_is_isolated():
    def fetch(url):
        return "<html></html>"

    def execute(html, plan, url):
        raise TimeoutError("extraction timeout")

    result = crawl(
        "https://example.com/jobs",
        PLAN,
        fetch,
        execute,
    )

    assert result.pages_crawled == 1
    assert result.stopped_reason == "extraction_error"


def test_crawler_preserves_max_pages_under_failure():
    calls = []

    pages = {
        "https://example.com/jobs?page=1": """
            <a rel="next" href="/jobs?page=2">Next</a>
        """,
        "https://example.com/jobs?page=2": """
            <a rel="next" href="/jobs?page=3">Next</a>
        """,
        "https://example.com/jobs?page=3": """
            <article><h2>Third</h2></article>
        """,
    }

    def fetch(url):
        calls.append(url)
        return pages[url]

    def execute(html, plan, url):
        return {"records": []}

    config = PaginationConfig(
        strategy=PaginationStrategy.NEXT_LINK,
        max_pages=2,
        max_records=100,
    )

    result = crawl(
        "https://example.com/jobs?page=1",
        PLAN,
        fetch,
        execute,
        config,
    )

    assert result.pages_crawled == 2
    assert len(calls) == 2
    assert result.stopped_reason == "max_pages"


def test_crawler_never_exceeds_record_limit_after_retries():
    def fetch(url):
        return """
            <article>
                <h2>Environmental Consultant</h2>
            </article>
        """

    def execute(html, plan, url):
        return {
            "records": [
                {"title": "A"},
                {"title": "B"},
                {"title": "C"},
            ]
        }

    config = PaginationConfig(
        strategy=PaginationStrategy.NEXT_LINK,
        max_pages=10,
        max_records=2,
    )

    result = crawl(
        "https://example.com/jobs",
        PLAN,
        fetch,
        execute,
        config,
    )

    assert len(result.records) == 2
    assert result.stopped_reason == "max_records"


def test_crawler_handles_fetch_exception_without_corrupting_state():
    def fetch(url):
        raise ConnectionError("connection reset")

    def execute(html, plan, url):
        return {"records": []}

    result = crawl(
        "https://example.com/jobs",
        PLAN,
        fetch,
        execute,
    )

    assert result.pages_crawled == 1
    assert result.urls_crawled == [
        "https://example.com/jobs"
    ]
    assert result.records == []


def test_crawler_result_remains_serializable_after_failure():
    def fetch(url):
        raise TimeoutError("timeout")

    def execute(html, plan, url):
        return {"records": []}

    result = crawl(
        "https://example.com/jobs",
        PLAN,
        fetch,
        execute,
    )

    data = result.to_dict()

    assert isinstance(data, dict)
    assert isinstance(data["records"], list)
    assert isinstance(data["urls_crawled"], list)
    assert data["pages_crawled"] == 1


def test_invalid_max_pages_is_rejected():
    with pytest.raises(ValueError):
        PaginationConfig(
            strategy=PaginationStrategy.NEXT_LINK,
            max_pages=0,
            max_records=100,
        )


def test_invalid_max_records_is_rejected():
    with pytest.raises(ValueError):
        PaginationConfig(
            strategy=PaginationStrategy.NEXT_LINK,
            max_pages=10,
            max_records=0,
        )
