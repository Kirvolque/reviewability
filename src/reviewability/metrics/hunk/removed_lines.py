from typing import override

from reviewability.diff.line_filter import meaningful_lines
from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.metrics.base import HunkMetric


class HunkRemovedLines(HunkMetric):
    name: str = "hunk.removed_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Lines removed in a hunk, excluding imports and blank lines."
    remediation: str = "Ensure deletions are isolated from unrelated changes."

    @override
    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(meaningful_lines(hunk.removed_lines, hunk.file_path)),
            value_type=self.value_type,
        )
