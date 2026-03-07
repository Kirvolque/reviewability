from reviewability.domain.models import Diff
from reviewability.domain.report import AnalysisReport, FileAnalysis, HunkAnalysis
from reviewability.metrics.base import FileMetric, HunkMetric, OverallMetric


class MetricRegistry:
    def __init__(self) -> None:
        self._hunk_metrics: dict[str, HunkMetric] = {}
        self._file_metrics: dict[str, FileMetric] = {}
        self._overall_metrics: dict[str, OverallMetric] = {}

    def add(self, metric: HunkMetric | FileMetric | OverallMetric) -> None:
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
        # Step 1: hunk metrics
        hunk_analyses = [
            HunkAnalysis(
                hunk=hunk,
                metrics=[m.calculate(hunk) for m in self._hunk_metrics.values()],
            )
            for file in diff.files
            for hunk in file.hunks
        ]

        # Step 2: file metrics
        file_analyses = [
            FileAnalysis(
                file=file,
                metrics=[m.calculate(file) for m in self._file_metrics.values()],
            )
            for file in diff.files
        ]

        # Step 3: overall metrics — derived from already-computed analyses
        overall = [
            m.calculate(hunk_analyses, file_analyses) for m in self._overall_metrics.values()
        ]

        return AnalysisReport(
            overall=overall,
            files=file_analyses,
            hunks=hunk_analyses,
        )
