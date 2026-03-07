from reviewability.domain.models import Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import HunkMetric


class HunkContextLines(HunkMetric):
    name: str = "hunk.context_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of unchanged context lines surrounding the change in a hunk."
    remediation: str = "Prefer smaller, focused hunks with less surrounding context."

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(hunk.context_lines),
            value_type=self.value_type,
        )
