from typing import override

from reviewability.domain.report import (
    FileAnalysis,
    HunkAnalysis,
    MetricValue,
    MetricValueType,
    OverallMetricResult,
)
from reviewability.metrics.base import OverallMetric


class OverallLinesChanged(OverallMetric):
    name: str = "overall.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines changed across the entire diff."
    remediation: str = "Reduce patch size by splitting unrelated changes into separate commits."

    @override
    def calculate(
        self, hunks: list[HunkAnalysis], files: list[FileAnalysis]
    ) -> OverallMetricResult:
        value = sum(
            m.value for h in hunks if (m := h.metrics.get("hunk.lines_changed")) is not None
        )
        return OverallMetricResult(
            value=MetricValue(name=self.name, value=value, value_type=self.value_type)
        )
