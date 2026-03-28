import math
from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.report import Analysis
from reviewability.metrics.base import OverallMetric
from reviewability.metrics.file.lines_changed import FileLinesChanged


class OverallScatterFactor(OverallMetric):
    name: str = "overall.scatter_factor"
    value_type: MetricValueType = MetricValueType.RATIO
    description: str = (
        "Normalized Shannon entropy of the distribution of changes across files. "
        "0.0 means all changes are in one file; 1.0 means changes are spread equally across all files."  # noqa: E501
    )
    remediation: str | None = None

    @override
    def calculate(
        self, hunks: list[Analysis], files: list[Analysis], moves: list[Analysis]
    ) -> MetricValue:
        if len(files) <= 1:
            return MetricValue(name=self.name, value=0.0, value_type=self.value_type)

        counts = [
            mv.value
            for f in files
            if (mv := f.metrics.metric(FileLinesChanged.name)) is not None and mv.value > 0
        ]
        total = sum(counts)
        if total == 0:
            return MetricValue(name=self.name, value=0.0, value_type=self.value_type)

        ps = [c / total for c in counts]
        entropy = -sum(p * math.log2(p) for p in ps)
        max_entropy = math.log2(len(counts))
        scatter = entropy / max_entropy if max_entropy > 0 else 0.0

        return MetricValue(name=self.name, value=scatter, value_type=self.value_type)
