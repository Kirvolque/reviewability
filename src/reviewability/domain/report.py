from dataclasses import dataclass
from enum import Enum
from typing import Any

from reviewability.domain.models import FileDiff, Hunk


class MetricValueType(Enum):
    """The data type of a metric's value, used for threshold comparison and display."""

    INTEGER = "integer"
    FLOAT = "float"
    RATIO = "ratio"  # float in range [0.0, 1.0]
    BOOLEAN = "boolean"


@dataclass(frozen=True)
class MetricValue:
    """A single computed metric result: name, value, and its type."""

    name: str
    value: Any
    value_type: MetricValueType


@dataclass(frozen=True)
class HunkAnalysis:
    """All metric results for a single hunk, plus its reviewability score."""

    hunk: Hunk
    metrics: list[MetricValue]
    score: float


@dataclass(frozen=True)
class FileAnalysis:
    """All metric results for a single file, plus its reviewability score."""

    file: FileDiff
    metrics: list[MetricValue]
    score: float


@dataclass(frozen=True)
class OverallAnalysis:
    """Diff-level metric results and the overall reviewability score."""

    metrics: list[MetricValue]
    score: float


@dataclass(frozen=True)
class AnalysisReport:
    """The complete analysis result for a diff.

    Contains per-hunk and per-file analyses plus an overall analysis.
    All scores range from 0.0 (hardest to review) to 1.0 (easiest to review).
    """

    overall: OverallAnalysis
    files: list[FileAnalysis]
    hunks: list[HunkAnalysis]
