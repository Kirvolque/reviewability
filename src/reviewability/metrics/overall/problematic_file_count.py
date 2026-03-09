from typing import override

from reviewability.domain.report import (
    Analysis,
    MetricValue,
    MetricValueType,
)
from reviewability.metrics.base import OverallMetric


class OverallProblematicFileCount(OverallMetric):
    name: str = "overall.problematic_file_count"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of files with a reviewability score below the configured threshold."
    remediation: str = "Simplify or split files with low reviewability scores."

    def __init__(self, score_threshold: float) -> None:
        self._score_threshold = score_threshold

    @override
    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        problematic = [f for f in files if f.score < self._score_threshold]
        return MetricValue(
            name=self.name,
            value=len(problematic),
            value_type=self.value_type,
            remediation=self.remediation,
        )
