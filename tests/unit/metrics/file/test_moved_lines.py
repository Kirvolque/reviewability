from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff, Hunk
from reviewability.metrics.file.moved_lines import FileMovedLines

metric = FileMovedLines()


def make_hunk(added: int, removed: int, *, is_likely_moved: bool = False) -> Hunk:
    return Hunk(
        file_path="a.py",
        source_start=1,
        source_length=removed,
        target_start=1,
        target_length=added,
        added_lines=["a"] * added,
        removed_lines=["r"] * removed,
        is_likely_moved=is_likely_moved,
    )


def make_file(hunks: list[Hunk]) -> FileDiff:
    return FileDiff(
        path="a.py",
        old_path=None,
        is_new_file=False,
        is_deleted_file=False,
        hunks=hunks,
    )


def test_counts_only_target_side_lines_for_moved_hunks():
    result = metric.calculate(
        make_file(
            [
                make_hunk(0, 5, is_likely_moved=True),
                make_hunk(5, 0, is_likely_moved=True),
                make_hunk(3, 0, is_likely_moved=False),
            ]
        )
    )
    assert result == MetricValue("file.moved_lines", 5, MetricValueType.INTEGER)
