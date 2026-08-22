from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urljoin

from bs4 import BeautifulSoup


@dataclass
class ParsedLink:
    text: str
    url: str


@dataclass
class ParsedImage:
    alt: str
    url: str


@dataclass
class ParsedPage:
    url: str
    title: str
    headings: list[str] = field(default_factory=list)
    paragraphs: list[str] = field(default_factory=list)
    links: list[ParsedLink] = field(default_factory=list)
    images: list[ParsedImage] = field(default_factory=list)
    lists: list[list[str]] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)


def _clean_text(value: str) -> str:
    """Normalize whitespace in extracted text."""
    return " ".join(value.split())


def parse_html(html: bytes | str, url: str) -> ParsedPage:
    """
    Parse an HTML document into a structured representation.

    The parser is intentionally deterministic. It does not execute
    JavaScript and therefore should be used for statically available HTML.
    """

    soup = BeautifulSoup(html, "html.parser")

    title_tag = soup.find("title")
    title = _clean_text(title_tag.get_text(" ", strip=True)) if title_tag else ""

    headings: list[str] = []

    for tag in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        text = _clean_text(tag.get_text(" ", strip=True))

        if text:
            headings.append(text)

    paragraphs: list[str] = []

    for tag in soup.find_all("p"):
        text = _clean_text(tag.get_text(" ", strip=True))

        if text:
            paragraphs.append(text)

    links: list[ParsedLink] = []

    for tag in soup.find_all("a", href=True):
        href = tag.get("href")

        if not isinstance(href, str) or not href.strip():
            continue

        text = _clean_text(tag.get_text(" ", strip=True))
        absolute_url = urljoin(url, href)

        links.append(
            ParsedLink(
                text=text,
                url=absolute_url,
            )
        )

    images: list[ParsedImage] = []

    for tag in soup.find_all("img", src=True):
        src = tag.get("src")

        if not isinstance(src, str) or not src.strip():
            continue

        alt = _clean_text(tag.get("alt", ""))
        absolute_url = urljoin(url, src)

        images.append(
            ParsedImage(
                alt=alt,
                url=absolute_url,
            )
        )

    lists: list[list[str]] = []

    for list_tag in soup.find_all(["ul", "ol"]):
        items: list[str] = []

        for item in list_tag.find_all("li", recursive=False):
            text = _clean_text(item.get_text(" ", strip=True))

            if text:
                items.append(text)

        if items:
            lists.append(items)

    tables: list[list[list[str]]] = []

    for table in soup.find_all("table"):
        rows: list[list[str]] = []

        for row in table.find_all("tr"):
            cells: list[str] = []

            for cell in row.find_all(["th", "td"]):
                text = _clean_text(cell.get_text(" ", strip=True))
                cells.append(text)

            if cells:
                rows.append(cells)

        if rows:
            tables.append(rows)

    return ParsedPage(
        url=url,
        title=title,
        headings=headings,
        paragraphs=paragraphs,
        links=links,
        images=images,
        lists=lists,
        tables=tables,
    )