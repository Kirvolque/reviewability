from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterator


class MetricValueType(Enum):
    """The data type of a metric's value, used for threshold comparison and display."""

    INTEGER = "integer"
    FLOAT = "float"
    RATIO = "ratio"  # float in range [0.0, 1.0]
    BOOLEAN = "boolean"


@dataclass(frozen=True)
class MetricValue:
    """A single computed metric result: name, value, type, and optional causes.

    Float and ratio values are automatically rounded to 2 decimal places at construction.
    """

    name: str
    value: Any
    value_type: MetricValueType
    remediation: str | None = None
    causes: list[MetricValue] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.value_type in (MetricValueType.FLOAT, MetricValueType.RATIO) and isinstance(
            self.value, float
        ):
            object.__setattr__(self, "value", round(self.value, 2))


class MetricResults:
    """An immutable, name-indexed collection of computed metric values.

    Supports iteration over all values and lookup by metric name.
    """

    def __init__(self, metrics: list[MetricValue]) -> None:
        self._by_name: dict[str, MetricValue] = {m.name: m for m in metrics}

    def get(self, name: str) -> MetricValue | None:
        """Return the MetricValue for the given metric name, or None if not present."""
        return self._by_name.get(name)

    def all(self) -> list[MetricValue]:
        """Return all metric values as a list."""
        return list(self._by_name.values())

    def __iter__(self) -> Iterator[MetricValue]:
        return iter(self._by_name.values())

    def __len__(self) -> int:
        return len(self._by_name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MetricResults):
            return self._by_name == other._by_name
        return NotImplemented

    def __repr__(self) -> str:
        return f"MetricResults({list(self._by_name.values())!r})"
