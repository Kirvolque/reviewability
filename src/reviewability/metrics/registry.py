from reviewability.domain.models import Diff
from reviewability.domain.report import AnalysisReport, FileAnalysis, HunkAnalysis, OverallAnalysis
from reviewability.metrics.base import FileMetric, HunkMetric, OverallMetric


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

    def run(self, diff: Diff) -> AnalysisReport:
        """Run all registered metrics against the diff and return a fully computed report."""
        # Step 1: hunk metrics
        hunk_analyses = [
            HunkAnalysis(
                hunk=hunk,
                metrics=[m.calculate(hunk) for m in self._hunk_metrics.values()],
                score=0.0,  # TODO: populated by Scorer
            )
            for file in diff.files
            for hunk in file.hunks
        ]

        # Step 2: file metrics
        file_analyses = [
            FileAnalysis(
                file=file,
                metrics=[m.calculate(file) for m in self._file_metrics.values()],
                score=0.0,  # TODO: populated by Scorer
            )
            for file in diff.files
        ]

        # Step 3: overall metrics — derived from already-computed analyses
        overall = OverallAnalysis(
            metrics=[
                m.calculate(hunk_analyses, file_analyses) for m in self._overall_metrics.values()
            ],
            score=0.0,  # TODO: populated by Scorer
        )

        return AnalysisReport(
            overall=overall,
            files=file_analyses,
            hunks=hunk_analyses,
        )
