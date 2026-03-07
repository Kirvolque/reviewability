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
        file_analyses = []
        hunk_analyses = []

        for file in diff.files:
            hunks = tuple(
                HunkAnalysis(
                    hunk=hunk,
                    metrics=tuple(m.calculate(hunk) for m in self._hunk_metrics.values()),
                )
                for hunk in file.hunks
            )
            hunk_analyses.extend(hunks)
            file_analyses.append(
                FileAnalysis(
                    file=file,
                    metrics=tuple(m.calculate(file) for m in self._file_metrics.values()),
                )
            )

        return AnalysisReport(
            overall=tuple(m.calculate(diff) for m in self._diff_metrics.values()),
            files=tuple(file_analyses),
            hunks=tuple(hunk_analyses),
        )
