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
        return {
            "records": self.records,
        }


# ---------------------------------------------------------------------------
# General helpers
# ---------------------------------------------------------------------------

def _clean_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(str(value).split())


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for value in values:
        cleaned = _clean_text(value)

        if not cleaned:
            continue

        if cleaned in seen:
            continue

        seen.add(cleaned)
        result.append(cleaned)

    return result


# ---------------------------------------------------------------------------
# Meta extraction
# ---------------------------------------------------------------------------

def _extract_meta_content(
    soup: BeautifulSoup,
    names: list[str],
) -> list[str]:
    wanted = {
        name.lower()
        for name in names
    }

    values: list[str] = []

    for tag in soup.find_all("meta"):
        name = (
            tag.get("name")
            or tag.get("property")
            or tag.get("itemprop")
        )

        if not name:
            continue

        if str(name).lower() not in wanted:
            continue

        content = tag.get("content")

        if content:
            values.append(str(content))

    return _unique(values)


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
        except (
            json.JSONDecodeError,
            TypeError,
        ):
            continue

        if isinstance(data, dict):
            documents.append(data)

        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    documents.append(item)

    return documents


def _flatten_json_values(
    value: Any,
    key_names: set[str],
) -> list[str]:
    values: list[str] = []

    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = (
                str(key)
                .lower()
                .replace("-", "")
                .replace("_", "")
            )

            if normalized_key in key_names:
                if isinstance(
                    child,
                    (str, int, float),
                ):
                    values.append(str(child))

            values.extend(
                _flatten_json_values(
                    child,
                    key_names,
                )
            )

    elif isinstance(value, list):
        for item in value:
            values.extend(
                _flatten_json_values(
                    item,
                    key_names,
                )
            )

    return values


# ---------------------------------------------------------------------------
# Coordinate extraction
# ---------------------------------------------------------------------------

def _extract_coordinates_from_text(
    text: str,
) -> tuple[str, str]:
    pattern = re.compile(
        r"(?<![\d.-])"
        r"(-?(?:90(?:\.0+)?|[0-8]?\d(?:\.\d+)?))"
        r"\s*[,;]\s*"
        r"(-?(?:180(?:\.0+)?|(?:1[0-7]\d|[1-9]?\d)(?:\.\d+)?))"
        r"(?![\d.-])"
    )

    match = pattern.search(text)

    if not match:
        return "", ""

    return (
        match.group(1),
        match.group(2),
    )


def _extract_coordinate_fields(
    soup: BeautifulSoup,
) -> tuple[str, str, str]:
    latitude = ""
    longitude = ""

    for document in _extract_json_ld(soup):
        lat_names = {
            "latitude",
            "lat",
        }

        lon_names = {
            "longitude",
            "lon",
            "lng",
        }

        lat_values = _flatten_json_values(
            document,
            lat_names,
        )

        lon_values = _flatten_json_values(
            document,
            lon_names,
        )

        if lat_values and not latitude:
            latitude = lat_values[0]

        if lon_values and not longitude:
            longitude = lon_values[0]

    text = _clean_text(
        soup.get_text(
            " ",
            strip=True,
        )
    )

    if not latitude or not longitude:
        text_lat, text_lon = (
            _extract_coordinates_from_text(text)
        )

        if not latitude:
            latitude = text_lat

        if not longitude:
            longitude = text_lon

    coordinates = ""

    if latitude and longitude:
        coordinates = (
            f"{latitude}, {longitude}"
        )

    return (
        latitude,
        longitude,
        coordinates,
    )


# ---------------------------------------------------------------------------
# General page extraction
# ---------------------------------------------------------------------------

