from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.metrics.base import HunkMetric


class HunkIsLikelyMoved(HunkMetric):
    name: str = "hunk.is_likely_moved"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "1 if this hunk is likely a movement of code from another location, 0 otherwise."  # noqa: E501
    remediation: str | None = None

    @override
    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=1 if hunk.is_likely_moved else 0,
            value_type=self.value_type,
        )
