from datetime import datetime, timezone

import pytest

from backend.app.services.intelligence.methane.quantification.top_down.gee.client import (
    GEEClient,
)
from backend.app.services.intelligence.methane.quantification.top_down.gee.collections import (
    SENTINEL5P_CH4_BAND,
    SENTINEL5P_CH4_COLLECTION,
    SENTINEL5P_CH4_UNCERTAINTY_BAND,
)
from backend.app.services.intelligence.methane.quantification.top_down.gee.sentinel5p import (
    Sentinel5PMethaneAdapter,
)


class FakeCollection:
    def __init__(self):
        self.date_args = None
        self.selected = None

    def filterDate(self, start, end):
        self.date_args = (start, end)
        return self

    def select(self, bands):
        self.selected = bands
        return self


class FakeEE:
    def __init__(self):
        self.collection = FakeCollection()

    def ImageCollection(self, collection_id):
        assert collection_id == SENTINEL5P_CH4_COLLECTION
        return self.collection


def make_adapter():
    fake_ee = FakeEE()
    client = GEEClient("test-project", ee_module=fake_ee)
    return Sentinel5PMethaneAdapter(client), fake_ee


def test_collection_uses_sentinel5p_ch4_dataset():
    adapter, fake_ee = make_adapter()

    result = adapter.collection()

    assert result is fake_ee.collection


def test_filter_date_applies_temporal_window():
    adapter, fake_ee = make_adapter()

    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 31, tzinfo=timezone.utc)

    result = adapter.filter_date(start, end)

    assert result is fake_ee.collection
    assert fake_ee.collection.date_args == (
        start.isoformat(),
        end.isoformat(),
    )


def test_invalid_date_window_is_rejected():
    adapter, _ = make_adapter()

    start = datetime(2026, 2, 1, tzinfo=timezone.utc)
    end = datetime(2026, 1, 1, tzinfo=timezone.utc)

    with pytest.raises(ValueError):
        adapter.filter_date(start, end)


def test_select_methane_band():
    adapter, fake_ee = make_adapter()

    result = adapter.select_methane(fake_ee.collection)

    assert result is fake_ee.collection
    assert fake_ee.collection.selected == SENTINEL5P_CH4_BAND


def test_select_methane_with_uncertainty():
    adapter, fake_ee = make_adapter()

    result = adapter.select_methane_with_uncertainty(
        fake_ee.collection
    )

    assert result is fake_ee.collection
    assert fake_ee.collection.selected == [
        SENTINEL5P_CH4_BAND,
        SENTINEL5P_CH4_UNCERTAINTY_BAND,
    ]


def test_metadata_contains_provenance():
    adapter, _ = make_adapter()

    metadata = adapter.metadata()

    assert metadata["platform"] == "Sentinel-5P"
    assert metadata["instrument"] == "TROPOMI"
    assert metadata["collection"] == SENTINEL5P_CH4_COLLECTION
    assert metadata["methane_band"] == SENTINEL5P_CH4_BAND
    assert metadata["uncertainty_band"] == SENTINEL5P_CH4_UNCERTAINTY_BAND


def test_normalize_observation():
    adapter, _ = make_adapter()

    observed_at = datetime(
        2026,
        1,
        15,
        tzinfo=timezone.utc,
    )

    observation = adapter.normalize_observation(
        observation_id="S5P-001",
        site_id="SITE-001",
        observed_at=observed_at,
        concentration=1850.0,
        unit="ppb",
        latitude=4.8156,
        longitude=7.0498,
        uncertainty=25.0,
    )

    assert observation.observation_id == "S5P-001"
    assert observation.site_id == "SITE-001"
    assert observation.observed_at == observed_at
    assert observation.concentration == 1850.0
    assert observation.unit == "ppb"
    assert observation.satellite == "Sentinel-5P"
    assert observation.product == SENTINEL5P_CH4_COLLECTION
    assert observation.latitude == 4.8156
    assert observation.longitude == 7.0498
    assert observation.uncertainty == 25.0


def test_normalized_observation_contains_provenance():
    adapter, _ = make_adapter()

    observation = adapter.normalize_observation(
        observation_id="S5P-002",
        site_id="SITE-002",
        observed_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        concentration=1800.0,
        unit="ppb",
    )

    assert observation.metadata["platform"] == "Sentinel-5P"
    assert observation.metadata["instrument"] == "TROPOMI"
    assert observation.metadata["provider"] == "EU/ESA/Copernicus"


def test_zero_concentration_can_be_normalized():
    adapter, _ = make_adapter()

    observation = adapter.normalize_observation(
        observation_id="S5P-003",
        site_id="SITE-003",
        observed_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        concentration=0.0,
        unit="ppb",
    )

    assert observation.concentration == 0.0


def test_optional_coordinates_can_be_omitted():
    adapter, _ = make_adapter()

    observation = adapter.normalize_observation(
        observation_id="S5P-004",
        site_id="SITE-004",
        observed_at=datetime(
            2026,
            1,
            1,
            tzinfo=timezone.utc,
        ),
        concentration=1900.0,
        unit="ppb",
    )

    assert observation.latitude is None
    assert observation.longitude is None
    assert observation.uncertainty is None
