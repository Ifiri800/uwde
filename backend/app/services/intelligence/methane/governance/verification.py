from __future__ import annotations

from collections.abc import Iterable

from .models import VerificationProtocol, VerificationLevel


def validate_verification_protocols(
    protocols: Iterable[VerificationProtocol],
) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()

    for protocol in protocols:
        if not isinstance(protocol, VerificationProtocol):
            errors.append("invalid verification protocol")
            continue

        if protocol.protocol_id in seen:
            errors.append(
                f"duplicate protocol_id: {protocol.protocol_id}"
            )

        if (
            protocol.level == VerificationLevel.INDEPENDENT
            and not protocol.independence_required
        ):
            errors.append(
                f"independent protocol {protocol.protocol_id} "
                "must require independence"
            )

        seen.add(protocol.protocol_id)

    return tuple(errors)


def build_verification_program(
    protocols: Iterable[VerificationProtocol],
) -> tuple[VerificationProtocol, ...]:
    result = tuple(protocols)

    errors = validate_verification_protocols(result)

    if errors:
        raise ValueError("; ".join(errors))

    return result
