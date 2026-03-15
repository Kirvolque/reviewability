from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.metrics.base import HunkMetric


class HunkChangeBalance(HunkMetric):
    name: str = "hunk.change_balance"
    value_type: MetricValueType = MetricValueType.RATIO
    description: str = (
        "Directionality ratio of a hunk: added_lines / (added_lines + removed_lines). "
        "0.0 = pure deletion, 1.0 = pure addition, 0.5 = equal mix of adds and removes. "
        "Measures change direction, not raw churn volume."
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
