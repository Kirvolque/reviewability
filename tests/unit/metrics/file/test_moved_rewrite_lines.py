from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import FileDiff, Hunk, HunkRewriteKind
from reviewability.metrics.file.moved_rewrite_lines import FileMovedRewriteLines

metric = FileMovedRewriteLines()


def make_hunk(added: int, removed: int, rewrite_kind: HunkRewriteKind | None = None) -> Hunk:
    return Hunk(
        file_path="a.py",
        source_start=1,
        source_length=removed,
        target_start=1,
        target_length=added,
        added_lines=["a"] * added,
        removed_lines=["r"] * removed,
        rewrite_kind=rewrite_kind,
    )


def make_file(hunks: list[Hunk]) -> FileDiff:
    return FileDiff(
        path="a.py",
        old_path=None,
        is_new_file=False,
        is_deleted_file=False,
        hunks=hunks,
    )


def test_sums_only_moved_rewrite_lines():
    result = metric.calculate(
        make_file(
            [
                make_hunk(2, 1, HunkRewriteKind.IN_PLACE_REWRITE),
                make_hunk(3, 2, HunkRewriteKind.MOVED_REWRITE),
                make_hunk(1, 1, HunkRewriteKind.MOVED_REWRITE),
            ]
        )
    )
    assert result == MetricValue("file.moved_rewrite_lines", 4, MetricValueType.INTEGER)
