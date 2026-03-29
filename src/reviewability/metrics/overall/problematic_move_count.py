from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric


class OverallProblematicMoveCount(OverallMetric):
    name: str = "overall.problematic_move_count"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of moves with a reviewability score below the configured threshold."
    remediation: str = "Simplify or split moves with low reviewability scores."

    def __init__(self, score_threshold: float) -> None:
        self._score_threshold = score_threshold

    @override
    def calculate(
        self, hunks: list[Analysis], files: list[Analysis], moves: list[Analysis]
    ) -> MetricValue:
        problematic = [m for m in moves if m.score < self._score_threshold]
        return MetricValue(
            name=self.name,
            value=len(problematic),
            value_type=self.value_type,
            remediation=self.remediation,
        )
