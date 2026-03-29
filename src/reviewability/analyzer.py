from reviewability.domain.models import Diff
from reviewability.domain.report import AnalysisReport
from reviewability.metrics.engine import MetricEngine
from reviewability.rules.engine import RuleEngine, RuleViolation


class Analyzer:
    """Orchestrates diff analysis: runs the metric engine and evaluates rules.

    Dependencies are injected via the constructor. Use ``create_analyzer``
    to build a fully configured instance from a ``ReviewabilityConfig``.
    """

    def __init__(
        self,
        engine: MetricEngine,
        hunk_rule_engine: RuleEngine,
        overall_rule_engine: RuleEngine,
    ) -> None:
        self._engine = engine
        self._hunk_rules = hunk_rule_engine
        self._overall_rules = overall_rule_engine

    def run(self, diff: Diff) -> tuple[AnalysisReport, list[RuleViolation]]:
        """Analyze a diff and return the report with all rule violations.

        Hunk-level rules are evaluated against each hunk's metrics.
        Overall rules are evaluated against the diff-level metrics.
        """
        report = self._engine.run(diff)

        hunk_violations = [
            violation for hunk in report.hunks for violation in self._hunk_rules.evaluate(hunk)
        ]
        overall_violations = self._overall_rules.evaluate(report.overall)

        return report, hunk_violations + overall_violations
