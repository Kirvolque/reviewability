from reviewability.domain.report import FileAnalysis, HunkAnalysis, MetricValue, MetricValueType
from reviewability.metrics.base import OverallMetric


class OverallFilesChanged(OverallMetric):
    name: str = "overall.files_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total number of files changed in the diff."
    remediation: str = "Split the change into smaller pull requests by concern."

    def calculate(self, hunks: list[HunkAnalysis], files: list[FileAnalysis]) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(files),
            value_type=self.value_type,
        )
