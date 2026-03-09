from pathlib import Path

from reviewability.domain.report import (
    MetricResults,
    MetricValue,
    MetricValueType,
)
from reviewability.metrics.engine import MetricEngine
from reviewability.metrics.file import FileHunkCount, FileLinesChanged
from reviewability.metrics.hunk import HunkAddedLines, HunkLinesChanged, HunkRemovedLines
from reviewability.metrics.overall import OverallFilesChanged, OverallLinesChanged
from reviewability.metrics.registry import MetricRegistry
from reviewability.parser.git import parse_diff_text
from reviewability.scoring.weighted import DefaultScorer

FIXTURES = Path(__file__).parent.parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text()


def make_registry() -> MetricRegistry:
    registry = MetricRegistry()
    for metric in [
        HunkLinesChanged(),
        HunkAddedLines(),
        HunkRemovedLines(),
        FileHunkCount(),
        FileLinesChanged(),
        OverallFilesChanged(),
        OverallLinesChanged(),
    ]:
        registry.add(metric)
    return registry


def make_scorer() -> DefaultScorer:
    return DefaultScorer(
        max_hunk_lines=50.0,
        max_diff_lines=200.0,
    )


def test_logic_change_report():
    diff = parse_diff_text(load("logic_change.diff"))
    scorer = make_scorer()
    report = MetricEngine(make_registry(), scorer).run(diff)

    # Check overall metric values (name and value only; remediation varies per metric)
    assert len(report.overall.metrics) == 2  # 2 overall metrics registered
    assert report.overall.metrics.get("overall.files_changed").value == 1  # type: ignore[union-attr]
    assert report.overall.metrics.get("overall.lines_changed").value == 2  # type: ignore[union-attr]

    # Build a MetricResults without remediation for score calculation comparison
    overall_for_score = MetricResults(
        [
            MetricValue("overall.files_changed", 1, MetricValueType.INTEGER),
            MetricValue("overall.lines_changed", 2, MetricValueType.INTEGER),
        ]
    )
    assert report.overall.score == scorer.overall_score(overall_for_score)

    # Check files
    assert len(report.files) == 1
    assert report.files[0].subject == diff.files[0]
    assert report.files[0].metrics.get("file.hunk_count").value == 1  # type: ignore[union-attr]
    assert report.files[0].metrics.get("file.lines_changed").value == 2  # type: ignore[union-attr]
    file_for_score = MetricResults(
        [
            MetricValue("file.hunk_count", 1, MetricValueType.INTEGER),
            MetricValue("file.lines_changed", 2, MetricValueType.INTEGER),
        ]
    )
    assert report.files[0].score == scorer.file_score(file_for_score)

    # Check hunks
    assert len(report.hunks) == 1
    assert report.hunks[0].subject == diff.files[0].hunks[0]
    assert report.hunks[0].metrics.get("hunk.lines_changed").value == 2  # type: ignore[union-attr]
    assert report.hunks[0].metrics.get("hunk.added_lines").value == 2  # type: ignore[union-attr]
    assert report.hunks[0].metrics.get("hunk.removed_lines").value == 0  # type: ignore[union-attr]
    hunk_for_score = MetricResults(
        [
            MetricValue("hunk.lines_changed", 2, MetricValueType.INTEGER),
            MetricValue("hunk.added_lines", 2, MetricValueType.INTEGER),
            MetricValue("hunk.removed_lines", 0, MetricValueType.INTEGER),
        ]
    )
    assert report.hunks[0].score == scorer.hunk_score(hunk_for_score)


def test_multi_file_change_report():
    diff = parse_diff_text(load("multi_file_change.diff"))
    report = MetricEngine(make_registry(), make_scorer()).run(diff)

    assert len(report.overall.metrics) == 2
    assert len(report.files) == 2
    assert len(report.hunks) == 2
    assert 0.0 <= report.overall.score <= 1.0

    for hunk_analysis in report.hunks:
        assert len(hunk_analysis.metrics) == 3
        assert 0.0 <= hunk_analysis.score <= 1.0
        metric_names = {m.name for m in hunk_analysis.metrics}
        assert metric_names == {"hunk.lines_changed", "hunk.added_lines", "hunk.removed_lines"}
