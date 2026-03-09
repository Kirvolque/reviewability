from dataclasses import dataclass
from typing import Any

from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.report import AnalysisReport, FileAnalysis, HunkAnalysis, MetricValue
from reviewability.metrics.hunk.churn_ratio import HunkChurnRatio
from reviewability.metrics.overall.churn_complexity import OverallChurnComplexity
from reviewability.rules.engine import RuleViolation, Severity

# Maps an overall metric to the single hunk/file metric that best explains its value.
# When drilling into sub-causes for these metrics, only the focused metric is surfaced.
_FOCUS_METRIC: dict[str, str] = {
    OverallChurnComplexity.name: HunkChurnRatio.name,
}


@dataclass(frozen=True)
class Recommendation:
    """An actionable suggestion derived from a problematic file or hunk.

    ``location`` identifies where the issue was found (file path or hunk coordinates).
    ``metric`` is the metric name that caused the low score.
    ``value`` is the computed metric value.
    ``remediation`` is the suggested action.
    """

    location: str
    metric: str
    value: Any
    remediation: str


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
    - Overall score is below ``config.min_overall_score``
    - Any rule violation has ERROR severity
    """

    def __init__(self, config: ReviewabilityConfig) -> None:
        self._config = config

    def evaluate(self, report: AnalysisReport, violations: list[RuleViolation]) -> GateResult:
        """Evaluate the analysis report and return a gate result."""
        score_failed = report.overall.score < self._config.min_overall_score
        error_violations = any(v.rule.severity == Severity.ERROR for v in violations)
        passed = not score_failed and not error_violations
        recommendations = self._build_recommendations(report) if not passed else []
        return GateResult(passed=passed, recommendations=recommendations)

    def _build_recommendations(self, report: AnalysisReport) -> list[Recommendation]:
        recs = []
        for omr in report.overall.metric_results:
            focus = _FOCUS_METRIC.get(omr.value.name)
            for cause in omr.causes:
                if isinstance(cause.value, FileAnalysis):
                    location = cause.value.file.path
                    for inner in cause.value.causes:
                        if isinstance(inner.value, MetricValue):
                            if focus is None or inner.value.name == focus:
                                recs.append(
                                    Recommendation(
                                        location=location,
                                        metric=inner.value.name,
                                        value=inner.value.value,
                                        remediation=inner.remediation,
                                    )
                                )
                elif isinstance(cause.value, HunkAnalysis):
                    hunk = cause.value.hunk
                    location = (
                        f"{hunk.file_path}"
                        f" @@ -{hunk.source_start},{hunk.source_length}"
                        f" +{hunk.target_start},{hunk.target_length} @@"
                    )
                    for inner in cause.value.causes:
                        if isinstance(inner.value, MetricValue):
                            if focus is None or inner.value.name == focus:
                                recs.append(
                                    Recommendation(
                                        location=location,
                                        metric=inner.value.name,
                                        value=inner.value.value,
                                        remediation=inner.remediation,
                                    )
                                )

        if not recs:
            # Fallback: no sub-cause recommendations found; surface the overall-level
            # metrics that actually drove the score (filtered by scorer.overall_score_inputs).
            # Skip zero-valued metrics — a metric at 0 did not contribute to the failure.
            for cause in report.overall.causes:
                if isinstance(cause.value, MetricValue) and cause.value.value:
                    recs.append(
                        Recommendation(
                            location="overall",
                            metric=cause.value.name,
                            value=cause.value.value,
                            remediation=cause.remediation,
                        )
                    )
        return recs
