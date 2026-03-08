import argparse
import json
import sys
from pathlib import Path

from reviewability.analyzer import create_analyzer
from reviewability.config.models import ReviewabilityConfig
from reviewability.config.parser import parse_config
from reviewability.gate import QualityGate
from reviewability.parser.git import parse_diff_text, parse_git_diff

_DEFAULT_CONFIG = Path("reviewability.toml")


def _load_config(path: Path) -> ReviewabilityConfig:
    if path.exists():
        return parse_config(path)
    return ReviewabilityConfig()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reviewability",
        description="Analyze code diffs and score their reviewability.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=_DEFAULT_CONFIG,
        metavar="PATH",
        help=f"Path to config file (default: {_DEFAULT_CONFIG})",
    )
    parser.add_argument(
        "--from-stdin",
        action="store_true",
        help="Read diff from stdin instead of running git diff",
    )
    parser.add_argument(
        "git_args",
        nargs="*",
        help="Arguments forwarded to git diff (e.g. HEAD~1 HEAD)",
    )
    args = parser.parse_args()

    diff = parse_diff_text(sys.stdin.read()) if args.from_stdin else parse_git_diff(*args.git_args)
    config = _load_config(args.config)
    report, violations = create_analyzer(config).run(diff)
    gate_result = QualityGate(config).evaluate(report, violations)

    output = {
        "score": report.overall.score,
        "files_changed": len(report.files),
        "hunks_changed": len(report.hunks),
        "overall": [{"name": m.name, "value": m.value} for m in report.overall.metrics],
        "files": [
            {
                "file": f.file.path,
                "score": f.score,
                "metrics": [{"name": m.name, "value": m.value} for m in f.metrics],
            }
            for f in report.files
        ],
        "hunks": [
            {
                "file": h.hunk.file_path,
                "score": h.score,
                "metrics": [{"name": m.name, "value": m.value} for m in h.metrics],
            }
            for h in report.hunks
        ],
        "violations": [str(v) for v in violations],
        "passed": gate_result.passed,
        "recommendations": gate_result.recommendations,
    }

    print(json.dumps(output, indent=2))

    if not gate_result.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
