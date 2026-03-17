from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric


class OverallInPlaceRewriteLines(OverallMetric):
    name: str = "overall.in_place_rewrite_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Target-side lines in hunks classified as in-place complex rewrites."
    remediation: str = (
        "Large in-place rewrites are hard to review."
        " Split mechanical cleanup from logic changes."
    )

    @override
    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        del files
        value = sum(
            metric.value
            for hunk in hunks
            if (metric := hunk.metrics.metric("hunk.in_place_rewrite_lines")) is not None
        )
        return MetricValue(name=self.name, value=value, value_type=self.value_type)
