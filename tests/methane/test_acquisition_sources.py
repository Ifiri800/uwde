from datetime import datetime, timezone

from backend.app.services.intelligence.methane.acquisition.ldar import (
    create_ldar_observation,
)
from backend.app.services.intelligence.methane.acquisition.direct_measurement import (
    create_direct_measurement,
)
from backend.app.services.intelligence.methane.acquisition.models import (
    AcquisitionCategory,
)


def test_ldar_source():
    observation = create_ldar_observation(
        "ldar-1",
        "OGI",
        datetime.now(timezone.utc),
        value=2.0,
        unit="kg/h",
    )

    assert observation.category == AcquisitionCategory.LDAR


def test_direct_measurement_source():
    observation = create_direct_measurement(
        "measurement-1",
        "flow_meter",
        datetime.now(timezone.utc),
        value=4.0,
        unit="kg/h",
    )

    assert observation.category == AcquisitionCategory.DIRECT_MEASUREMENT
