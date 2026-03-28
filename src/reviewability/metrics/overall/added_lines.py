from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric


class OverallAddedLines(OverallMetric):
    name: str = "overall.added_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines added across the entire diff."
    remediation: str = "Keep additions under 400 lines per review session."

    @override
    def calculate(
        self, hunks: list[Analysis], files: list[Analysis], groups: list[Analysis]
    ) -> MetricValue:
        value = sum(
            m.value for h in hunks if (m := h.metrics.metric("hunk.added_lines")) is not None
        )
        return MetricValue(
            name=self.name,
            value=value,
            value_type=self.value_type,
            remediation=self.remediation,
        )
