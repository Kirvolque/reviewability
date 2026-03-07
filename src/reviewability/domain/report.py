from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from reviewability.domain.models import FileDiff, Hunk


class MetricValueType(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    RATIO = "ratio"  # float in range [0.0, 1.0]
    BOOLEAN = "boolean"


@dataclass(frozen=True)
class MetricValue:
    name: str
    value: Any
    value_type: MetricValueType


@dataclass(frozen=True)
class HunkAnalysis:
    hunk: Hunk
    metrics: tuple[MetricValue, ...] = field(default_factory=tuple)
    score: float | None = None


@dataclass(frozen=True)
class FileAnalysis:
    file: FileDiff
    metrics: tuple[MetricValue, ...] = field(default_factory=tuple)
    score: float | None = None


@dataclass(frozen=True)
class AnalysisReport:
    overall: tuple[MetricValue, ...] = field(default_factory=tuple)
    files: tuple[FileAnalysis, ...] = field(default_factory=tuple)
    hunks: tuple[HunkAnalysis, ...] = field(default_factory=tuple)
    score: float | None = None
