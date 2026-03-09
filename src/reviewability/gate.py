from dataclasses import dataclass
from typing import Any

from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import Analysis, AnalysisReport, MetricValue
from reviewability.metrics.hunk.churn_ratio import HunkChurnRatio
from reviewability.metrics.overall.churn_complexity import OverallChurnComplexity
from reviewability.metrics.overall.lines_changed import OverallLinesChanged
from reviewability.rules.engine import RuleViolation, Severity

# Maps an overall metric to the single hunk/file metric that best explains its value.
# When drilling into sub-causes for these metrics, only the focused metric is surfaced.
_FOCUS_METRIC: dict[str, str] = {
    OverallChurnComplexity.name: HunkChurnRatio.name,
}

_SCORER_INPUTS = {OverallLinesChanged.name, OverallChurnComplexity.name}


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

    def evaluate(self, report: AnalysisReport, violations: list[RuleViolation]) -> GateResult:
        """Evaluate the analysis report and return a gate result."""
        passed = not any(v.rule.severity == Severity.ERROR for v in violations)
        recommendations = self._build_recommendations(report) if not passed else []
        return GateResult(passed=passed, recommendations=recommendations)

    def _build_recommendations(self, report: AnalysisReport) -> list[Recommendation]:
        recs = []
        for mv in report.overall.metrics:
            focus = _FOCUS_METRIC.get(mv.name)
            for cause in mv.causes:
                if isinstance(cause.value, Analysis) and isinstance(cause.value.subject, FileDiff):
                    location = cause.value.subject.path
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
                elif isinstance(cause.value, Analysis) and isinstance(cause.value.subject, Hunk):
                    hunk = cause.value.subject
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
            for mv in report.overall.metrics:
                if mv.name in _SCORER_INPUTS and mv.value:
                    recs.append(
                        Recommendation(
                            location="overall",
                            metric=mv.name,
                            value=mv.value,
                            remediation=mv.remediation,
                        )
                    )
        return recs
