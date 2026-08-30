from backend.app.services.intelligence.ai.entities import (
    EntityRecognitionResult,
    RecognizedEntity,
    recognize_entities,
)


def test_empty_text_returns_no_entities():
    result = recognize_entities("")

    assert isinstance(result, EntityRecognitionResult)
    assert result.entities == ()
    assert result.entity_count == 0
    assert not result.has_entities


def test_company_is_recognized():
    result = recognize_entities(
        "Acme Energy Ltd expanded its operations."
    )

    assert result.has_entities

    organizations = [
        entity
        for entity in result.entities
        if entity.entity_type == "organization"
    ]

    assert len(organizations) == 1
    assert organizations[0].text == "Acme Energy Ltd"
    assert organizations[0].normalized_value == "Acme Energy Ltd"


def test_location_is_recognized():
    result = recognize_entities(
        "The company expanded into Nigeria and Lagos."
    )

    locations = [
        entity
        for entity in result.entities
        if entity.entity_type == "location"
    ]

    assert len(locations) == 2
    assert {entity.normalized_value for entity in locations} == {
        "Nigeria",
        "Lagos",
    }


def test_percentage_and_currency_are_recognized():
    result = recognize_entities(
        "Revenue increased by 15% to NGN 2,500,000."
    )

    assert any(
        entity.entity_type == "percentage"
        and entity.text == "15%"
        for entity in result.entities
    )

    assert any(
        entity.entity_type == "currency"
        and "NGN" in entity.text
        for entity in result.entities
    )


def test_date_is_recognized():
    result = recognize_entities(
        "The report was published on January 15, 2026."
    )

    dates = [
        entity
        for entity in result.entities
        if entity.entity_type == "date"
    ]

    assert len(dates) == 1
    assert dates[0].normalized_value == "January 15, 2026"


def test_entity_positions_are_valid():
    text = "Acme Energy Ltd entered Nigeria."
    result = recognize_entities(text)

    for entity in result.entities:
        assert text[entity.start:entity.end] == entity.text
        assert 0 <= entity.start <= entity.end <= len(text)


def test_recognition_is_deterministic():
    text = (
        "Acme Energy Ltd increased revenue by 15% in Nigeria "
        "on January 15, 2026."
    )

    first = recognize_entities(text)
    second = recognize_entities(text)

    assert first == second


def test_recognized_entity_validation():
    entity = RecognizedEntity(
        text="Nigeria",
        entity_type="location",
        normalized_value="Nigeria",
        confidence=0.95,
        start=0,
        end=7,
    )

    assert entity.entity_type == "location"
    assert entity.confidence == 0.95


def test_non_string_input_is_rejected():
    try:
        recognize_entities(None)
    except TypeError as exc:
        assert "text must be a string" in str(exc)
    else:
        raise AssertionError("Expected TypeError")
