from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric
from reviewability.metrics.hunk.lines_changed import HunkLinesChanged


class OverallUnexplainedLines(OverallMetric):
    """Lines that still require individual review after exact move correspondence.

    Singleton hunks are unexplained by definition. For detected moves, only residual
    lines not covered by exact old-to-new correspondence are included. This metric is
    intentionally separate from raw diff size, which remains useful for policy limits.
    """

    name: str = "overall.unexplained_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Changed lines not explained by exact move correspondence."
    remediation: str | None = None

    @override
    def calculate(
        self, hunks: list[Analysis], files: list[Analysis], moves: list[Analysis]
    ) -> MetricValue:
        singleton_lines = sum(
            metric.value
            for hunk in hunks
            if (metric := hunk.metrics.metric(HunkLinesChanged.name)) is not None
        )
        move_residual_lines = sum(
            len(move.subject.residual_removed_lines) + len(move.subject.residual_added_lines)
            for move in moves
        )
        return MetricValue(
            name=self.name,
            value=singleton_lines + move_residual_lines,
            value_type=self.value_type,
        )
