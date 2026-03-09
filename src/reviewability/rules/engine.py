from dataclasses import dataclass
from enum import Enum
from typing import Callable

from reviewability.domain.report import Statistics


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class Rule:
    """A predicate rule evaluated against a Statistics context.

    ``check`` receives the full statistics (metrics + score) and returns
    None if the rule passes, or a human-readable message string if it fails.
    """

    severity: Severity
    check: Callable[[Statistics], str | None]


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

    def evaluate(self, stats: Statistics) -> list[RuleViolation]:
        """Return all rule violations found in the given statistics."""
        return [
            RuleViolation(rule=rule, message=message)
            for rule in self._rules
            if (message := rule.check(stats)) is not None
        ]
