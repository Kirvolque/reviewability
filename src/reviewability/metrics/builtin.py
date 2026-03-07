from reviewability.domain.models import Diff, FileDiff, Hunk
from reviewability.domain.report import MetricValue, MetricValueType
from reviewability.metrics.base import HunkMetric, FileMetric, DiffMetric


class HunkLinesChanged(HunkMetric):
    """Total lines added + removed in a hunk."""
    name = "hunk.lines_changed"

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.added_count + hunk.removed_count,
            value_type=MetricValueType.INTEGER,
        )


class HunkAddedLines(HunkMetric):
    """Number of added lines in a hunk."""
    name = "hunk.added_lines"

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.added_count,
            value_type=MetricValueType.INTEGER,
        )


class HunkRemovedLines(HunkMetric):
    """Number of removed lines in a hunk."""
    name = "hunk.removed_lines"

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.removed_count,
            value_type=MetricValueType.INTEGER,
        )


class FileHunkCount(FileMetric):
    """Number of hunks in a file."""
    name = "file.hunk_count"

    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(file.hunks),
            value_type=MetricValueType.INTEGER,
        )


class FileLinesChanged(FileMetric):
    """Total lines added + removed across all hunks in a file."""
    name = "file.lines_changed"

    def calculate(self, file: FileDiff) -> MetricValue:
        total = sum(h.added_count + h.removed_count for h in file.hunks)
        return MetricValue(
            name=self.name,
            value=total,
            value_type=MetricValueType.INTEGER,
        )


class DiffFilesChanged(DiffMetric):
    """Total number of files changed in the diff."""
    name = "diff.files_changed"

    def calculate(self, diff: Diff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=diff.total_files_changed,
            value_type=MetricValueType.INTEGER,
        )


class DiffTotalLinesChanged(DiffMetric):
    """Total lines added + removed across the entire diff."""
    name = "diff.total_lines_changed"

    def calculate(self, diff: Diff) -> MetricValue:
        total = sum(
            h.added_count + h.removed_count
            for f in diff.files
            for h in f.hunks
        )
        return MetricValue(
            name=self.name,
            value=total,
            value_type=MetricValueType.INTEGER,
        )
