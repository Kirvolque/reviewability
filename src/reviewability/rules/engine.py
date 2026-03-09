from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol

from reviewability.domain.metric import MetricValue


class RuleContext(Protocol):
    """Minimal interface required by rules for evaluation."""

    @property
    def score(self) -> float: ...

    def get(self, name: str) -> MetricValue | None: ...


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Rule:
    """A predicate rule evaluated against a RuleContext.

    ``check`` receives the full context (metrics + score) and returns
    None if the rule passes, or a human-readable message string if it fails.
    """

    severity: Severity
    check: Callable[[RuleContext], str | None]


@dataclass(frozen=True)
class RuleViolation:
    """A rule whose predicate failed, with the message produced by the check."""

    rule: Rule
    message: str

    def __str__(self) -> str:
        return f"[{self.rule.severity.value.upper()}] {self.message}"


class RuleEngine:
    """Evaluates a set of rules against a collection of metric values."""

    def __init__(self, rules: list[Rule]) -> None:
        self._rules = rules

    def evaluate(self, context: RuleContext) -> list[RuleViolation]:
        """Return all rule violations found in the given context."""
        return [
            RuleViolation(rule=rule, message=message)
            for rule in self._rules
            if (message := rule.check(context)) is not None
        ]
