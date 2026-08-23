from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from backend.app.services.extraction_engine import ExtractionPlan


@dataclass
class ExtractionResult:
    records: list[dict[str, Any]]

    def model_dump(self) -> dict[str, Any]:
        return {"records": self.records}


def _clean_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(value.split())


def _extract_field(
    element,
    field_name: str,
    base_url: str,
) -> str:
    aliases = {
        "title": [
            "h1",
            "h2",
            "h3",
            ".job-title",
            ".title",
            "[data-testid='job-title']",
        ],
        "company": [
            ".company",
            ".company-name",
            "[data-testid='company']",
        ],
        "location": [
            ".location",
            ".job-location",
            "[data-testid='location']",
        ],
        "salary": [
            ".salary",
            ".compensation",
            "[data-testid='salary']",
        ],
        "description": [
            ".description",
            ".job-description",
            "[data-testid='description']",
        ],
        "posted_date": [
            "time",
            ".posted-date",
            ".date",
            "[data-testid='posted-date']",
        ],
        "application_url": [
            "a[href*='apply']",
            "a.apply",
            ".apply a",
            "a[href]",
        ],
    }

    selectors = aliases.get(field_name, [f".{field_name}"])

    for selector in selectors:
        match = element.select_one(selector)

        if not match:
            continue

        if field_name == "application_url":
            href = match.get("href")
            if href:
                return urljoin(base_url, href)

        text = _clean_text(match.get_text(" ", strip=True))

        if text:
            return text

    return ""


def _find_record_elements(soup: BeautifulSoup):
    selectors = [
        "article",
        ".job",
        ".job-card",
        ".job-listing",
        "[data-testid='job']",
        "[data-testid='job-card']",
    ]

    for selector in selectors:
        elements = soup.select(selector)

        if elements:
            return elements

    return [soup]


def execute_extraction(
    html: str,
    plan: ExtractionPlan,
    base_url: str = "",
) -> ExtractionResult:
    if not html:
        return ExtractionResult(records=[])

    soup = BeautifulSoup(html, "html.parser")
    record_elements = _find_record_elements(soup)

    records: list[dict[str, Any]] = []

    for element in record_elements:
        record: dict[str, Any] = {}

        for field in plan.fields:
            value = _extract_field(
                element,
                field.name,
                base_url,
            )

            if value:
                record[field.name] = value

        if record:
            records.append(record)

    return ExtractionResult(records=records)
