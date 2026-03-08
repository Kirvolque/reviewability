from typing import override

from reviewability.domain.models import FileDiff
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import FileMetric


class FileAddedLines(FileMetric):
    name: str = "file.added_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines added across all hunks in a file."
    remediation: str = "Break large additions into smaller, reviewable pull requests."

    @override
    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=file.total_added,
            value_type=self.value_type,
        )
