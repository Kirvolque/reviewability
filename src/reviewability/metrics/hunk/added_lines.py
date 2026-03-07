from reviewability.domain.models import Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import HunkMetric


class HunkAddedLines(HunkMetric):
    name: str = "hunk.added_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of lines added in a hunk."
    remediation: str = "Break large additions into smaller, reviewable chunks."

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.added_count,
            value_type=self.value_type,
        )
