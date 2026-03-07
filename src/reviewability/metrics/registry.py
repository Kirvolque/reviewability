from reviewability.metrics.base import HunkMetric, FileMetric, DiffMetric, MetricResult, MetricScope
from reviewability.domain.models import Diff


class MetricRegistry:
    def __init__(self) -> None:
        self._hunk_metrics: dict[str, HunkMetric] = {}
        self._file_metrics: dict[str, FileMetric] = {}
        self._diff_metrics: dict[str, DiffMetric] = {}

    def register(self, metric: HunkMetric | FileMetric | DiffMetric) -> None:
        match metric.scope:
            case MetricScope.HUNK:
                self._hunk_metrics[metric.name] = metric
            case MetricScope.FILE:
                self._file_metrics[metric.name] = metric
            case MetricScope.DIFF:
                self._diff_metrics[metric.name] = metric

    def run(self, diff: Diff) -> list[MetricResult]:
        results: list[MetricResult] = []

        for file in diff.files:
            for i, hunk in enumerate(file.hunks):
                for metric in self._hunk_metrics.values():
                    result = metric.calculate(hunk)
                    result.file_path = file.path
                    result.hunk_index = i
                    results.append(result)

            for metric in self._file_metrics.values():
                results.append(metric.calculate(file))

        for metric in self._diff_metrics.values():
            results.append(metric.calculate(diff))

        return results
