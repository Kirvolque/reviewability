import subprocess

from unidiff import PatchSet

from reviewability.config.models import ReviewabilityConfig
from reviewability.diff.line_filter import import_prefixes_for
from reviewability.diff.move_detector import MoveDetector
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import ChangeType, Diff, FileDiff, Hunk, HunkType, Move, MoveType


def parse_diff_text(diff_text: str, config: ReviewabilityConfig) -> Diff:
    patch = PatchSet(diff_text)
    files = [
        FileDiff(
            path=patched_file.path,
            old_path=(
                patched_file.source_file.removeprefix("a/") if patched_file.is_rename else None
            ),
            is_new_file=patched_file.is_added_file,
            is_deleted_file=patched_file.is_removed_file,
            hunks=[_build_hunk(patched_file.path, hunk, config) for hunk in patched_file],
        )
        for patched_file in patch
    ]

    all_hunks = [hunk for file in files for hunk in file.hunks]
    moves = MoveDetector(DiffSimilarityCalculator()).detect(all_hunks)
    _assign_hunk_types(all_hunks, moves)
    move_ids = {id(h) for m in moves for h in m.hunks}
    singleton_hunks = [h for h in all_hunks if id(h) not in move_ids]
    return Diff(files=files, moves=moves, singleton_hunks=singleton_hunks)


def _build_hunk(file_path: str, hunk, config: ReviewabilityConfig) -> Hunk:
    """Build a Hunk with pre-filtered added/removed lines and change_order."""
    prefixes = import_prefixes_for(file_path, config.import_prefixes)

    # Build ordered change list then filter together so all three fields stay in sync.
    raw_changes = [
        (ChangeType.ADDED if line.is_added else ChangeType.REMOVED, str(line.value))
        for line in hunk
        if not line.is_context
    ]
    filtered = [
        (ct, norm)
        for ct, raw in raw_changes
        if (norm := " ".join(raw.split()))
        if not norm.startswith(prefixes)
    ]

    return Hunk(
        file_path=file_path,
        added_lines=[norm for ct, norm in filtered if ct == ChangeType.ADDED],
        removed_lines=[norm for ct, norm in filtered if ct == ChangeType.REMOVED],
        context_lines=[str(line.value) for line in hunk if line.is_context],
        change_order=tuple(ct for ct, _ in filtered),
    )


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


def parse_git_diff(config: ReviewabilityConfig, *git_diff_args: str) -> Diff:
    """Run `git diff <args>` and parse the output."""
    result = subprocess.run(
        ["git", "diff", *git_diff_args],
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_diff_text(result.stdout, config)
