from abc import ABC, abstractmethod

from reviewability.domain.report import MetricResults


class ReviewabilityScorer(ABC):
    """Computes reviewability scores at each analysis level.

    Scores range from 0.0 (hardest to review) to 1.0 (easiest to review).
    All methods receive only metric values — no raw diff data.
    """

    @abstractmethod
    def hunk_score(self, metrics: MetricResults) -> float: ...

    @abstractmethod
    def file_score(self, metrics: MetricResults) -> float: ...

    @abstractmethod
    def overall_score(self, metrics: MetricResults) -> float: ...

    def overall_score_inputs(self) -> set[str] | None:
        """Return the metric names that drive overall_score(), or None to use all.

        When not None, the engine will restrict overall causes to only these metrics,
        so that recommendations surface only what actually caused the score to drop.
        Use metric class name attributes (e.g. ``OverallLinesChanged.name``) rather
        than string literals to keep references refactor-safe.
        """
        return None

