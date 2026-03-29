import argparse
import json
import sys
from pathlib import Path

from reviewability.analyzer import create_analyzer
from reviewability.config.parser import parse_config
from reviewability.diff_reader import parse_diff_text, parse_git_diff
from reviewability.gate import QualityGate

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

    recommendations = [
        {
            "location": r.location,
            "metric": r.metric,
            "value": r.value,
            "remediation": r.remediation,
        }
        for r in gate_result.recommendations
    ]

    output: dict = {
        "score": round(report.overall.score, 2),
        "passed": gate_result.passed,
        "violations": [str(v) for v in violations],
        "recommendations": recommendations,
    }

    if args.detailed:
        output["files_changed"] = len(report.files)
        output["hunks_changed"] = len(report.hunks)
        output["overall"] = [{"name": m.name, "value": m.value} for m in report.overall.metrics]
        output["files"] = [
            {
                "file": f.subject.path,
                "score": round(f.score, 2),
                "metrics": [{"name": m.name, "value": m.value} for m in f.metrics],
            }
            for f in report.files
        ]
        output["moves"] = [
            {
                "move_id": m.subject.move_id,
                "hunk_count": len(m.subject.hunks),
                "score": round(m.score, 2),
                "metrics": [{"name": mt.name, "value": mt.value} for mt in m.metrics],
            }
            for m in report.moves
        ]
        output["hunks"] = [
            {
                "file": h.subject.file_path,
                "score": round(h.score, 2),
                "metrics": [{"name": m.name, "value": m.value} for m in h.metrics],
            }
            for h in report.hunks
        ]

    print(json.dumps(output, indent=2))

    if not gate_result.passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
