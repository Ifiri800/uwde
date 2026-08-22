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
    "title": ("title", "job title", "position", "role"),
    "company": ("company", "employer", "organization", "organisation"),
    "location": ("location", "city", "address"),
    "salary": ("salary", "pay", "compensation", "wage"),
    "description": ("description", "job description", "details"),
    "application_url": (
        "application url",
        "application link",
        "apply url",
        "apply link",
        "application",
    ),
    "url": ("url", "link", "website"),
    "email": ("email", "email address"),
    "phone": ("phone", "phone number", "telephone"),
    "date": ("date", "posted date", "publication date"),
}


def _normalize_instruction(instruction: str) -> str:
    return re.sub(r"\s+", " ", instruction).strip()


def _field_from_phrase(phrase: str) -> ExtractionField:
    normalized = phrase.lower().strip()

    # Remove common articles from field descriptions.
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
            elif canonical_name == "date":
                data_type = "date"

            return ExtractionField(
                name=canonical_name,
                description=phrase.strip(),
                data_type=data_type,
            )

    safe_name = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_")

    return ExtractionField(
        name=safe_name or "field",
        description=phrase.strip(),
    )


def build_extraction_plan(instruction: str) -> ExtractionPlan:
    """
    Convert a natural-language extraction instruction into a basic
    deterministic extraction plan.

    This first version intentionally avoids an external LLM dependency.
    It provides predictable behavior that can later be replaced or
    augmented by an AI planning layer.
    """

    normalized = _normalize_instruction(instruction)

    if not normalized:
        raise ValueError("Extraction instruction cannot be empty.")

    # Remove common introductory phrases.
    cleaned = re.sub(
        r"^(please\s+)?(extract|get|find|collect|retrieve)\s+",
        "",
        normalized,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"^(the\s+)?(following\s+)?(information|data|fields?)\s*:?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Normalize conjunctions before splitting.
    cleaned = re.sub(r"\s+and\s+", ",", cleaned, flags=re.IGNORECASE)

    phrases = [
        phrase.strip(" .;:")
        for phrase in re.split(r",|;", cleaned)
        if phrase.strip(" .;:")
    ]

    fields: list[ExtractionField] = []

    for phrase in phrases:
        field = _field_from_phrase(phrase)

        if not field.name:
            continue

        if not any(existing.name == field.name for existing in fields):
            fields.append(field)

    if not fields:
        raise ValueError("Could not identify extraction fields.")

    return ExtractionPlan(
        instruction=normalized,
        fields=fields,
    )