from __future__ import annotations

from .provider import LLMProvider, LLMRequest, LLMResponse


class DeterministicLLMProvider:
    """
    Offline provider implementation for development and testing.

    It implements the same provider contract as an external LLM adapter,
    allowing the UWDE AI layer to operate without network access or API keys.
    """

    @property
    def name(self) -> str:
        return "deterministic"

    def generate(self, request: LLMRequest) -> LLMResponse:
        if not isinstance(request, LLMRequest):
            raise TypeError("request must be an LLMRequest")

        content = (
            "Deterministic provider response for intelligence analysis."
        )

        return LLMResponse(
            content=content,
            model=request.model or "deterministic",
            provider=self.name,
            confidence=0.50,
            metadata={
                "mode": "offline",
                "deterministic": True,
            },
        )


def get_default_provider() -> LLMProvider:
    """Return the provider used by default for offline-safe operation."""

    return DeterministicLLMProvider()
