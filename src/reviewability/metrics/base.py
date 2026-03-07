from abc import ABC, abstractmethod

from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import FileAnalysis, HunkAnalysis, MetricValue, MetricValueType


class HunkMetric(ABC):
    """Calculates a metric for a single hunk."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def value_type(self) -> MetricValueType: ...

    @abstractmethod
    def calculate(self, hunk: Hunk) -> MetricValue: ...


class FileMetric(ABC):
    """Calculates a metric for a single file across all its hunks."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def value_type(self) -> MetricValueType: ...

    @abstractmethod
    def calculate(self, file: FileDiff) -> MetricValue: ...


class OverallMetric(ABC):
    """Calculates a diff-level metric derived from already-computed hunk and file analyses.

    Overall metrics are second-order: they aggregate lower-level results
    rather than traversing the raw diff again.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def value_type(self) -> MetricValueType: ...

    @abstractmethod
    def calculate(self, hunks: list[HunkAnalysis], files: list[FileAnalysis]) -> MetricValue: ...
