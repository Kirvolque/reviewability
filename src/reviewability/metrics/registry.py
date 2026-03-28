from reviewability.metrics.base import FileMetric, HunkMetric, MoveMetric, OverallMetric


class MetricRegistry:
    """Stores metric definitions, organised by level.

    This is the only intentionally mutable structure in the codebase.
    Metrics can only be added, not removed or replaced.
    """

    def __init__(self) -> None:
        self._hunk_metrics: dict[str, HunkMetric] = {}
        self._file_metrics: dict[str, FileMetric] = {}
        self._move_metrics: dict[str, MoveMetric] = {}
        self._overall_metrics: dict[str, OverallMetric] = {}

    def add(self, metric: HunkMetric | FileMetric | MoveMetric | OverallMetric) -> None:
        """Register a metric. Silently replaces if a metric with the same name exists."""
        if isinstance(metric, HunkMetric):
            self._hunk_metrics[metric.name] = metric
        elif isinstance(metric, FileMetric):
            self._file_metrics[metric.name] = metric
        elif isinstance(metric, MoveMetric):
            self._move_metrics[metric.name] = metric
        elif isinstance(metric, OverallMetric):
            self._overall_metrics[metric.name] = metric

    def hunk_metrics(self) -> list[HunkMetric]:
        """Return all registered hunk-level metrics."""
        return list(self._hunk_metrics.values())

    def file_metrics(self) -> list[FileMetric]:
        """Return all registered file-level metrics."""
        return list(self._file_metrics.values())

    def move_metrics(self) -> list[MoveMetric]:
        """Return all registered move-level metrics."""
        return list(self._move_metrics.values())

    def overall_metrics(self) -> list[OverallMetric]:
        """Return all registered overall-level metrics."""
        return list(self._overall_metrics.values())
