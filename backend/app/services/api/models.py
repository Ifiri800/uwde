from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class APIRequest:
    """Normalized request definition for API acquisition."""

    url: str
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    body: Any | None = None
    timeout_seconds: float = 15.0

    def __post_init__(self) -> None:
        if not self.url.strip():
            raise ValueError("url must not be empty")

        if self.method.upper() not in {
            "GET",
            "POST",
            "PUT",
            "PATCH",
            "DELETE",
        }:
            raise ValueError(
                f"Unsupported HTTP method: {self.method}"
            )

        if self.timeout_seconds <= 0:
            raise ValueError(
                "timeout_seconds must be greater than zero"
            )


@dataclass(frozen=True)
class APIResponse:
    """Normalized API response."""

    url: str
    final_url: str
    status_code: int
    content_type: str
    headers: dict[str, str]
    body: bytes

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


@dataclass
class APIAcquisitionResult:
    """Serializable result returned by API acquisition."""

    status: str
    url: str
    final_url: str = ""
    status_code: int = 0
    content_type: str = ""
    records: list[dict[str, Any]] = field(
        default_factory=list
    )
    data: Any | None = None
    errors: list[str] = field(
        default_factory=list
    )
    pages_crawled: int = 0

    @property
    def record_count(self) -> int:
        return len(self.records)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "url": self.url,
            "final_url": self.final_url,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "records": self.records,
            "record_count": self.record_count,
            "data": self.data,
            "errors": self.errors,
            "pages_crawled": self.pages_crawled,
        }
