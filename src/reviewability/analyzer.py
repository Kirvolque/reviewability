from reviewability.config.models import ReviewabilityConfig
from reviewability.domain.models import Diff
from reviewability.domain.report import AnalysisReport
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
from reviewability.rules.engine import Rule, RuleEngine, RuleViolation, Severity
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


def _build_hunk_rules(config: ReviewabilityConfig) -> list[Rule]:
    return [
        Rule(
            severity=Severity.WARNING,
            check=lambda m: (
                f"Hunk has {v.value} lines, exceeds limit of {config.max_hunk_lines}"
                if (v := m.get("hunk.lines_changed")) is not None
                and v.value > config.max_hunk_lines
                else None
            ),
        ),
    ]


def _build_overall_rules(config: ReviewabilityConfig) -> list[Rule]:
    return [
        Rule(
            severity=Severity.ERROR,
            check=lambda m: (
                f"Diff has {v.value} lines changed, exceeds limit of {config.max_diff_lines}"
                if (v := m.get("overall.lines_changed")) is not None
                and v.value > config.max_diff_lines
                else None
            ),
        ),
        Rule(
            severity=Severity.WARNING,
            check=lambda m: (
                f"Diff has {v.value} problematic hunks, exceeds limit of {config.max_problematic_hunks}"  # noqa: E501
                if (v := m.get("overall.problematic_hunk_count")) is not None
                and v.value > config.max_problematic_hunks
                else None
            ),
        ),
        Rule(
            severity=Severity.WARNING,
            check=lambda m: (
                f"Diff has {v.value} problematic files, exceeds limit of {config.max_problematic_files}"  # noqa: E501
                if (v := m.get("overall.problematic_file_count")) is not None
                and v.value > config.max_problematic_files
                else None
            ),
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
