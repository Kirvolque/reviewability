from typing import override

from reviewability.domain.report import (
    Analysis,
    Cause,
    MetricValue,
    MetricValueType,
)
from reviewability.metrics.base import OverallMetric


class OverallProblematicHunkCount(OverallMetric):
    name: str = "overall.problematic_hunk_count"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of hunks with a reviewability score below the configured threshold."
    remediation: str = "Simplify or split hunks with low reviewability scores."

    def __init__(self, score_threshold: float) -> None:
        self._score_threshold = score_threshold

    @override
    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        problematic = [h for h in hunks if h.score < self._score_threshold]
        return MetricValue(
            name=self.name,
            value=len(problematic),
            value_type=self.value_type,
            remediation=self.remediation,
            causes=[Cause(value=h) for h in problematic],
        )
