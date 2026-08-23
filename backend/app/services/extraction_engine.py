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


_FIELD_ALIASES = {
    # General website fields
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

    # Geographic fields
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

    # Common structured data fields
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
}


def _normalize_instruction(instruction: str) -> str:
    return re.sub(r"\s+", " ", instruction).strip()


def _field_from_phrase(phrase: str) -> ExtractionField:
    normalized = phrase.lower().strip()

    # Remove common articles.
    normalized = re.sub(
        r"^(the|a|an)\s+",
        "",
        normalized,
    )

    for canonical_name, aliases in _FIELD_ALIASES.items():
        if normalized in aliases:
            data_type = "string"

            if canonical_name == "salary":
                data_type = "number"

            elif canonical_name in (
                "date",
                "posted_date",
            ):
                data_type = "date"

            elif canonical_name in (
                "latitude",
                "longitude",
            ):
                data_type = "number"

            elif canonical_name == "coordinates":
                data_type = "coordinates"

            return ExtractionField(
                name=canonical_name,
                description=phrase.strip(),
                data_type=data_type,
            )

    # Support unknown/custom fields.
    safe_name = re.sub(
        r"[^a-z0-9]+",
        "_",
        normalized,
    ).strip("_")

    return ExtractionField(
        name=safe_name or "field",
        description=phrase.strip(),
    )


def build_extraction_plan(instruction: str) -> ExtractionPlan:
    """
    Convert a natural-language extraction instruction
    into a deterministic extraction plan.

    Examples:

        Extract the page title and headings

        Extract company, location and salary

        Extract latitude, longitude and address

        Extract coordinates and website URL

    The planner intentionally avoids an external LLM
    dependency for this first implementation.
    """

    normalized = _normalize_instruction(instruction)

    if not normalized:
        raise ValueError(
            "Extraction instruction cannot be empty."
        )

    # Remove common introductory phrases.
    cleaned = re.sub(
        r"^(please\s+)?"
        r"(extract|get|find|collect|retrieve)\s+",
        "",
        normalized,
        flags=re.IGNORECASE,
    )

    # Remove phrases such as:
    # "the following information:"
    # "the following data:"
    # "these fields:"
    cleaned = re.sub(
        r"^(the\s+)?"
        r"(following\s+)?"
        r"(information|data|fields?)"
        r"\s*:?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Convert conjunctions to separators.
    cleaned = re.sub(
        r"\s+and\s+",
        ",",
        cleaned,
        flags=re.IGNORECASE,
    )

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