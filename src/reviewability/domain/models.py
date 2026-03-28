import itertools
from dataclasses import dataclass, field
from enum import Enum


class GroupType(str, Enum):
    """Classification for a hunk group based on move-aware diff similarity."""

    MOVED = "moved"
    MOVED_MODIFIED = "moved_modified"


@dataclass(kw_only=True)
class DiffNode:
    """Common base for all addressable units within a diff (hunks and files)."""


@dataclass
class Hunk(DiffNode):
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

    @property
    def is_pure_deletion(self) -> bool:
        """Check if hunk is pure deletion (only removed lines, no added lines)."""
        return self.removed_count > 0 and self.added_count == 0

    @property
    def is_pure_addition(self) -> bool:
        """Check if hunk is pure addition (only added lines, no removed lines)."""
        return self.added_count > 0 and self.removed_count == 0


@dataclass
class FileDiff(DiffNode):
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


@dataclass
class HunkGroup(DiffNode):
    """A logical group of two or more related hunks identified by the HunkGrouper.

    Hunks in the same group are likely connected (e.g. a code move or cross-hunk
    rewrite). Ungrouped hunks are not represented here; see ``Diff.singleton_hunks``.
    """

    group_id: int | None
    hunks: tuple[Hunk, ...]
    similarity: float
    group_type: GroupType


@dataclass
class Diff:
    """The complete diff (e.g. a pull request or branch comparison)."""

    files: list[FileDiff] = field(default_factory=list)
    groups: list[HunkGroup] = field(default_factory=list)
    singleton_hunks: list[Hunk] = field(default_factory=list)

    @property
    def all_hunks(self) -> list[Hunk]:
        """All hunks across all files, in file order."""
        return [hunk for file in self.files for hunk in file.hunks]

    @property
    def total_files_changed(self) -> int:
        return len(self.files)

    @property
    def total_hunks(self) -> int:
        return sum(len(f.hunks) for f in self.files)
