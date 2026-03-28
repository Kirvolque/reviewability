from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric


class OverallMovedLines(OverallMetric):
    name: str = "overall.moved_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Target-side lines in hunks identified as likely code movements."
    remediation: str | None = None

    @override
    def calculate(
        self, hunks: list[Analysis], files: list[Analysis], groups: list[Analysis]
    ) -> MetricValue:
        value = sum(
            m.value
            for h in hunks
            if h.subject.is_likely_moved
            if (m := h.metrics.metric("hunk.added_lines")) is not None
        )
        return MetricValue(name=self.name, value=value, value_type=self.value_type)
