from __future__ import annotations

from dataclasses import dataclass, field

from .models import (
    QualityAssessment,
    QualityDimension,
)


class RegistryError(ValueError):
    """Raised when quality registry rules are violated."""


@dataclass
class QualityRegistry:
    """
    Registry of Layer 6 quality assessments.

    The registry provides deterministic storage and retrieval
    of one assessment per quality dimension.
    """

    _assessments: dict[
        QualityDimension,
        QualityAssessment,
    ] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def register(
        self,
        assessment: QualityAssessment,
    ) -> QualityAssessment:
        if not isinstance(
            assessment,
            QualityAssessment,
        ):
            raise TypeError(
                "assessment must be a QualityAssessment"
            )

        dimension = assessment.dimension

        if dimension in self._assessments:
            raise RegistryError(
                f"quality dimension already registered: "
                f"{dimension.value}"
            )

        self._assessments[dimension] = assessment

        return assessment

    def get(
        self,
        dimension: QualityDimension,
    ) -> QualityAssessment:
        self._validate_dimension(dimension)

        try:
            return self._assessments[dimension]
        except KeyError as exc:
            raise RegistryError(
                f"quality dimension not registered: "
                f"{dimension.value}"
            ) from exc

    def unregister(
        self,
        dimension: QualityDimension,
    ) -> QualityAssessment:
        self._validate_dimension(dimension)

        try:
            return self._assessments.pop(
                dimension
            )
        except KeyError as exc:
            raise RegistryError(
                f"quality dimension not registered: "
                f"{dimension.value}"
            ) from exc

    def contains(
        self,
        dimension: QualityDimension,
    ) -> bool:
        self._validate_dimension(dimension)

        return dimension in self._assessments

    def list_assessments(
        self,
    ) -> tuple[QualityAssessment, ...]:
        return tuple(
            self._assessments.values()
        )

    def count(self) -> int:
        return len(self._assessments)

    def clear(self) -> None:
        self._assessments.clear()

    @staticmethod
    def _validate_dimension(
        dimension: QualityDimension,
    ) -> None:
        if not isinstance(
            dimension,
            QualityDimension,
        ):
            raise TypeError(
                "dimension must be a QualityDimension"
            )
