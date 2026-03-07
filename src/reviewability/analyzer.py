from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.models import Diff
from reviewability.domain.report import AnalysisReport
from reviewability.metrics.builtin import (
    FileHunkCount,
    FileLinesChanged,
    HunkAddedLines,
    HunkLinesChanged,
    HunkRemovedLines,
    OverallFilesChanged,
    OverallLinesChanged,
    OverallProblematicFileCount,
    OverallProblematicHunkCount,
)
from reviewability.metrics.registry import MetricRegistry
from reviewability.rules.engine import Rule, RuleEngine, RuleViolation, Severity
from reviewability.scoring.weighted import MetricWeight, WeightedReviewabilityScorer


def _build_registry(config: ReviewabilityConfig) -> MetricRegistry:
    registry = MetricRegistry()
    for metric in [
        HunkLinesChanged(),
        HunkAddedLines(),
        HunkRemovedLines(),
        FileHunkCount(),
        FileLinesChanged(),
        OverallFilesChanged(),
        OverallLinesChanged(),
        OverallProblematicHunkCount(config.hunk_score_threshold),
        OverallProblematicFileCount(config.file_score_threshold),
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


def _build_hunk_rules(config: ReviewabilityConfig) -> list[Rule]:
    return [
        Rule(
            metric_name="hunk.lines_changed",
            threshold=config.max_hunk_lines,
            operator="gt",
            severity=Severity.WARNING,
            message="Hunk exceeds the maximum allowed size",
        ),
    ]


def _build_overall_rules(config: ReviewabilityConfig) -> list[Rule]:
    return [
        Rule(
            metric_name="overall.lines_changed",
            threshold=config.max_diff_lines,
            operator="gt",
            severity=Severity.ERROR,
            message="Diff exceeds the maximum total lines changed",
        ),
        Rule(
            metric_name="overall.problematic_hunk_count",
            threshold=config.max_problematic_hunks,
            operator="gt",
            severity=Severity.WARNING,
            message="Diff contains too many problematic hunks",
        ),
        Rule(
            metric_name="overall.problematic_file_count",
            threshold=config.max_problematic_files,
            operator="gt",
            severity=Severity.WARNING,
            message="Diff contains too many problematic files",
        ),
    ]


class Analyzer:
    """Runs diff analysis and rule evaluation driven by a ReviewabilityConfig.

    Builds the metric registry, scorer, and rule engine from the config,
    then exposes a single ``run`` method to analyze a diff.
    """

    def __init__(self, config: ReviewabilityConfig) -> None:
        self._registry = _build_registry(config)
        self._scorer = _build_scorer(config)
        self._hunk_rules = RuleEngine(_build_hunk_rules(config))
        self._overall_rules = RuleEngine(_build_overall_rules(config))

    def run(self, diff: Diff) -> tuple[AnalysisReport, list[RuleViolation]]:
        """Analyze a diff and return the report with all rule violations.

        Hunk-level rules are evaluated against each hunk's metrics.
        Overall rules are evaluated against the diff-level metrics.
        """
        report = self._registry.run(diff, self._scorer)

        hunk_violations = [
            violation
            for hunk in report.hunks
            for violation in self._hunk_rules.evaluate(hunk.metrics)
        ]
        overall_violations = self._overall_rules.evaluate(report.overall.metrics)

        return report, hunk_violations + overall_violations
