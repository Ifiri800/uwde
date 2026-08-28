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


_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
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
        "first paragraph",
        "first paragraphs",
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
    "latitude": ("latitude", "lat"),
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
    "date": ("date",),

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


def _normalize_instruction(instruction: str) -> str:
    return re.sub(r"\s+", " ", instruction).strip()


def _normalize_phrase(phrase: str) -> str:
    normalized = phrase.lower().strip()
    normalized = re.sub(r"^(the|a|an)\s+", "", normalized)
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

    if canonical_name in numeric_fields:
        return "number"

    if canonical_name in date_fields:
        return "date"

    if canonical_name in {
        "ipcc_tier",
        "ipcc_tier_1",
        "ipcc_tier_2",
        "ipcc_tier_3",
    }:
        return "number"

    if canonical_name == "coordinates":
        return "coordinates"

    return "string"


def _field_from_phrase(phrase: str) -> ExtractionField:
    normalized = _normalize_phrase(phrase)

    # Handle semantic aliases such as:
    # "page heading as title"
    # "first paragraph as description"
    # "website title as title"
    alias_rules = [
        (
            r"(?:page|website)\s+heading(?:s)?\s+as\s+title",
            "title",
        ),
        (
            r"heading(?:s)?\s+as\s+title",
            "title",
        ),
        (
            r"(?:page|website)\s+title\s+as\s+title",
            "title",
        ),
        (
            r"first\s+paragraph\s+as\s+description",
            "description",
        ),
        (
            r"paragraph\s+as\s+description",
            "description",
        ),
        (
            r"first\s+paragraph\s+as\s+description",
            "description",
        ),
    ]

    for pattern, canonical_name in alias_rules:
        if re.fullmatch(pattern, normalized):
            return ExtractionField(
                name=canonical_name,
                description=phrase.strip(),
                data_type=_infer_data_type(canonical_name),
            )

    for canonical_name, aliases in _FIELD_ALIASES.items():
        if normalized in aliases:
            return ExtractionField(
                name=canonical_name,
                description=phrase.strip(),
                data_type=_infer_data_type(canonical_name),
            )

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


def _split_instruction_fields(cleaned: str) -> list[str]:
    """
    Split extraction instructions while preserving semantic phrases.

    Example:
        page heading as title and first paragraph as description

    becomes:
        page heading as title
        first paragraph as description
    """

    # Split "and" when it introduces another extraction expression.
    parts = re.split(
        r"\s+(?:and|&)\s+",
        cleaned,
        flags=re.IGNORECASE,
    )

    phrases: list[str] = []

    for part in parts:
        # Commas and semicolons remain valid separators.
        for phrase in re.split(r",|;", part):
            phrase = phrase.strip(" .;:")
            if phrase:
                phrases.append(phrase)

    return phrases


def build_extraction_plan(instruction: str) -> ExtractionPlan:
    normalized = _normalize_instruction(instruction)

    if not normalized:
        raise ValueError(
            "Extraction instruction cannot be empty."
        )

    cleaned = re.sub(
        r"^(please\s+)?"
        r"(extract|get|find|collect|retrieve|show|list|obtain)\s+",
        "",
        normalized,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"^(the\s+)?"
        r"(following\s+)?"
        r"(information|data|fields?)"
        r"\s*:?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    phrases = _split_instruction_fields(cleaned)

    fields: list[ExtractionField] = []
    seen: set[str] = set()

    for phrase in phrases:
        field = _field_from_phrase(phrase)

        if not field.name:
            continue

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


