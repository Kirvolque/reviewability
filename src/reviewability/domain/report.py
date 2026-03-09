from __future__ import annotations

from dataclasses import dataclass

from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import FileDiff, Hunk


@dataclass(frozen=True)
class Analysis:
    """Metric results and reviewability score for a single hunk or file.

    ``subject`` is the domain object being analysed (``Hunk`` or ``FileDiff``).
    """

    subject: Hunk | FileDiff
    metrics: MetricResults
    score: float

    def get(self, name: str) -> MetricValue | None:
        """Return the MetricValue for the given metric name, or None if not present."""
        return self.metrics.get(name)


@dataclass(frozen=True)
class OverallAnalysis:
    """Diff-level metric results and the overall reviewability score."""

    metrics: MetricResults
    score: float

    def get(self, name: str) -> MetricValue | None:
        """Return the MetricValue for the given metric name, or None if not present."""
        return self.metrics.get(name)


@dataclass(frozen=True)
class AnalysisReport:
    """The complete analysis result for a diff.

    Contains per-hunk and per-file analyses plus an overall analysis.
    All scores range from 0.0 (hardest to review) to 1.0 (easiest to review).
    """

    overall: OverallAnalysis
    files: list[Analysis]
    hunks: list[Analysis]
