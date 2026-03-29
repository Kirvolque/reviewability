import subprocess

from reviewability.config.models import ReviewabilityConfig
from reviewability.diff_reader import parse_diff_text
from reviewability.domain.models import Diff


def parse_git_diff(config: ReviewabilityConfig, *git_diff_args: str) -> Diff:
    """Run ``git diff <args>`` and parse the output."""
    result = subprocess.run(
        ["git", "diff", *git_diff_args],
        capture_output=True,
        text=True,
        check=True,
    )
    return parse_diff_text(result.stdout, config)
