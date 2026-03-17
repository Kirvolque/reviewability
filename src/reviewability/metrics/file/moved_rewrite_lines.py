from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff, HunkRewriteKind
from reviewability.metrics.base import FileMetric


class FileMovedRewriteLines(FileMetric):
    name: str = "file.moved_rewrite_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Target-side lines in file hunks classified as moved complex rewrites."
    remediation: str = "Separate moved rewrites from the main behavioural change when possible."

    @override
    def calculate(self, file: FileDiff) -> MetricValue:
        value = sum(
            hunk.added_count
            for hunk in file.hunks
            if hunk.rewrite_kind is HunkRewriteKind.MOVED_REWRITE
        )
        return MetricValue(name=self.name, value=value, value_type=self.value_type)
