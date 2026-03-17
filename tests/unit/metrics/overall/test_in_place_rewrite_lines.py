from reviewability.domain.metric import MetricResults, MetricValue, MetricValueType
from reviewability.domain.models import Hunk
from reviewability.domain.report import Analysis
from reviewability.metrics.overall.in_place_rewrite_lines import OverallInPlaceRewriteLines

metric = OverallInPlaceRewriteLines()


def make_hunk_analysis(value: int) -> Analysis:
    return Analysis(
        subject=Hunk(
            file_path="a.py",
            source_start=1,
            source_length=1,
            target_start=1,
            target_length=1,
        ),
        metrics=MetricResults(
            [MetricValue("hunk.in_place_rewrite_lines", value, MetricValueType.INTEGER)]
        ),
        score=1.0,
    )


def test_sums_hunk_rewrite_lines():
    result = metric.calculate([make_hunk_analysis(3), make_hunk_analysis(5)], [])
    assert result == MetricValue("overall.in_place_rewrite_lines", 8, MetricValueType.INTEGER)
