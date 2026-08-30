from backend.app.services.intelligence.ai.provider import LLMRequest, LLMResponse
from backend.app.services.intelligence.ai.providers import (
    DeterministicLLMProvider,
    get_default_provider,
)


def test_provider_name():
    provider = DeterministicLLMProvider()

    assert provider.name == "deterministic"


def test_provider_generates_response():
    provider = DeterministicLLMProvider()

    response = provider.generate(
        LLMRequest(prompt="Analyze market intelligence.")
    )

    assert isinstance(response, LLMResponse)
    assert response.content
    assert response.provider == "deterministic"


def test_provider_uses_requested_model():
    provider = DeterministicLLMProvider()

    response = provider.generate(
        LLMRequest(
            prompt="Analyze.",
            model="test-model",
        )
    )

    assert response.model == "test-model"


def test_provider_uses_default_model():
    provider = DeterministicLLMProvider()

    response = provider.generate(
        LLMRequest(prompt="Analyze.")
    )

    assert response.model == "deterministic"


def test_provider_response_is_confidently_bounded():
    provider = DeterministicLLMProvider()

    response = provider.generate(
        LLMRequest(prompt="Analyze.")
    )

    assert 0.0 <= response.confidence <= 1.0


def test_provider_marks_response_as_deterministic():
    provider = DeterministicLLMProvider()

    response = provider.generate(
        LLMRequest(prompt="Analyze.")
    )

    assert response.metadata["deterministic"] is True
    assert response.metadata["mode"] == "offline"


def test_provider_is_deterministic():
    provider = DeterministicLLMProvider()
    request = LLMRequest(prompt="Analyze market intelligence.")

    first = provider.generate(request)
    second = provider.generate(request)

    assert first == second


def test_invalid_request_type_is_rejected():
    provider = DeterministicLLMProvider()

    try:
        provider.generate("Analyze.")
    except TypeError as exc:
        assert "request must be an LLMRequest" in str(exc)


def test_default_provider_is_available():
    provider = get_default_provider()

    assert isinstance(provider, DeterministicLLMProvider)
    assert provider.name == "deterministic"


def test_default_provider_generates_response():
    provider = get_default_provider()

    response = provider.generate(
        LLMRequest(prompt="Analyze intelligence.")
    )

    assert response.provider == "deterministic"
    assert response.content
