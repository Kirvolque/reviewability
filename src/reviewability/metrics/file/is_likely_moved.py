from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff
from reviewability.metrics.base import FileMetric


class FileIsLikelyMoved(FileMetric):
    name: str = "file.is_likely_moved"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "1 if this file is likely a movement from another path, 0 otherwise."
    remediation: str | None = None

    @override
    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=1 if file.is_likely_moved else 0,
            value_type=self.value_type,
        )
