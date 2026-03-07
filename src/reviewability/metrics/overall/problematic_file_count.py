from reviewability.domain.report import FileAnalysis, HunkAnalysis, MetricValue, MetricValueType
from reviewability.metrics.base import OverallMetric


class OverallProblematicFileCount(OverallMetric):
    name: str = "overall.problematic_file_count"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of files with a reviewability score below the configured threshold."
    remediation: str = "Simplify or split files with low reviewability scores."

    def __init__(self, score_threshold: float) -> None:
        self._score_threshold = score_threshold

    def calculate(self, hunks: list[HunkAnalysis], files: list[FileAnalysis]) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=sum(1 for f in files if f.score < self._score_threshold),
            value_type=self.value_type,
        )
