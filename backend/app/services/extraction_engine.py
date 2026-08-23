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
    "title": (
        "title",
        "job title",
        "position",
        "role",
    ),
    "company": (
        "company",
        "company name",
        "employer",
        "organization",
        "organisation",
        "organization name",
        "organisation name",
    ),
    "location": (
        "location",
        "job location",
        "city",
        "address",
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
        "link",
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
    """Normalize whitespace in the user's instruction."""
    return re.sub(r"\s+", " ", instruction).strip()


def _field_from_phrase(phrase: str) -> ExtractionField:
    """
    Convert a natural-language field phrase into an extraction field.
    """

    original_phrase = phrase.strip()

    normalized = original_phrase.lower().strip()

    # Remove common articles.
    normalized = re.sub(
        r"^(the|a|an)\s+",
        "",
        normalized,
    )

    # Normalize internal whitespace.
    normalized = re.sub(r"\s+", " ", normalized)

    # Check known aliases.
    for canonical_name, aliases in _FIELD_ALIASES.items():
        if normalized in aliases:
            data_type = "string"

            if canonical_name == "salary":
                data_type = "number"

            elif canonical_name in {
                "date",
                "posted_date",
            }:
                data_type = "date"

            return ExtractionField(
                name=canonical_name,
                description=original_phrase,
                data_type=data_type,
            )

    # Fall back to a safe field name for custom fields.
    safe_name = re.sub(
        r"[^a-z0-9]+",
        "_",
        normalized,
    ).strip("_")

    if not safe_name:
        safe_name = "field"

    return ExtractionField(
        name=safe_name,
        description=original_phrase,
        data_type="string",
    )


def _split_field_phrases(text: str) -> list[str]:
    """
    Split a natural-language list of requested fields.

    Supports examples such as:

        title, company, location

        title and company and location

        title, company and location

        title; company; location
    """

    # Normalize semicolons to commas.
    text = re.sub(r"\s*;\s*", ",", text)

    # Convert common conjunctions to commas.
    text = re.sub(
        r"\s+(?:and|&)\s+",
        ",",
        text,
        flags=re.IGNORECASE,
    )

    phrases = []

    for phrase in text.split(","):
        cleaned = phrase.strip(" .;:")

        if cleaned:
            phrases.append(cleaned)

    return phrases


def build_extraction_plan(instruction: str) -> ExtractionPlan:
    """
    Convert a natural-language extraction instruction into a
    deterministic extraction plan.

    Examples:

        Extract job title, company and location

        Extract the title and headings

        Get company name, salary and application URL

        Extract title, description and posted date

    The planner intentionally does not require an external AI service.
    """

    normalized = _normalize_instruction(instruction)

    if not normalized:
        raise ValueError(
            "Extraction instruction cannot be empty."
        )

    cleaned = normalized

    # Remove common introductory phrases.
    cleaned = re.sub(
        r"^(please\s+)?"
        r"(extract|get|find|collect|retrieve|"
        r"scrape|return|show)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove phrases such as:
    #
    # "the following information"
    # "the following data"
    # "the following fields"
    cleaned = re.sub(
        r"^(the\s+)?"
        r"(following\s+)?"
        r"(information|data|fields?)"
        r"\s*:?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Remove a leading "from every..." clause only when it
    # introduces the website/listing context rather than fields.
    cleaned = re.sub(
        r"^(from|for)\s+"
        r"(every|each|all)\s+"
        r"(listing|listings|record|records|item|items|"
        r"result|results)\s*[:,]?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    phrases = _split_field_phrases(cleaned)

    if not phrases:
        raise ValueError(
            "Could not identify extraction fields."
        )

    fields: list[ExtractionField] = []

    for phrase in phrases:
        field = _field_from_phrase(phrase)

        if not field.name:
            continue

        fields.append(field)

    if not fields:
        raise ValueError(
            "Could not identify extraction fields."
        )

    # Remove duplicate fields while preserving order.
    unique_fields: list[ExtractionField] = []
    seen_names: set[str] = set()

    for field in fields:
        if field.name in seen_names:
            continue

        seen_names.add(field.name)
        unique_fields.append(field)

    return ExtractionPlan(
        instruction=normalized,
        fields=unique_fields,
    )