from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff, HunkRewriteKind
from reviewability.metrics.base import FileMetric


class FileInPlaceRewriteLines(FileMetric):
    name: str = "file.in_place_rewrite_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Target-side lines in file hunks classified as in-place complex rewrites."
    remediation: str = "Break large in-place rewrites into smaller reviewable changes."

    @override
    def calculate(self, file: FileDiff) -> MetricValue:
        value = sum(
            hunk.added_count
            for hunk in file.hunks
            if hunk.rewrite_kind is HunkRewriteKind.IN_PLACE_REWRITE
        )
        return MetricValue(name=self.name, value=value, value_type=self.value_type)
