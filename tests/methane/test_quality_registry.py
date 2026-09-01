from backend.app.services.intelligence.methane.quality.models import (
    QualityAssessment,
    QualityDimension,
    QualityStatus,
)
from backend.app.services.intelligence.methane.quality.registry import (
    QualityRegistry,
    RegistryError,
)


def assessment(
    dimension=QualityDimension.ACCURACY,
    score=90.0,
):
    return QualityAssessment(
        dimension=dimension,
        status=QualityStatus.PASS,
        score=score,
    )


def test_registry_starts_empty():
    registry = QualityRegistry()

    assert registry.count() == 0
    assert registry.list_assessments() == ()


def test_register_assessment():
    registry = QualityRegistry()

    item = assessment()

    result = registry.register(item)

    assert result is item
    assert registry.count() == 1
    assert registry.get(
        QualityDimension.ACCURACY
    ) is item


def test_duplicate_dimension_is_rejected():
    registry = QualityRegistry()

    registry.register(assessment())

    try:
        registry.register(assessment())
    except RegistryError as exc:
        assert "already registered" in str(exc).lower()
    else:
        raise AssertionError(
            "duplicate dimension should raise RegistryError"
        )


def test_get_missing_dimension_is_rejected():
    registry = QualityRegistry()

    try:
        registry.get(QualityDimension.ACCURACY)
    except RegistryError:
        pass
    else:
        raise AssertionError(
            "missing dimension should raise RegistryError"
        )


def test_unregister_returns_assessment():
    registry = QualityRegistry()

    item = assessment()

    registry.register(item)

    removed = registry.unregister(
        QualityDimension.ACCURACY
    )

    assert removed is item
    assert registry.count() == 0


def test_unregister_missing_dimension_is_rejected():
    registry = QualityRegistry()

    try:
        registry.unregister(
            QualityDimension.ACCURACY
        )
    except RegistryError:
        pass
    else:
        raise AssertionError(
            "missing dimension should raise RegistryError"
        )


def test_contains_dimension():
    registry = QualityRegistry()

    assert not registry.contains(
        QualityDimension.ACCURACY
    )

    registry.register(assessment())

    assert registry.contains(
        QualityDimension.ACCURACY
    )


def test_list_assessments_preserves_registration_order():
    registry = QualityRegistry()

    first = assessment(
        QualityDimension.COMPLETENESS,
        95.0,
    )
    second = assessment(
        QualityDimension.ACCURACY,
        85.0,
    )

    registry.register(first)
    registry.register(second)

    assert registry.list_assessments() == (
        first,
        second,
    )


def test_invalid_assessment_is_rejected():
    registry = QualityRegistry()

    try:
        registry.register("invalid")
    except TypeError:
        pass
    else:
        raise AssertionError(
            "invalid assessment should raise TypeError"
        )


def test_invalid_dimension_is_rejected():
    registry = QualityRegistry()

    try:
        registry.get("accuracy")
    except TypeError:
        pass
    else:
        raise AssertionError(
            "invalid dimension should raise TypeError"
        )


def test_clear_removes_all_assessments():
    registry = QualityRegistry()

    registry.register(
        assessment(
            QualityDimension.ACCURACY
        )
    )
    registry.register(
        assessment(
            QualityDimension.COMPLETENESS
        )
    )

    registry.clear()

    assert registry.count() == 0
    assert registry.list_assessments() == ()
