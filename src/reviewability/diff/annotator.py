from __future__ import annotations
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TypeVar

from reviewability.diff.complex_rewrite import ComplexRewriteDetector
from reviewability.diff.movement import MovementDetector
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Diff, FileDiff, Hunk, HunkRewriteKind

T = TypeVar("T", Hunk, FileDiff)


@dataclass(frozen=True)
class DiffAnnotator:
    """Enriches a parsed ``Diff`` with structural insights before metric calculation.

    Currently performs two structural passes:

    - movement detection for hunks, setting ``is_likely_moved``
    - complex rewrite classification for hunks, setting ``rewrite_kind``

    Enrichment mutates hunk-level annotation fields in place and returns the same
    ``Diff`` instance.
    """

    movement_detector: MovementDetector = field(default_factory=MovementDetector)
    complex_rewrite_detector: ComplexRewriteDetector = field(
        default_factory=ComplexRewriteDetector
    )
    similarity_calculator: DiffSimilarityCalculator = field(
        default_factory=DiffSimilarityCalculator
    )

    def enrich(self, diff: Diff) -> Diff:
        """Populate structural hunk annotations in place and return ``diff``."""
        moved_hunk_ids, rewrite_kinds_by_hunk_id = self._detect_structural_matches(diff)

        if not moved_hunk_ids and not rewrite_kinds_by_hunk_id:
            return diff

        for file in diff.files:
            self._annotate_hunks(file, moved_hunk_ids, rewrite_kinds_by_hunk_id)
        return diff

    def _detect_structural_matches(
        self,
        diff: Diff,
    ) -> tuple[set[int], dict[int, HunkRewriteKind]]:
        """Detect moved hunk pairs first, then classify complex rewrites for unmatched hunks.

        Movement detection operates only on pure-deletion / pure-insertion pairs.
        Rewrite detection covers two cases:
        - Cross-hunk: unmatched pure-deletion + pure-insertion pairs (same as before)
        - Self: mixed hunks (both added and removed lines) compared against themselves
        """
        deletion_hunks = [h for f in diff.files for h in f.hunks if _is_pure_deletion(h)]
        insertion_hunks = [h for f in diff.files for h in f.hunks if _is_pure_insertion(h)]
        mixed_hunks = [h for f in diff.files for h in f.hunks if _is_mixed(h)]

        hunk_lines_by_id = {
            id(hunk): tuple(
                self.similarity_calculator.content_lines(
                    hunk.removed_lines if _is_pure_deletion(hunk) else hunk.added_lines,
                    hunk.file_path,
                )
            )
            for hunk in (*deletion_hunks, *insertion_hunks)
        }

        moved_hunk_ids = _find_moved_pairs(
            deletion_hunks,
            insertion_hunks,
            lambda deletion, insertion: self._is_hunk_pair_likely_moved(
                deletion,
                insertion,
                hunk_lines_by_id=hunk_lines_by_id,
            ),
        )

        cross_rewrite_kinds = _find_rewrite_pairs(
            [hunk for hunk in deletion_hunks if id(hunk) not in moved_hunk_ids],
            [hunk for hunk in insertion_hunks if id(hunk) not in moved_hunk_ids],
            lambda deletion, insertion: self._classify_rewrite_kind(deletion, insertion),
        )

        self_rewrite_kinds = {
            id(hunk): kind
            for hunk in mixed_hunks
            if (kind := self._classify_rewrite_kind(hunk, hunk)) is not None
        }

        return moved_hunk_ids, {**cross_rewrite_kinds, **self_rewrite_kinds}

    def _is_hunk_pair_likely_moved(
        self,
        deletion: Hunk,
        insertion: Hunk,
        *,
        hunk_lines_by_id: dict[int, tuple[str, ...]],
    ) -> bool:
        """Check one deletion/addition hunk pair against movement detection rules."""
        deletion_lines = hunk_lines_by_id[id(deletion)]
        insertion_lines = hunk_lines_by_id[id(insertion)]

        return self.movement_detector.hunks_are_likely_moved(
            deletion,
            insertion,
            similarity=self.similarity_calculator.pair_sequence_similarity(
                id(deletion), id(insertion), deletion_lines, insertion_lines
            ),
            deletion_line_count=len(deletion_lines),
            insertion_line_count=len(insertion_lines),
        )

    def _classify_rewrite_kind(self, deletion: Hunk, insertion: Hunk) -> HunkRewriteKind | None:
        """Classify one unmatched deletion/addition hunk pair as a complex rewrite."""
        return self.complex_rewrite_detector.classify_rewrite(
            deletion,
            insertion,
            self.similarity_calculator,
        )

    def _annotate_hunks(
        self,
        file: FileDiff,
        moved_hunk_ids: set[int],
        rewrite_kinds_by_hunk_id: dict[int, HunkRewriteKind],
    ) -> None:
        """Apply enrichment flags to hunks belonging to one file."""
        for hunk in file.hunks:
            if id(hunk) in moved_hunk_ids:
                hunk.is_likely_moved = True
            if id(hunk) in rewrite_kinds_by_hunk_id:
                hunk.rewrite_kind = rewrite_kinds_by_hunk_id[id(hunk)]


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


def _find_rewrite_pairs(
    sources: list[T],
    targets: list[T],
    classify: Callable[[T, T], HunkRewriteKind | None],
) -> dict[int, HunkRewriteKind]:
    """Return rewrite classifications for all matched source/target pairs.

    Each source and target is matched at most once. Once a pair is classified,
    both are removed from further consideration.
    """
    matched_ids: set[int] = set()
    classifications: dict[int, HunkRewriteKind] = {}
    for source in sources:
        if id(source) in matched_ids:
            continue
        for target in targets:
            if id(target) in matched_ids:
                continue
            if (kind := classify(source, target)) is not None:
                matched_ids.add(id(source))
                matched_ids.add(id(target))
                classifications[id(source)] = kind
                classifications[id(target)] = kind
                break
    return classifications


def _is_pure_deletion(hunk: Hunk) -> bool:
    return hunk.removed_count > 0 and hunk.added_count == 0


def _is_pure_insertion(hunk: Hunk) -> bool:
    return hunk.added_count > 0 and hunk.removed_count == 0


def _is_mixed(hunk: Hunk) -> bool:
    return hunk.removed_count > 0 and hunk.added_count > 0
