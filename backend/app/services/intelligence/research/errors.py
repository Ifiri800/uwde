class MarketResearchError(Exception):
    """Base exception for the Market Research Engine."""


class InvalidResearchSpecification(MarketResearchError):
    """Raised when a research specification is invalid."""


class ResearchPlanningError(MarketResearchError):
    """Raised when a research plan cannot be generated."""


class EvidenceValidationError(MarketResearchError):
    """Raised when research evidence fails validation."""


class MarketModelError(MarketResearchError):
    """Raised when the market model cannot be constructed."""


class MarketSizingError(MarketResearchError):
    """Raised when market sizing cannot be completed."""


class ResearchValidationError(MarketResearchError):
    """Raised when a research result fails validation."""


class ResearchGenerationError(MarketResearchError):
    """Raised when research output cannot be generated."""
