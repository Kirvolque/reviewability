from typing import override

from reviewability.domain.models import FileDiff
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import FileMetric


class FileLinesChanged(FileMetric):
    name: str = "file.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines added and removed across all hunks in a file."
    remediation: str = "Split large file changes across multiple commits or pull requests."

    @override
    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=file.total_added + file.total_removed,
            value_type=self.value_type,
        )
