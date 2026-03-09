from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric


class OverallFilesChanged(OverallMetric):
    name: str = "overall.files_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total number of files changed in the diff."
    remediation: str = "Split the change into smaller pull requests by concern."

    @override
    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(files),
            value_type=self.value_type,
            remediation=self.remediation,
        )
