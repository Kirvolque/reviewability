from dataclasses import dataclass
from typing import Any

from reviewability.domain.report import AnalysisReport
from reviewability.metrics.overall.lines_changed import OverallLinesChanged
from reviewability.metrics.overall.scatter_factor import OverallScatterFactor
from reviewability.rules.engine import RuleViolation, Severity

_SCORER_INPUTS = {OverallLinesChanged.name, OverallScatterFactor.name}


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

    def evaluate(self, report: AnalysisReport, violations: list[RuleViolation]) -> GateResult:
        """Evaluate the analysis report and return a gate result."""
        passed = not any(v.rule.severity == Severity.ERROR for v in violations)
        recommendations = self._build_recommendations(report) if not passed else []
        return GateResult(passed=passed, recommendations=recommendations)

    def _build_recommendations(self, report: AnalysisReport) -> list[Recommendation]:
        return [
            Recommendation(
                location="overall",
                metric=mv.name,
                value=mv.value,
                remediation=mv.remediation,
            )
            for mv in report.overall.metrics
            if mv.name in _SCORER_INPUTS and mv.value
        ]
