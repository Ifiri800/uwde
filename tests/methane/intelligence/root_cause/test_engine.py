from backend.app.services.intelligence.methane.intelligence.root_cause import (
    identify_root_cause,
)


def test_root_causes_are_ordered_by_signal_strength():
    result = identify_root_cause(
        {
            "equipment_failure": 0.90,
            "process_change": 0.50,
            "weather": 0.20,
        }
    )

    assert result[0] == "equipment_failure"
    assert len(result) == 3
