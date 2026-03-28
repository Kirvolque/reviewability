from abc import ABC, abstractmethod

from reviewability.domain.metric import MetricResults


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
    def move_score(self, metrics: MetricResults) -> float: ...

    @abstractmethod
    def overall_score(self, metrics: MetricResults) -> float: ...
