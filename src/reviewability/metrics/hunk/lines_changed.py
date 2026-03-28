from typing import override

from reviewability.diff.line_filter import meaningful_lines
from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.metrics.base import HunkMetric


class HunkLinesChanged(HunkMetric):
    name: str = "hunk.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines added and removed in a hunk, excluding imports and blank lines."
    remediation: str = "Split the hunk into smaller, focused changes."

    @override
    def calculate(self, hunk: Hunk) -> MetricValue:
        added = len(meaningful_lines(hunk.added_lines, hunk.file_path))
        removed = len(meaningful_lines(hunk.removed_lines, hunk.file_path))
        return MetricValue(
            name=self.name,
            value=added + removed,
            value_type=self.value_type,
        )
