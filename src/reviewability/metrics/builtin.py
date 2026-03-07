from reviewability.domain.models import FileDiff, Hunk
from reviewability.domain.report import FileAnalysis, HunkAnalysis, MetricValue, MetricValueType
from reviewability.metrics.base import FileMetric, HunkMetric, OverallMetric


class HunkLinesChanged(HunkMetric):
    name: str = "hunk.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines added and removed in a hunk."
    remediation: str = "Split the hunk into smaller, focused changes."

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.added_count + hunk.removed_count,
            value_type=self.value_type,
        )


class HunkAddedLines(HunkMetric):
    name: str = "hunk.added_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of lines added in a hunk."
    remediation: str = "Break large additions into smaller, reviewable chunks."

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.added_count,
            value_type=self.value_type,
        )


class HunkRemovedLines(HunkMetric):
    name: str = "hunk.removed_lines"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of lines removed in a hunk."
    remediation: str = "Ensure deletions are isolated from unrelated changes."

    def calculate(self, hunk: Hunk) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=hunk.removed_count,
            value_type=self.value_type,
        )


class FileHunkCount(FileMetric):
    name: str = "file.hunk_count"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Number of separate change regions (hunks) in a file."
    remediation: str = "Consider grouping related changes to reduce scattered edits."

    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(file.hunks),
            value_type=self.value_type,
        )


class FileLinesChanged(FileMetric):
    name: str = "file.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines added and removed across all hunks in a file."
    remediation: str = "Split large file changes across multiple commits or pull requests."

    def calculate(self, file: FileDiff) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=sum(h.added_count + h.removed_count for h in file.hunks),
            value_type=self.value_type,
        )


class OverallFilesChanged(OverallMetric):
    name: str = "overall.files_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total number of files changed in the diff."
    remediation: str = "Split the change into smaller pull requests by concern."

    def calculate(self, hunks: list[HunkAnalysis], files: list[FileAnalysis]) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=len(files),
            value_type=self.value_type,
        )


class OverallLinesChanged(OverallMetric):
    name: str = "overall.lines_changed"
    value_type: MetricValueType = MetricValueType.INTEGER
    description: str = "Total lines changed across the entire diff."
    remediation: str = "Reduce patch size by splitting unrelated changes into separate commits."

    def calculate(self, hunks: list[HunkAnalysis], files: list[FileAnalysis]) -> MetricValue:
        return MetricValue(
            name=self.name,
            value=sum(
                m.value for h in hunks if (m := h.metrics.get(HunkLinesChanged.name)) is not None
            ),
            value_type=self.value_type,
        )
