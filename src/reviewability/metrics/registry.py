from reviewability.metrics.base import HunkMetric, FileMetric, DiffMetric
from reviewability.domain.models import Diff
from reviewability.domain.report import AnalysisReport, HunkAnalysis, FileAnalysis


class MetricRegistry:
    def __init__(self) -> None:
        self._hunk_metrics: dict[str, HunkMetric] = {}
        self._file_metrics: dict[str, FileMetric] = {}
        self._diff_metrics: dict[str, DiffMetric] = {}

    def register(self, metric: HunkMetric | FileMetric | DiffMetric) -> None:
        if isinstance(metric, HunkMetric):
            self._hunk_metrics[metric.name] = metric
        elif isinstance(metric, FileMetric):
            self._file_metrics[metric.name] = metric
        elif isinstance(metric, DiffMetric):
            self._diff_metrics[metric.name] = metric

    def run(self, diff: Diff) -> AnalysisReport:
        report = AnalysisReport()

        for file in diff.files:
            hunk_analyses = []
            for hunk in file.hunks:
                metrics = [m.calculate(hunk) for m in self._hunk_metrics.values()]
                hunk_analyses.append(HunkAnalysis(hunk=hunk, metrics=metrics))

            file_metrics = [m.calculate(file) for m in self._file_metrics.values()]
            report.files.append(FileAnalysis(file=file, metrics=file_metrics))
            report.hunks.extend(hunk_analyses)

        report.overall = [m.calculate(diff) for m in self._diff_metrics.values()]

        return report
