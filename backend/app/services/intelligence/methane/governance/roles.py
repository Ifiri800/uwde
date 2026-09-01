from __future__ import annotations

from collections.abc import Iterable

from .models import GovernanceRole, RoleType


def build_roles(
    roles: Iterable[GovernanceRole],
) -> tuple[GovernanceRole, ...]:
    """Normalize governance roles and reject duplicate role types."""

    result = []
    seen: set[RoleType] = set()

    for role in roles:
        if not isinstance(role, GovernanceRole):
            raise TypeError("all roles must be GovernanceRole instances")

        if role.role in seen:
            raise ValueError(f"duplicate role: {role.role.value}")

        seen.add(role.role)
        result.append(role)

    return tuple(result)


def has_required_roles(
    roles: Iterable[GovernanceRole],
) -> bool:
    required = {
        RoleType.MRV_OWNER,
        RoleType.DATA_OWNER,
        RoleType.QA_QC_OWNER,
        RoleType.VERIFIER,
        RoleType.LDAR_MANAGER,
    }

    actual = {
        role.role
        for role in roles
        if isinstance(role, GovernanceRole)
    }

    return required.issubset(actual)
