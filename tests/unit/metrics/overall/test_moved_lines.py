from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.moved_lines import OverallMovedLines

metric = OverallMovedLines()


def make_hunk_analysis(added: int, *, is_likely_moved: bool) -> Analysis:
    return Analysis(
        subject=Hunk(
            file_path="a.py",
            source_start=1,
            source_length=1,
            target_start=1,
            target_length=1,
            is_likely_moved=is_likely_moved,
        ),
        metrics=MetricResults([MetricValue("hunk.added_lines", added, MetricValueType.INTEGER)]),
        score=1.0,
    )


def test_counts_only_target_side_lines_for_moved_hunks():
    result = metric.calculate(
        [
            make_hunk_analysis(0, is_likely_moved=True),
            make_hunk_analysis(5, is_likely_moved=True),
            make_hunk_analysis(7, is_likely_moved=False),
        ],
        [],
    )
    assert result == MetricValue("overall.moved_lines", 5, MetricValueType.INTEGER)
