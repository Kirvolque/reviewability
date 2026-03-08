from typing import override

from reviewability.domain.models import FileDiff
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import FileMetric


class FileHunkCount(FileMetric):
    name: str = "file.hunk_count"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of separate change regions (hunks) in a file."
    remediation: str = "Consider grouping related changes to reduce scattered edits."

    @override
    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(file.hunks),
            value_type=self.value_type,
        )