def _extract_general_field(
    soup: BeautifulSoup,
    field_name: str,
    base_url: str,
) -> str:

    if field_name == "title":
        title = soup.title

        if title:
            value = _clean_text(
                title.get_text(
                    " ",
                    strip=True,
                )
            )

            if value:
                return value

        heading = soup.find("h1")

        if heading:
            return _clean_text(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )

        return ""

    if field_name == "headings":
        values = [
            _clean_text(
                heading.get_text(
                    " ",
                    strip=True,
                )
            )
            for heading in soup.find_all(
                [
                    "h1",
                    "h2",
                    "h3",
                    "h4",
                    "h5",
                    "h6",
                ]
            )
        ]

        return " | ".join(
            _unique(values)
        )

    if field_name == "paragraphs":
        values = [
            _clean_text(
                paragraph.get_text(
                    " ",
                    strip=True,
                )
            )
            for paragraph in soup.find_all(
                "p"
            )
        ]

        return " | ".join(
            _unique(values)
        )

    if field_name == "links":
        links: list[str] = []

        for link in soup.find_all(
            "a",
            href=True,
        ):
            href = link.get("href")

            if href:
                links.append(
                    urljoin(
                        base_url,
                        str(href),
                    )
                )

        return " | ".join(
            _unique(links)
        )

    if field_name == "images":
        images: list[str] = []

        for image in soup.find_all("img"):
            source = (
                image.get("src")
                or image.get("data-src")
                or image.get("data-lazy-src")
            )

            if source:
                images.append(
                    urljoin(
                        base_url,
                        str(source),
                    )
                )

        return " | ".join(
            _unique(images)
        )

    return ""


# ---------------------------------------------------------------------------
# Environmental / GHG selectors
# ---------------------------------------------------------------------------

