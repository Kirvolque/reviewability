from dataclasses import dataclass
from enum import Enum
from typing import Callable

from reviewability.domain.report import MetricValue


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Rule:
    metric_name: str
    threshold: float
    operator: str  # "gt", "lt", "gte", "lte", "eq"
    severity: Severity
    message: str


@dataclass(frozen=True)
class RuleViolation:
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
    def __init__(self, rules: list[Rule]) -> None:
        self._rules = rules

    def evaluate(self, metrics: list[MetricValue]) -> list[RuleViolation]:
        metrics_by_name: dict[str, list[MetricValue]] = {
            name: [m for m in metrics if m.name == name] for name in {m.name for m in metrics}
        }
        return [
            RuleViolation(rule=rule, metric_value=metric)
            for rule in self._rules
            for metric in metrics_by_name.get(rule.metric_name, [])
            if (op := _OPS.get(rule.operator)) and op(metric.value, rule.threshold)
        ]
