from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from backend.app.services.intelligence.domain.entities import Company
from backend.app.services.intelligence.domain.evidence import Evidence
from backend.app.services.intelligence.domain.signals import Signal


class CompetitorType(StrEnum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    EMERGING = "emerging"


@dataclass(frozen=True)
class CompetitorRelationship:
    company_id: str
    competitor_id: str
    competitor_type: CompetitorType
    confidence: float
    evidence_ids: tuple[str, ...] = ()
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

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0"
            )

    def to_dict(self) -> dict:
        return {
            "company_id": self.company_id,
            "competitor_id": self.competitor_id,
            "competitor_type": self.competitor_type.value,
            "confidence": self.confidence,
            "evidence_ids": list(self.evidence_ids),
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class CompetitorIdentificationResult:
    relationships: tuple[CompetitorRelationship, ...]
    candidates_evaluated: int

    def __post_init__(self) -> None:
        if self.candidates_evaluated < 0:
            raise ValueError(
                "candidates_evaluated cannot be negative"
            )

    def to_dict(self) -> dict:
        return {
            "relationships": [
                relationship.to_dict()
                for relationship in self.relationships
            ],
            "candidates_evaluated": self.candidates_evaluated,
        }


class CompetitorIdentifier:
    """
    Deterministically identifies competitive relationships between
    companies using company attributes and supporting signals.

    The model deliberately does not treat industry equality alone as
    sufficient evidence of competition.
    """

    MIN_DIRECT_CONFIDENCE = 0.70
    MIN_INDIRECT_CONFIDENCE = 0.55
    MIN_EMERGING_CONFIDENCE = 0.50

    def identify(
        self,
        company: Company,
        candidates: list[Company],
        signals: list[Signal] | None = None,
        evidence: list[Evidence] | None = None,
    ) -> CompetitorIdentificationResult:
        if not isinstance(company, Company):
            raise TypeError("company must be a Company")

        if not isinstance(candidates, list):
            raise TypeError("candidates must be a list")

        if any(
            not isinstance(candidate, Company)
            for candidate in candidates
        ):
            raise TypeError(
                "candidates must contain only Company objects"
            )

        if signals is not None:
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

        signal_records = signals or []
        evidence_records = evidence or []

        relationships: list[CompetitorRelationship] = []
        seen: set[tuple[str, str]] = set()

        for candidate in candidates:
            if candidate.entity_id == company.entity_id:
                continue

            relationship = self._evaluate(
                company,
                candidate,
                signal_records,
                evidence_records,
            )

            if relationship is None:
                continue

            key = (
                relationship.company_id,
                relationship.competitor_id,
            )

            if key in seen:
                continue

            seen.add(key)
            relationships.append(relationship)

        return CompetitorIdentificationResult(
            relationships=tuple(relationships),
            candidates_evaluated=len(candidates),
        )

    def _evaluate(
        self,
        company: Company,
        candidate: Company,
        signals: list[Signal],
        evidence: list[Evidence],
    ) -> CompetitorRelationship | None:
        reasons: list[str] = []
        score = 0.0

        same_industry = self._same_text(
            company.industry,
            candidate.industry,
        )

        same_country = self._same_text(
            company.country,
            candidate.country,
        )

        same_region = self._same_text(
            company.region,
            candidate.region,
        )

        if same_industry:
            score += 0.35
            reasons.append("same industry")

        if same_country:
            score += 0.10
            reasons.append("same country")

        if same_region:
            score += 0.10
            reasons.append("same region")

        relevant_signals = [
            signal
            for signal in signals
            if signal.entity_id == candidate.entity_id
        ]

        signal_types = {
            signal.signal_type.value
            for signal in relevant_signals
        }

        if "new_product" in signal_types:
            score += 0.15
            reasons.append("new product activity")

        if "product_launch" in signal_types:
            score += 0.15
            reasons.append("product launch activity")

        if "price_change" in signal_types:
            score += 0.15
            reasons.append("pricing activity")

        if "company_expansion" in signal_types:
            score += 0.10
            reasons.append("company expansion activity")

        if "technology_adoption" in signal_types:
            score += 0.10
            reasons.append("technology adoption activity")

        if "competitor_change" in signal_types:
            score += 0.20
            reasons.append("competitive-change signal")

        supporting_evidence_ids: list[str] = []

        evidence_by_id = {
            item.evidence_id: item
            for item in evidence
        }

        for signal in relevant_signals:
            for evidence_id in signal.evidence_ids:
                if evidence_id in evidence_by_id:
                    if evidence_id not in supporting_evidence_ids:
                        supporting_evidence_ids.append(evidence_id)

        if supporting_evidence_ids:
            evidence_confidence = max(
                evidence_by_id[evidence_id].confidence
                for evidence_id in supporting_evidence_ids
            )
            score += 0.15 * evidence_confidence
            reasons.append("supporting evidence available")

        score = min(round(score, 4), 1.0)

        if same_industry and same_country and score >= 0.70:
            competitor_type = CompetitorType.DIRECT
            threshold = self.MIN_DIRECT_CONFIDENCE
        elif score >= 0.55:
            competitor_type = CompetitorType.INDIRECT
            threshold = self.MIN_INDIRECT_CONFIDENCE
        elif relevant_signals and score >= 0.50:
            competitor_type = CompetitorType.EMERGING
            threshold = self.MIN_EMERGING_CONFIDENCE
        else:
            return None

        if score < threshold:
            return None

        return CompetitorRelationship(
            company_id=company.entity_id,
            competitor_id=candidate.entity_id,
            competitor_type=competitor_type,
            confidence=score,
            evidence_ids=tuple(supporting_evidence_ids),
            reasons=tuple(reasons),
        )

    @staticmethod
    def _same_text(
        first: str | None,
        second: str | None,
    ) -> bool:
        if not first or not second:
            return False

        return first.strip().casefold() == second.strip().casefold()


def identify_competitors(
    company: Company,
    candidates: list[Company],
    signals: list[Signal] | None = None,
    evidence: list[Evidence] | None = None,
) -> CompetitorIdentificationResult:
    """
    Convenience function using the default competitor identifier.
    """
    return CompetitorIdentifier().identify(
        company,
        candidates,
        signals,
        evidence,
    )
