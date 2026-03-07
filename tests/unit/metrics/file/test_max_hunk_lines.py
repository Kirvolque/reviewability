from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.file.max_hunk_lines import FileMaxHunkLines

metric = FileMaxHunkLines()


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
    result = metric.calculate(make_file([make_hunk(3, 2)]))
    assert result == MetricValue("file.max_hunk_lines", 5, MetricValueType.INTEGER)


def test_picks_largest():
    result = metric.calculate(make_file([make_hunk(1, 1), make_hunk(5, 3), make_hunk(2, 0)]))
    assert result == MetricValue("file.max_hunk_lines", 8, MetricValueType.INTEGER)


def test_no_hunks():
    result = metric.calculate(make_file([]))
    assert result == MetricValue("file.max_hunk_lines", 0, MetricValueType.INTEGER)


def test_all_equal_hunks():
    result = metric.calculate(make_file([make_hunk(2, 2), make_hunk(2, 2)]))
    assert result == MetricValue("file.max_hunk_lines", 4, MetricValueType.INTEGER)


def test_addition_only_hunk():
    result = metric.calculate(make_file([make_hunk(7, 0)]))
    assert result == MetricValue("file.max_hunk_lines", 7, MetricValueType.INTEGER)


def test_removal_only_hunk():
    result = metric.calculate(make_file([make_hunk(0, 5)]))
    assert result == MetricValue("file.max_hunk_lines", 5, MetricValueType.INTEGER)
