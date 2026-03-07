from reviewability.domain.models import Diff
from reviewability.domain.report import AnalysisReport, FileAnalysis, HunkAnalysis
from reviewability.metrics.base import DiffMetric, FileMetric, HunkMetric


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
        return AnalysisReport(
            overall=[m.calculate(diff) for m in self._diff_metrics.values()],
            files=[
                FileAnalysis(
                    file=file,
                    metrics=[m.calculate(file) for m in self._file_metrics.values()],
                )
                for file in diff.files
            ],
            hunks=[
                HunkAnalysis(
                    hunk=hunk,
                    metrics=[m.calculate(hunk) for m in self._hunk_metrics.values()],
                )
                for file in diff.files
                for hunk in file.hunks
            ],
        )
