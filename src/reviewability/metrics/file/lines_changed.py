from typing import override

from reviewability.diff.line_filter import meaningful_lines
from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff
from reviewability.metrics.base import FileMetric


class FileLinesChanged(FileMetric):
    name: str = "file.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = (
        "Total lines added and removed across all hunks in a file, "
        "excluding imports and blank lines."
    )
    remediation: str = "Split large file changes across multiple commits or pull requests."

    @override
    def calculate(self, file: FileDiff) -> MetricValue:
        total = sum(
            len(meaningful_lines(hunk.added_lines, file.path))
            + len(meaningful_lines(hunk.removed_lines, file.path))
            for hunk in file.hunks
        )
        return MetricValue(
            name=self.name,
            value=total,
            value_type=self.value_type,
        )
