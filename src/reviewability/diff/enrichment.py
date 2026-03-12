from __future__ import annotations

import dataclasses
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

from reviewability.diff.movement import MovementDetector
from reviewability.domain.models import Diff, FileDiff, Hunk

T = TypeVar("T", Hunk, FileDiff)


@dataclass(frozen=True)
class DiffEnricher:
    """Enriches a parsed ``Diff`` with structural insights before metric calculation.

    Currently detects likely code movements between hunks and files, setting the
    ``is_likely_moved`` flag on affected ``Hunk`` and ``FileDiff`` instances.

    Since domain objects are immutable, enrichment produces a new ``Diff`` with
    replacement instances where flags have changed.
    """

    detector: MovementDetector = field(default_factory=MovementDetector)

    def enrich(self, diff: Diff) -> Diff:
        """Return a new ``Diff`` with structural flags populated."""
        moved_hunk_ids, moved_file_ids = self._detect_movements(diff)

        if not moved_hunk_ids and not moved_file_ids:
            return diff

        return dataclasses.replace(
            diff,
            files=[self._enrich_file(f, moved_hunk_ids, moved_file_ids) for f in diff.files],
        )

    def _detect_movements(self, diff: Diff) -> tuple[set[int], set[int]]:
        deletion_hunks = [h for f in diff.files for h in f.hunks if _is_pure_deletion(h)]
        insertion_hunks = [h for f in diff.files for h in f.hunks if _is_pure_insertion(h)]
        deleted_files = [f for f in diff.files if f.is_deleted_file]
        new_files = [f for f in diff.files if f.is_new_file]

        moved_hunk_ids = _find_moved_pairs(
            deletion_hunks, insertion_hunks, self.detector.hunks_are_likely_moved
        )
        moved_file_ids = _find_moved_pairs(
            deleted_files, new_files, self.detector.files_are_likely_moved
        )

        return moved_hunk_ids, moved_file_ids

    def _enrich_file(
        self, file: FileDiff, moved_hunk_ids: set[int], moved_file_ids: set[int]
    ) -> FileDiff:
        hunks_changed = any(id(h) in moved_hunk_ids for h in file.hunks)
        file_moved = id(file) in moved_file_ids

        if not hunks_changed and not file_moved:
            return file

        new_hunks = [
            dataclasses.replace(h, is_likely_moved=True) if id(h) in moved_hunk_ids else h
            for h in file.hunks
        ]
        return dataclasses.replace(file, hunks=new_hunks, is_likely_moved=file_moved)


def _find_moved_pairs(
    sources: list[T],
    targets: list[T],
    is_moved: Callable[[T, T], bool],
) -> set[int]:
    """Return the set of object IDs for all matched source/target pairs.

    Each source and target is matched at most once. Once a pair is found,
    both are removed from further consideration.
    """
    matched: set[int] = set()
    for source in sources:
        if id(source) in matched:
            continue
        for target in targets:
            if id(target) in matched:
                continue
            if is_moved(source, target):
                matched.add(id(source))
                matched.add(id(target))
                break
    return matched


def _is_pure_deletion(hunk: Hunk) -> bool:
    return hunk.removed_count > 0 and hunk.added_count == 0


def _is_pure_insertion(hunk: Hunk) -> bool:
    return hunk.added_count > 0 and hunk.removed_count == 0
