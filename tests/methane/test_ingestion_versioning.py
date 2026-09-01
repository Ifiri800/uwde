from datetime import datetime, timedelta, timezone

import pytest

from backend.app.services.intelligence.methane.ingestion.versioning import (
    DataVersion,
    VersioningError,
    create_version,
    generate_checksum,
    latest_version,
    validate_version_chain,
    version_changed,
)


def test_generate_checksum_is_deterministic():
    first = generate_checksum({"value": 10})
    second = generate_checksum({"value": 10})

    assert first == second


def test_generate_checksum_produces_sha256():
    result = generate_checksum("methane")

    assert len(result) == 64
    assert all(character in "0123456789abcdef" for character in result)


def test_create_version():
    timestamp = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=timezone.utc,
    )

    version = create_version(
        version_id="v1",
        dataset_id="dataset-001",
        value={"emission": 100},
        created_at=timestamp,
    )

    assert isinstance(version, DataVersion)
    assert version.version_id == "v1"
    assert version.dataset_id == "dataset-001"
    assert version.parent_version_id is None
    assert version.created_at == timestamp
    assert version.checksum


def test_create_version_rejects_naive_timestamp():
    with pytest.raises(VersioningError):
        create_version(
            version_id="v1",
            dataset_id="dataset-001",
            value=100,
            created_at=datetime(2026, 8, 31, 12, 0),
        )


def test_validate_single_root_version():
    version = create_version(
        version_id="v1",
        dataset_id="dataset-001",
        value=100,
    )

    assert validate_version_chain((version,)) is True


def test_validate_version_chain():
    timestamp = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=timezone.utc,
    )

    first = create_version(
        version_id="v1",
        dataset_id="dataset-001",
        value=100,
        created_at=timestamp,
    )

    second = create_version(
        version_id="v2",
        dataset_id="dataset-001",
        value=110,
        parent_version_id="v1",
        created_at=timestamp + timedelta(hours=1),
    )

    assert validate_version_chain((first, second)) is True


def test_validate_version_chain_rejects_invalid_parent():
    timestamp = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=timezone.utc,
    )

    first = create_version(
        version_id="v1",
        dataset_id="dataset-001",
        value=100,
        created_at=timestamp,
    )

    second = create_version(
        version_id="v2",
        dataset_id="dataset-001",
        value=110,
        parent_version_id="wrong-parent",
        created_at=timestamp + timedelta(hours=1),
    )

    with pytest.raises(VersioningError):
        validate_version_chain((first, second))


def test_validate_version_chain_rejects_duplicate_versions():
    version = create_version(
        version_id="v1",
        dataset_id="dataset-001",
        value=100,
    )

    with pytest.raises(VersioningError):
        validate_version_chain((version, version))


def test_latest_version():
    timestamp = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=timezone.utc,
    )

    first = create_version(
        version_id="v1",
        dataset_id="dataset-001",
        value=100,
        created_at=timestamp,
    )

    second = create_version(
        version_id="v2",
        dataset_id="dataset-001",
        value=110,
        parent_version_id="v1",
        created_at=timestamp + timedelta(hours=1),
    )

    assert latest_version((first, second)) == second


def test_latest_version_empty():
    assert latest_version(()) is None


def test_version_changed():
    timestamp = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=timezone.utc,
    )

    first = create_version(
        version_id="v1",
        dataset_id="dataset-001",
        value=100,
        created_at=timestamp,
    )

    second = create_version(
        version_id="v2",
        dataset_id="dataset-001",
        value=110,
        parent_version_id="v1",
        created_at=timestamp + timedelta(hours=1),
    )

    assert version_changed(first, second) is True


def test_version_changed_false_for_same_checksum():
    timestamp = datetime(
        2026,
        8,
        31,
        12,
        0,
        tzinfo=timezone.utc,
    )

    first = create_version(
        version_id="v1",
        dataset_id="dataset-001",
        value=100,
        created_at=timestamp,
    )

    second = create_version(
        version_id="v2",
        dataset_id="dataset-001",
        value=100,
        parent_version_id="v1",
        created_at=timestamp + timedelta(hours=1),
    )

    assert version_changed(first, second) is False
