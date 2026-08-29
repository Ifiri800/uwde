from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from typing import Any

from backend.app.services.api.errors import (
    APIResponseError,
)
from backend.app.services.api.models import (
    APIResponse,
)


JSON_CONTENT_TYPES = {
    "application/json",
    "application/problem+json",
}

XML_CONTENT_TYPES = {
    "application/xml",
    "text/xml",
}


def _base_content_type(content_type: str) -> str:
    return content_type.split(";", 1)[0].strip().lower()


def _xml_to_dict(element: ET.Element) -> Any:
    children = list(element)

    if not children:
        return element.text or ""

    result: dict[str, Any] = {}

    for child in children:
        value = _xml_to_dict(child)

        if child.tag in result:
            existing = result[child.tag]

            if not isinstance(existing, list):
                result[child.tag] = [existing]

            result[child.tag].append(value)
        else:
            result[child.tag] = value

    if element.attrib:
        result["@attributes"] = dict(element.attrib)

    return result


def parse_api_response(
    response: APIResponse,
) -> Any:
    """
    Parse an API response according to its content type.

    Supported formats:
    - JSON
    - JSON-compatible media types
    - XML
    - plain text
    """

    content_type = _base_content_type(
        response.content_type
    )

    try:
        text = response.body.decode(
            "utf-8",
            errors="replace",
        )
    except Exception as exc:
        raise APIResponseError(
            "Unable to decode API response."
        ) from exc

    if not text.strip():
        return None

    if (
        content_type in JSON_CONTENT_TYPES
        or content_type.endswith("+json")
    ):
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise APIResponseError(
                "API returned invalid JSON."
            ) from exc

    if (
        content_type in XML_CONTENT_TYPES
        or content_type.endswith("+xml")
    ):
        try:
            root = ET.fromstring(text)
        except ET.ParseError as exc:
            raise APIResponseError(
                "API returned invalid XML."
            ) from exc

        return {
            root.tag: _xml_to_dict(root)
        }

    if content_type == "text/plain":
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    raise APIResponseError(
        "Unsupported API response content type: "
        f"{content_type or 'unknown'}"
    )


__all__ = [
    "JSON_CONTENT_TYPES",
    "XML_CONTENT_TYPES",
    "parse_api_response",
]
