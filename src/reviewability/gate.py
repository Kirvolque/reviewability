from dataclasses import dataclass
from typing import Any

from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.models import Hunk, Move
from reviewability.domain.report import Analysis, AnalysisReport
from reviewability.rules.engine import RuleViolation, Severity


@dataclass(frozen=True)
class Recommendation:
    """An actionable suggestion derived from a quality gate failure.

    ``location`` identifies where the issue was found.
    ``metric`` is the metric name that caused the low score.
    ``value`` is the computed metric value.
    ``remediation`` is the suggested action.
    """

    location: str
    metric: str
    value: Any
    remediation: str | None


@dataclass(frozen=True)
class GateResult:
    """The outcome of a quality gate evaluation.

    ``passed`` is True if the diff meets all configured thresholds.
    ``recommendations`` contains actionable suggestions when the gate fails.
    """

    passed: bool
    recommendations: list[Recommendation]


class QualityGate:
    """Decides whether a diff passes or fails based on scores, metrics, and config.

    Failure conditions:
    - Any rule violation has ERROR severity
    """

    def evaluate(
        self,
        report: AnalysisReport,
        violations: list[RuleViolation],
        config: ReviewabilityConfig,
    ) -> GateResult:
        """Evaluate the analysis report and return a gate result."""
        passed = not any(v.rule.severity == Severity.ERROR for v in violations)
        recommendations = self._build_recommendations(report, config) if not passed else []
        return GateResult(passed=passed, recommendations=recommendations)

    def _build_recommendations(
        self, report: AnalysisReport, config: ReviewabilityConfig
    ) -> list[Recommendation]:
        recs: list[Recommendation] = []

        for analysis in (*report.hunks, *report.moves):
            if analysis.score < config.hunk_score_threshold:
                location = self._location(analysis)
                for mv in analysis.metrics:
                    if mv.remediation is not None:
                        recs.append(
                            Recommendation(
                                location=location,
                                metric=mv.name,
                                value=mv.value,
                                remediation=mv.remediation,
                            )
                        )

        for mv in report.overall.metrics:
            if mv.remediation is not None:
                recs.append(
                    Recommendation(
                        location="overall",
                        metric=mv.name,
                        value=mv.value,
                        remediation=mv.remediation,
                    )
                )

        return recs

    @staticmethod
    def _location(analysis: Analysis) -> str:
        """Derive a human-readable location string from an analysis subject."""
        subject = analysis.subject
        if isinstance(subject, Hunk):
            return subject.file_path
        if isinstance(subject, Move):
            return f"move:{subject.move_id}"
        return str(subject)
