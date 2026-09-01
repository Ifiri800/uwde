from __future__ import annotations

from .models import RegulatorySource, RequirementTrace


class RegulatoryRegistry:
    """Registry for authoritative methane MRV regulatory sources."""

    def __init__(self) -> None:
        self._sources: dict[str, RegulatorySource] = {}
        self._traces: dict[str, RequirementTrace] = {}

    def register_source(
        self,
        source: RegulatorySource,
    ) -> None:

        if not isinstance(source, RegulatorySource):
            raise TypeError(
                "source must be a RegulatorySource"
            )

        if source.source_id in self._sources:
            raise ValueError(
                f"source already registered: {source.source_id}"
            )

        self._sources[source.source_id] = source

    def register_trace(
        self,
        trace: RequirementTrace,
    ) -> None:

        if not isinstance(trace, RequirementTrace):
            raise TypeError(
                "trace must be a RequirementTrace"
            )

        if trace.source_id not in self._sources:
            raise ValueError(
                f"unknown regulatory source: {trace.source_id}"
            )

        if trace.trace_id in self._traces:
            raise ValueError(
                f"trace already registered: {trace.trace_id}"
            )

        self._traces[trace.trace_id] = trace

    def get_source(
        self,
        source_id: str,
    ) -> RegulatorySource | None:
        return self._sources.get(source_id)

    def get_trace(
        self,
        trace_id: str,
    ) -> RequirementTrace | None:
        return self._traces.get(trace_id)

    @property
    def sources(self) -> tuple[RegulatorySource, ...]:
        return tuple(self._sources.values())

    @property
    def traces(self) -> tuple[RequirementTrace, ...]:
        return tuple(self._traces.values())
