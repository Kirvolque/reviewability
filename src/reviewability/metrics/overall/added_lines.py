from typing import override

from reviewability.domain.report import (
    FileAnalysis,
    HunkAnalysis,
    MetricValue,
    MetricValueType,
    OverallMetricResult,
)
from reviewability.metrics.base import OverallMetric


class OverallAddedLines(OverallMetric):
    name: str = "overall.added_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines added across the entire diff."
    remediation: str = "Keep additions under 400 lines per review session."

    @override
    def calculate(
        self, hunks: list[HunkAnalysis], files: list[FileAnalysis]
    ) -> OverallMetricResult:
        value = sum(m.value for h in hunks if (m := h.metrics.get("hunk.added_lines")) is not None)
        return OverallMetricResult(
            value=MetricValue(name=self.name, value=value, value_type=self.value_type)
        )
