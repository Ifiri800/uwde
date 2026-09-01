from backend.app.services.intelligence.methane.intelligence.hotspots import (
    identify_hotspots,
)


def test_hotspots_are_ranked():
    results = identify_hotspots(
        [
            ("a", 0.90),
            ("b", 0.80),
            ("c", 0.40),
        ]
    )

    assert len(results) == 2
    assert results[0].entity_id == "a"
    assert results[0].rank == 1
    assert results[1].rank == 2
