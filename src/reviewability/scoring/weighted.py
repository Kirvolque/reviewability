from dataclasses import dataclass
from typing import override

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


class SizeChurnWeightedScorer(WeightedReviewabilityScorer):
    """Extends the weighted scorer with a size×churn interaction for the overall score.

    overall_score = max(0, 1 − size_ratio × (1 + churn_complexity))

    where:
      size_ratio       = overall.lines_changed / max_diff_lines  (clamped to 1.0)
      churn_complexity = overall.churn_complexity                (0.0–1.0)

    Effect: a small diff passes even if changes are highly interleaved.
    As the diff grows toward the limit, interleaved hunks are penalised
    progressively more — a large diff of pure additions/deletions scores
    better than one of equal size with mixed adds and removes throughout.

    Hunk and file scoring are unchanged (linear by lines_changed).
    """

    def __init__(
        self,
        max_diff_lines: float,
        hunk_weights: list[MetricWeight],
        file_weights: list[MetricWeight],
    ) -> None:
        super().__init__(
            hunk_weights=hunk_weights,
            file_weights=file_weights,
            overall_weights=[],
        )
        self._max_diff_lines = max_diff_lines

    @override
    def overall_score(self, metrics: MetricResults) -> float:
        """Score = max(0, 1 − size_ratio × (1 + churn_complexity))."""
        lines = metrics.get("overall.lines_changed")
        if lines is None:
            return 1.0
        size_ratio = min(lines.value / self._max_diff_lines, 1.0)
        churn_mv = metrics.get("overall.churn_complexity")
        churn = churn_mv.value if churn_mv is not None else 0.0
        return max(0.0, 1.0 - size_ratio * (1.0 + churn))
