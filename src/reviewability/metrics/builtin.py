from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import FileAnalysis, HunkAnalysis, MetricValue, MetricValueType
from reviewability.metrics.base import FileMetric, HunkMetric, OverallMetric


class HunkLinesChanged(HunkMetric):
    """Total lines added + removed in a hunk."""

    name: str = "hunk.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.added_count + hunk.removed_count,
            value_type=self.value_type,
        )


class HunkAddedLines(HunkMetric):
    """Number of added lines in a hunk."""

    name: str = "hunk.added_lines"
    value_type: MetricValueType = MetricValueType.INTEGER

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.added_count,
            value_type=self.value_type,
        )


class HunkRemovedLines(HunkMetric):
    """Number of removed lines in a hunk."""

    name: str = "hunk.removed_lines"
    value_type: MetricValueType = MetricValueType.INTEGER

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.removed_count,
            value_type=self.value_type,
        )


class FileHunkCount(FileMetric):
    """Number of hunks in a file."""

    name: str = "file.hunk_count"
    value_type: MetricValueType = MetricValueType.INTEGER

    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(file.hunks),
            value_type=self.value_type,
        )


class FileLinesChanged(FileMetric):
    """Total lines added + removed across all hunks in a file."""

    name: str = "file.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER

    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=sum(h.added_count + h.removed_count for h in file.hunks),
            value_type=self.value_type,
        )


class OverallFilesChanged(OverallMetric):
    """Total number of files changed in the diff."""

    name: str = "overall.files_changed"
    value_type: MetricValueType = MetricValueType.INTEGER

    def calculate(self, hunks: list[HunkAnalysis], files: list[FileAnalysis]) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(files),
            value_type=self.value_type,
        )


class OverallLinesChanged(OverallMetric):
    """Total lines changed across the entire diff, derived from hunk analyses."""

    name: str = "overall.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER

    def calculate(self, hunks: list[HunkAnalysis], files: list[FileAnalysis]) -> MetricValue:
        total = sum(m.value for h in hunks for m in h.metrics if m.name == HunkLinesChanged.name)
        return MetricValue(
            name=self.name,
            value=total,
            value_type=self.value_type,
        )
