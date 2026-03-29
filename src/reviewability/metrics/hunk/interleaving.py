from typing import override

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import ChangeType, Hunk
from reviewability.metrics.base import HunkMetric


class HunkInterleaving(HunkMetric):
    """Normalized measure of how much additions and deletions alternate within a hunk [0.0, 1.0].

    Counts alternating runs of added/removed lines, then normalizes by the maximum possible
    run count::

        interleaving = (segments − 1) / max(changed − 1, 1)

    - 0.0 — all additions then all deletions (or vice versa): clean block substitution
    - 1.0 — every line alternates type: maximum interleaving, hardest to review

    Examples::

        ++ --      → 2 segments, 4 lines → 0.33
        + - + -    → 4 segments, 4 lines → 1.0
        +++ ---    → 2 segments, 6 lines → 0.2
    """

    name: str = "hunk.interleaving"
    value_type: MetricValueType = MetricValueType.RATIO
    description: str = (
        "How much additions and deletions alternate within the hunk (0.0 = clean block "
        "substitution, 1.0 = every line alternates). Higher = harder to review."
    )
    remediation: str = (
        "Additions and deletions are heavily interleaved, making the change hard to follow. "
        "Separate the deletions and additions into distinct commits or hunks."
    )

    @override
    def calculate(self, hunk: Hunk) -> MetricValue:
        value = self._interleaving(hunk.change_order)
        return MetricValue(
            name=self.name,
            value=value,
            value_type=self.value_type,
            remediation=self.remediation if value > 0.0 else None,
        )

    def _interleaving(self, sequence: tuple[ChangeType, ...]) -> float:
        """Compute normalized interleaving score from an ordered change-type sequence."""
        n = len(sequence)
        if n <= 1:
            return 0.0
        segments = sum(1 for i in range(n) if i == 0 or sequence[i] != sequence[i - 1])
        return (segments - 1) / (n - 1)
