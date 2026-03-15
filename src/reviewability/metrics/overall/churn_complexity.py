from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric
from reviewability.metrics.hunk.change_balance import HunkChangeBalance

_INTERLEAVING_THRESHOLD = 0.5


class OverallChurnComplexity(OverallMetric):
    name: str = "overall.churn_complexity"
    value_type: MetricValueType = MetricValueType.RATIO
    description: str = (
        "Average interleaving complexity across all hunks. "
        "Computed as mean(1 − |2×change_balance − 1|) per hunk: "
        "0.0 means all hunks are directional (pure additions or deletions), "
        "1.0 means all hunks are maximally interleaved (equal adds and removes)."
    )
    remediation: str = (
        "Split mixed hunks into separate directional commits: one for deletions, one for additions."
    )

    @override
    def calculate(self, hunks: list[Analysis], files: list[Analysis]) -> MetricValue:
        mix_per_hunk: list[tuple[float, Analysis]] = []
        for h in hunks:
            if h.subject.is_likely_moved:
                continue
            mv = h.metrics.metric(HunkChangeBalance.name)
            if mv is not None:
                mix = 1.0 - abs(2.0 * mv.value - 1.0)
                mix_per_hunk.append((mix, h))

        avg = sum(m for m, _ in mix_per_hunk) / len(mix_per_hunk) if mix_per_hunk else 0.0

        return MetricValue(
            name=self.name,
            value=avg,
            value_type=self.value_type,
            remediation=self.remediation,
        )
