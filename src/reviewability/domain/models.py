from dataclasses import dataclass, field
from enum import Enum


class ChangeType(str, Enum):
    """Direction of a single changed line within a hunk."""

    ADDED = "added"
    REMOVED = "removed"


class HunkType(str, Enum):
    """Classification for an individual hunk based on its content and move membership."""

    PURE_ADDITION = "pure_addition"
    PURE_DELETION = "pure_deletion"
    MOVE = "move"
    MIXED = "mixed"


class MoveType(str, Enum):
    """Classification for a code move based on move-aware diff similarity."""

    PURE = "pure"
    MODIFIED = "modified"


@dataclass(kw_only=True)
class DiffNode:
    """Common base for all addressable units within a diff (hunks and files)."""


@dataclass
class Hunk(DiffNode):
    """A contiguous block of changes within a single file."""

    file_path: str
    added_lines: list[str] = field(default_factory=list)
    removed_lines: list[str] = field(default_factory=list)
    context_lines: list[str] = field(default_factory=list)
    change_order: tuple[ChangeType, ...] = field(default_factory=tuple)
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
class Move(DiffNode):
    """A logical group of two or more related hunks identified by the MoveDetector.

    Hunks in the same move are likely connected (e.g. a code move or cross-hunk
    rewrite). Ungrouped hunks are not included in any move.

    ``length`` is the meaningful-line size of the largest hunk in the move
    (blank lines and import/package declarations excluded), computed at parse time.
    """

    move_id: int | None
    hunks: tuple[Hunk, ...]
    similarity: float
    move_type: MoveType
    length: int


@dataclass
class Diff:
    """The complete diff (e.g. a pull request or branch comparison)."""

    files: list[FileDiff] = field(default_factory=list)
    moves: list[Move] = field(default_factory=list)
    singleton_hunks: list[Hunk] = field(default_factory=list)

    @property
    def all_hunks(self) -> list[Hunk]:
        """All hunks across all files, in file order."""
        return [hunk for file in self.files for hunk in file.hunks]
