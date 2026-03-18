from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff
from reviewability.metrics.base import FileMetric


class FileMovedLines(FileMetric):
    name: str = "file.moved_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Target-side lines in hunks identified as likely code movements."
    remediation: str | None = None

    @override
    def calculate(self, file: FileDiff) -> MetricValue:
        value = sum(hunk.added_count for hunk in file.hunks if hunk.is_likely_moved)
        return MetricValue(name=self.name, value=value, value_type=self.value_type)
