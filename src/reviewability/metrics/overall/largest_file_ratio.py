from typing import override

from reviewability.domain.report import (
    FileAnalysis,
    HunkAnalysis,
    MetricValue,
    MetricValueType,
    OverallMetricResult,
)
from reviewability.metrics.base import OverallMetric


class OverallLargestFileRatio(OverallMetric):
    name: str = "overall.largest_file_ratio"
    value_type: MetricValueType = MetricValueType.RATIO
    description: str = (
        "Fraction of total diff lines concentrated in the single most-changed file. "
        "A low value means changes are scattered across many files."
    )
    remediation: str = "Split the diff so no single file dominates, or group scattered changes."

    @override
    def calculate(
        self, hunks: list[HunkAnalysis], files: list[FileAnalysis]
    ) -> OverallMetricResult:
        values = [m.value for f in files if (m := f.metrics.get("file.lines_changed")) is not None]
        total = sum(values)
        ratio = max(values) / total if total > 0 else 0.0
        return OverallMetricResult(
            value=MetricValue(name=self.name, value=ratio, value_type=self.value_type)
        )
