from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff
from reviewability.metrics.base import FileMetric


class FileMaxHunkLines(FileMetric):
    name: str = "file.max_hunk_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Lines changed in the largest single hunk within a file."
    remediation: str = "Split the large hunk into smaller, focused changes."

    @override
    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=max((h.added_count + h.removed_count for h in file.hunks), default=0),
            value_type=self.value_type,
        )
