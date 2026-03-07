from reviewability.domain.models import Diff, FileDiff, Hunk
from reviewability.domain.report import (
    AnalysisReport,
    FileAnalysis,
    HunkAnalysis,
    MetricResults,
    OverallAnalysis,
)
from reviewability.metrics.base import FileMetric, HunkMetric, OverallMetric
from reviewability.scoring.base import ReviewabilityScorer


class MetricRegistry:
    """Stores metric definitions and runs them against a diff in the correct order.

    This is the only intentionally mutable structure in the codebase.
    Metrics can only be added, not removed or replaced.
    Calculation order is enforced: hunk -> file -> overall.
    """

    def __init__(self) -> None:
        self._hunk_metrics: dict[str, HunkMetric] = {}
        self._file_metrics: dict[str, FileMetric] = {}
        self._overall_metrics: dict[str, OverallMetric] = {}

    def add(self, metric: HunkMetric | FileMetric | OverallMetric) -> None:
        """Register a metric. Silently replaces if a metric with the same name exists."""
        if isinstance(metric, HunkMetric):
            self._hunk_metrics[metric.name] = metric
        elif isinstance(metric, FileMetric):
            self._file_metrics[metric.name] = metric
        elif isinstance(metric, OverallMetric):
            self._overall_metrics[metric.name] = metric

    def hunk_metrics(self) -> list[HunkMetric]:
        return list(self._hunk_metrics.values())

    def file_metrics(self) -> list[FileMetric]:
        return list(self._file_metrics.values())

    def overall_metrics(self) -> list[OverallMetric]:
        return list(self._overall_metrics.values())

    def run(self, diff: Diff, scorer: ReviewabilityScorer) -> AnalysisReport:
        """Run all registered metrics against the diff and return a fully computed report.

        Construction is strictly bottom-up: scores are computed before each
        analysis object is constructed, so no object is ever incomplete.
        """
        # Step 1: hunk metrics + scores -> HunkAnalysis (fully built)
        hunk_analyses = [
            _build_hunk_analysis(
                hunk, [m.calculate(hunk) for m in self._hunk_metrics.values()], scorer
            )  # noqa: E501
            for file in diff.files
            for hunk in file.hunks
        ]

        # Step 2: file metrics + scores -> FileAnalysis (fully built)
        file_analyses = [
            _build_file_analysis(
                file, [m.calculate(file) for m in self._file_metrics.values()], scorer
            )  # noqa: E501
            for file in diff.files
        ]

        # Step 3: overall metrics + score -> OverallAnalysis (fully built)
        overall_metrics = MetricResults(
            [m.calculate(hunk_analyses, file_analyses) for m in self._overall_metrics.values()]
        )
        overall = OverallAnalysis(
            metrics=overall_metrics,
            score=scorer.overall_score(overall_metrics),
        )

        return AnalysisReport(
            overall=overall,
            files=file_analyses,
            hunks=hunk_analyses,
        )


def _build_hunk_analysis(hunk: Hunk, metrics: list, scorer: ReviewabilityScorer) -> HunkAnalysis:
    results = MetricResults(metrics)
    return HunkAnalysis(hunk=hunk, metrics=results, score=scorer.hunk_score(results))


def _build_file_analysis(
    file: FileDiff, metrics: list, scorer: ReviewabilityScorer
) -> FileAnalysis:
    results = MetricResults(metrics)
    return FileAnalysis(file=file, metrics=results, score=scorer.file_score(results))
