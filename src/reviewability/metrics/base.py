from abc import ABC, abstractmethod

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff, Hunk, HunkGroup
from reviewability.domain.report import Analysis


class Metric(ABC):
    """Base interface for all metrics.

    Every metric has a name, a value type, a human-readable description,
    and a remediation hint shown when a rule threshold is violated.
    """

    name: str
    value_type: MetricValueType
    description: str
    remediation: str


class HunkMetric(Metric, ABC):
    """Calculates a metric for a single hunk."""

    @abstractmethod
    def calculate(self, hunk: Hunk) -> MetricValue: ...


class FileMetric(Metric, ABC):
    """Calculates a metric for a single file across all its hunks."""

    @abstractmethod
    def calculate(self, file: FileDiff) -> MetricValue: ...


class GroupMetric(Metric, ABC):
    """Calculates a metric for a single hunk group.

    Group metrics are second-order: they receive the pre-built ``HunkGroup``
    domain object and the hunk analyses that belong to it.
    """

    @abstractmethod
    def calculate(self, group: HunkGroup, hunk_analyses: list[Analysis]) -> MetricValue: ...


class OverallMetric(Metric, ABC):
    """Calculates a diff-level metric derived from already-computed hunk and file analyses.

    Overall metrics are second-order: they aggregate lower-level results
    rather than traversing the raw diff again.
    """

    @abstractmethod
    def calculate(
        self, hunks: list[Analysis], files: list[Analysis], groups: list[Analysis]
    ) -> MetricValue: ...
