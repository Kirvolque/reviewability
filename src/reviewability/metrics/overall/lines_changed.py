from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric


class OverallLinesChanged(OverallMetric):
    name: str = "overall.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines changed across the entire diff."
    remediation: str = "Reduce patch size by splitting unrelated changes into separate commits."

    @override
    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        value = sum(
            m.value for h in hunks if (m := h.metrics.metric("hunk.lines_changed")) is not None
        )
        return MetricValue(
            name=self.name,
            value=value,
            value_type=self.value_type,
            remediation=self.remediation,
        )
