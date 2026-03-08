from typing import override

from reviewability.domain.report import (
    FileAnalysis,
    HunkAnalysis,
    MetricValue,
    MetricValueType,
    OverallMetricResult,
)
from reviewability.metrics.base import OverallMetric


class OverallChurnComplexity(OverallMetric):
    name: str = "overall.churn_complexity"
    value_type: MetricValueType = MetricValueType.RATIO
    description: str = (
        "Average interleaving complexity across all hunks. "
        "Computed as mean(1 − |2×churn_ratio − 1|) per hunk: "
        "0.0 means all hunks are directional (pure additions or deletions), "
        "1.0 means all hunks are maximally interleaved (equal adds and removes)."
    )
    remediation: str = (
        "Split mixed hunks into separate directional commits: "
        "one for deletions, one for additions."
    )

    @override
    def calculate(
        self, hunks: list[HunkAnalysis], files: list[FileAnalysis]
    ) -> OverallMetricResult:
        mix_values = [
            1.0 - abs(2.0 * mv.value - 1.0)
            for h in hunks
            if (mv := h.metrics.get("hunk.churn_ratio")) is not None
        ]
        avg = sum(mix_values) / len(mix_values) if mix_values else 0.0
        return OverallMetricResult(
            value=MetricValue(name=self.name, value=avg, value_type=self.value_type)
        )
