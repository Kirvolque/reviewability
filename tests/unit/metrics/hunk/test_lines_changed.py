from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.metrics.hunk.lines_changed import HunkLinesChanged

metric = HunkLinesChanged()


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


def test_additions_only():
    result = metric.calculate(make_hunk(["a", "b"], []))
    assert result == MetricValue("hunk.lines_changed", 2, MetricValueType.INTEGER)


def test_removals_only():
    result = metric.calculate(make_hunk([], ["x"]))
    assert result == MetricValue("hunk.lines_changed", 1, MetricValueType.INTEGER)


def test_mixed():
    result = metric.calculate(make_hunk(["a", "b"], ["x", "y", "z"]))
    assert result == MetricValue("hunk.lines_changed", 5, MetricValueType.INTEGER)


def test_empty():
    result = metric.calculate(make_hunk([], []))
    assert result == MetricValue("hunk.lines_changed", 0, MetricValueType.INTEGER)
