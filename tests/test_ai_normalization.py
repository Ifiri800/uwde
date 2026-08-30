from backend.app.services.intelligence.ai.entities import RecognizedEntity
from backend.app.services.intelligence.ai.normalization import (
    EntityNormalizationResult,
    NormalizedEntity,
    normalize_entities,
)


def test_empty_entities_returns_empty_result():
    result = normalize_entities(())

    assert isinstance(result, EntityNormalizationResult)
    assert result.entities == ()
    assert result.entity_count == 0
    assert not result.has_entities


def test_organization_is_normalized():
    entities = (
        RecognizedEntity(
            text="Acme Energy LTD",
            entity_type="organization",
            normalized_value="Acme Energy LTD",
            confidence=0.9,
        ),
    )

    result = normalize_entities(entities)

    assert result.entity_count == 1
    assert result.entities[0].canonical_value == "Acme Energy Ltd"


def test_equivalent_entities_are_merged():
    entities = (
        RecognizedEntity(
            text="Acme Energy Ltd",
            entity_type="organization",
            normalized_value="Acme Energy Ltd",
            confidence=0.9,
        ),
        RecognizedEntity(
            text="Acme Energy LTD",
            entity_type="organization",
            normalized_value="Acme Energy LTD",
            confidence=0.8,
        ),
    )

    result = normalize_entities(entities)

    assert result.entity_count == 1
    entity = result.entities[0]

    assert entity.canonical_value == "Acme Energy Ltd"
    assert entity.occurrences == 2
    assert set(entity.source_texts) == {
        "Acme Energy Ltd",
        "Acme Energy LTD",
    }


def test_location_is_canonicalized():
    entity = RecognizedEntity(
        text="nigeria",
        entity_type="location",
        normalized_value="nigeria",
        confidence=0.95,
    )

    result = normalize_entities((entity,))

    assert result.entities[0].canonical_value == "Nigeria"


def test_currency_is_canonicalized():
    entity = RecognizedEntity(
        text="NGN 2,500,000",
        entity_type="currency",
        normalized_value="NGN 2,500,000",
        confidence=0.9,
    )

    result = normalize_entities((entity,))

    assert result.entities[0].canonical_value == "NGN 2500000"


def test_percentage_is_canonicalized():
    entity = RecognizedEntity(
        text="15 %",
        entity_type="percentage",
        normalized_value="15 %",
        confidence=0.98,
    )

    result = normalize_entities((entity,))

    assert result.entities[0].canonical_value == "15%"


def test_confidence_is_averaged():
    entities = (
        RecognizedEntity(
            text="Nigeria",
            entity_type="location",
            normalized_value="Nigeria",
            confidence=0.8,
        ),
        RecognizedEntity(
            text="NIGERIA",
            entity_type="location",
            normalized_value="NIGERIA",
            confidence=1.0,
        ),
    )

    result = normalize_entities(entities)

    assert result.entities[0].confidence == 0.9


def test_result_is_deterministic():
    entity = RecognizedEntity(
        text="Lagos",
        entity_type="location",
        normalized_value="Lagos",
        confidence=0.95,
    )

    first = normalize_entities((entity,))
    second = normalize_entities((entity,))

    assert first == second


def test_normalized_entity_validation():
    entity = NormalizedEntity(
        entity_type="location",
        canonical_value="Nigeria",
    )

    assert entity.canonical_value == "Nigeria"
