from __future__ import annotations

import json
import re
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


# ---------------------------------------------------------------------------
# Basic utilities
# ---------------------------------------------------------------------------

def _clean_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(value.split())


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = _clean_text(value)

        if not cleaned:
            continue

        key = cleaned.lower()

        if key in seen:
            continue

        seen.add(key)
        result.append(cleaned)

    return result


def _first_text(element, selectors: list[str]) -> str:
    for selector in selectors:
        match = element.select_one(selector)

        if not match:
            continue

        text = _clean_text(
            match.get_text(" ", strip=True)
        )

        if text:
            return text

    return ""


# ---------------------------------------------------------------------------
# JSON-LD
# ---------------------------------------------------------------------------

def _extract_json_ld(
    soup: BeautifulSoup,
) -> list[dict[str, Any]]:
    documents: list[dict[str, Any]] = []

    for script in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    ):
        raw = script.string or script.get_text()

        if not raw:
            continue

        try:
            data = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue

        if isinstance(data, dict):
            documents.append(data)

        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    documents.append(item)

    return documents


# ---------------------------------------------------------------------------
# Coordinates
# ---------------------------------------------------------------------------

def _extract_coordinates_from_text(
    text: str,
) -> tuple[str, str]:
    pattern = re.compile(
        r"(?<![\d.-])"
        r"(-?(?:90(?:\.0+)?|"
        r"[0-8]?\d(?:\.\d+)?))"
        r"\s*[,;]\s*"
        r"(-?(?:180(?:\.0+)?|"
        r"(?:1[0-7]\d|[1-9]?\d)(?:\.\d+)?))"
        r"(?![\d.-])"
    )

    match = pattern.search(text)

    if not match:
        return "", ""

    return match.group(1), match.group(2)


def _extract_coordinate_fields(
    soup: BeautifulSoup,
) -> tuple[str, str, str]:

    latitude = ""
    longitude = ""

    # JSON-LD / Schema.org
    for document in _extract_json_ld(soup):

        geo = document.get("geo")

        candidates = [document]

        if isinstance(geo, dict):
            candidates.append(geo)

        for candidate in candidates:

            lat = candidate.get("latitude")
            lon = candidate.get("longitude")

            if lat is not None and not latitude:
                latitude = str(lat)

            if lon is not None and not longitude:
                longitude = str(lon)

    # Meta tags
    if not latitude:
        for selector in [
            "meta[name='latitude']",
            "meta[property='latitude']",
            "meta[name='geo.position']",
            "meta[property='place:location:latitude']",
        ]:
            element = soup.select_one(selector)

            if element and element.get("content"):
                latitude = str(element.get("content")).split(";")[0]
                break

    if not longitude:
        for selector in [
            "meta[name='longitude']",
            "meta[property='longitude']",
            "meta[name='geo.position']",
            "meta[property='place:location:longitude']",
        ]:
            element = soup.select_one(selector)

            if element and element.get("content"):
                content = str(element.get("content"))

                if ";" in content:
                    parts = content.split(";")

                    if len(parts) > 1:
                        longitude = parts[1]

                else:
                    longitude = content

                break

    # HTML data attributes
    if not latitude:
        element = soup.select_one(
            "[data-latitude], [data-lat]"
        )

        if element:
            latitude = str(
                element.get("data-latitude")
                or element.get("data-lat")
                or ""
            )

    if not longitude:
        element = soup.select_one(
            "[data-longitude], [data-lng], [data-lon]"
        )

        if element:
            longitude = str(
                element.get("data-longitude")
                or element.get("data-lng")
                or element.get("data-lon")
                or ""
            )

    # Page text
    if not latitude or not longitude:
        text = soup.get_text(
            " ",
            strip=True,
        )

        text_lat, text_lon = _extract_coordinates_from_text(text)

        if not latitude:
            latitude = text_lat

        if not longitude:
            longitude = text_lon

    coordinates = ""

    if latitude and longitude:
        coordinates = f"{latitude}, {longitude}"

    return (
        _clean_text(latitude),
        _clean_text(longitude),
        _clean_text(coordinates),
    )


