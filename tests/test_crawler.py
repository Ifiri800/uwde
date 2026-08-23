import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.services.crawler import crawl
from app.services.extraction_engine import build_extraction_plan
from app.services.extraction_executor import execute_extraction
from app.services.pagination import PaginationConfig, PaginationStrategy


PAGES = {
    "https://example.com/jobs?page=1": """
        <html>
            <body>
                <article class="job">
                    <h2 class="title">Environmental Consultant</h2>
                    <div class="company">Eco Consulting Ltd</div>
                    <div class="location">Lagos</div>
                    <a class="apply" href="/apply/1">Apply</a>
                </article>

                <a rel="next" href="/jobs?page=2">Next</a>
            </body>
        </html>
    """,
    "https://example.com/jobs?page=2": """
        <html>
            <body>
                <article class="job">
                    <h2 class="title">Climate Specialist</h2>
                    <div class="company">Climate Africa</div>
                    <div class="location">Abuja</div>
                    <a class="apply" href="/apply/2">Apply</a>
                </article>
            </body>
        </html>
    """,
}


def fake_fetch(url):
    return PAGES[url]


def fake_execute(html, plan, url):
    return execute_extraction(
        html,
        plan,
        url,
    )


def test_crawls_multiple_pages():
    plan = build_extraction_plan(
        "Extract the job title, company, location, and application URL."
    )

    result = crawl(
        "https://example.com/jobs?page=1",
        plan,
        fake_fetch,
        fake_execute,
    )

    assert result.pages_crawled == 2
    assert len(result.records) == 2
    assert result.urls_crawled == [
        "https://example.com/jobs?page=1",
        "https://example.com/jobs?page=2",
    ]


def test_stops_at_max_pages():
    plan = build_extraction_plan(
        "Extract the job title."
    )

    config = PaginationConfig(
        strategy=PaginationStrategy.NEXT_LINK,
        max_pages=1,
        max_records=100,
    )

    result = crawl(
        "https://example.com/jobs?page=1",
        plan,
        fake_fetch,
        fake_execute,
        config,
    )

    assert result.pages_crawled == 1
    assert result.stopped_reason == "max_pages"


def test_stops_at_max_records():
    plan = build_extraction_plan(
        "Extract the job title."
    )

    config = PaginationConfig(
        strategy=PaginationStrategy.NEXT_LINK,
        max_pages=10,
        max_records=1,
    )

    result = crawl(
        "https://example.com/jobs?page=1",
        plan,
        fake_fetch,
        fake_execute,
        config,
    )

    assert len(result.records) == 1
    assert result.stopped_reason == "max_records"


def test_prevents_duplicate_urls():
    plan = build_extraction_plan(
        "Extract the job title."
    )

    pages = {
        "https://example.com/jobs?page=1": """
            <article>
                <h2>Environmental Consultant</h2>
                <a rel="next" href="/jobs?page=1">Next</a>
            </article>
        """
    }

    def fetch(url):
        return pages[url]

    result = crawl(
        "https://example.com/jobs?page=1",
        plan,
        fetch,
        fake_execute,
    )

    assert result.pages_crawled == 1
    assert result.stopped_reason == "duplicate_url"


def test_returns_serializable_result():
    plan = build_extraction_plan(
        "Extract the job title."
    )

    result = crawl(
        "https://example.com/jobs?page=1",
        plan,
        fake_fetch,
        fake_execute,
    )

    data = result.to_dict()

    assert data["pages_crawled"] == 2
    assert len(data["records"]) == 2
    assert len(data["urls_crawled"]) == 2


def test_rejects_empty_start_url():
    plan = build_extraction_plan(
        "Extract the job title."
    )

    try:
        crawl(
            "",
            plan,
            fake_fetch,
            fake_execute,
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_rejects_negative_rate_limit():
    plan = build_extraction_plan(
        "Extract the job title."
    )

    try:
        crawl(
            "https://example.com/jobs?page=1",
            plan,
            fake_fetch,
            fake_execute,
            rate_limit_seconds=-1,
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass
