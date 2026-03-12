from reviewability.config.models import ReviewabilityConfig
from reviewability.diff.enrichment import DiffEnricher
from reviewability.domain.models import Diff
from reviewability.domain.report import AnalysisReport
from reviewability.metrics.engine import MetricEngine
from reviewability.metrics.file import (
    FileAddedLines,
    FileHunkCount,
    FileLinesChanged,
    FileMaxHunkLines,
    FileRemovedLines,
)
from reviewability.metrics.hunk import (
    HunkAddedLines,
    HunkChurnRatio,
    HunkContextLines,
    HunkLinesChanged,
    HunkRemovedLines,
)
from reviewability.metrics.overall import (
    OverallAddedLines,
    OverallChangeEntropy,
    OverallChurnComplexity,
    OverallFilesChanged,
    OverallLargestFileRatio,
    OverallLinesChanged,
    OverallProblematicFileCount,
    OverallProblematicHunkCount,
    OverallRemovedLines,
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
        enricher: DiffEnricher | None = None,
    ) -> None:
        self._engine = engine
        self._hunk_rules = hunk_rule_engine
        self._overall_rules = overall_rule_engine
        self._enricher = enricher or DiffEnricher()

    def run(self, diff: Diff) -> tuple[AnalysisReport, list[RuleViolation]]:
        """Analyze a diff and return the report with all rule violations.

        Hunk-level rules are evaluated against each hunk's metrics.
        Overall rules are evaluated against the diff-level metrics.
        """
        report = self._engine.run(self._enricher.enrich(diff))

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
        HunkChurnRatio(),
        FileHunkCount(),
        FileLinesChanged(),
        FileAddedLines(),
        FileRemovedLines(),
        FileMaxHunkLines(),
        OverallFilesChanged(),
        OverallLinesChanged(),
        OverallAddedLines(),
        OverallRemovedLines(),
        OverallProblematicHunkCount(config.hunk_score_threshold),
        OverallProblematicFileCount(config.file_score_threshold),
        OverallChangeEntropy(),
        OverallLargestFileRatio(),
        OverallChurnComplexity(),
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
