import subprocess

from unidiff import PatchSet

from reviewability.diff.move_detector import MoveDetector
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import ChangeType, Diff, FileDiff, Hunk, HunkType, Move, MoveType


def parse_diff_text(diff_text: str) -> Diff:
    patch = PatchSet(diff_text)
    files = [
        FileDiff(
            path=patched_file.path,
            old_path=(
                patched_file.source_file.removeprefix("a/") if patched_file.is_rename else None
            ),
            is_new_file=patched_file.is_added_file,
            is_deleted_file=patched_file.is_removed_file,
            hunks=[
                Hunk(
                    file_path=patched_file.path,
                    added_lines=[str(line.value) for line in hunk if line.is_added],
                    removed_lines=[str(line.value) for line in hunk if line.is_removed],
                    context_lines=[str(line.value) for line in hunk if line.is_context],
                    change_order=tuple(
                        ChangeType.ADDED if line.is_added else ChangeType.REMOVED
                        for line in hunk
                        if not line.is_context
                    ),
                )
                for hunk in patched_file
            ],
        )
        for patched_file in patch
    ]

    all_hunks = [hunk for file in files for hunk in file.hunks]
    moves = MoveDetector(DiffSimilarityCalculator()).detect(all_hunks)
    _assign_hunk_types(all_hunks, moves)
    move_ids = {id(h) for m in moves for h in m.hunks}
    singleton_hunks = [h for h in all_hunks if id(h) not in move_ids]
    return Diff(files=files, moves=moves, singleton_hunks=singleton_hunks)


def _assign_hunk_types(all_hunks: list[Hunk], moves: list[Move]) -> None:
    """Assign HunkType to every hunk in-place.

    Called once in the reader after move detection, before the Diff is constructed.
    Hunks in moves with MoveType.PURE get HunkType.MOVE; all others in moves
    get HunkType.MIXED. Singleton hunks are classified by their line content.
    """
    move_hunk_ids = {id(h) for m in moves if m.move_type == MoveType.PURE for h in m.hunks}
    mixed_hunk_ids = {id(h) for m in moves if m.move_type != MoveType.PURE for h in m.hunks}

    for hunk in all_hunks:
        if id(hunk) in move_hunk_ids:
            hunk.hunk_type = HunkType.MOVE
        elif id(hunk) in mixed_hunk_ids:
            hunk.hunk_type = HunkType.MIXED
        elif hunk.added_lines and not hunk.removed_lines:
            hunk.hunk_type = HunkType.PURE_ADDITION
        elif hunk.removed_lines and not hunk.added_lines:
            hunk.hunk_type = HunkType.PURE_DELETION
        else:
            hunk.hunk_type = HunkType.MIXED


def parse_git_diff(*git_diff_args: str) -> Diff:
    """Run `git diff <args>` and parse the output."""
    result = subprocess.run(
        ["git", "diff", *git_diff_args],
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_diff_text(result.stdout)
