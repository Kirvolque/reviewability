from typing import override

from reviewability.domain.models import Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import HunkMetric


class HunkChurnRatio(HunkMetric):
    name: str = "hunk.churn_ratio"
    value_type: MetricValueType = MetricValueType.RATIO
    description: str = (
        "Ratio of added lines to total changed lines in a hunk. "
        "Values near 0.0 indicate a mostly-deletion hunk; near 1.0, a mostly-addition hunk."
    )
    remediation: str = (
        "This hunk mixes deletions and additions together, making it hard to follow. "
        "Split into two separate commits: one that removes the old code, one that adds the new."
    )

    @override
    def calculate(self, hunk: Hunk) -> MetricValue:
        total = hunk.added_count + hunk.removed_count
        ratio = hunk.added_count / total if total > 0 else 0.0
        return MetricValue(
            name=self.name,
            value=ratio,
            value_type=self.value_type,
            remediation=self.remediation,
        )
