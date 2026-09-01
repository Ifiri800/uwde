from backend.app.services.intelligence.methane.quantification.bottom_up.factors import (
    EmissionFactor,
    validate_emission_factor,
)


def test_valid_emission_factor():
    factor = EmissionFactor(
        factor_id="EF-001",
        value=0.25,
        unit="kg_ch4/unit",
        source="IPCC",
        methodology="default",
        tier="Tier 1",
    )

    assert validate_emission_factor(factor) == factor


def test_factor_accepts_zero():
    factor = EmissionFactor(
        factor_id="EF-002",
        value=0.0,
        unit="kg_ch4/unit",
        source="IPCC",
    )

    assert validate_emission_factor(factor) == factor


def test_factor_rejects_negative_value():
    factor = EmissionFactor(
        factor_id="EF-003",
        value=-0.1,
        unit="kg_ch4/unit",
        source="IPCC",
    )

    try:
        validate_emission_factor(factor)
        assert False
    except ValueError:
        pass


def test_factor_rejects_missing_unit():
    factor = EmissionFactor(
        factor_id="EF-004",
        value=0.1,
        unit="",
        source="IPCC",
    )

    try:
        validate_emission_factor(factor)
        assert False
    except ValueError:
        pass


def test_factor_rejects_missing_source():
    factor = EmissionFactor(
        factor_id="EF-005",
        value=0.1,
        unit="kg_ch4/unit",
        source="",
    )

    try:
        validate_emission_factor(factor)
        assert False
    except ValueError:
        pass


def test_factor_accepts_uncertainty():
    factor = EmissionFactor(
        factor_id="EF-006",
        value=0.1,
        unit="kg_ch4/unit",
        source="IPCC",
        uncertainty=0.02,
    )

    assert validate_emission_factor(factor).uncertainty == 0.02


def test_factor_rejects_negative_uncertainty():
    factor = EmissionFactor(
        factor_id="EF-007",
        value=0.1,
        unit="kg_ch4/unit",
        source="IPCC",
        uncertainty=-0.01,
    )

    try:
        validate_emission_factor(factor)
        assert False
    except ValueError:
        pass
