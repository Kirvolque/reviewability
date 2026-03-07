from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.file.hunk_count import FileHunkCount

metric = FileHunkCount()


def make_hunk() -> Hunk:
    return Hunk(
        file_path="a.py",
        source_start=1,
        source_length=1,
        target_start=1,
        target_length=1,
        added_lines=["x"],
    )


def make_file(hunk_count: int) -> FileDiff:
    return FileDiff(
        path="a.py",
        old_path=None,
        is_new_file=False,
        is_deleted_file=False,
        hunks=[make_hunk() for _ in range(hunk_count)],
    )


def test_no_hunks():
    assert metric.calculate(make_file(0)) == MetricValue(
        "file.hunk_count", 0, MetricValueType.INTEGER
    )


def test_one_hunk():
    assert metric.calculate(make_file(1)) == MetricValue(
        "file.hunk_count", 1, MetricValueType.INTEGER
    )


def test_multiple_hunks():
    assert metric.calculate(make_file(4)) == MetricValue(
        "file.hunk_count", 4, MetricValueType.INTEGER
    )
