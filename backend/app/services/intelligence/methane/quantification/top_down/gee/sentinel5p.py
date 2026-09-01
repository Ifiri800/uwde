from __future__ import annotations

from datetime import datetime

from ..satellite import SatelliteObservation
from .client import GEEClient
from .collections import (
    SENTINEL5P_CH4_COLLECTION,
    SENTINEL5P_CH4_BAND,
    SENTINEL5P_CH4_UNCERTAINTY_BAND,
    SENTINEL5P_PLATFORM,
    SENTINEL5P_INSTRUMENT,
    SENTINEL5P_PROVIDER,
)
from .errors import GEEDatasetError


class Sentinel5PMethaneAdapter:
    """
    Earth Engine adapter for Sentinel-5P/TROPOMI methane data.
    """

    collection_id = SENTINEL5P_CH4_COLLECTION
    methane_band = SENTINEL5P_CH4_BAND
    uncertainty_band = SENTINEL5P_CH4_UNCERTAINTY_BAND

    def __init__(self, client: GEEClient):
        self.client = client

    def collection(self):
        """
        Return the Sentinel-5P methane ImageCollection.
        """
        try:
            return self.client.image_collection(
                self.collection_id
            )
        except Exception as exc:
            raise GEEDatasetError(
                "Unable to access Sentinel-5P methane collection"
            ) from exc

    def filter_date(
        self,
        start: datetime,
        end: datetime,
    ):
        """
        Apply an inclusive temporal window to the collection.
        """
        if end <= start:
            raise ValueError(
                "end must be later than start"
            )

        return self.collection().filterDate(
            start.isoformat(),
            end.isoformat(),
        )

    def select_methane(self, collection):
        """
        Select the principal methane concentration band.
        """
        return collection.select(self.methane_band)

    def select_methane_with_uncertainty(self, collection):
        """
        Select methane concentration and uncertainty bands.
        """
        return collection.select(
            [
                self.methane_band,
                self.uncertainty_band,
            ]
        )

    def metadata(self) -> dict[str, str]:
        """
        Return stable provenance metadata for Sentinel-5P.
        """
        return {
            "platform": SENTINEL5P_PLATFORM,
            "instrument": SENTINEL5P_INSTRUMENT,
            "provider": SENTINEL5P_PROVIDER,
            "collection": self.collection_id,
            "methane_band": self.methane_band,
            "uncertainty_band": self.uncertainty_band,
        }

    def normalize_observation(
        self,
        *,
        observation_id: str,
        site_id: str,
        observed_at: datetime,
        concentration: float,
        unit: str,
        latitude: float | None = None,
        longitude: float | None = None,
        uncertainty: float | None = None,
    ) -> SatelliteObservation:
        """
        Convert an extracted Sentinel-5P observation into
        the UWDE satellite domain model.
        """
        return SatelliteObservation(
            observation_id=observation_id,
            site_id=site_id,
            observed_at=observed_at,
            concentration=concentration,
            unit=unit,
            satellite=SENTINEL5P_PLATFORM,
            product=self.collection_id,
            latitude=latitude,
            longitude=longitude,
            uncertainty=uncertainty,
            metadata=self.metadata(),
        )
