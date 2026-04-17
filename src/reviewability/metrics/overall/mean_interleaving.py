from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric
from reviewability.metrics.hunk.interleaving import HunkInterleaving
from reviewability.metrics.hunk.lines_changed import HunkLinesChanged


class OverallMeanInterleaving(OverallMetric):
    """Weighted mean of hunk.interleaving across singleton hunks [0.0, 1.0].

    Each hunk's interleaving score is weighted by its line count so that large,
    highly-interleaved hunks dominate the signal. Hunks that are part of a move
    are excluded (they are scored at the move level instead).

    - 0.0 — all hunks are clean block substitutions (additions then deletions or vice versa)
    - 1.0 — all hunks alternate every line
    """

    name: str = "overall.mean_interleaving"
    value_type: MetricValueType = MetricValueType.RATIO
    description: str = (
        "Weighted mean of hunk.interleaving across singleton hunks "
        "(weighted by hunk size). 0.0 = no interleaving, 1.0 = maximum."
    )
    remediation: str = (
        "Many hunks have heavily interleaved additions and deletions. "
        "Separate deletions and additions into focused commits."
    )

    @override
    def calculate(
        self, hunks: list[Analysis], files: list[Analysis], moves: list[Analysis]
    ) -> MetricValue:
        total_weight = 0.0
        weighted_sum = 0.0
        for hunk in hunks:
            interleaving_mv = hunk.metric(HunkInterleaving.name)
            lines_mv = hunk.metric(HunkLinesChanged.name)
            if interleaving_mv is None or lines_mv is None:
                continue
            weight = max(lines_mv.value, 1)
            weighted_sum += interleaving_mv.value * weight
            total_weight += weight

        value = weighted_sum / total_weight if total_weight > 0 else 0.0
        return MetricValue(
            name=self.name,
            value=round(value, 4),
            value_type=self.value_type,
            remediation=self.remediation if value > 0.1 else None,
        )
