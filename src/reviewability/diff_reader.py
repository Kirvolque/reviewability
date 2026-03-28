import subprocess

from unidiff import PatchSet

from reviewability.diff.grouper import HunkGrouper
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Diff, FileDiff, Hunk, HunkGroup


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
    grouper_result = HunkGrouper(DiffSimilarityCalculator()).group(all_hunks)
    groups: list[HunkGroup] = []
    for gid, members in grouper_result.items():
        if gid is None:
            groups += [HunkGroup(group_id=None, hunks=(hunk,)) for hunk in members]
        else:
            groups.append(HunkGroup(group_id=gid, hunks=tuple(members)))

    return Diff(files=files, groups=groups)


def parse_git_diff(*git_diff_args: str) -> Diff:
    """Run `git diff <args>` and parse the output."""
    result = subprocess.run(
        ["git", "diff", *git_diff_args],
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_diff_text(result.stdout)
