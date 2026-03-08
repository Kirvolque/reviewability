import json
import subprocess
import sys
import tempfile
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
MULTI_FILE_DIFF = FIXTURES_DIR / "multi_file_change.diff"


def _write_config(content: str) -> Path:
    """Write a TOML config to a temporary file and return its path."""
    tmp = tempfile.NamedTemporaryFile(suffix=".toml", delete=False, mode="w")
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def test_passing_analysis() -> None:
    """Permissive config should result in a passing analysis with exit code 0."""
    config_content = """\
[reviewability]
min_overall_score = 0.0
max_diff_lines = 1000
max_hunk_lines = 200
hunk_score_threshold = 0.1
file_score_threshold = 0.1
max_problematic_hunks = 100
max_problematic_files = 100
"""
    config_path = _write_config(config_content)
    try:
        diff_text = MULTI_FILE_DIFF.read_text()
        cmd = [
            sys.executable,
            "-m",
            "reviewability.cli",
            "--from-stdin",
            "--config",
            str(config_path),
        ]
        result = subprocess.run(cmd, input=diff_text, capture_output=True, text=True)
        assert result.returncode == 0, (
            f"Expected exit code 0, got {result.returncode}.\nstderr: {result.stderr}"
        )
        output = json.loads(result.stdout)
        assert output["passed"] is True
        assert 0.0 <= output["score"] <= 1.0
        assert output["files_changed"] > 0
        assert output["hunks_changed"] > 0
        assert isinstance(output["violations"], list)
        assert output["recommendations"] == []
    finally:
        config_path.unlink(missing_ok=True)


def test_failing_analysis() -> None:
    """Strict config should result in a failing analysis with exit code 1."""
    config_content = """\
[reviewability]
min_overall_score = 0.99
max_diff_lines = 1
max_hunk_lines = 200
hunk_score_threshold = 0.1
file_score_threshold = 0.1
max_problematic_hunks = 100
max_problematic_files = 100
"""
    config_path = _write_config(config_content)
    try:
        diff_text = MULTI_FILE_DIFF.read_text()
        cmd = [
            sys.executable,
            "-m",
            "reviewability.cli",
            "--from-stdin",
            "--config",
            str(config_path),
        ]
        result = subprocess.run(cmd, input=diff_text, capture_output=True, text=True)
        assert result.returncode == 1, (
            f"Expected exit code 1, got {result.returncode}.\nstderr: {result.stderr}"
        )
        output = json.loads(result.stdout)
        assert output["passed"] is False
        assert len(output["violations"]) > 0
        assert 0.0 <= output["score"] <= 1.0
    finally:
        config_path.unlink(missing_ok=True)
