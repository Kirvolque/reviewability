from reviewability.domain.models import FileDiff
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import FileMetric


class FileRemovedLines(FileMetric):
    name: str = "file.removed_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines removed across all hunks in a file."
    remediation: str = "Ensure deletions are isolated from unrelated additions."

    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=file.total_removed,
            value_type=self.value_type,
        )
