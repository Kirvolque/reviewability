from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator

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


class MetricResults:
    """An immutable, name-indexed collection of computed metric values.

    Supports iteration over all values and lookup by metric name.
    """

    def __init__(self, metrics: list[MetricValue]) -> None:
        self._by_name: dict[str, MetricValue] = {m.name: m for m in metrics}

    def get(self, name: str) -> MetricValue | None:
        """Return the MetricValue for the given metric name, or None if not present."""
        return self._by_name.get(name)

    def all(self) -> list[MetricValue]:
        """Return all metric values as a list."""
        return list(self._by_name.values())

    def __iter__(self) -> Iterator[MetricValue]:
        return iter(self._by_name.values())

    def __len__(self) -> int:
        return len(self._by_name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MetricResults):
            return self._by_name == other._by_name
        return NotImplemented

    def __repr__(self) -> str:
        return f"MetricResults({list(self._by_name.values())!r})"


@dataclass(frozen=True)
class Cause:
    """A single cause explaining why a score is imperfect or why a metric counted something.

    ``value`` can be any analysis object or metric value:
    - ``MetricValue`` — a specific metric that drove a score below 1.0
    - ``Analysis`` — a hunk or file counted as problematic by an overall metric

    ``remediation`` is populated when ``value`` is a ``MetricValue``;
    empty otherwise (the inner analysis object carries its own causes).
    """

    value: MetricValue | Analysis
    remediation: str = ""


@dataclass(frozen=True)
class Analysis:
    """Metric results and reviewability score for a single hunk or file.

    ``subject`` is the domain object being analysed (``Hunk`` or ``FileDiff``).
    ``causes`` is non-empty when ``score < 1.0``.
    """

    subject: Hunk | FileDiff
    metrics: MetricResults
    score: float
    causes: list[Cause] = field(default_factory=list)


@dataclass(frozen=True)
class OverallMetricResult:
    """The result of an overall metric calculation.

    Extends a plain ``MetricValue`` with the analyses that directly caused
    the metric's value (e.g. the specific hunks counted as problematic).
    Empty ``causes`` means the metric is purely aggregate with no traceable
    sub-analyses.
    """

    value: MetricValue
    causes: list[Cause] = field(default_factory=list)
    remediation: str = ""


@dataclass(frozen=True)
class OverallAnalysis:
    """Diff-level metric results and the overall reviewability score.

    ``metric_results`` carries the full per-metric results including any
    traceable causes, enabling downstream recommendation logic.
    """

    metrics: MetricResults
    score: float
    metric_results: list[OverallMetricResult] = field(default_factory=list)


class Statistics:
    """Unified context object passed to rules during evaluation.

    Combines ``MetricResults`` with the computed score for the same level
    (hunk, file, or overall). Rules can inspect any metric by name, or the
    score via the ``SCORE_KEY`` constant — without needing to know which
    analysis level they are operating at.
    """

    SCORE_KEY: str = "score"

    def __init__(self, metrics: MetricResults, score: float) -> None:
        self._metrics = metrics
        self._score = score

    @property
    def score(self) -> float:
        """The reviewability score for this analysis level (0.0–1.0)."""
        return self._score

    @property
    def metrics(self) -> MetricResults:
        """All computed metric values at this analysis level."""
        return self._metrics

    def get(self, name: str) -> MetricValue | None:
        """Return the MetricValue for ``name``, or None if not present.

        The special key ``Statistics.SCORE_KEY`` returns the score as a
        synthetic ``MetricValue`` so score-based rules use the same interface
        as metric-based rules.
        """
        if name == self.SCORE_KEY:
            return MetricValue(name=name, value=self._score, value_type=MetricValueType.RATIO)
        return self._metrics.get(name)


@dataclass(frozen=True)
class AnalysisReport:
    """The complete analysis result for a diff.

    Contains per-hunk and per-file analyses plus an overall analysis.
    All scores range from 0.0 (hardest to review) to 1.0 (easiest to review).
    """

    overall: OverallAnalysis
    files: list[Analysis]
    hunks: list[Analysis]
