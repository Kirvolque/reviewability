from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk, HunkRewriteKind
from reviewability.metrics.base import HunkMetric


class HunkInPlaceRewriteLines(HunkMetric):
    name: str = "hunk.in_place_rewrite_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Target-side lines in a hunk classified as an in-place complex rewrite."
    remediation: str = "Split the rewrite into smaller, easier-to-follow steps."

    @override
    def calculate(self, hunk: Hunk) -> MetricValue:
        value = hunk.added_count if hunk.rewrite_kind is HunkRewriteKind.IN_PLACE_REWRITE else 0
        return MetricValue(
            name=self.name, value=value, value_type=self.value_type, remediation=self.remediation
        )
