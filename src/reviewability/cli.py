import argparse
import json
import sys
from pathlib import Path

from reviewability.config.parser import parse_config
from reviewability.diff_reader import parse_diff_text
from reviewability.factory import create_analyzer
from reviewability.formatter import build_output
from reviewability.gate import QualityGate
from reviewability.git import parse_git_diff

_DEFAULT_CONFIG = Path("reviewability.toml")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reviewability",
        description="Analyze code diffs and score their reviewability.",
    )
    parser.add_argument(
        "-c",
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
        "--detailed",
        action="store_true",
        help="Include per-file and per-hunk metric breakdowns in the output",
    )
    parser.add_argument(
        "git_args",
        nargs="*",
        help="Arguments forwarded to git diff (e.g. HEAD~1 HEAD)",
    )
    args = parser.parse_args()

    config = parse_config(args.config)
    if args.from_stdin:
        diff = parse_diff_text(sys.stdin.read(), config)
    else:
        diff = parse_git_diff(config, *args.git_args)
    report, violations = create_analyzer(config).run(diff)
    gate_result = QualityGate().evaluate(report, violations, config)

    print(json.dumps(build_output(report, violations, gate_result, args.detailed), indent=2))

    if not gate_result.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
