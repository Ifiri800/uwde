from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class LLMRequest:
    """Provider-independent request sent to an external LLM."""

    prompt: str
    system_prompt: str = ""
    model: str = ""
    temperature: float = 0.0
    max_tokens: int | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("prompt is required")

        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")

        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")


@dataclass(frozen=True)
class LLMResponse:
    """Provider-independent response returned by an external LLM."""

    content: str
    model: str = ""
    provider: str = ""
    confidence: float = 0.0
    usage: Mapping[str, Any] | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("content is required")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


class LLMProvider(Protocol):
    """Contract implemented by external LLM providers."""

    @property
    def name(self) -> str:
        ...

    def generate(self, request: LLMRequest) -> LLMResponse:
        ...
