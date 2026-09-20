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

    assert report["fixture_count"] == 20
    assert fixtures["pure_cross_file"]["reviewability"]["unexplained_lines"] == 0
    assert fixtures["modified_operator"]["reviewability"]["moves"][0][
        "residual_removed_lines"
    ] == ["if balance > 0:"]
    assert fixtures["pure_cross_file"]["git"]["renames"] == [
        {"similarity": 100, "source": "src/legacy.py", "target": "src/pricing.py"}
    ]
