from __future__ import annotations

from dataclasses import dataclass

from .errors import (
    ResearchGenerationError,
    ResearchPlanningError,
    ResearchValidationError,
)
from .models import (
    MarketResearchProject,
    MarketResearchSpecification,
    ResearchQualityScore,
)
from .planner import create_research_plan
from .sources import ResearchSource, analyze_sources
from .extraction import ExtractionObservation, extract_observations
from .validation import (
    ResearchValidationResult,
    validate_evidence,
    validate_research_project,
)
from .report import MarketResearchReport, generate_report


@dataclass(frozen=True)
class ResearchEngineResult:
    project: MarketResearchProject
    report: MarketResearchReport | None
    validation: ResearchValidationResult
    plan_steps: int
    source_count: int
    evidence_count: int


class ResearchEngine:
    """
    Orchestrates the UWDE Market Research Intelligence workflow.

    The engine coordinates research components without duplicating
    crawling, browser automation, document acquisition, or forecasting.
    """

    def __init__(
        self,
        specification: MarketResearchSpecification,
    ) -> None:

        if not isinstance(
            specification,
            MarketResearchSpecification,
        ):
            raise TypeError(
                "specification must be a MarketResearchSpecification"
            )

        self.specification = specification

        self.project = MarketResearchProject(
            specification=specification,
        )

    def plan(self):

        try:
            plan = create_research_plan(
                self.specification
            )

        except Exception as exc:
            raise ResearchPlanningError(
                f"Research planning failed: {exc}"
            ) from exc

        self.project.status = "planned"

        return plan

    def add_evidence(
        self,
        observations: list[ExtractionObservation],
    ) -> None:

        result = extract_observations(
            observations
        )

        validation = validate_evidence(
            result.evidence
        )

        if not validation.valid:
            raise ResearchValidationError(
                "; ".join(validation.errors)
            )

        self.project.evidence.extend(
            result.evidence.items
        )

        self.project.status = "evidence_collected"

    def add_sources(
        self,
        sources: list[ResearchSource],
    ):

        analysis = analyze_sources(
            sources
        )

        self.project.status = "sources_analyzed"

        return analysis

    def validate(self) -> ResearchValidationResult:

        result = validate_research_project(
            self.project
        )

        if not result.valid:
            self.project.status = "validation_failed"
        else:
            self.project.status = "validated"

        return result

    def calculate_quality(
        self,
        *,
        source_quality: float = 0.0,
        evidence_coverage: float = 0.0,
        numerical_consistency: float = 0.0,
        segmentation_quality: float = 0.0,
        forecast_confidence: float = 0.0,
        citation_coverage: float = 0.0,
    ) -> ResearchQualityScore:

        values = (
            source_quality,
            evidence_coverage,
            numerical_consistency,
            segmentation_quality,
            forecast_confidence,
            citation_coverage,
        )

        if any(
            not 0.0 <= value <= 1.0
            for value in values
        ):
            raise ValueError(
                "quality values must be between 0.0 and 1.0"
            )

        overall = sum(values) / len(values)

        quality = ResearchQualityScore(
            source_quality=source_quality,
            evidence_coverage=evidence_coverage,
            numerical_consistency=numerical_consistency,
            segmentation_quality=segmentation_quality,
            forecast_confidence=forecast_confidence,
            citation_coverage=citation_coverage,
            overall_score=round(
                overall,
                6,
            ),
        )

        self.project.quality = quality

        return quality

    def _calculate_automatic_quality(
        self,
        *,
        source_analysis=None,
    ) -> ResearchQualityScore:

        source_quality = 0.0

        if source_analysis is not None:
            source_quality = (
                source_analysis.average_quality
            )

        evidence_coverage = (
            1.0
            if self.project.evidence
            else 0.0
        )

        citation_coverage = (
            1.0
            if self.project.evidence
            and source_analysis is not None
            and source_analysis.sources
            else 0.0
        )

        numerical_consistency = (
            1.0
            if self.project.estimates
            else 0.0
        )

        segmentation_quality = (
            1.0
            if self.specification.segments
            else 0.0
        )

        forecast_confidence = 0.0

        quality = self.calculate_quality(
            source_quality=source_quality,
            evidence_coverage=evidence_coverage,
            numerical_consistency=numerical_consistency,
            segmentation_quality=segmentation_quality,
            forecast_confidence=forecast_confidence,
            citation_coverage=citation_coverage,
        )

        return quality

    def generate_report(
        self,
        *,
        executive_summary: str,
        sources: list[str] | None = None,
    ) -> MarketResearchReport:

        if not executive_summary.strip():
            raise ResearchGenerationError(
                "executive_summary is required"
            )

        validation = self.validate()

        if not validation.valid:
            raise ResearchGenerationError(
                "Cannot generate report from an invalid "
                "research project: "
                + "; ".join(validation.errors)
            )

        if self.project.quality is None:
            self.calculate_quality(
                source_quality=(
                    1.0
                    if sources
                    else 0.0
                ),
                evidence_coverage=(
                    1.0
                    if self.project.evidence
                    else 0.0
                ),
                numerical_consistency=(
                    1.0
                    if self.project.estimates
                    else 0.0
                ),
                segmentation_quality=(
                    1.0
                    if self.specification.segments
                    else 0.0
                ),
                forecast_confidence=0.0,
                citation_coverage=(
                    1.0
                    if sources and self.project.evidence
                    else 0.0
                ),
            )

        report = generate_report(
            research_id=self.specification.research_id,
            market_name=self.specification.market_name,
            executive_summary=executive_summary,
            findings=self.project.findings,
            insights=self.project.insights,
            recommendations=self.project.recommendations,
            sources=sources or [],
            confidence=(
                self.project.quality.overall_score
                if self.project.quality
                else 0.0
            ),
        )

        self.project.status = "completed"

        return report

    def run(
        self,
        *,
        observations: list[ExtractionObservation] | None = None,
        sources: list[ResearchSource] | None = None,
        executive_summary: str | None = None,
    ) -> ResearchEngineResult:

        plan = self.plan()

        source_analysis = None

        if sources:
            source_analysis = self.add_sources(
                sources
            )

        if observations:
            self.add_evidence(
                observations
            )

        validation = self.validate()

        self._calculate_automatic_quality(
            source_analysis=source_analysis
        )

        report = None

        if executive_summary is not None:
            report = self.generate_report(
                executive_summary=executive_summary,
                sources=[
                    source.url
                    for source in sources or []
                ],
            )

        return ResearchEngineResult(
            project=self.project,
            report=report,
            validation=validation,
            plan_steps=len(plan.steps),
            source_count=len(sources or []),
            evidence_count=len(
                self.project.evidence
            ),
        )


def create_research_engine(
    specification: MarketResearchSpecification,
) -> ResearchEngine:

    return ResearchEngine(
        specification
    )


def run_research(
    specification: MarketResearchSpecification,
    *,
    observations: list[ExtractionObservation] | None = None,
    sources: list[ResearchSource] | None = None,
    executive_summary: str | None = None,
) -> ResearchEngineResult:

    return ResearchEngine(
        specification
    ).run(
        observations=observations,
        sources=sources,
        executive_summary=executive_summary,
    )
