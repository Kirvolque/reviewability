from dataclasses import dataclass

from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.report import AnalysisReport
from reviewability.rules.engine import RuleViolation, Severity


@dataclass(frozen=True)
class GateResult:
    """The outcome of a quality gate evaluation.

    ``passed`` is True if the diff meets all configured thresholds.
    ``recommendations`` contains actionable suggestions when the gate fails
    (populated in a future step).
    """

    passed: bool
    recommendations: list[str]


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
        return GateResult(passed=passed, recommendations=[])
