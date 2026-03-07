from pathlib import Path

from reviewability.domain.report import (
    AnalysisReport,
    FileAnalysis,
    HunkAnalysis,
    MetricValue,
    MetricValueType,
)
from reviewability.metrics.builtin import (
    FileHunkCount,
    FileLinesChanged,
    HunkAddedLines,
    HunkLinesChanged,
    HunkRemovedLines,
    OverallFilesChanged,
    OverallLinesChanged,
)
from reviewability.metrics.registry import MetricRegistry
from reviewability.parser.git import parse_diff_text

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


def test_logic_change_report():
    diff = parse_diff_text(load("logic_change.diff"))
    report = make_registry().run(diff)

    assert report == AnalysisReport(
        overall=[
            MetricValue("overall.files_changed", 1, MetricValueType.INTEGER),
            MetricValue("overall.lines_changed", 2, MetricValueType.INTEGER),
        ],
        files=[
            FileAnalysis(
                file=diff.files[0],
                metrics=[
                    MetricValue("file.hunk_count", 1, MetricValueType.INTEGER),
                    MetricValue("file.lines_changed", 2, MetricValueType.INTEGER),
                ],
            )
        ],
        hunks=[
            HunkAnalysis(
                hunk=diff.files[0].hunks[0],
                metrics=[
                    MetricValue("hunk.lines_changed", 2, MetricValueType.INTEGER),
                    MetricValue("hunk.added_lines", 2, MetricValueType.INTEGER),
                    MetricValue("hunk.removed_lines", 0, MetricValueType.INTEGER),
                ],
            )
        ],
    )


def test_multi_file_change_report():
    diff = parse_diff_text(load("multi_file_change.diff"))
    report = make_registry().run(diff)

    assert report.overall == [
        MetricValue("overall.files_changed", 2, MetricValueType.INTEGER),
        MetricValue("overall.lines_changed", 12, MetricValueType.INTEGER),
    ]
    assert len(report.files) == 2
    assert len(report.hunks) == 2

    # Each hunk has all 3 hunk-level metrics
    for hunk_analysis in report.hunks:
        assert len(hunk_analysis.metrics) == 3
        metric_names = {m.name for m in hunk_analysis.metrics}
        assert metric_names == {"hunk.lines_changed", "hunk.added_lines", "hunk.removed_lines"}
