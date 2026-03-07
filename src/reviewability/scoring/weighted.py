from dataclasses import dataclass

from reviewability.domain.report import MetricResults
from reviewability.scoring.base import ReviewabilityScorer


@dataclass(frozen=True)
class MetricWeight:
    """Defines how a single metric contributes to the reviewability score.

    The metric value is normalized against max_value (clamped to [0.0, 1.0])
    and then scaled by weight. Higher metric value = lower reviewability score.
    """

    metric_name: str
    max_value: float
    weight: float = 1.0


class WeightedReviewabilityScorer(ReviewabilityScorer):
    """Computes scores as a weighted sum of normalized metric values.

    Score = 1.0 - sum(weight * clamp(value / max_value)) / sum(weights)

    Metrics not listed in the weights are ignored.
    """

    def __init__(
        self,
        hunk_weights: list[MetricWeight],
        file_weights: list[MetricWeight],
        overall_weights: list[MetricWeight],
    ) -> None:
        self._hunk_weights = {w.metric_name: w for w in hunk_weights}
        self._file_weights = {w.metric_name: w for w in file_weights}
        self._overall_weights = {w.metric_name: w for w in overall_weights}

    def hunk_score(self, metrics: MetricResults) -> float:
        return self._compute(metrics, self._hunk_weights)

    def file_score(self, metrics: MetricResults) -> float:
        return self._compute(metrics, self._file_weights)

    def overall_score(self, metrics: MetricResults) -> float:
        return self._compute(metrics, self._overall_weights)

    @staticmethod
    def _compute(metrics: MetricResults, weights: dict[str, MetricWeight]) -> float:
        if not weights:
            return 1.0

        total_weight = sum(w.weight for w in weights.values())
        if total_weight == 0.0:
            return 1.0

        weighted_load = sum(
            w.weight * min(m.value / w.max_value, 1.0)
            for name, w in weights.items()
            if (m := metrics.get(name)) is not None
        )
        return max(0.0, 1.0 - weighted_load / total_weight)
