from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff, Hunk
from reviewability.metrics.file.lines_changed import FileLinesChanged

metric = FileLinesChanged()


def make_file(hunks: list[Hunk]) -> FileDiff:
    return FileDiff(
        path="a.py", old_path=None, is_new_file=False, is_deleted_file=False, hunks=hunks
    )


def make_hunk(added: int, removed: int) -> Hunk:
    return Hunk(
        file_path="a.py",
        added_lines=["x"] * added,
        removed_lines=["y"] * removed,
    )


def test_single_hunk():
    result = metric.calculate(make_file([make_hunk(3, 2)]))
    assert result == MetricValue("file.lines_changed", 5, MetricValueType.INTEGER)


def test_multiple_hunks():
    result = metric.calculate(make_file([make_hunk(2, 1), make_hunk(0, 3)]))
    assert result == MetricValue("file.lines_changed", 6, MetricValueType.INTEGER)


def test_no_hunks():
    result = metric.calculate(make_file([]))
    assert result == MetricValue("file.lines_changed", 0, MetricValueType.INTEGER)
