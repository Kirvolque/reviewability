from abc import ABC, abstractmethod

from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import FileAnalysis, HunkAnalysis, MetricValue, MetricValueType


class HunkMetric(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def value_type(self) -> MetricValueType: ...

    @abstractmethod
    def calculate(self, hunk: Hunk) -> MetricValue: ...


class FileMetric(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def value_type(self) -> MetricValueType: ...

    @abstractmethod
    def calculate(self, file: FileDiff) -> MetricValue: ...


class OverallMetric(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def value_type(self) -> MetricValueType: ...

    @abstractmethod
    def calculate(self, hunks: list[HunkAnalysis], files: list[FileAnalysis]) -> MetricValue: ...
