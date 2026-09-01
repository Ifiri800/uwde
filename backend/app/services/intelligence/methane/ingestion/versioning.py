from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping


class VersioningError(ValueError):
    """Raised when ingestion versioning rules are violated."""


@dataclass(frozen=True)
class DataVersion:
    version_id: str
    dataset_id: str
    created_at: datetime
    checksum: str
    parent_version_id: str | None = None
    metadata: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.version_id.strip():
            raise ValueError("version_id is required")

        if not self.dataset_id.strip():
            raise ValueError("dataset_id is required")

        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be a datetime")

        if self.created_at.tzinfo is None:
            raise VersioningError(
                "created_at must be timezone-aware"
            )

        if not self.checksum.strip():
            raise ValueError("checksum is required")


def generate_checksum(value: Any) -> str:
    """Generate a deterministic SHA-256 checksum for a value."""
    payload = repr(value).encode("utf-8")
    return sha256(payload).hexdigest()


def create_version(
    version_id: str,
    dataset_id: str,
    value: Any,
    parent_version_id: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    created_at: datetime | None = None,
) -> DataVersion:
    """Create an immutable dataset version."""
    timestamp = created_at or datetime.now(timezone.utc)

    if timestamp.tzinfo is None:
        raise VersioningError(
            "created_at must be timezone-aware"
        )

    return DataVersion(
        version_id=version_id,
        dataset_id=dataset_id,
        created_at=timestamp,
        checksum=generate_checksum(value),
        parent_version_id=parent_version_id,
        metadata=metadata,
    )


def validate_version_chain(
    versions: tuple[DataVersion, ...],
) -> bool:
    """Validate chronological and parent-child version lineage."""
    if not versions:
        return True

    seen: set[str] = set()

    for index, version in enumerate(versions):
        if version.version_id in seen:
            raise VersioningError(
                f"duplicate version_id: {version.version_id}"
            )

        seen.add(version.version_id)

        if index == 0:
            if version.parent_version_id is not None:
                raise VersioningError(
                    "first version cannot have a parent"
                )
            continue

        previous = versions[index - 1]

        if version.parent_version_id != previous.version_id:
            raise VersioningError(
                "version parent does not match previous version"
            )

        if version.created_at < previous.created_at:
            raise VersioningError(
                "versions must be chronological"
            )

    return True


def latest_version(
    versions: tuple[DataVersion, ...],
) -> DataVersion | None:
    """Return the most recently created version."""
    if not versions:
        return None

    return max(
        versions,
        key=lambda version: version.created_at,
    )


def version_changed(
    first: DataVersion,
    second: DataVersion,
) -> bool:
    """Determine whether two versions contain different data."""
    if not isinstance(first, DataVersion):
        raise TypeError("first must be DataVersion")

    if not isinstance(second, DataVersion):
        raise TypeError("second must be DataVersion")

    return first.checksum != second.checksum
