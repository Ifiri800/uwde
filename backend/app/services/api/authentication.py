from __future__ import annotations

import base64
from dataclasses import dataclass, field
from enum import Enum


class APIAuthType(str, Enum):
    NONE = "none"
    API_KEY_HEADER = "api_key_header"
    API_KEY_QUERY = "api_key_query"
    BEARER = "bearer"
    BASIC = "basic"
    CUSTOM_HEADERS = "custom_headers"


@dataclass(frozen=True)
class APIAuthentication:
    """
    Authentication configuration for an API request.

    Secrets are intentionally excluded from serialization,
    logging, and representations.
    """

    auth_type: APIAuthType = APIAuthType.NONE
    api_key: str | None = None
    token: str | None = None
    username: str | None = None
    password: str | None = None
    key_name: str = "X-API-Key"
    custom_headers: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.auth_type == APIAuthType.API_KEY_HEADER:
            if not self.api_key:
                raise ValueError(
                    "api_key is required for API key header authentication."
                )

            if not self.key_name.strip():
                raise ValueError(
                    "key_name must not be empty."
                )

        elif self.auth_type == APIAuthType.API_KEY_QUERY:
            if not self.api_key:
                raise ValueError(
                    "api_key is required for API key query authentication."
                )

            if not self.key_name.strip():
                raise ValueError(
                    "key_name must not be empty."
                )

        elif self.auth_type == APIAuthType.BEARER:
            if not self.token:
                raise ValueError(
                    "token is required for bearer authentication."
                )

        elif self.auth_type == APIAuthType.BASIC:
            if self.username is None:
                raise ValueError(
                    "username is required for basic authentication."
                )

            if self.password is None:
                raise ValueError(
                    "password is required for basic authentication."
                )

        elif self.auth_type == APIAuthType.CUSTOM_HEADERS:
            if not self.custom_headers:
                raise ValueError(
                    "custom_headers must not be empty."
                )

    def apply(
        self,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> tuple[dict[str, str], dict[str, object]]:
        """
        Apply authentication credentials to request headers
        and/or query parameters.

        Returns new dictionaries and does not mutate the inputs.
        """

        result_headers = dict(headers or {})
        result_params = dict(params or {})

        if self.auth_type == APIAuthType.NONE:
            return result_headers, result_params

        if self.auth_type == APIAuthType.API_KEY_HEADER:
            result_headers[self.key_name] = str(self.api_key)

        elif self.auth_type == APIAuthType.API_KEY_QUERY:
            result_params[self.key_name] = str(self.api_key)

        elif self.auth_type == APIAuthType.BEARER:
            result_headers["Authorization"] = (
                f"Bearer {self.token}"
            )

        elif self.auth_type == APIAuthType.BASIC:
            credentials = (
                f"{self.username}:{self.password}"
            )

            encoded = base64.b64encode(
                credentials.encode("utf-8")
            ).decode("ascii")

            result_headers["Authorization"] = (
                f"Basic {encoded}"
            )

        elif self.auth_type == APIAuthType.CUSTOM_HEADERS:
            result_headers.update(
                self.custom_headers
            )

        return result_headers, result_params

    def safe_dict(self) -> dict[str, object]:
        """
        Return a serialization-safe representation.

        Authentication secrets are never returned.
        """

        return {
            "auth_type": self.auth_type.value,
            "key_name": self.key_name,
            "has_api_key": bool(self.api_key),
            "has_token": bool(self.token),
            "has_username": bool(self.username),
            "has_password": bool(self.password),
            "custom_header_names": sorted(
                self.custom_headers.keys()
            ),
        }


__all__ = [
    "APIAuthType",
    "APIAuthentication",
]