# ---------------------------------------------------------------------------
# General page fields
# ---------------------------------------------------------------------------

def _extract_general_field(
    soup: BeautifulSoup,
    field_name: str,
    base_url: str,
) -> str:

    if field_name == "title":

        if soup.title:
            return _clean_text(
                soup.title.get_text(
                    " ",
                    strip=True,
                )
            )

        return ""

    if field_name == "headings":

        values = []

        for heading in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6"]
        ):
            values.append(
                _clean_text(
                    heading.get_text(
                        " ",
                        strip=True,
                    )
                )
            )

        return " | ".join(_unique(values))

    if field_name == "paragraphs":

        values = []

        for paragraph in soup.find_all("p"):
            values.append(
                _clean_text(
                    paragraph.get_text(
                        " ",
                        strip=True,
                    )
                )
            )

        return " | ".join(_unique(values))

    if field_name == "links":

        values = []

        for link in soup.find_all(
            "a",
            href=True,
        ):
            values.append(
                urljoin(
                    base_url,
                    str(link.get("href")),
                )
            )

        return " | ".join(_unique(values))

    if field_name == "images":

        values = []

        for image in soup.find_all("img"):

            source = (
                image.get("src")
                or image.get("data-src")
                or image.get("data-lazy-src")
            )

            if source:
                values.append(
                    urljoin(
                        base_url,
                        str(source),
                    )
                )

        return " | ".join(_unique(values))

    return ""


# ---------------------------------------------------------------------------
# Field extraction
# ---------------------------------------------------------------------------

FIELD_SELECTORS: dict[str, list[str]] = {

    "title": [
        # Common job-title selectors
        ".job-title",
        ".job_title",
        ".jobtitle",
        ".position-title",
        ".position_title",
        ".role-title",
        ".role_title",
        "[data-testid='job-title']",
        "[data-testid='job_title']",
        "[data-job-title]",

        # Semantic headings inside a record
        "h2.job-title",
        "h3.job-title",
        "h2",
        "h3",

        # Generic title classes last
        ".title",
    ],

    "company": [
        ".company",
        ".company-name",
        ".company_name",
        ".employer",
        ".employer-name",
        ".organization",
        ".organisation",
        "[data-testid='company']",
        "[data-testid='company-name']",
        "[data-company]",
    ],

    "location": [
        ".location",
        ".job-location",
        ".job_location",
        ".location-name",
        ".location_name",
        ".address",
        ".city",
        "[data-testid='location']",
        "[data-testid='job-location']",
        "[data-location]",
    ],

    "salary": [
        ".salary",
        ".salary-range",
        ".salary_range",
        ".compensation",
        ".pay",
        ".pay-range",
        ".pay_range",
        ".rate",
        "[data-testid='salary']",
        "[data-salary]",
    ],

    "description": [
        ".description",
        ".job-description",
        ".job_description",
        ".summary",
        ".job-summary",
        ".job_summary",
        ".details",
        "[data-testid='description']",
        "[data-testid='job-description']",
        "[data-description]",
    ],

    "posted_date": [
        "time[datetime]",
        "time",
        ".posted-date",
        ".posted_date",
        ".date-posted",
        ".date_posted",
        ".posting-date",
        ".posting_date",
        ".date",
        "[data-testid='posted-date']",
        "[data-posted-date]",
    ],

    "application_url": [
        "a[href*='apply']",
        "a[href*='application']",
        "a.apply",
        ".apply a",
        ".application a",
        "[data-testid='apply']",
        "[data-testid='application-link']",
    ],

    "url": [
        "a[href]",
    ],

    "email": [
        "a[href^='mailto:']",
        ".email",
        "[data-email]",
    ],

    "phone": [
        "a[href^='tel:']",
        ".phone",
        ".telephone",
        "[data-phone]",
    ],

    "latitude": [
        "[data-latitude]",
        "[data-lat]",
        ".latitude",
    ],

    "longitude": [
        "[data-longitude]",
        "[data-lng]",
        "[data-lon]",
        ".longitude",
    ],

    "coordinates": [
        "[data-coordinates]",
        ".coordinates",
        ".geo",
    ],
}


