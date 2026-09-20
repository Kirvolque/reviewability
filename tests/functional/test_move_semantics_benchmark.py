import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
SCRIPT = ROOT / "scripts" / "benchmark_move_semantics.py"


def test_benchmark_runner_reports_current_and_git_signals(tmp_path: Path) -> None:
    output_path = tmp_path / "benchmark.json"

    subprocess.run(
        [sys.executable, str(SCRIPT), "--output", str(output_path)],
        check=True,
        cwd=ROOT,
    )

    report = json.loads(output_path.read_text())
    fixtures = {fixture["name"]: fixture for fixture in report["fixtures"]}

    assert report["fixture_count"] == 21
    assert report["evaluation"]["reviewability_file_pair"] == {
        "true_positive": 16,
        "false_positive": 1,
        "false_negative": 0,
        "precision": 0.941,
        "recall": 1.0,
        "f1": 0.97,
    }
    assert report["evaluation"]["git_file_rename"] == {
        "true_positive": 11,
        "false_positive": 0,
        "false_negative": 5,
        "precision": 1.0,
        "recall": 0.688,
        "f1": 0.815,
    }
    assert fixtures["pure_cross_file"]["reviewability"]["unexplained_lines"] == 0
    assert fixtures["modified_operator"]["reviewability"]["moves"][0][
        "residual_removed_lines"
    ] == ["if balance > 0:"]
    assert fixtures["pure_cross_file"]["git"]["renames"] == [
        {"similarity": 100, "source": "src/legacy.py", "target": "src/pricing.py"}
    ]
