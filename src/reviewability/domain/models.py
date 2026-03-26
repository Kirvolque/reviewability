import itertools
from dataclasses import dataclass, field
from enum import Enum


class HunkRewriteKind(str, Enum):
    """Classification for a heavy rewrite detected between deletion/addition hunks."""

    IN_PLACE_REWRITE = "in_place_rewrite"
    MOVED_REWRITE = "moved_rewrite"


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
    is_likely_moved: bool = False
    # Optional enrichment output: detected heavy rewrite classification.
    rewrite_kind: HunkRewriteKind | None = None
    # Assigned by HunkGrouper: groups hunks that are logically connected (moves, rewrites).
    # None = singleton (unconnected); int = group index shared across connected hunks.
    group_id: int | None = None

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
class Diff:
    """The complete diff (e.g. a pull request or branch comparison)."""

    files: list[FileDiff] = field(default_factory=list)

    @property
    def total_files_changed(self) -> int:
        return len(self.files)

    @property
    def total_hunks(self) -> int:
        return sum(len(f.hunks) for f in self.files)
