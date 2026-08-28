from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from backend.app.services.intelligence.domain.entities import Company
from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import Signal, SignalType


class PositioningLevel(StrEnum):
    STRONG = "strong"
    FAVORABLE = "favorable"
    NEUTRAL = "neutral"
    WEAK = "weak"
    UNKNOWN = "unknown"


class PositioningDimension(StrEnum):
    MARKET_ALIGNMENT = "market_alignment"
    PRODUCT_ACTIVITY = "product_activity"
    PRICING_ACTIVITY = "pricing_activity"
    GEOGRAPHIC_PRESENCE = "geographic_presence"
    TECHNOLOGY_ADOPTION = "technology_adoption"
    COMPANY_EXPANSION = "company_expansion"
    HIRING_GROWTH = "hiring_growth"
    FUNDING_ACTIVITY = "funding_activity"
    COMPETITIVE_ACTIVITY = "competitive_activity"


@dataclass(frozen=True)
class PositioningAssessment:
    dimension: PositioningDimension
    score: float
    level: PositioningLevel
    confidence: float
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("score must be between 0.0 and 1.0")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

    def to_dict(self) -> dict:
        return {
            "dimension": self.dimension.value,
            "score": self.score,
            "level": self.level.value,
            "confidence": self.confidence,
            "signal_ids": list(self.signal_ids),
            "evidence_ids": list(self.evidence_ids),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class CompetitivePositioningResult:
    company_id: str
    competitor_id: str
    overall_score: float
    level: PositioningLevel
    confidence: float
    assessments: tuple[PositioningAssessment, ...]
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    relative_advantages: tuple[str, ...] = ()
    relative_disadvantages: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.company_id.strip():
            raise ValueError("company_id is required")

        if not self.competitor_id.strip():
            raise ValueError("competitor_id is required")

        if self.company_id == self.competitor_id:
            raise ValueError(
                "company_id and competitor_id must differ"
            )

        if not 0.0 <= self.overall_score <= 1.0:
            raise ValueError(
                "overall_score must be between 0.0 and 1.0"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "competitor_id": self.competitor_id,
            "overall_score": self.overall_score,
            "level": self.level.value,
            "confidence": self.confidence,
            "assessments": [
                assessment.to_dict()
                for assessment in self.assessments
            ],
            "signal_ids": list(self.signal_ids),
            "evidence_ids": list(self.evidence_ids),
            "relative_advantages": list(self.relative_advantages),
            "relative_disadvantages": list(
                self.relative_disadvantages
            ),
            "reasons": list(self.reasons),
        }


class CompetitivePositioningEngine:
    """
    Deterministically evaluates a company relative to a competitor.

    The engine uses company attributes plus intelligence signals and
    supporting evidence. Every dimension produces an explainable
    structured assessment rather than an opaque aggregate score.
    """

    DIMENSION_WEIGHTS: dict[PositioningDimension, float] = {
        PositioningDimension.MARKET_ALIGNMENT: 0.15,
        PositioningDimension.PRODUCT_ACTIVITY: 0.12,
        PositioningDimension.PRICING_ACTIVITY: 0.10,
        PositioningDimension.GEOGRAPHIC_PRESENCE: 0.10,
        PositioningDimension.TECHNOLOGY_ADOPTION: 0.10,
        PositioningDimension.COMPANY_EXPANSION: 0.10,
        PositioningDimension.HIRING_GROWTH: 0.08,
        PositioningDimension.FUNDING_ACTIVITY: 0.08,
        PositioningDimension.COMPETITIVE_ACTIVITY: 0.17,
    }

    def evaluate(
        self,
        company: Company,
        competitor: Company,
        signals: list[Signal],
        evidence: list[Evidence] | None = None,
    ) -> CompetitivePositioningResult:
        if not isinstance(company, Company):
            raise TypeError("company must be a Company")

        if not isinstance(competitor, Company):
            raise TypeError("competitor must be a Company")

        if company.entity_id == competitor.entity_id:
            raise ValueError(
                "company and competitor must differ"
            )

        if not isinstance(signals, list):
            raise TypeError("signals must be a list")

        if any(
            not isinstance(signal, Signal)
            for signal in signals
        ):
            raise TypeError(
                "signals must contain only Signal objects"
            )

        if evidence is not None:
            if not isinstance(evidence, list):
                raise TypeError("evidence must be a list")

            if any(
                not isinstance(item, Evidence)
                for item in evidence
            ):
                raise TypeError(
                    "evidence must contain only Evidence objects"
                )

        evidence_by_id = {
            item.evidence_id: item
            for item in (evidence or [])
        }

        company_signals = [
            signal
            for signal in signals
            if signal.entity_id == company.entity_id
        ]

        competitor_signals = [
            signal
            for signal in signals
            if signal.entity_id == competitor.entity_id
        ]

        assessments = (
            self._market_alignment(company, competitor),
            self._signal_dimension(
                PositioningDimension.PRODUCT_ACTIVITY,
                company_signals,
                competitor_signals,
                {
                    SignalType.NEW_PRODUCT,
                    SignalType.PRODUCT_LAUNCH,
                },
                evidence_by_id,
            ),
            self._signal_dimension(
                PositioningDimension.PRICING_ACTIVITY,
                company_signals,
                competitor_signals,
                {SignalType.PRICE_CHANGE},
                evidence_by_id,
            ),
            self._geographic_presence(company, competitor),
            self._signal_dimension(
                PositioningDimension.TECHNOLOGY_ADOPTION,
                company_signals,
                competitor_signals,
                {SignalType.TECHNOLOGY_ADOPTION},
                evidence_by_id,
            ),
            self._signal_dimension(
                PositioningDimension.COMPANY_EXPANSION,
                company_signals,
                competitor_signals,
                {
                    SignalType.COMPANY_EXPANSION,
                    SignalType.MARKET_GROWTH,
                },
                evidence_by_id,
            ),
            self._signal_dimension(
                PositioningDimension.HIRING_GROWTH,
                company_signals,
                competitor_signals,
                {SignalType.HIRING_SIGNAL},
                evidence_by_id,
            ),
            self._signal_dimension(
                PositioningDimension.FUNDING_ACTIVITY,
                company_signals,
                competitor_signals,
                {SignalType.FUNDING_SIGNAL},
                evidence_by_id,
            ),
            self._signal_dimension(
                PositioningDimension.COMPETITIVE_ACTIVITY,
                company_signals,
                competitor_signals,
                {SignalType.COMPETITOR_CHANGE},
                evidence_by_id,
            ),
        )

        overall_score = round(
            sum(
                assessment.score
                * self.DIMENSION_WEIGHTS[assessment.dimension]
                for assessment in assessments
            ),
            4,
        )

        confidence = round(
            sum(
                assessment.confidence
                * self.DIMENSION_WEIGHTS[assessment.dimension]
                for assessment in assessments
            ),
            4,
        )

        signal_ids = tuple(
            signal.signal_id
            for signal in company_signals + competitor_signals
        )

        evidence_ids: list[str] = []

        for signal in company_signals + competitor_signals:
            for evidence_id in signal.evidence_ids:
                if (
                    evidence_id in evidence_by_id
                    and evidence_id not in evidence_ids
                ):
                    evidence_ids.append(evidence_id)

        advantages = tuple(
            assessment.dimension.value
            for assessment in assessments
            if assessment.score >= 0.70
        )

        disadvantages = tuple(
            assessment.dimension.value
            for assessment in assessments
            if assessment.score < 0.40
        )

        activity_dimensions = {
            PositioningDimension.PRODUCT_ACTIVITY,
            PositioningDimension.PRICING_ACTIVITY,
            PositioningDimension.GEOGRAPHIC_PRESENCE,
            PositioningDimension.TECHNOLOGY_ADOPTION,
            PositioningDimension.COMPANY_EXPANSION,
            PositioningDimension.HIRING_GROWTH,
            PositioningDimension.FUNDING_ACTIVITY,
            PositioningDimension.COMPETITIVE_ACTIVITY,
        }

        activity_reasons = [
            reason
            for assessment in assessments
            if assessment.dimension in activity_dimensions
            for reason in assessment.reasons
        ]

        other_reasons = [
            reason
            for assessment in assessments
            if assessment.dimension not in activity_dimensions
            for reason in assessment.reasons
        ]

        reasons = tuple(
            activity_reasons + other_reasons
        )

        return CompetitivePositioningResult(
            company_id=company.entity_id,
            competitor_id=competitor.entity_id,
            overall_score=overall_score,
            level=self._level(overall_score),
            confidence=confidence,
            assessments=assessments,
            signal_ids=signal_ids,
            evidence_ids=tuple(evidence_ids),
            relative_advantages=advantages,
            relative_disadvantages=disadvantages,
            reasons=reasons,
        )

    def _market_alignment(
        self,
        company: Company,
        competitor: Company,
    ) -> PositioningAssessment:
        reasons: list[str] = []
        score = 0.0

        if self._same_text(
            company.industry,
            competitor.industry,
        ):
            score += 0.70
            reasons.append("same industry")

        if self._same_text(
            company.country,
            competitor.country,
        ):
            score += 0.20
            reasons.append("same country")

        if self._same_text(
            company.region,
            competitor.region,
        ):
            score += 0.10
            reasons.append("same region")

        return PositioningAssessment(
            dimension=PositioningDimension.MARKET_ALIGNMENT,
            score=min(round(score, 4), 1.0),
            level=self._level(min(score, 1.0)),
            confidence=1.0 if reasons else 0.0,
            reasons=tuple(reasons),
        )

    def _geographic_presence(
        self,
        company: Company,
        competitor: Company,
    ) -> PositioningAssessment:
        reasons: list[str] = []
        score = 0.0

        if self._same_text(
            company.country,
            competitor.country,
        ):
            score += 0.60
            reasons.append("same country presence")

        if self._same_text(
            company.region,
            competitor.region,
        ):
            score += 0.30
            reasons.append("same regional presence")

        if self._same_text(
            company.city,
            competitor.city,
        ):
            score += 0.10
            reasons.append("same city presence")

        return PositioningAssessment(
            dimension=PositioningDimension.GEOGRAPHIC_PRESENCE,
            score=min(round(score, 4), 1.0),
            level=self._level(min(score, 1.0)),
            confidence=1.0 if reasons else 0.0,
            reasons=tuple(reasons),
        )

    def _signal_dimension(
        self,
        dimension: PositioningDimension,
        company_signals: list[Signal],
        competitor_signals: list[Signal],
        signal_types: set[SignalType],
        evidence_by_id: dict[str, Evidence],
    ) -> PositioningAssessment:
        company_records = [
            signal
            for signal in company_signals
            if signal.signal_type in signal_types
        ]

        competitor_records = [
            signal
            for signal in competitor_signals
            if signal.signal_type in signal_types
        ]

        company_strength = self._signal_strength(
            company_records,
        )
        competitor_strength = self._signal_strength(
            competitor_records,
        )

        if not company_records and not competitor_records:
            score = 0.50
            confidence = 0.0
            reasons = ("no supporting activity detected",)
        else:
            score = round(
                0.50
                + (
                    company_strength
                    - competitor_strength
                )
                / 2,
                4,
            )

            confidence = round(
                max(
                    [
                        signal.confidence
                        for signal in (
                            company_records
                            + competitor_records
                        )
                    ],
                    default=0.0,
                ),
                4,
            )

            reasons = self._relative_signal_reasons(
                company_records,
                competitor_records,
                dimension,
            )

        signal_ids = tuple(
            signal.signal_id
            for signal in (
                company_records + competitor_records
            )
        )

        evidence_ids: list[str] = []

        for signal in (
            company_records + competitor_records
        ):
            for evidence_id in signal.evidence_ids:
                if (
                    evidence_id in evidence_by_id
                    and evidence_id not in evidence_ids
                ):
                    evidence_ids.append(evidence_id)

        return PositioningAssessment(
            dimension=dimension,
            score=max(0.0, min(score, 1.0)),
            level=self._level(score),
            confidence=confidence,
            signal_ids=signal_ids,
            evidence_ids=tuple(evidence_ids),
            reasons=reasons,
        )

    @staticmethod
    def _signal_strength(
        signals: list[Signal],
    ) -> float:
        if not signals:
            return 0.0

        return min(
            1.0,
            sum(
                signal.confidence * max(signal.strength, 0.0)
                for signal in signals
            ),
        )

    @staticmethod
    def _relative_signal_reasons(
        company_signals: list[Signal],
        competitor_signals: list[Signal],
        dimension: PositioningDimension,
    ) -> tuple[str, ...]:
        company_strength = CompetitivePositioningEngine._signal_strength(
            company_signals
        )
        competitor_strength = CompetitivePositioningEngine._signal_strength(
            competitor_signals
        )

        label = dimension.value.replace("_", " ")

        if company_strength > competitor_strength:
            return (
                f"company has stronger {label}",
            )

        if competitor_strength > company_strength:
            return (
                f"competitor has stronger {label}",
            )

        return (
            f"company and competitor have comparable {label}",
        )

    @staticmethod
    def _same_text(
        first: str | None,
        second: str | None,
    ) -> bool:
        if not first or not second:
            return False

        return first.strip().casefold() == second.strip().casefold()

    @staticmethod
    def _level(score: float) -> PositioningLevel:
        if score >= 0.75:
            return PositioningLevel.STRONG

        if score >= 0.60:
            return PositioningLevel.FAVORABLE

        if score >= 0.40:
            return PositioningLevel.NEUTRAL

        if score > 0.0:
            return PositioningLevel.WEAK

        return PositioningLevel.UNKNOWN


def evaluate_competitive_positioning(
    company: Company,
    competitor: Company,
    signals: list[Signal],
    evidence: list[Evidence] | None = None,
) -> CompetitivePositioningResult:
    """
    Convenience function using the default positioning engine.
    """
    return CompetitivePositioningEngine().evaluate(
        company,
        competitor,
        signals,
        evidence,
    )