_FIELD_SELECTORS: dict[str, list[str]] = {
    "facility": [
        "[data-facility]",
        "[data-facility-name]",
        ".facility",
        ".facility-name",
        ".site-name",
        ".plant-name",
        "[itemprop='name']",
    ],
    "facility_id": [
        "[data-facility-id]",
        ".facility-id",
        ".site-id",
        ".plant-id",
    ],
    "facility_type": [
        "[data-facility-type]",
        ".facility-type",
        ".site-type",
        ".plant-type",
    ],
    "operator": [
        "[data-operator]",
        ".operator",
        ".facility-operator",
        ".site-operator",
    ],
    "owner": [
        "[data-owner]",
        ".owner",
        ".facility-owner",
        ".site-owner",
    ],
    "location": [
        "[data-location]",
        ".location",
        ".address",
        ".facility-location",
        ".site-location",
        "[itemprop='address']",
    ],

    # Methane
    "methane": [
        "[data-methane]",
        ".methane",
        ".ch4",
    ],
    "methane_concentration": [
        "[data-methane-concentration]",
        "[data-ch4-concentration]",
        ".methane-concentration",
        ".ch4-concentration",
        ".methane-ppm",
        ".ch4-ppm",
    ],
    "methane_emissions": [
        "[data-methane-emissions]",
        "[data-ch4-emissions]",
        ".methane-emissions",
        ".ch4-emissions",
    ],
    "methane_leak_rate": [
        "[data-methane-leak-rate]",
        ".methane-leak-rate",
        ".ch4-leak-rate",
    ],
    "methane_flow_rate": [
        "[data-methane-flow-rate]",
        ".methane-flow-rate",
        ".ch4-flow-rate",
    ],

    # GHG
    "ghg": [
        "[data-ghg]",
        ".ghg",
        ".greenhouse-gas",
    ],
    "co2": [
        "[data-co2]",
        ".co2",
        ".carbon-dioxide",
    ],
    "co2e": [
        "[data-co2e]",
        ".co2e",
        ".co2-equivalent",
    ],
    "nitrous_oxide": [
        "[data-n2o]",
        "[data-nitrous-oxide]",
        ".n2o",
        ".nitrous-oxide",
    ],
    "emissions": [
        "[data-emissions]",
        ".emissions",
        ".emission",
        ".total-emissions",
    ],
    "emission_quantity": [
        "[data-emission-quantity]",
        ".emission-quantity",
        ".emissions-quantity",
    ],
    "emission_unit": [
        "[data-emission-unit]",
        ".emission-unit",
    ],
    "emission_source": [
        "[data-emission-source]",
        ".emission-source",
        ".source",
    ],
    "emission_category": [
        "[data-emission-category]",
        ".emission-category",
        ".source-category",
    ],

    # Activity
    "activity_data": [
        "[data-activity-data]",
        ".activity-data",
        ".activity",
    ],
    "activity_type": [
        "[data-activity-type]",
        ".activity-type",
    ],
    "activity_quantity": [
        "[data-activity-quantity]",
        ".activity-quantity",
        ".activity-value",
    ],
    "activity_unit": [
        "[data-activity-unit]",
        ".activity-unit",
    ],
    "fuel_consumption": [
        "[data-fuel-consumption]",
        ".fuel-consumption",
        ".fuel-use",
    ],
    "energy_consumption": [
        "[data-energy-consumption]",
        ".energy-consumption",
        ".energy-use",
    ],
    "electricity_consumption": [
        "[data-electricity-consumption]",
        ".electricity-consumption",
        ".electricity-use",
    ],
    "gas_consumption": [
        "[data-gas-consumption]",
        ".gas-consumption",
        ".natural-gas-consumption",
    ],

    # Emission factors
    "emission_factor": [
        "[data-emission-factor]",
        ".emission-factor",
        ".emission-factors",
    ],
    "emission_factor_value": [
        "[data-emission-factor-value]",
        ".emission-factor-value",
        ".factor-value",
    ],
    "emission_factor_unit": [
        "[data-emission-factor-unit]",
        ".emission-factor-unit",
        ".factor-unit",
    ],
    "emission_factor_source": [
        "[data-emission-factor-source]",
        ".emission-factor-source",
        ".factor-source",
    ],

    # Inventory
    "inventory": [
        "[data-inventory]",
        ".inventory",
        ".ghg-inventory",
        ".emissions-inventory",
    ],
    "inventory_year": [
        "[data-inventory-year]",
        ".inventory-year",
        ".reporting-year",
        ".base-year",
    ],
    "inventory_period": [
        "[data-inventory-period]",
        ".inventory-period",
        ".reporting-period",
    ],
    "inventory_total": [
        "[data-inventory-total]",
        ".inventory-total",
        ".total-inventory",
    ],
    "reporting_entity": [
        "[data-reporting-entity]",
        ".reporting-entity",
    ],

    # IPCC
    "ipcc": [
        "[data-ipcc]",
        ".ipcc",
        ".ipcc-method",
    ],
    "ipcc_tier": [
        "[data-ipcc-tier]",
        ".ipcc-tier",
        ".tier",
    ],
    "ipcc_tier_1": [
        "[data-ipcc-tier-1]",
        ".ipcc-tier-1",
        ".tier-1",
    ],
    "ipcc_tier_2": [
        "[data-ipcc-tier-2]",
        ".ipcc-tier-2",
        ".tier-2",
    ],
    "ipcc_tier_3": [
        "[data-ipcc-tier-3]",
        ".ipcc-tier-3",
        ".tier-3",
    ],
    "ipcc_category": [
        "[data-ipcc-category]",
        ".ipcc-category",
    ],
    "ipcc_subcategory": [
        "[data-ipcc-subcategory]",
        ".ipcc-subcategory",
    ],

    # GHG Protocol
    "scope_1": [
        "[data-scope-1]",
        ".scope-1",
        ".scope1",
        ".scope-one",
    ],
    "scope_2": [
        "[data-scope-2]",
        ".scope-2",
        ".scope2",
        ".scope-two",
    ],
    "scope_3": [
        "[data-scope-3]",
        ".scope-3",
        ".scope3",
        ".scope-three",
    ],
    "scope": [
        "[data-scope]",
        ".scope",
        ".ghg-scope",
    ],
    "scope_3_category": [
        "[data-scope-3-category]",
        ".scope-3-category",
        ".scope3-category",
    ],

    # Meteorology
    "meteorological_data": [
        "[data-meteorological-data]",
        ".meteorological-data",
        ".meteorology",
        ".weather-data",
    ],
    "temperature": [
        "[data-temperature]",
        "[data-ambient-temperature]",
        ".temperature",
        ".ambient-temperature",
    ],
    "humidity": [
        "[data-humidity]",
        ".humidity",
        ".relative-humidity",
    ],
    "wind_speed": [
        "[data-wind-speed]",
        ".wind-speed",
        ".wind-velocity",
    ],
    "wind_direction": [
        "[data-wind-direction]",
        ".wind-direction",
    ],
    "pressure": [
        "[data-pressure]",
        ".pressure",
        ".atmospheric-pressure",
    ],
    "precipitation": [
        "[data-precipitation]",
        ".precipitation",
        ".rainfall",
    ],
    "solar_radiation": [
        "[data-solar-radiation]",
        ".solar-radiation",
        ".solar-irradiance",
    ],
    "weather_station": [
        "[data-weather-station]",
        ".weather-station",
        ".meteorological-station",
    ],
    "weather_date": [
        "[data-weather-date]",
        ".weather-date",
        ".observation-date",
    ],

    # Monitoring
    "monitoring": [
        "[data-monitoring]",
        ".monitoring",
        ".monitoring-data",
    ],
    "monitoring_method": [
        "[data-monitoring-method]",
        ".monitoring-method",
        ".measurement-method",
    ],
    "sampling_location": [
        "[data-sampling-location]",
        ".sampling-location",
        ".sample-location",
    ],
    "sampling_point": [
        "[data-sampling-point]",
        ".sampling-point",
        ".sample-point",
    ],
    "detection_limit": [
        "[data-detection-limit]",
        ".detection-limit",
        ".lod",
    ],

    # Measurement
    "value": [
        "[data-value]",
        ".value",
        ".measurement",
        ".measured-value",
    ],
    "unit": [
        "[data-unit]",
        ".unit",
        ".measurement-unit",
    ],
    "concentration": [
        "[data-concentration]",
        ".concentration",
    ],
    "measurement_date": [
        "[data-measurement-date]",
        ".measurement-date",
        ".sampling-date",
    ],
    "measurement_time": [
        "[data-measurement-time]",
        ".measurement-time",
        ".sampling-time",
    ],
}


