from __future__ import annotations

from typing import Protocol

from reviewability.domain.metric import MetricValue


class RuleContext(Protocol):
    """Minimal interface required by rules for evaluation."""

    score: float

    def metric(self, name: str) -> MetricValue | None: ...