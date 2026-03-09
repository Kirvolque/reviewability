from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.metrics.base import HunkMetric


class HunkAddedLines(HunkMetric):
    name: str = "hunk.added_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of lines added in a hunk."
    remediation: str = "Break large additions into smaller, reviewable chunks."

    @override
    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.added_count,
            value_type=self.value_type,
        )
