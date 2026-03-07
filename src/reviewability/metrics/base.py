from abc import ABC, abstractmethod

from reviewability.domain.models import Diff, FileDiff, Hunk
from reviewability.domain.report import MetricValue


class HunkMetric(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def calculate(self, hunk: Hunk) -> MetricValue: ...


class FileMetric(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def calculate(self, file: FileDiff) -> MetricValue: ...


class DiffMetric(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def calculate(self, diff: Diff) -> MetricValue: ...
