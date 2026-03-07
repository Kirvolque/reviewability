from reviewability.domain.models import Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import HunkMetric


class HunkRemovedLines(HunkMetric):
    name: str = "hunk.removed_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of lines removed in a hunk."
    remediation: str = "Ensure deletions are isolated from unrelated changes."

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.removed_count,
            value_type=self.value_type,
        )