_JSON_KEY_ALIASES: dict[str, tuple[str, ...]] = {
    "facility": (
        "facility",
        "facilityname",
        "sitename",
        "plantname",
        "installationname",
    ),
    "facility_id": (
        "facilityid",
        "siteid",
        "plantid",
    ),
    "facility_type": (
        "facilitytype",
        "sitetype",
        "planttype",
    ),
    "operator": (
        "operator",
        "facilityoperator",
        "siteoperator",
    ),
    "owner": (
        "owner",
        "facilityowner",
        "siteowner",
    ),
    "methane": (
        "methane",
        "ch4",
    ),
    "methane_concentration": (
        "methaneconcentration",
        "ch4concentration",
        "methaneppm",
        "ch4ppm",
    ),
    "methane_emissions": (
        "methaneemissions",
        "ch4emissions",
    ),
    "co2": (
        "co2",
        "carbondioxide",
    ),
    "co2e": (
        "co2e",
        "co2equivalent",
        "carbondioxideequivalent",
    ),
    "nitrous_oxide": (
        "n2o",
        "nitrousoxide",
    ),
    "emissions": (
        "emissions",
        "emission",
        "totalemissions",
    ),
    "emission_factor": (
        "emissionfactor",
        "emissionfactors",
    ),
    "activity_data": (
        "activitydata",
        "activity",
        "activitylevel",
    ),
    "inventory": (
        "inventory",
        "ghginventory",
        "emissionsinventory",
    ),
    "inventory_year": (
        "inventoryyear",
        "reportingyear",
        "baseyear",
    ),
    "ipcc_tier": (
        "ipcc_tier",
        "ipcctier",
        "tier",
    ),
    "scope_1": (
        "scope1",
        "scope_1",
    ),
    "scope_2": (
        "scope2",
        "scope_2",
    ),
    "scope_3": (
        "scope3",
        "scope_3",
    ),
    "temperature": (
        "temperature",
        "ambienttemperature",
        "airtemperature",
    ),
    "humidity": (
        "humidity",
        "relativehumidity",
    ),
    "wind_speed": (
        "windspeed",
        "windvelocity",
    ),
    "wind_direction": (
        "winddirection",
    ),
    "pressure": (
        "pressure",
        "atmosphericpressure",
    ),
    "precipitation": (
        "precipitation",
        "rainfall",
    ),
    "solar_radiation": (
        "solarradiation",
        "solarirradiance",
    ),
    "weather_station": (
        "weatherstation",
        "meteorologicalstation",
    ),
}


