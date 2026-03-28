import subprocess

from unidiff import PatchSet

from reviewability.diff.grouper import HunkGrouper
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Diff, FileDiff, GroupType, Hunk, HunkGroup, HunkType


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
                    source_start=hunk.source_start,
                    source_length=hunk.source_length,
                    target_start=hunk.target_start,
                    target_length=hunk.target_length,
                    added_lines=[str(line.value) for line in hunk if line.is_added],
                    removed_lines=[str(line.value) for line in hunk if line.is_removed],
                    context_lines=[str(line.value) for line in hunk if line.is_context],
                )
                for hunk in patched_file
            ],
        )
        for patched_file in patch
    ]

    all_hunks = [hunk for file in files for hunk in file.hunks]
    groups = HunkGrouper(DiffSimilarityCalculator()).group(all_hunks)
    _assign_hunk_types(all_hunks, groups)
    return Diff(files=files, groups=groups)


def _assign_hunk_types(all_hunks: list[Hunk], groups: list[HunkGroup]) -> None:
    """Assign HunkType to every hunk in-place.

    Called once in the reader after grouping, before the Diff is constructed.
    Grouped hunks with GroupType.MOVED get HunkType.MOVE; all others in groups
    get HunkType.MIXED. Singleton hunks are classified by their line content.
    """
    move_hunk_ids = {id(h) for g in groups if g.group_type == GroupType.MOVED for h in g.hunks}
    mixed_hunk_ids = {id(h) for g in groups if g.group_type != GroupType.MOVED for h in g.hunks}

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
