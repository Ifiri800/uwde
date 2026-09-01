from __future__ import annotations

from .authentication import initialize_earth_engine
from .errors import GEEDatasetError


class GEEClient:
    """
    Thin UWDE wrapper around the Google Earth Engine Python API.
    """

    def __init__(self, project: str, *, ee_module=None):
        self.project = project
        self._ee = ee_module

    def initialize(self) -> None:
        initialize_earth_engine(
            self.project,
            ee_module=self._ee,
        )

    @property
    def ee(self):
        if self._ee is None:
            try:
                import ee
            except ImportError as exc:
                raise GEEDatasetError(
                    "The earthengine-api package is not installed"
                ) from exc

            self._ee = ee

        return self._ee

    def image_collection(self, collection_id: str):
        if not collection_id.strip():
            raise GEEDatasetError(
                "collection_id is required"
            )

        return self.ee.ImageCollection(collection_id)
