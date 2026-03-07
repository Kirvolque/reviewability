from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from reviewability.domain.models import Hunk, FileDiff


class MetricValueType(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    RATIO = "ratio"      # float in range [0.0, 1.0]
    BOOLEAN = "boolean"


@dataclass
class MetricValue:
    name: str
    value: Any
    value_type: MetricValueType


@dataclass
class HunkAnalysis:
    hunk: Hunk
    metrics: list[MetricValue] = field(default_factory=list)


@dataclass
class FileAnalysis:
    file: FileDiff
    metrics: list[MetricValue] = field(default_factory=list)


@dataclass
class AnalysisReport:
    overall: list[MetricValue] = field(default_factory=list)
    files: list[FileAnalysis] = field(default_factory=list)
    hunks: list[HunkAnalysis] = field(default_factory=list)
