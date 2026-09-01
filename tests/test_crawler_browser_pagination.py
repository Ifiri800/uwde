import sys
from pathlib import Path

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


class FakeBrowser:
    def __init__(self):
        self.calls = []

    def load_more(self, url):
        self.calls.append(("load_more", url))

        return {
            "url": url,
            "html": """
                <html>
                    <body>
                        <article>
                            <h2>Climate Specialist</h2>
                        </article>
                    </body>
                </html>
            """,
        }

    def infinite_scroll(self, url):
        self.calls.append(("infinite_scroll", url))

        return {
            "url": url,
            "html": """
                <html>
                    <body>
                        <article>
                            <h2>Environmental Analyst</h2>
                        </article>
                    </body>
                </html>
            """,
        }


def test_load_more_executes_browser_pagination():
    browser = FakeBrowser()

    def fetch(url):
        return """
            <html>
                <body>
                    <article>
                        <h2>Environmental Consultant</h2>
                    </article>
                    <button id="load-more">Load More</button>
                </body>
            </html>
        """

    def execute(html, plan, url):
        if "Climate Specialist" in html:
            return {
                "records": [
                    {"title": "Climate Specialist"}
                ]
            }

        return {
            "records": [
                {"title": "Environmental Consultant"}
            ]
        }

    config = PaginationConfig(
        strategy=PaginationStrategy.LOAD_MORE,
        max_pages=2,
        max_records=100,
    )

    result = crawl(
        "https://example.com/jobs",
        PLAN,
        fetch,
        execute,
        config,
        browser=browser,
    )

    assert result.pages_crawled == 2
    assert len(result.records) == 2
    assert result.stopped_reason == "no_next_page"
    assert browser.calls == [
        ("load_more", "https://example.com/jobs")
    ]


def test_infinite_scroll_executes_browser_pagination():
    browser = FakeBrowser()

    def fetch(url):
        return """
            <html>
                <body>
                    <article>
                        <h2>Environmental Consultant</h2>
                    </article>
                    <div data-infinite-scroll="true">
                        Results
                    </div>
                </body>
            </html>
        """

    def execute(html, plan, url):
        if "Environmental Analyst" in html:
            return {
                "records": [
                    {"title": "Environmental Analyst"}
                ]
            }

        return {
            "records": [
                {"title": "Environmental Consultant"}
            ]
        }

    config = PaginationConfig(
        strategy=PaginationStrategy.INFINITE_SCROLL,
        max_pages=2,
        max_records=100,
    )

    result = crawl(
        "https://example.com/jobs",
        PLAN,
        fetch,
        execute,
        config,
        browser=browser,
    )

    assert result.pages_crawled == 2
    assert len(result.records) == 2
    assert result.stopped_reason == "no_next_page"
    assert browser.calls == [
        ("infinite_scroll", "https://example.com/jobs")
    ]
