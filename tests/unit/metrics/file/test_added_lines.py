from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.file.added_lines import FileAddedLines

metric = FileAddedLines()


def make_file(hunks: list[Hunk]) -> FileDiff:
    return FileDiff(
        path="a.py", old_path=None, is_new_file=False, is_deleted_file=False, hunks=hunks
    )


def make_hunk(added: int, removed: int) -> Hunk:
    return Hunk(
        file_path="a.py",
        source_start=1,
        source_length=removed,
        target_start=1,
        target_length=added,
        added_lines=["x"] * added,
        removed_lines=["y"] * removed,
    )


def test_single_hunk():
    result = metric.calculate(make_file([make_hunk(4, 1)]))
    assert result == MetricValue("file.added_lines", 4, MetricValueType.INTEGER)


def test_multiple_hunks():
    result = metric.calculate(make_file([make_hunk(2, 0), make_hunk(3, 5)]))
    assert result == MetricValue("file.added_lines", 5, MetricValueType.INTEGER)


def test_no_additions():
    result = metric.calculate(make_file([make_hunk(0, 3)]))
    assert result == MetricValue("file.added_lines", 0, MetricValueType.INTEGER)


def test_no_hunks():
    result = metric.calculate(make_file([]))
    assert result == MetricValue("file.added_lines", 0, MetricValueType.INTEGER)
