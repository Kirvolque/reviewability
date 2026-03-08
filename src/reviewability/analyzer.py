from reviewability.config.models import ReviewabilityConfig
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
from reviewability.scoring.weighted import MetricWeight, WeightedReviewabilityScorer


def _build_registry(config: ReviewabilityConfig) -> MetricRegistry:
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
    ]:
        registry.add(metric)
    return registry


def _build_scorer(config: ReviewabilityConfig) -> WeightedReviewabilityScorer:
    return WeightedReviewabilityScorer(
        hunk_weights=[MetricWeight("hunk.lines_changed", max_value=float(config.max_hunk_lines))],
        file_weights=[MetricWeight("file.lines_changed", max_value=float(config.max_diff_lines))],
        overall_weights=[
            MetricWeight("overall.lines_changed", max_value=float(config.max_diff_lines))
        ],
    )


class Analyzer:
    """Runs diff analysis and rule evaluation driven by a ReviewabilityConfig.

    Builds the metric registry, scorer, and rule engine from the config,
    then exposes a single ``run`` method to analyze a diff.
    """

    def __init__(self, config: ReviewabilityConfig) -> None:
        registry = _build_registry(config)
        scorer = _build_scorer(config)
        self._engine = MetricEngine(registry, scorer)
        self._hunk_rules = RuleEngine(hunk_rules(config))
        self._overall_rules = RuleEngine(overall_rules(config))

    def run(self, diff: Diff) -> tuple[AnalysisReport, list[RuleViolation]]:
        """Analyze a diff and return the report with all rule violations.

        Hunk-level rules are evaluated against each hunk's metrics.
        Overall rules are evaluated against the diff-level metrics.
        """
        report = self._engine.run(diff)

        hunk_violations = [
            violation
            for hunk in report.hunks
            for violation in self._hunk_rules.evaluate(hunk.metrics)
        ]
        overall_violations = self._overall_rules.evaluate(report.overall.metrics)

        return report, hunk_violations + overall_violations
