from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.metrics.hunk.removed_lines import HunkRemovedLines

metric = HunkRemovedLines()


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


def test_with_removals():
    result = metric.calculate(make_hunk([], ["x", "y"]))
    assert result == MetricValue("hunk.removed_lines", 2, MetricValueType.INTEGER)


def test_without_removals():
    result = metric.calculate(make_hunk(["a", "b"], []))
    assert result == MetricValue("hunk.removed_lines", 0, MetricValueType.INTEGER)


def test_mixed():
    result = metric.calculate(make_hunk(["a"], ["x", "y"]))
    assert result == MetricValue("hunk.removed_lines", 2, MetricValueType.INTEGER)


def test_empty_hunk():
    result = metric.calculate(make_hunk([], []))
    assert result == MetricValue("hunk.removed_lines", 0, MetricValueType.INTEGER)
