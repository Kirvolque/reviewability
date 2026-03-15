from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.metrics.hunk.change_balance import HunkChangeBalance

metric = HunkChangeBalance()

_REMEDIATION = metric.remediation


def make_hunk(added: list[str], removed: list[str]) -> Hunk:
    return Hunk(
        file_path="a.py",
        source_start=1,
        source_length=len(removed),
        target_start=1,
        target_length=len(added),
        added_lines=added,
        removed_lines=removed,
    )


def test_pure_addition():
    result = metric.calculate(make_hunk(["a", "b"], []))
    assert result == MetricValue("hunk.change_balance", 1.0, MetricValueType.RATIO, _REMEDIATION)


def test_pure_deletion():
    result = metric.calculate(make_hunk([], ["x", "y"]))
    assert result == MetricValue("hunk.change_balance", 0.0, MetricValueType.RATIO, _REMEDIATION)


def test_balanced_edit():
    result = metric.calculate(make_hunk(["a"], ["x"]))
    assert result == MetricValue("hunk.change_balance", 0.5, MetricValueType.RATIO, _REMEDIATION)


def test_empty_hunk():
    result = metric.calculate(make_hunk([], []))
    assert result == MetricValue("hunk.change_balance", 0.0, MetricValueType.RATIO, _REMEDIATION)


def test_unbalanced_edit():
    # 3 added, 1 removed → ratio = 0.75
    result = metric.calculate(make_hunk(["a", "b", "c"], ["x"]))
    assert result == MetricValue("hunk.change_balance", 0.75, MetricValueType.RATIO, _REMEDIATION)
