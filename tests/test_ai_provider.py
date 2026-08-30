from backend.app.services.intelligence.ai.provider import (
    LLMProvider,
    LLMRequest,
    LLMResponse,
)


def test_llm_request_defaults():
    request = LLMRequest(prompt="Analyze this intelligence.")

    assert request.prompt == "Analyze this intelligence."
    assert request.temperature == 0.0
    assert request.model == ""


def test_llm_request_accepts_configuration():
    request = LLMRequest(
        prompt="Analyze this intelligence.",
        system_prompt="You are an intelligence analyst.",
        model="test-model",
        temperature=0.2,
        max_tokens=500,
    )

    assert request.system_prompt
    assert request.model == "test-model"
    assert request.temperature == 0.2
    assert request.max_tokens == 500


def test_llm_request_rejects_empty_prompt():
    try:
        LLMRequest(prompt="")
    except ValueError as exc:
        assert "prompt is required" in str(exc)


def test_llm_request_rejects_invalid_temperature():
    try:
        LLMRequest(prompt="Analyze.", temperature=3.0)
    except ValueError as exc:
        assert "temperature" in str(exc)


def test_llm_request_rejects_invalid_max_tokens():
    try:
        LLMRequest(prompt="Analyze.", max_tokens=0)
    except ValueError as exc:
        assert "max_tokens" in str(exc)


def test_llm_response_defaults():
    response = LLMResponse(content="Analysis complete.")

    assert response.content == "Analysis complete."
    assert response.confidence == 0.0


def test_llm_response_accepts_provider_metadata():
    response = LLMResponse(
        content="Analysis complete.",
        model="test-model",
        provider="test",
        confidence=0.9,
        usage={"input_tokens": 10, "output_tokens": 20},
    )

    assert response.provider == "test"
    assert response.confidence == 0.9
    assert response.usage["input_tokens"] == 10


def test_llm_response_rejects_empty_content():
    try:
        LLMResponse(content="")
    except ValueError as exc:
        assert "content is required" in str(exc)


def test_llm_response_rejects_invalid_confidence():
    try:
        LLMResponse(content="Analysis", confidence=1.5)
    except ValueError as exc:
        assert "confidence" in str(exc)


def test_provider_protocol_exposes_generate_contract():
    assert hasattr(LLMProvider, "generate")
