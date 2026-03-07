from reviewability.domain.models import Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.hunk.context_lines import HunkContextLines

metric = HunkContextLines()


def make_hunk(context: list[str]) -> Hunk:
    return Hunk(
        file_path="a.py",
        source_start=1,
        source_length=3,
        target_start=1,
        target_length=3,
        added_lines=["new"],
        removed_lines=["old"],
        context_lines=context,
    )


def test_with_context():
    result = metric.calculate(make_hunk(["ctx1", "ctx2", "ctx3"]))
    assert result == MetricValue("hunk.context_lines", 3, MetricValueType.INTEGER)


def test_without_context():
    result = metric.calculate(make_hunk([]))
    assert result == MetricValue("hunk.context_lines", 0, MetricValueType.INTEGER)


def test_context_does_not_count_change_lines():
    # Changes (added/removed) must not affect the context line count.
    hunk = Hunk(
        file_path="a.py",
        source_start=1,
        source_length=10,
        target_start=1,
        target_length=10,
        added_lines=["a"] * 5,
        removed_lines=["b"] * 5,
        context_lines=["ctx"],
    )
    result = metric.calculate(hunk)
    assert result == MetricValue("hunk.context_lines", 1, MetricValueType.INTEGER)


def test_large_context():
    result = metric.calculate(make_hunk(["c"] * 20))
    assert result == MetricValue("hunk.context_lines", 20, MetricValueType.INTEGER)
