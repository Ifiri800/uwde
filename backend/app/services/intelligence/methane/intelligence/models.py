from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class IntelligenceType(str, Enum):
    ANOMALY = "anomaly"
    DATA_FUSION = "data_fusion"
    EQUIPMENT_RISK = "equipment_risk"
    LEAK_PROBABILITY = "leak_probability"
    PATTERN = "pattern"
    EMISSION_PREDICTION = "emission_prediction"
    SOURCE_ATTRIBUTION = "source_attribution"
    SUPER_EMITTER = "super_emitter"


class IntelligenceMethod(str, Enum):
    DETERMINISTIC = "deterministic"
    STATISTICAL = "statistical"
    RULE_BASED = "rule_based"
    MACHINE_LEARNING = "machine_learning"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class IntelligenceFeature:
    """Canonical Layer 10 intelligence feature."""

    name: str
    value: float
    source: str | None = None
    unit: str | None = None
    confidence: float = 1.0
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )


@dataclass(frozen=True)
class IntelligencePrediction:
    """Canonical Layer 10 intelligence prediction."""

    prediction_id: str
    entity_id: str
    intelligence_type: IntelligenceType
    method: IntelligenceMethod
    value: float
    confidence: float
    feature_names: tuple[str, ...] = ()
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    model_id: str | None = None
    explanation: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.value < 0.0:
            raise ValueError(
                "prediction value cannot be negative"
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "prediction_id": self.prediction_id,
            "entity_id": self.entity_id,
            "intelligence_type": self.intelligence_type.value,
            "method": self.method.value,
            "value": self.value,
            "confidence": self.confidence,
            "feature_names": list(self.feature_names),
            "signal_ids": list(self.signal_ids),
            "evidence_ids": list(self.evidence_ids),
            "model_id": self.model_id,
            "explanation": self.explanation,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class IntelligenceResult:
    """Canonical Layer 10 intelligence result."""

    entity_id: str
    intelligence_type: IntelligenceType
    predictions: tuple[IntelligencePrediction, ...] = ()
    features: tuple[IntelligenceFeature, ...] = ()
    confidence: float = 0.0
    signal_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                "confidence must be between 0 and 1"
            )

    @property
    def prediction_count(self) -> int:
        return len(self.predictions)

    @property
    def feature_count(self) -> int:
        return len(self.features)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "intelligence_type": self.intelligence_type.value,
            "predictions": [
                prediction.to_dict()
                for prediction in self.predictions
            ],
            "features": [
                {
                    "name": feature.name,
                    "value": feature.value,
                    "source": feature.source,
                    "unit": feature.unit,
                    "confidence": feature.confidence,
                    "metadata": dict(feature.metadata),
                }
                for feature in self.features
            ],
            "confidence": self.confidence,
            "signal_ids": list(self.signal_ids),
            "evidence_ids": list(self.evidence_ids),
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }


class DecisionPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass(frozen=True)
class IntelligenceDecision:
    entity_id: str
    decision_type: str
    priority: DecisionPriority
    score: float
    confidence: float
    rationale: tuple[str, ...] = ()
    recommended_actions: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    signal_ids: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class IntelligenceAlert:
    alert_id: str
    entity_id: str
    alert_type: str
    priority: DecisionPriority
    score: float
    message: str
    evidence_ids: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class IntelligenceRecommendation:
    recommendation_id: str
    entity_id: str
    action: str
    priority: DecisionPriority
    rationale: str
    expected_outcome: str
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class IntelligenceRanking:
    entity_id: str
    rank: int
    score: float
    category: str
    rationale: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class IntelligenceTrend:
    entity_id: str
    direction: str
    magnitude: float
    baseline: float
    current: float
    confidence: float
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class IntelligenceRisk:
    entity_id: str
    score: float
    level: RiskLevel
    factors: tuple[str, ...] = ()
    confidence: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)
