from typing import override

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
        return MetricValue(
            name=self.name,
            value=len(hunk.added_lines) + len(hunk.removed_lines),
            value_type=self.value_type,
        )
