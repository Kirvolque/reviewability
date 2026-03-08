import json
import subprocess
import sys
from pathlib import Path

import pytest

CASES_DIR = Path(__file__).parent / "cases"

_pass_cases = sorted(p.name for p in CASES_DIR.iterdir() if p.name.startswith("pass_"))
_fail_cases = sorted(p.name for p in CASES_DIR.iterdir() if p.name.startswith("fail_"))

_EXPECTED_EXIT_CODE = {"pass": 0, "fail": 1}


def _run(case_name: str) -> tuple[int, dict]:
    case = CASES_DIR / case_name
    diff_text = (case / "diff.patch").read_text()
    config_path = case / "config.toml"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "reviewability.cli",
            "--from-stdin",
            "--detailed",
            "--config",
            str(config_path),
        ],
        input=diff_text,
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    return result.returncode, output


@pytest.mark.parametrize("case_name", _pass_cases)
def test_pass_case(case_name: str) -> None:
    case = CASES_DIR / case_name
    expected = json.loads((case / "expected.json").read_text())
    returncode, output = _run(case_name)
    assert returncode == 0, f"[{case_name}] expected exit 0, got {returncode}"
    assert output == expected, f"[{case_name}] output mismatch"


@pytest.mark.parametrize("case_name", _fail_cases)
def test_fail_case(case_name: str) -> None:
    case = CASES_DIR / case_name
    expected = json.loads((case / "expected.json").read_text())
    returncode, output = _run(case_name)
    assert returncode == 1, f"[{case_name}] expected exit 1, got {returncode}"
    assert output == expected, f"[{case_name}] output mismatch"
