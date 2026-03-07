import itertools
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Hunk:
    """A contiguous block of changes within a single file."""

    file_path: str
    source_start: int
    source_length: int
    target_start: int
    target_length: int
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    context_lines: list[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return self.source_length

    @property
    def char_count(self) -> int:
        all_lines = itertools.chain(self.added_lines, self.removed_lines, self.context_lines)
        return sum(len(line) for line in all_lines)

    @property
    def added_count(self) -> int:
        return len(self.added_lines)

    @property
    def removed_count(self) -> int:
        return len(self.removed_lines)


@dataclass(frozen=True)
class FileDiff:
    """All changes to a single file within a diff."""

    path: str
    old_path: str | None  # set if file was renamed
    is_new_file: bool
    is_deleted_file: bool
    hunks: list[Hunk] = field(default_factory=list)

    @property
    def total_added(self) -> int:
        return sum(h.added_count for h in self.hunks)

    @property
    def total_removed(self) -> int:
        return sum(h.removed_count for h in self.hunks)


@dataclass(frozen=True)
class Diff:
    """The complete diff (e.g. a pull request or branch comparison)."""

    files: list[FileDiff] = field(default_factory=list)

    @property
    def total_files_changed(self) -> int:
        return len(self.files)

    @property
    def total_hunks(self) -> int:
        return sum(len(f.hunks) for f in self.files)
