from typing import override

from reviewability.domain.report import (
    Analysis,
    MetricValue,
    MetricValueType,
    OverallMetricResult,
)
from reviewability.metrics.base import OverallMetric


class OverallRemovedLines(OverallMetric):
    name: str = "overall.removed_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines removed across the entire diff."
    remediation: str = "Ensure large deletions are reviewed separately from additions."

    @override
    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> OverallMetricResult:
        value = sum(
            m.value for h in hunks if (m := h.metrics.get("hunk.removed_lines")) is not None
        )
        return OverallMetricResult(
            value=MetricValue(name=self.name, value=value, value_type=self.value_type)
        )
