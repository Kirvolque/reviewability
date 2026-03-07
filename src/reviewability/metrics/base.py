from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from reviewability.domain.models import Diff, FileDiff, Hunk


class MetricScope(Enum):
    HUNK = "hunk"
    FILE = "file"
    DIFF = "diff"


@dataclass
class MetricResult:
    metric_name: str
    scope: MetricScope
    value: Any
    # Metadata — only set for hunk/file scope
    file_path: str | None = None
    hunk_index: int | None = None


class HunkMetric(ABC):
    scope = MetricScope.HUNK

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def calculate(self, hunk: Hunk) -> MetricResult: ...


class FileMetric(ABC):
    scope = MetricScope.FILE

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def calculate(self, file: FileDiff) -> MetricResult: ...


class DiffMetric(ABC):
    scope = MetricScope.DIFF

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def calculate(self, diff: Diff) -> MetricResult: ...
