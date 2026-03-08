from typing import override

from reviewability.domain.report import (
    FileAnalysis,
    HunkAnalysis,
    MetricValue,
    MetricValueType,
    OverallMetricResult,
)
from reviewability.metrics.base import OverallMetric


class OverallFilesChanged(OverallMetric):
    name: str = "overall.files_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total number of files changed in the diff."
    remediation: str = "Split the change into smaller pull requests by concern."

    @override
    def calculate(
        self, hunks: list[HunkAnalysis], files: list[FileAnalysis]
    ) -> OverallMetricResult:
        return OverallMetricResult(
            value=MetricValue(name=self.name, value=len(files), value_type=self.value_type)
        )
