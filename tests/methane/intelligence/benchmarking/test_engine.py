from backend.app.services.intelligence.methane.intelligence.benchmarking import (
    benchmark_facilities,
)


def test_facility_benchmark_is_calculated():
    results = benchmark_facilities(
        [
            ("facility-a", 10.0),
            ("facility-b", 20.0),
        ]
    )

    assert len(results) == 2
    assert results[0].metadata["peer_mean"] == 15.0
