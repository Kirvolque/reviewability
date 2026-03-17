from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric


class OverallMovedRewriteLines(OverallMetric):
    name: str = "overall.moved_rewrite_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Target-side lines in hunks classified as moved complex rewrites."
    remediation: str = (
        "Moved rewrites combine relocation with behavior changes."
        " Separate the move from the modification into distinct commits."
    )

    @override
    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        del files
        value = sum(
            metric.value
            for hunk in hunks
            if (metric := hunk.metrics.metric("hunk.moved_rewrite_lines")) is not None
        )
        return MetricValue(name=self.name, value=value, value_type=self.value_type)
