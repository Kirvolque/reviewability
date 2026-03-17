from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk, HunkRewriteKind
from reviewability.metrics.base import HunkMetric


class HunkMovedRewriteLines(HunkMetric):
    name: str = "hunk.moved_rewrite_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Target-side lines in a hunk classified as a moved complex rewrite."
    remediation: str = "Separate relocation from behavioural rewrites when possible."

    @override
    def calculate(self, hunk: Hunk) -> MetricValue:
        value = hunk.added_count if hunk.rewrite_kind is HunkRewriteKind.MOVED_REWRITE else 0
        return MetricValue(name=self.name, value=value, value_type=self.value_type)
