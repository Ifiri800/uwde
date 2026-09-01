from .models import (
    DecisionPriority,
    IntelligenceAlert,
    IntelligenceDecision,
    IntelligenceRanking,
    IntelligenceRecommendation,
    IntelligenceRisk,
    IntelligenceTrend,
    RiskLevel,
)

__all__ = [
    "DecisionPriority",
    "RiskLevel",
    "IntelligenceDecision",
    "IntelligenceAlert",
    "IntelligenceRecommendation",
    "IntelligenceRanking",
    "IntelligenceTrend",
    "IntelligenceRisk",
    "MethaneDecisionEngine",
    "make_decision",
    "MethaneIntelligenceDecisionResult",
    "MethaneIntelligenceOrchestrator",
    "evaluate_methane_intelligence",
]


def __getattr__(name: str):
    if name in {"MethaneDecisionEngine", "make_decision"}:
        from .engine import MethaneDecisionEngine, make_decision

        return {
            "MethaneDecisionEngine": MethaneDecisionEngine,
            "make_decision": make_decision,
        }[name]

    if name in {
        "MethaneIntelligenceDecisionResult",
        "MethaneIntelligenceOrchestrator",
        "evaluate_methane_intelligence",
    }:
        from .orchestrator import (
            MethaneIntelligenceDecisionResult,
            MethaneIntelligenceOrchestrator,
            evaluate_methane_intelligence,
        )

        return {
            "MethaneIntelligenceDecisionResult":
                MethaneIntelligenceDecisionResult,
            "MethaneIntelligenceOrchestrator":
                MethaneIntelligenceOrchestrator,
            "evaluate_methane_intelligence":
                evaluate_methane_intelligence,
        }[name]

    raise AttributeError(name)
