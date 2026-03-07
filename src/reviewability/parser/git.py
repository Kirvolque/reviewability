import subprocess

from unidiff import PatchSet

from reviewability.domain.models import Diff, FileDiff, Hunk


def parse_diff_text(diff_text: str) -> Diff:
    patch = PatchSet(diff_text)
    files: list[FileDiff] = []

    for patched_file in patch:
        hunks: list[Hunk] = []
        for hunk in patched_file:
            added = [str(line.value) for line in hunk if line.is_added]
            removed = [str(line.value) for line in hunk if line.is_removed]
            context = [str(line.value) for line in hunk if line.is_context]
            hunks.append(
                Hunk(
                    file_path=patched_file.path,
                    source_start=hunk.source_start,
                    source_length=hunk.source_length,
                    target_start=hunk.target_start,
                    target_length=hunk.target_length,
                    added_lines=added,
                    removed_lines=removed,
                    context_lines=context,
                )
            )

        files.append(
            FileDiff(
                path=patched_file.path,
                old_path=patched_file.source_file if patched_file.is_rename else None,
                is_new_file=patched_file.is_added_file,
                is_deleted_file=patched_file.is_removed_file,
                hunks=hunks,
            )
        )

    return Diff(files=files)


def parse_git_diff(*git_diff_args: str) -> Diff:
    """Run `git diff <args>` and parse the output."""
    result = subprocess.run(
        ["git", "diff", *git_diff_args],
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_diff_text(result.stdout)
