from backend.app.services.intelligence.methane.inventory.models import (
    EmissionSource,
    EmissionSourceType,
)


def test_emission_source_types():
    assert EmissionSourceType.FUGITIVE.value == "fugitive"
    assert EmissionSourceType.VENTING.value == "venting"
    assert EmissionSourceType.FLARING.value == "flaring"
    assert EmissionSourceType.COMBUSTION.value == "combustion"
    assert EmissionSourceType.PROCESS.value == "process"
    assert EmissionSourceType.OTHER_METHANE.value == "other_methane"


def test_emission_source_requires_component():
    source = EmissionSource(
        id="src-1",
        name="Valve leak",
        source_type=EmissionSourceType.FUGITIVE,
        component_id="comp-1",
    )

    assert source.component_id == "comp-1"
    assert source.methane_relevant is True
