from __future__ import annotations

from dataclasses import asdict, dataclass

from backend.app.services.html_parser import ParsedPage, parse_html
from backend.app.services.http_fetcher import FetchError, fetch_url


@dataclass
class WebsiteAnalysis:
    url: str
    final_url: str
    status_code: int
    content_type: str
    title: str
    headings: list[str]
    paragraphs_count: int
    links_count: int
    images_count: int
    lists_count: int
    tables_count: int

    def to_dict(self) -> dict:
        return asdict(self)


def analyze_website(url: str) -> WebsiteAnalysis:
    """
    Fetch and analyze a website's statically available HTML.

    The request passes through the URL security layer and the secure
    HTTP fetcher before the HTML is parsed.
    """

    result = fetch_url(url)

    page: ParsedPage = parse_html(
        result.body,
        result.final_url,
    )

    return WebsiteAnalysis(
        url=result.url,
        final_url=result.final_url,
        status_code=result.status_code,
        content_type=result.content_type,
        title=page.title,
        headings=page.headings,
        paragraphs_count=len(page.paragraphs),
        links_count=len(page.links),
        images_count=len(page.images),
        lists_count=len(page.lists),
        tables_count=len(page.tables),
    )