def _extract_field(
    element,
    field_name: str,
    base_url: str,
) -> str:

    selectors = FIELD_SELECTORS.get(
        field_name,
        [f".{field_name}"],
    )

    for selector in selectors:

        match = element.select_one(selector)

        if not match:
            continue

        # URLs
        if field_name in {
            "application_url",
            "url",
        }:

            href = match.get("href")

            if href:
                return urljoin(
                    base_url,
                    str(href),
                )

        # Email
        if field_name == "email":

            href = match.get("href")

            if href and str(href).startswith(
                "mailto:"
            ):
                return str(href)[7:]

            data_email = match.get("data-email")

            if data_email:
                return str(data_email)

        # Phone
        if field_name == "phone":

            href = match.get("href")

            if href and str(href).startswith(
                "tel:"
            ):
                return str(href)[4:]

            data_phone = match.get("data-phone")

            if data_phone:
                return str(data_phone)

        # Latitude
        if field_name == "latitude":

            value = (
                match.get("data-latitude")
                or match.get("data-lat")
                or match.get("content")
            )

            if value:
                return _clean_text(str(value))

        # Longitude
        if field_name == "longitude":

            value = (
                match.get("data-longitude")
                or match.get("data-lng")
                or match.get("data-lon")
                or match.get("content")
            )

            if value:
                return _clean_text(str(value))

        # Coordinates
        if field_name == "coordinates":

            value = (
                match.get("data-coordinates")
                or match.get("content")
            )

            if value:
                return _clean_text(str(value))

        # Posted date
        if field_name == "posted_date":

            datetime_value = match.get("datetime")

            if datetime_value:
                return _clean_text(
                    str(datetime_value)
                )

        # Normal text
        text = _clean_text(
            match.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            return text

    return ""


# ---------------------------------------------------------------------------
# Record detection
# ---------------------------------------------------------------------------

def _find_record_elements(
    soup: BeautifulSoup,
):
    selectors = [

        # Explicit job records
        "article.job",
        "article.job-card",
        "article.job-listing",

        ".job-card",
        ".job-listing",
        ".job-item",
        ".job",

        "[data-testid='job']",
        "[data-testid='job-card']",
        "[data-testid='job-listing']",

        "[data-job-id]",
        "[data-job]",
    ]

    for selector in selectors:

        elements = soup.select(selector)

        if elements:
            return elements

    # Generic article fallback
    articles = soup.find_all("article")

    if articles:
        return articles

    return [soup]


# ---------------------------------------------------------------------------
# JSON-LD record extraction
# ---------------------------------------------------------------------------

def _json_ld_job_records(
    soup: BeautifulSoup,
) -> list[dict[str, Any]]:

    records: list[dict[str, Any]] = []

    for document in _extract_json_ld(soup):

        job_type = document.get("@type")

        types = job_type if isinstance(
            job_type,
            list,
        ) else [job_type]

        if "JobPosting" not in types:
            continue

        record: dict[str, Any] = {}

        title = document.get("title")

        if title:
            record["title"] = _clean_text(
                str(title)
            )

        company = document.get("hiringOrganization")

        if isinstance(company, dict):
            company_name = company.get("name")

            if company_name:
                record["company"] = _clean_text(
                    str(company_name)
                )

        location = document.get("jobLocation")

        if isinstance(location, dict):

            address = location.get("address")

            if isinstance(address, dict):

                parts = []

                for key in [
                    "streetAddress",
                    "addressLocality",
                    "addressRegion",
                    "postalCode",
                    "addressCountry",
                ]:
                    value = address.get(key)

                    if value:
                        parts.append(
                            _clean_text(str(value))
                        )

                if parts:
                    record["location"] = ", ".join(parts)

        salary = document.get("baseSalary")

        if isinstance(salary, dict):

            value = salary.get("value")

            if isinstance(value, dict):
                value = value.get("value")

            if value is not None:
                record["salary"] = _clean_text(
                    str(value)
                )

        description = document.get(
            "description"
        )

        if description:
            description_soup = BeautifulSoup(
                str(description),
                "html.parser",
            )

            record["description"] = _clean_text(
                description_soup.get_text(
                    " ",
                    strip=True,
                )
            )

        posted_date = document.get(
            "datePosted"
        )

        if posted_date:
            record["posted_date"] = _clean_text(
                str(posted_date)
            )

        application_url = document.get(
            "url"
        )

        if application_url:
            record["application_url"] = _clean_text(
                str(application_url)
            )

        if record:
            records.append(record)

    return records


# ---------------------------------------------------------------------------
# Main extraction function
# ---------------------------------------------------------------------------

def execute_extraction(
    html: str,
    plan: ExtractionPlan,
    base_url: str = "",
) -> ExtractionResult:

    if not html:
        return ExtractionResult(
            records=[]
        )

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    requested_fields = {
        field.name
        for field in plan.fields
    }

    # -----------------------------------------------------------------------
    # Page-level extraction
    # -----------------------------------------------------------------------

    general_fields = {
        "page_title",
        "headings",
        "paragraphs",
        "links",
        "images",
        "latitude",
        "longitude",
        "coordinates",
    }

    # "title" is NOT treated as a general field here.
    #
    # This is important:
    # "job title" should be extracted from each job record,
    # not from <title> of the entire HTML page.
    page_fields = requested_fields.intersection(
        general_fields
    )

    if page_fields:

        record: dict[str, Any] = {}

        latitude = ""
        longitude = ""
        coordinates = ""

        if requested_fields.intersection(
            {
                "latitude",
                "longitude",
                "coordinates",
            }
        ):

            (
                latitude,
                longitude,
                coordinates,
            ) = _extract_coordinate_fields(
                soup
            )

        for field_name in page_fields:

            if field_name == "latitude":
                value = latitude

            elif field_name == "longitude":
                value = longitude

            elif field_name == "coordinates":
                value = coordinates

            else:
                value = _extract_general_field(
                    soup,
                    field_name,
                    base_url,
                )

            if value:
                record[field_name] = value

        if record and not requested_fields.intersection(
            {
                "title",
                "company",
                "location",
                "salary",
                "description",
                "posted_date",
                "application_url",
                "url",
                "email",
                "phone",
            }
        ):
            return ExtractionResult(
                records=[record]
            )

    # -----------------------------------------------------------------------
    # Try structured JobPosting JSON-LD first
    # -----------------------------------------------------------------------

    json_records = _json_ld_job_records(
        soup
    )

    if json_records:

        filtered_records = []

        for source_record in json_records:

            record = {}

            for field_name in requested_fields:

                if field_name in source_record:

                    record[field_name] = (
                        source_record[field_name]
                    )

            if record:
                filtered_records.append(record)

        if filtered_records:
            return ExtractionResult(
                records=filtered_records
            )

    # -----------------------------------------------------------------------
    # HTML record extraction
    # -----------------------------------------------------------------------

    record_elements = _find_record_elements(
        soup
    )

    records: list[dict[str, Any]] = []

    for element in record_elements:

        record: dict[str, Any] = {}

        for field in plan.fields:

            field_name = field.name

            # Page-level fields should not be extracted
            # repeatedly from every record.
            if field_name in general_fields:
                continue

            value = _extract_field(
                element,
                field_name,
                base_url,
            )

            if value:
                record[field_name] = value

        # Only add genuine structured records.
        if record:
            records.append(record)

    # -----------------------------------------------------------------------
    # If record extraction produced nothing, attempt a more intelligent
    # heading-based fallback.
    # -----------------------------------------------------------------------

    if not records:

        headings = soup.find_all(
            ["h2", "h3"]
        )

        for heading in headings:

            title = _clean_text(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

            if not title:
                continue

            # Look for the closest useful container.
            container = heading.parent

            if not container:
                continue

            record = {}

            if "title" in requested_fields:
                record["title"] = title

            for field_name in requested_fields:

                if field_name == "title":
                    continue

                if field_name in general_fields:
                    continue

                value = _extract_field(
                    container,
                    field_name,
                    base_url,
                )

                if value:
                    record[field_name] = value

            if record:
                records.append(record)

    return ExtractionResult(
        records=records
    )