from reviewability.domain.metric import MetricValue, MetricValueType
from reviewability.domain.models import Hunk, HunkRewriteKind
from reviewability.metrics.hunk.in_place_rewrite_lines import HunkInPlaceRewriteLines

metric = HunkInPlaceRewriteLines()


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


def test_returns_changed_lines_for_in_place_rewrite():
    result = metric.calculate(make_hunk(3, 2, HunkRewriteKind.IN_PLACE_REWRITE))
    assert result == MetricValue(
        "hunk.in_place_rewrite_lines", 3, MetricValueType.INTEGER, remediation=metric.remediation
    )


def test_returns_zero_for_other_hunks():
    result = metric.calculate(make_hunk(3, 2, HunkRewriteKind.MOVED_REWRITE))
    assert result == MetricValue(
        "hunk.in_place_rewrite_lines", 0, MetricValueType.INTEGER, remediation=metric.remediation
    )
