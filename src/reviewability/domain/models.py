from dataclasses import dataclass, field
from enum import Enum


class HunkType(str, Enum):
    """Classification for an individual hunk based on its content and group membership."""

    PURE_ADDITION = "pure_addition"
    PURE_DELETION = "pure_deletion"
    MOVE = "move"
    MIXED = "mixed"


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
    hunk_type: HunkType | None = None

    @property
    def added_count(self) -> int:
        return len(self.added_lines)

    @property
    def removed_count(self) -> int:
        return len(self.removed_lines)


@dataclass
class FileDiff(DiffNode):
    """All changes to a single file within a diff."""

    path: str
    old_path: str | None  # set if file was renamed
    is_new_file: bool
    is_deleted_file: bool
    hunks: list[Hunk] = field(default_factory=list)


@dataclass
class HunkGroup(DiffNode):
    """A logical group of two or more related hunks identified by the HunkGrouper.

    Hunks in the same group are likely connected (e.g. a code move or cross-hunk
    rewrite). Ungrouped hunks are not included in any group.

    ``length`` is the meaningful-line size of the largest hunk in the group
    (blank lines and import/package declarations excluded), computed at parse time.
    """

    group_id: int | None
    hunks: tuple[Hunk, ...]
    similarity: float
    group_type: GroupType
    length: int


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
