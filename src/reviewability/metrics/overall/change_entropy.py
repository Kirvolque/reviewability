import math
from typing import override

from reviewability.domain.report import (
    FileAnalysis,
    HunkAnalysis,
    MetricValue,
    MetricValueType,
    OverallMetricResult,
)
from reviewability.metrics.base import OverallMetric


class OverallChangeEntropy(OverallMetric):
    name: str = "overall.change_entropy"
    value_type: MetricValueType = MetricValueType.FLOAT
    description: str = (
        "Shannon entropy of the distribution of changes across files. "
        "Higher values indicate changes are more scattered across many files."
    )
    remediation: str = "Group related changes into fewer files, or split the diff by concern."

    @override
    def calculate(
        self, hunks: list[HunkAnalysis], files: list[FileAnalysis]
    ) -> OverallMetricResult:
        values = [
            m.value
            for f in files
            if (m := f.metrics.get("file.lines_changed")) is not None and m.value > 0
        ]
        total = sum(values)
        if total == 0:
            return OverallMetricResult(
                value=MetricValue(name=self.name, value=0.0, value_type=self.value_type)
            )

        entropy = -sum((v / total) * math.log2(v / total) for v in values)
        return OverallMetricResult(
            value=MetricValue(name=self.name, value=entropy, value_type=self.value_type)
        )
