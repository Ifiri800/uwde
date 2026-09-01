import pytest

from backend.app.services.intelligence.methane.quantification.bottom_up.ipcc import (
    IPCCMethod,
    IPCCMethodology,
    create_ipcc_methodology,
    validate_ipcc_methodology,
)


def test_tier_1_methodology():
    methodology = create_ipcc_methodology(
        IPCCMethod.TIER_1,
        "IPCC Tier 1",
    )

    assert methodology.method == IPCCMethod.TIER_1
    assert methodology.name == "IPCC Tier 1"


def test_tier_2_methodology():
    methodology = create_ipcc_methodology(
        IPCCMethod.TIER_2,
        "IPCC Tier 2",
    )

    assert methodology.method == IPCCMethod.TIER_2


def test_tier_3_methodology():
    methodology = create_ipcc_methodology(
        IPCCMethod.TIER_3,
        "IPCC Tier 3",
    )

    assert methodology.method == IPCCMethod.TIER_3


def test_description_is_preserved():
    methodology = create_ipcc_methodology(
        IPCCMethod.TIER_2,
        "IPCC Tier 2",
        "Detailed source-specific methodology.",
    )

    assert methodology.description == (
        "Detailed source-specific methodology."
    )


def test_valid_methodology_is_returned():
    methodology = IPCCMethodology(
        method=IPCCMethod.TIER_1,
        name="Default methodology",
    )

    assert validate_ipcc_methodology(methodology) == methodology


def test_missing_name_is_rejected():
    methodology = IPCCMethodology(
        method=IPCCMethod.TIER_1,
        name="",
    )

    with pytest.raises(ValueError):
        validate_ipcc_methodology(methodology)


def test_invalid_methodology_object_is_rejected():
    with pytest.raises(ValueError):
        validate_ipcc_methodology("invalid")
