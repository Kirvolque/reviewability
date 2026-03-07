import argparse
import json
import sys

from reviewability.metrics.registry import MetricRegistry
from reviewability.parser.git import parse_diff_text, parse_git_diff
from reviewability.rules.engine import RuleEngine


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="reviewability",
        description="Analyze code diffs for review cognitive load.",
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

    registry = MetricRegistry()
    # TODO: register metrics here

    engine = RuleEngine(rules=[])
    # TODO: load rules from config

    report = registry.run(diff)
    all_metrics = [
        *report.overall,
        *(m for f in report.files for m in f.metrics),
        *(m for h in report.hunks for m in h.metrics),
    ]  # noqa: E501
    violations = engine.evaluate(all_metrics)

    output = {
        "files": diff.total_files_changed,
        "hunks": diff.total_hunks,
        "score": report.score,
        "metrics": {
            "overall": [{"name": m.name, "value": m.value} for m in report.overall],
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
        },
        "violations": [str(v) for v in violations],
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