def _extract_environmental_field(
    element,
    soup: BeautifulSoup,
    field_name: str,
) -> str:

    selectors = _FIELD_SELECTORS.get(
        field_name,
        [],
    )

    for selector in selectors:
        try:
            match = element.select_one(selector)
        except Exception:
            continue

        if not match:
            continue

        attributes = (
            f"data-{field_name.replace('_', '-')}",
            "content",
            "value",
            "datetime",
        )

        for attribute in attributes:
            value = match.get(attribute)

            if value:
                return _clean_text(
                    str(value)
                )

        text = _clean_text(
            match.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            return text

    # JSON-LD fallback
    aliases = _JSON_KEY_ALIASES.get(
        field_name,
        (),
    )

    json_names = {
        name
        .replace("-", "")
        .replace("_", "")
        .lower()
        for name in aliases
    }

    if json_names:
        values: list[str] = []

        for document in _extract_json_ld(soup):
            values.extend(
                _flatten_json_values(
                    document,
                    json_names,
                )
            )

        values = _unique(values)

        if values:
            return values[0]

    # Meta fallback
    meta_names = [
        field_name,
        field_name.replace("_", "-"),
        field_name.replace("_", " "),
    ]

    values = _extract_meta_content(
        soup,
        meta_names,
    )

    if values:
        return values[0]

    # Label fallback
    labels = [
        field_name.replace("_", " "),
        field_name.replace("_", "-"),
    ]

    page_text = _clean_text(
        element.get_text(
            " ",
            strip=True,
        )
    )

    for label in labels:
        pattern = re.compile(
            rf"\b{re.escape(label)}"
            rf"\s*[:=-]\s*"
            rf"([^|;\n]+)",
            re.IGNORECASE,
        )

        match = pattern.search(page_text)

        if match:
            return _clean_text(
                match.group(1)
            )

    return ""


# ---------------------------------------------------------------------------
# Standard structured fields
# ---------------------------------------------------------------------------

_STANDARD_SELECTORS: dict[
    str,
    list[str],
] = {
    "title": [
        ".job-title",
        ".title",
        "[data-testid='job-title']",
        "[data-job-title]",
        "h2",
        "h3",
    ],
    "company": [
        ".company",
        ".company-name",
        "[data-testid='company']",
        "[data-company]",
    ],
    "location": [
        ".location",
        ".job-location",
        "[data-testid='location']",
        "[data-location]",
    ],
    "salary": [
        ".salary",
        ".compensation",
        "[data-testid='salary']",
        "[data-salary]",
    ],
    "description": [
        ".description",
        ".job-description",
        "[data-testid='description']",
        "[data-description]",
    ],
    "posted_date": [
        "time",
        ".posted-date",
        ".date",
        "[data-testid='posted-date']",
        "[data-posted-date]",
    ],
    "application_url": [
        "a[href*='apply']",
        "a.apply",
        ".apply a",
        "[data-application-url]",
    ],
    "url": [
        "a[href]",
        "link[href]",
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
}


def _extract_field(
    element,
    field_name: str,
    base_url: str,
    soup: BeautifulSoup | None = None,
) -> str:

    selectors = _STANDARD_SELECTORS.get(
        field_name,
        [],
    )

    for selector in selectors:
        try:
            match = element.select_one(selector)
        except Exception:
            continue

        if not match:
            continue

        # Application URL
        if field_name == "application_url":
            href = match.get("href")

            if href:
                return urljoin(
                    base_url,
                    str(href),
                )

            data_url = match.get(
                "data-application-url"
            )

            if data_url:
                return urljoin(
                    base_url,
                    str(data_url),
                )

        # Generic URL
        if field_name == "url":
            href = match.get("href")

            if href:
                return urljoin(
                    base_url,
                    str(href),
                )

        # Email
        if field_name == "email":
            href = match.get("href")

            if href and str(href).lower().startswith(
                "mailto:"
            ):
                return str(href)[7:]

            data_email = match.get(
                "data-email"
            )

            if data_email:
                return _clean_text(
                    str(data_email)
                )

        # Phone
        if field_name == "phone":
            href = match.get("href")

            if href and str(href).lower().startswith(
                "tel:"
            ):
                return str(href)[4:]

            data_phone = match.get(
                "data-phone"
            )

            if data_phone:
                return _clean_text(
                    str(data_phone)
                )

        # Attribute-based values
        for attribute in (
            f"data-{field_name.replace('_', '-')}",
            "content",
            "datetime",
            "value",
        ):
            value = match.get(attribute)

            if value:
                return _clean_text(
                    str(value)
                )

        text = _clean_text(
            match.get_text(
                " ",
                strip=True,
            )
        )

        if text:
            return text

    # Environmental extraction
    if soup is not None:
        value = _extract_environmental_field(
            element,
            soup,
            field_name,
        )

        if value:
            return value

    return ""


# ---------------------------------------------------------------------------
# Record detection
# ---------------------------------------------------------------------------

def _find_record_elements(
    soup: BeautifulSoup,
):
    """
    Find repeated content containers.

    Important:
    We intentionally prioritize job/listing containers before
    generic page-level elements such as h1.
    """

    selectors = [
        "[data-testid='job-card']",
        "[data-testid='job']",
        "[data-job]",
        ".job-card",
        ".job-listing",
        ".job",
        "article.job",
        "article[data-job]",
        ".listing-card",
        ".listing",
        ".facility-card",
        ".facility",
        ".emission-record",
        ".emission",
        ".inventory-record",
        ".monitoring-record",
        ".data-record",
        ".record",
        "article",
    ]

    for selector in selectors:
        try:
            elements = soup.select(selector)
        except Exception:
            continue

        if not elements:
            continue

        # Avoid selecting a single page wrapper when there
        # are clearly repeated records.
        if len(elements) >= 2:
            return elements

    # If exactly one article exists, it may still be a record.
    articles = soup.select("article")

    if len(articles) == 1:
        return articles

    return [soup]


# ---------------------------------------------------------------------------
# Detect whether a plan is page-level
# ---------------------------------------------------------------------------

def _is_page_level_plan(
    plan: ExtractionPlan,
) -> bool:
    """
    Determine whether an extraction plan should operate on the
    entire page rather than repeated record elements.

    Supports both canonical page-level fields and semantic
    instructions such as:

        page heading as title
        first paragraph as description
    """

    page_fields = {
        "headings",
        "paragraphs",
        "links",
        "images",
        "latitude",
        "longitude",
        "coordinates",
    }

    field_names = {
        field.name
        for field in plan.fields
    }

    # Canonical page-level extraction.
    if field_names and field_names.issubset(page_fields):
        return True

    # Semantic page-level extraction.
    semantic_text = " ".join(
        field.description.lower()
        for field in plan.fields
    )

    semantic_markers = (
        "page heading",
        "page title",
        "first paragraph",
        "second paragraph",
        "third paragraph",
        "page paragraph",
        "page text",
        "website heading",
        "website title",
    )

    return any(
        marker in semantic_text
        for marker in semantic_markers
    )

def _extract_semantic_page_field(
    soup: BeautifulSoup,
    field: ExtractionField,
    base_url: str = "",
) -> str:
    """
    Extract a field according to the semantic wording of the
    extraction instruction.

    Examples:

        "page heading as title"
            -> first visible heading

        "first paragraph as description"
            -> first paragraph
    """

    description = field.description.lower().strip()

    # ---------------------------------------------------------------
    # Page heading
    # ---------------------------------------------------------------

    if (
        "page heading" in description
        or "website heading" in description
        or "heading as" in description
    ):
        for selector in ("h1", "h2", "h3", "h4", "h5", "h6"):
            match = soup.select_one(selector)

            if match:
                value = _clean_text(
                    match.get_text(
                        " ",
                        strip=True,
                    )
                )

                if value:
                    return value

    # ---------------------------------------------------------------
    # First paragraph
    # ---------------------------------------------------------------

    if "first paragraph" in description:
        paragraphs = soup.select("p")

        if paragraphs:
            value = _clean_text(
                paragraphs[0].get_text(
                    " ",
                    strip=True,
                )
            )

            if value:
                return value

    # ---------------------------------------------------------------
    # Second paragraph
    # ---------------------------------------------------------------

    if "second paragraph" in description:
        paragraphs = soup.select("p")

        if len(paragraphs) >= 2:
            value = _clean_text(
                paragraphs[1].get_text(
                    " ",
                    strip=True,
                )
            )

            if value:
                return value

    # ---------------------------------------------------------------
    # Third paragraph
    # ---------------------------------------------------------------

    if "third paragraph" in description:
        paragraphs = soup.select("p")

        if len(paragraphs) >= 3:
            value = _clean_text(
                paragraphs[2].get_text(
                    " ",
                    strip=True,
                )
            )

            if value:
                return value

    # ---------------------------------------------------------------
    # Page title
    # ---------------------------------------------------------------

    if (
        "page title" in description
        and soup.title
    ):
        value = _clean_text(
            soup.title.get_text(
                " ",
                strip=True,
            )
        )

        if value:
            return value

    return ""

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

    field_names = {
        field.name
        for field in plan.fields
    }

    # ---------------------------------------------------------------
    # Pure page-level extraction
    # ---------------------------------------------------------------

    if _is_page_level_plan(plan):

        record: dict[str, Any] = {}

        latitude = ""
        longitude = ""
        coordinates = ""

        if field_names.intersection(
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

        for field in plan.fields:
            value = ""

            # First honor semantic wording such as:
            # "page heading as title"
            # "first paragraph as description"
            value = _extract_semantic_page_field(
                soup,
                field,
                base_url,
            )

            if not value and field.name in {
                "title",
                "headings",
                "paragraphs",
                "links",
                "images",
            }:
                value = _extract_general_field(
                    soup,
                    field.name,
                    base_url,
                )

            elif not value and field.name == "latitude":
                value = latitude

            elif field.name == "longitude":
                value = longitude

            elif field.name == "coordinates":
                value = coordinates

            if value:
                record[field.name] = value

        if record:
            return ExtractionResult(
                records=[record]
            )

        return ExtractionResult(
            records=[]
        )

    # ---------------------------------------------------------------
    # Repeated-record extraction
    # ---------------------------------------------------------------

    record_elements = _find_record_elements(
        soup
    )

    records: list[dict[str, Any]] = []

    for element in record_elements:
        record: dict[str, Any] = {}

        for field in plan.fields:
            value = _extract_field(
                element,
                field.name,
                base_url,
                soup,
            )

            if value:
                record[field.name] = value

        if record:
            records.append(record)

    # ---------------------------------------------------------------
    # Important fallback:
    #
    # If generic record detection found the whole page, do not return
    # the page title as a fake job record. Try article/job selectors
    # once more.
    # ---------------------------------------------------------------

    if (
        len(records) == 1
        and record_elements
        and record_elements[0] is soup
    ):
        fallback_selectors = [
            "[data-testid='job-card']",
            "[data-testid='job']",
            ".job-card",
            ".job-listing",
            ".job",
            "article",
        ]

        fallback_elements = []

        for selector in fallback_selectors:
            found = soup.select(selector)

            if len(found) >= 2:
                fallback_elements = found
                break

        if fallback_elements:
            records = []

            for element in fallback_elements:
                record: dict[str, Any] = {}

                for field in plan.fields:
                    value = _extract_field(
                        element,
                        field.name,
                        base_url,
                        soup,
                    )

                    if value:
                        record[field.name] = value

                if record:
                    records.append(record)

    return ExtractionResult(
        records=records
    )


