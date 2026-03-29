import pytest

from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import ChangeType, Hunk
from reviewability.metrics.hunk.interleaving import HunkInterleaving

A = ChangeType.ADDED
R = ChangeType.REMOVED

metric = HunkInterleaving()


def make_hunk(added: list[str], removed: list[str], change_order: tuple[ChangeType, ...]) -> Hunk:
    return Hunk(
        file_path="a.py",
        added_lines=added,
        removed_lines=removed,
        change_order=change_order,
    )


def result(value: float, has_remediation: bool = False) -> MetricValue:
    return MetricValue(
        "hunk.interleaving",
        value,
        MetricValueType.RATIO,
        remediation=metric.remediation if has_remediation else None,
    )


def test_empty():
    assert metric.calculate(make_hunk([], [], ())) == result(0.0)


def test_pure_addition():
    assert metric.calculate(make_hunk(["a", "b", "c"], [], (A, A, A))) == result(0.0)


def test_pure_deletion():
    assert metric.calculate(make_hunk([], ["x", "y"], (R, R))) == result(0.0)


def test_block_substitution():
    # A A R R → 2 segments, 4 lines → (2-1)/(4-1) = 0.33
    hunk = make_hunk(["a", "b"], ["x", "y"], (A, A, R, R))
    assert metric.calculate(hunk) == result(0.33, has_remediation=True)


def test_fully_alternating():
    # A R A R → 4 segments, 4 lines → 1.0
    hunk = make_hunk(["a", "b"], ["x", "y"], (A, R, A, R))
    assert metric.calculate(hunk) == result(1.0, has_remediation=True)


def test_single_add_single_remove():
    # A R → 2 segments, 2 lines → (2-1)/(2-1) = 1.0
    hunk = make_hunk(["a"], ["x"], (A, R))
    assert metric.calculate(hunk) == result(1.0, has_remediation=True)


def test_imports_filtered_out():
    # change_order has 4 entries but both imports are filtered → only 2 meaningful lines
    # remaining sequence: [ADDED, REMOVED] → 2 segments, 2 lines → 1.0
    hunk = make_hunk(
        added=["import foo", "real addition"],
        removed=["import bar", "real removal"],
        change_order=(A, R, A, R),
    )
    assert metric.calculate(hunk) == result(1.0, has_remediation=True)


def test_all_lines_filtered_out():
    hunk = make_hunk(
        added=["import foo"],
        removed=["import bar"],
        change_order=(A, R),
    )
    assert metric.calculate(hunk) == result(0.0)


@pytest.mark.parametrize(
    "change_order, expected",
    [
        # 3 lines, fully alternating: (3-1)/(3-1) = 1.0
        ((A, R, A), 1.0),
        # 5 lines, 3 segments: (3-1)/(5-1) = 0.5
        ((A, A, R, R, A), 0.5),
        # 6 lines, 2 segments: (2-1)/(6-1) = 0.2
        ((A, A, A, R, R, R), 0.2),
    ],
)
def test_normalization(change_order: tuple[ChangeType, ...], expected: float):
    added = ["x"] * sum(1 for c in change_order if c == A)
    removed = ["x"] * sum(1 for c in change_order if c == R)
    hunk = make_hunk(added, removed, change_order)
    assert metric.calculate(hunk) == result(expected, has_remediation=expected > 0)
