from dataclasses import dataclass
from typing import Any

from reviewability.domain.models import Hunk
from reviewability.domain.report import AnalysisReport
from reviewability.metrics.hunk.churn_ratio import HunkChurnRatio
from reviewability.metrics.overall.churn_complexity import OverallChurnComplexity
from reviewability.metrics.overall.lines_changed import OverallLinesChanged
from reviewability.rules.engine import RuleViolation, Severity

# Maps an overall metric to the hunk metric that best explains it.
# When this overall metric contributes to failure, the gate surfaces the
# worst hunks ranked by their score, annotated with the focus metric.
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
            if focus is None:
                continue

            for h in sorted(report.hunks, key=lambda h: h.score):
                if not isinstance(h.subject, Hunk):
                    continue
                focus_mv = h.metrics.get(focus)
                if focus_mv is None or not focus_mv.value:
                    continue
                hunk = h.subject
                recs.append(
                    Recommendation(
                        location=(
                            f"{hunk.file_path}"
                            f" @@ -{hunk.source_start},{hunk.source_length}"
                            f" +{hunk.target_start},{hunk.target_length} @@"
                        ),
                        metric=focus_mv.name,
                        value=focus_mv.value,
                        remediation=focus_mv.remediation,
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
