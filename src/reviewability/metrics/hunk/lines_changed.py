from reviewability.domain.models import Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import HunkMetric


class HunkLinesChanged(HunkMetric):
    name: str = "hunk.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines added and removed in a hunk."
    remediation: str = "Split the hunk into smaller, focused changes."

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.added_count + hunk.removed_count,
            value_type=self.value_type,
        )
