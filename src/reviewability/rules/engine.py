from dataclasses import dataclass
from enum import Enum

from reviewability.metrics.base import MetricResult


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass
class Rule:
    metric_name: str
    threshold: float
    operator: str  # "gt", "lt", "gte", "lte", "eq"
    severity: Severity
    message: str


@dataclass
class RuleViolation:
    rule: Rule
    result: MetricResult

    def __str__(self) -> str:
        location = f"{self.result.file_path}" if self.result.file_path else "diff"
        if self.result.hunk_index is not None:
            location += f" hunk #{self.result.hunk_index}"
        return (
            f"[{self.rule.severity.value.upper()}] {location}: "
            f"{self.rule.message} (value={self.result.value}, threshold={self.rule.threshold})"
        )


_OPS = {
    "gt":  lambda v, t: v > t,
    "lt":  lambda v, t: v < t,
    "gte": lambda v, t: v >= t,
    "lte": lambda v, t: v <= t,
    "eq":  lambda v, t: v == t,
}


class RuleEngine:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = rules

    def evaluate(self, results: list[MetricResult]) -> list[RuleViolation]:
        violations: list[RuleViolation] = []
        results_by_metric: dict[str, list[MetricResult]] = {}
        for r in results:
            results_by_metric.setdefault(r.metric_name, []).append(r)

        for rule in self.rules:
            for result in results_by_metric.get(rule.metric_name, []):
                op = _OPS.get(rule.operator)
                if op and op(result.value, rule.threshold):
                    violations.append(RuleViolation(rule=rule, result=result))

        return violations
