from __future__ import annotations

import re
from dataclasses import asdict, dataclass


@dataclass
class ExtractionField:
    name: str
    description: str
    data_type: str = "string"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ExtractionPlan:
    instruction: str
    fields: list[ExtractionField]

    def to_dict(self) -> dict:
        return {
            "instruction": self.instruction,
            "fields": [field.to_dict() for field in self.fields],
        }


# ---------------------------------------------------------------------------
# Canonical field aliases
# ---------------------------------------------------------------------------

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    # -----------------------------------------------------------------------
    # General website fields
    # -----------------------------------------------------------------------
    "title": (
        "title",
        "page title",
        "website title",
        "job title",
        "position",
        "role",
    ),
    "headings": (
        "heading",
        "headings",
        "page heading",
        "page headings",
        "website heading",
        "website headings",
    ),
    "paragraphs": (
        "paragraph",
        "paragraphs",
        "page paragraphs",
        "website paragraphs",
        "text",
        "page text",
    ),
    "links": (
        "link",
        "links",
        "page links",
        "website links",
    ),
    "images": (
        "image",
        "images",
        "page images",
        "website images",
        "pictures",
        "photos",
    ),

    # -----------------------------------------------------------------------
    # Geographic fields
    # -----------------------------------------------------------------------
    "latitude": (
        "latitude",
        "lat",
    ),
    "longitude": (
        "longitude",
        "longitude coordinate",
        "lng",
        "lon",
    ),
    "coordinates": (
        "coordinate",
        "coordinates",
        "geo coordinate",
        "geo coordinates",
        "geocoordinate",
        "geocoordinates",
        "gps coordinates",
        "gps location",
    ),

    # -----------------------------------------------------------------------
    # Common structured fields
    # -----------------------------------------------------------------------
    "company": (
        "company",
        "company name",
        "employer",
        "organization",
        "organisation",
    ),
    "location": (
        "location",
        "city",
        "address",
        "physical address",
        "site location",
        "facility location",
        "geographic location",
    ),
    "salary": (
        "salary",
        "pay",
        "compensation",
        "wage",
    ),
    "description": (
        "description",
        "job description",
        "details",
    ),
    "application_url": (
        "application url",
        "application link",
        "apply url",
        "apply link",
        "application",
    ),
    "url": (
        "url",
        "link url",
        "website url",
        "website",
    ),
    "email": (
        "email",
        "email address",
    ),
    "phone": (
        "phone",
        "phone number",
        "telephone",
        "telephone number",
    ),
    "posted_date": (
        "posted date",
        "publication date",
        "published date",
        "date posted",
    ),
    "date": (
        "date",
    ),

    # -----------------------------------------------------------------------
    # Facility / organization information
    # -----------------------------------------------------------------------
    "facility": (
        "facility",
        "facility name",
        "facility name and location",
        "plant",
        "plant name",
        "site",
        "site name",
        "installation",
        "installation name",
        "industrial facility",
        "production facility",
    ),
    "facility_id": (
        "facility id",
        "facility identifier",
        "site id",
        "site identifier",
        "plant id",
        "plant identifier",
    ),
    "facility_type": (
        "facility type",
        "site type",
        "plant type",
        "installation type",
    ),
    "operator": (
        "operator",
        "facility operator",
        "site operator",
        "plant operator",
    ),
    "owner": (
        "owner",
        "facility owner",
        "site owner",
        "plant owner",
    ),

    # -----------------------------------------------------------------------
    # Methane / CH4
    # -----------------------------------------------------------------------
    "methane": (
        "methane",
        "methane concentration",
        "ch4",
        "ch4 concentration",
        "methane emissions",
        "methane emission",
        "methane release",
        "methane leakage",
        "methane leak",
    ),
    "methane_concentration": (
        "methane concentration",
        "ch4 concentration",
        "methane content",
        "ch4 content",
        "methane ppm",
        "ch4 ppm",
    ),
    "methane_emissions": (
        "methane emissions",
        "methane emission",
        "ch4 emissions",
        "ch4 emission",
        "methane released",
        "methane release",
    ),
    "methane_leak_rate": (
        "methane leak rate",
        "methane leakage rate",
        "ch4 leak rate",
        "ch4 leakage rate",
    ),
    "methane_flow_rate": (
        "methane flow rate",
        "ch4 flow rate",
        "methane gas flow",
        "ch4 gas flow",
    ),

    # -----------------------------------------------------------------------
    # Greenhouse gases
    # -----------------------------------------------------------------------
    "ghg": (
        "ghg",
        "greenhouse gas",
        "greenhouse gases",
        "ghg emissions",
    ),
    "co2": (
        "co2",
        "carbon dioxide",
        "carbon dioxide emissions",
        "co2 emissions",
    ),
    "co2e": (
        "co2e",
        "co2 equivalent",
        "carbon dioxide equivalent",
        "carbon dioxide equivalents",
        "ghg co2e",
    ),
    "nitrous_oxide": (
        "nitrous oxide",
        "n2o",
        "n2o emissions",
    ),

    # -----------------------------------------------------------------------
    # Emissions
    # -----------------------------------------------------------------------
    "emissions": (
        "emissions",
        "emission",
        "total emissions",
        "ghg emissions",
        "greenhouse gas emissions",
    ),
    "emission_quantity": (
        "emission quantity",
        "emissions quantity",
        "emission amount",
        "emissions amount",
        "emission volume",
        "emission mass",
    ),
    "emission_unit": (
        "emission unit",
        "emissions unit",
        "emission units",
    ),
    "emission_source": (
        "emission source",
        "emissions source",
        "source of emissions",
        "source category",
    ),
    "emission_category": (
        "emission category",
        "emissions category",
        "source category",
    ),

    # -----------------------------------------------------------------------
    # Activity data
    # -----------------------------------------------------------------------
    "activity_data": (
        "activity data",
        "activity",
        "activity level",
        "activity quantity",
        "activity amount",
        "operational activity data",
    ),
    "activity_type": (
        "activity type",
        "activity category",
    ),
    "activity_quantity": (
        "activity quantity",
        "activity amount",
        "activity volume",
        "activity value",
        "activity level",
    ),
    "activity_unit": (
        "activity unit",
        "activity units",
    ),
    "fuel_consumption": (
        "fuel consumption",
        "fuel use",
        "fuel usage",
        "fuel consumed",
    ),
    "energy_consumption": (
        "energy consumption",
        "energy use",
        "energy usage",
        "energy consumed",
    ),
    "electricity_consumption": (
        "electricity consumption",
        "electricity use",
        "electricity usage",
        "electricity consumed",
    ),
    "gas_consumption": (
        "gas consumption",
        "natural gas consumption",
        "natural gas use",
        "gas used",
    ),

    # -----------------------------------------------------------------------
    # Emission factors
    # -----------------------------------------------------------------------
    "emission_factor": (
        "emission factor",
        "emission factors",
        "ef",
        "ghg emission factor",
        "co2 emission factor",
        "methane emission factor",
        "ch4 emission factor",
    ),
    "emission_factor_value": (
        "emission factor value",
        "emission factor amount",
        "emission factor rate",
        "factor value",
    ),
    "emission_factor_unit": (
        "emission factor unit",
        "emission factor units",
        "factor unit",
    ),
    "emission_factor_source": (
        "emission factor source",
        "emission factor reference",
        "emission factor database",
        "factor source",
    ),

    # -----------------------------------------------------------------------
    # GHG inventory
    # -----------------------------------------------------------------------
    "inventory": (
        "inventory",
        "ghg inventory",
        "emissions inventory",
        "greenhouse gas inventory",
        "emission inventory",
    ),
    "inventory_year": (
        "inventory year",
        "reporting year",
        "assessment year",
        "base year",
    ),
    "inventory_period": (
        "inventory period",
        "reporting period",
        "assessment period",
    ),
    "inventory_total": (
        "inventory total",
        "total inventory",
        "total emissions inventory",
    ),
    "reporting_entity": (
        "reporting entity",
        "reporting organization",
        "reporting organisation",
        "reporting company",
    ),

    # -----------------------------------------------------------------------
    # IPCC methodology / tiers
    # -----------------------------------------------------------------------
    "ipcc": (
        "ipcc",
        "ipcc method",
        "ipcc methodology",
        "ipcc guidelines",
    ),
    "ipcc_tier": (
        "ipcc tier",
        "ipcc tiers",
        "tier",
        "tier level",
        "methodological tier",
    ),
    "ipcc_tier_1": (
        "ipcc tier 1",
        "tier 1",
        "tier one",
    ),
    "ipcc_tier_2": (
        "ipcc tier 2",
        "tier 2",
        "tier two",
    ),
    "ipcc_tier_3": (
        "ipcc tier 3",
        "tier 3",
        "tier three",
    ),
    "ipcc_category": (
        "ipcc category",
        "ipcc source category",
        "ipcc sector",
    ),
    "ipcc_subcategory": (
        "ipcc subcategory",
        "ipcc source subcategory",
    ),

    # -----------------------------------------------------------------------
    # GHG Protocol scopes
    # -----------------------------------------------------------------------
    "scope_1": (
        "scope 1",
        "scope 1 emissions",
        "scope one",
        "direct emissions",
        "direct ghg emissions",
    ),
    "scope_2": (
        "scope 2",
        "scope 2 emissions",
        "scope two",
        "indirect emissions",
        "purchased energy emissions",
    ),
    "scope_3": (
        "scope 3",
        "scope 3 emissions",
        "scope three",
        "value chain emissions",
        "scope 3 value chain",
    ),
    "scope": (
        "scope",
        "ghg scope",
        "emissions scope",
    ),
    "scope_3_category": (
        "scope 3 category",
        "scope 3 categories",
        "scope three category",
        "value chain category",
    ),

    # -----------------------------------------------------------------------
    # Meteorological data
    # -----------------------------------------------------------------------
    "meteorological_data": (
        "meteorological data",
        "meteorological information",
        "met data",
        "weather data",
        "weather information",
        "meteorology",
    ),
    "temperature": (
        "temperature",
        "ambient temperature",
        "air temperature",
        "atmospheric temperature",
    ),
    "humidity": (
        "humidity",
        "relative humidity",
    ),
    "wind_speed": (
        "wind speed",
        "average wind speed",
        "wind velocity",
    ),
    "wind_direction": (
        "wind direction",
        "prevailing wind direction",
    ),
    "pressure": (
        "pressure",
        "atmospheric pressure",
        "barometric pressure",
    ),
    "precipitation": (
        "precipitation",
        "rainfall",
        "rain fall",
    ),
    "solar_radiation": (
        "solar radiation",
        "solar irradiance",
        "radiation",
    ),
    "weather_station": (
        "weather station",
        "meteorological station",
        "met station",
    ),
    "weather_date": (
        "weather date",
        "observation date",
        "meteorological date",
    ),

    # -----------------------------------------------------------------------
    # Units / measurements
    # -----------------------------------------------------------------------
    "value": (
        "value",
        "measurement",
        "measured value",
        "measurement value",
    ),
    "unit": (
        "unit",
        "units",
        "measurement unit",
        "measurement units",
    ),
    "concentration": (
        "concentration",
        "gas concentration",
        "pollutant concentration",
    ),
    "measurement_date": (
        "measurement date",
        "sampling date",
        "monitoring date",
        "observation date",
    ),
    "measurement_time": (
        "measurement time",
        "sampling time",
        "monitoring time",
        "observation time",
    ),

    # -----------------------------------------------------------------------
    # Monitoring / environmental data
    # -----------------------------------------------------------------------
    "monitoring": (
        "monitoring",
        "environmental monitoring",
        "emissions monitoring",
        "monitoring data",
    ),
    "monitoring_method": (
        "monitoring method",
        "measurement method",
        "measurement technique",
        "monitoring technique",
    ),
    "sampling_location": (
        "sampling location",
        "sample location",
        "monitoring location",
        "measurement location",
    ),
    "sampling_point": (
        "sampling point",
        "sample point",
        "monitoring point",
        "measurement point",
    ),
    "detection_limit": (
        "detection limit",
        "limit of detection",
        "lod",
    ),

    # -----------------------------------------------------------------------
    # Dates / periods
    # -----------------------------------------------------------------------
    "start_date": (
        "start date",
        "period start",
        "reporting start date",
    ),
    "end_date": (
        "end date",
        "period end",
        "reporting end date",
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_instruction(instruction: str) -> str:
    return re.sub(r"\s+", " ", instruction).strip()


def _normalize_phrase(phrase: str) -> str:
    normalized = phrase.lower().strip()

    normalized = re.sub(
        r"^(the|a|an)\s+",
        "",
        normalized,
    )

    normalized = normalized.strip(" .;:")

    return normalized


def _infer_data_type(canonical_name: str) -> str:
    numeric_fields = {
        "salary",
        "latitude",
        "longitude",
        "methane_concentration",
        "methane_emissions",
        "methane_leak_rate",
        "methane_flow_rate",
        "co2",
        "co2e",
        "nitrous_oxide",
        "emissions",
        "emission_quantity",
        "emission_factor",
        "emission_factor_value",
        "activity_quantity",
        "fuel_consumption",
        "energy_consumption",
        "electricity_consumption",
        "gas_consumption",
        "temperature",
        "humidity",
        "wind_speed",
        "wind_direction",
        "pressure",
        "precipitation",
        "solar_radiation",
        "value",
        "concentration",
        "detection_limit",
    }

    date_fields = {
        "date",
        "posted_date",
        "inventory_year",
        "measurement_date",
        "weather_date",
        "start_date",
        "end_date",
    }

    integer_or_year_fields = {
        "inventory_year",
        "ipcc_tier",
        "ipcc_tier_1",
        "ipcc_tier_2",
        "ipcc_tier_3",
    }

    if canonical_name in numeric_fields:
        return "number"

    if canonical_name in date_fields:
        return "date"

    if canonical_name in integer_or_year_fields:
        return "number"

    if canonical_name == "coordinates":
        return "coordinates"

    return "string"


def _field_from_phrase(phrase: str) -> ExtractionField:
    normalized = _normalize_phrase(phrase)

    # Exact alias matching first.
    for canonical_name, aliases in _FIELD_ALIASES.items():
        if normalized in aliases:
            return ExtractionField(
                name=canonical_name,
                description=phrase.strip(),
                data_type=_infer_data_type(canonical_name),
            )

    # -----------------------------------------------------------------------
    # Intelligent phrase matching.
    #
    # This handles instructions such as:
    # "methane concentration in ppm"
    # "total scope 1 emissions"
    # "facility name"
    # "IPCC Tier 2 emission factor"
    # -----------------------------------------------------------------------

    pattern_rules: list[tuple[str, tuple[str, ...]]] = [
        (
            "methane_concentration",
            (
                "methane concentration",
                "ch4 concentration",
                "methane ppm",
                "ch4 ppm",
            ),
        ),
        (
            "methane_emissions",
            (
                "methane emissions",
                "methane emission",
                "ch4 emissions",
                "ch4 emission",
            ),
        ),
        (
            "emission_factor",
            (
                "emission factor",
                "emission factors",
            ),
        ),
        (
            "activity_data",
            (
                "activity data",
                "activity level",
            ),
        ),
        (
            "inventory",
            (
                "ghg inventory",
                "emissions inventory",
                "emission inventory",
                "greenhouse gas inventory",
            ),
        ),
        (
            "meteorological_data",
            (
                "meteorological data",
                "weather data",
                "meteorological information",
            ),
        ),
        (
            "scope_1",
            (
                "scope 1",
                "scope one",
            ),
        ),
        (
            "scope_2",
            (
                "scope 2",
                "scope two",
            ),
        ),
        (
            "scope_3",
            (
                "scope 3",
                "scope three",
            ),
        ),
        (
            "ipcc_tier",
            (
                "ipcc tier",
                "methodological tier",
            ),
        ),
        (
            "facility",
            (
                "facility",
                "plant",
                "installation",
                "site",
            ),
        ),
        (
            "temperature",
            (
                "temperature",
                "ambient temperature",
                "air temperature",
            ),
        ),
        (
            "humidity",
            (
                "humidity",
                "relative humidity",
            ),
        ),
        (
            "wind_speed",
            (
                "wind speed",
                "wind velocity",
            ),
        ),
        (
            "wind_direction",
            (
                "wind direction",
            ),
        ),
    ]

    for canonical_name, patterns in pattern_rules:
        if any(pattern in normalized for pattern in patterns):
            return ExtractionField(
                name=canonical_name,
                description=phrase.strip(),
                data_type=_infer_data_type(canonical_name),
            )

    # -----------------------------------------------------------------------
    # Support custom fields.
    # -----------------------------------------------------------------------

    safe_name = re.sub(
        r"[^a-z0-9]+",
        "_",
        normalized,
    ).strip("_")

    return ExtractionField(
        name=safe_name or "field",
        description=phrase.strip(),
        data_type="string",
    )


# ---------------------------------------------------------------------------
# Public planner
# ---------------------------------------------------------------------------

def build_extraction_plan(instruction: str) -> ExtractionPlan:
    """
    Convert a natural-language extraction instruction into
    a deterministic extraction plan.

    Examples:

        Extract the page title and headings

        Extract company, location and salary

        Extract latitude, longitude and address

        Extract methane concentration, facility and temperature

        Extract activity data, emission factor and inventory data

        Extract IPCC Tier 2, Scope 1, Scope 2 and Scope 3 emissions

    The planner intentionally avoids an external LLM dependency
    for this implementation.
    """

    normalized = _normalize_instruction(instruction)

    if not normalized:
        raise ValueError(
            "Extraction instruction cannot be empty."
        )

    # ---------------------------------------------------------------
    # Remove common introductory phrases.
    # ---------------------------------------------------------------

    cleaned = re.sub(
        r"^(please\s+)?"
        r"(extract|get|find|collect|retrieve|show|list|obtain)\s+",
        "",
        normalized,
        flags=re.IGNORECASE,
    )

    # ---------------------------------------------------------------
    # Remove phrases such as:
    #
    # "the following information:"
    # "the following data:"
    # "these fields:"
    # ---------------------------------------------------------------

    cleaned = re.sub(
        r"^(the\s+)?"
        r"(following\s+)?"
        r"(information|data|fields?)"
        r"\s*:?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # ---------------------------------------------------------------
    # Normalize common conjunctions.
    # ---------------------------------------------------------------

    cleaned = re.sub(
        r"\s+and\s+",
        ",",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Also allow "&".
    cleaned = re.sub(
        r"\s*&\s*",
        ",",
        cleaned,
    )

    # ---------------------------------------------------------------
    # Split requested fields.
    # ---------------------------------------------------------------

    phrases = [
        phrase.strip(" .;:")
        for phrase in re.split(r",|;", cleaned)
        if phrase.strip(" .;:")
    ]

    fields: list[ExtractionField] = []
    seen: set[str] = set()

    for phrase in phrases:
        field = _field_from_phrase(phrase)

        if not field.name:
            continue

        # Prevent duplicate fields.
        if field.name in seen:
            continue

        seen.add(field.name)
        fields.append(field)

    if not fields:
        raise ValueError(
            "Could not identify extraction fields."
        )

    return ExtractionPlan(
        instruction=normalized,
        fields=fields,
    )