from backend.app.services.intelligence.methane.intelligence.ranking import (
    rank_assets,
)


def test_assets_are_ranked_descending():
    results = rank_assets(
        [
            ("asset-b", 0.70),
            ("asset-a", 0.90),
        ]
    )

    assert results[0].entity_id == "asset-a"
    assert results[0].rank == 1
    assert results[1].rank == 2
