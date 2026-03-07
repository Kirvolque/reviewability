from dataclasses import dataclass
from enum import Enum
from typing import Callable

from reviewability.domain.report import MetricResults, MetricValue


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Rule:
    """A threshold rule applied to a named metric.

    Operators: "gt", "lt", "gte", "lte", "eq"
    """

    metric_name: str
    threshold: float
    operator: str
    severity: Severity
    message: str


@dataclass(frozen=True)
class RuleViolation:
    """A rule that was triggered by a metric value exceeding its threshold."""

    rule: Rule
    metric_value: MetricValue

    def __str__(self) -> str:
        return (
            f"[{self.rule.severity.value.upper()}] {self.rule.message} "
            f"(value={self.metric_value.value}, threshold={self.rule.threshold})"
        )


_OPS: dict[str, Callable[[float, float], bool]] = {
    "gt": lambda v, t: v > t,
    "lt": lambda v, t: v < t,
    "gte": lambda v, t: v >= t,
    "lte": lambda v, t: v <= t,
    "eq": lambda v, t: v == t,
}


class RuleEngine:
    """Evaluates a set of rules against a collection of metric values."""

    def __init__(self, rules: list[Rule]) -> None:
        self._rules = rules

    def evaluate(self, metrics: MetricResults) -> list[RuleViolation]:
        """Return all rule violations found in the given metric values."""
        return [
            RuleViolation(rule=rule, metric_value=metric)
            for rule in self._rules
            if (metric := metrics.get(rule.metric_name)) is not None
            if (op := _OPS.get(rule.operator)) and op(metric.value, rule.threshold)
        ]
