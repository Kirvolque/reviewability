from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.models import Diff
from reviewability.domain.report import AnalysisReport
from reviewability.metrics.engine import MetricEngine
from reviewability.metrics.file import FileLinesChanged
from reviewability.metrics.hunk import (
    HunkAddedLines,
    HunkChangeBalance,
    HunkContextLines,
    HunkInterleaving,
    HunkLinesChanged,
    HunkRemovedLines,
)
from reviewability.metrics.move import MoveEditComplexity
from reviewability.metrics.overall import (
    OverallAddedLines,
    OverallFilesChanged,
    OverallLinesChanged,
    OverallProblematicFileCount,
    OverallProblematicHunkCount,
    OverallScatterFactor,
)
from reviewability.metrics.registry import MetricRegistry
from reviewability.rules.definitions import hunk_rules, overall_rules
from reviewability.rules.engine import RuleEngine, RuleViolation
from reviewability.scoring.weighted import DefaultScorer


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


def create_analyzer(config: ReviewabilityConfig) -> Analyzer:
    """Build a fully configured ``Analyzer`` from a ``ReviewabilityConfig``."""
    registry = MetricRegistry()
    for metric in [
        HunkLinesChanged(),
        HunkAddedLines(),
        HunkRemovedLines(),
        HunkContextLines(),
        HunkChangeBalance(),
        HunkInterleaving(),
        FileLinesChanged(),
        OverallFilesChanged(),
        OverallLinesChanged(),
        OverallAddedLines(),
        OverallProblematicHunkCount(config.hunk_score_threshold),
        OverallProblematicFileCount(config.file_score_threshold),
        OverallScatterFactor(),
        MoveEditComplexity(config.max_move_lines, config.move_similarity_penalty),
    ]:
        registry.add(metric)

    scorer = DefaultScorer(
        max_hunk_lines=float(config.max_hunk_lines),
        max_diff_lines=float(config.max_diff_lines),
    )

    return Analyzer(
        engine=MetricEngine(registry, scorer),
        hunk_rule_engine=RuleEngine(hunk_rules(config)),
        overall_rule_engine=RuleEngine(overall_rules(config)),
    )
