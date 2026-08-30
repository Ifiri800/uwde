from backend.app.services.intelligence.ai.semantic import (
    SemanticAnalysis,
    SemanticConcept,
    analyze_semantics,
)


def test_empty_text_returns_empty_analysis():
    result = analyze_semantics("")

    assert isinstance(result, SemanticAnalysis)
    assert result.topics == ()
    assert result.concepts == ()
    assert result.intents == ()
    assert result.sentiment == "neutral"
    assert result.confidence == 0.0


def test_market_competitive_semantics_are_detected():
    result = analyze_semantics(
        "The competitor entered the market and increased pricing."
    )

    assert "market" in result.topics
    assert "competition" in result.topics
    assert "competitive activity" in {
        concept.name for concept in result.concepts
    }
    assert "pricing" in {
        concept.name for concept in result.concepts
    }
    assert "competitive_analysis" in result.intents


def test_forecast_and_opportunity_intents_are_detected():
    result = analyze_semantics(
        "Future growth creates an opportunity for investment."
    )

    assert "forecasting" in result.topics
    assert "opportunity_identification" in result.intents
    assert "forecast" in result.intents
    assert result.sentiment == "positive"


def test_risk_semantics_are_detected():
    result = analyze_semantics(
        "The market faces a significant competitive threat and risk."
    )

    assert "risk" in result.topics
    assert "risk_assessment" in result.intents
    assert result.sentiment == "negative"


def test_mixed_sentiment_is_detected():
    result = analyze_semantics(
        "Market growth is positive, but the competitor creates a serious risk."
    )

    assert result.sentiment == "mixed"


def test_semantic_concept_validation():
    concept = SemanticConcept(
        name="market",
        category="market",
        confidence=0.9,
    )

    assert concept.name == "market"
    assert concept.category == "market"
    assert concept.confidence == 0.9


def test_non_string_input_is_rejected():
    try:
        analyze_semantics(None)
    except TypeError as exc:
        assert "text must be a string" in str(exc)
    else:
        raise AssertionError("Expected TypeError")
