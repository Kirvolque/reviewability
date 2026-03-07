from reviewability.domain.report import FileAnalysis, HunkAnalysis, MetricValue, MetricValueType
from reviewability.metrics.base import OverallMetric


class OverallRemovedLines(OverallMetric):
    name: str = "overall.removed_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines removed across the entire diff."
    remediation: str = "Ensure large deletions are reviewed separately from additions."

    def calculate(self, hunks: list[HunkAnalysis], files: list[FileAnalysis]) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=sum(
                m.value for h in hunks if (m := h.metrics.get("hunk.removed_lines")) is not None
            ),
            value_type=self.value_type,
        )
