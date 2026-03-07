import argparse
import json
import sys

from reviewability.parser.git import parse_diff_text, parse_git_diff
from reviewability.metrics.registry import MetricRegistry
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

    if args.from_stdin:
        diff = parse_diff_text(sys.stdin.read())
    else:
        diff = parse_git_diff(*args.git_args)

    registry = MetricRegistry()
    # TODO: register metrics here

    engine = RuleEngine(rules=[])
    # TODO: load rules from config

    results = registry.run(diff)
    violations = engine.evaluate(results)

    output = {
        "files": diff.total_files_changed,
        "hunks": diff.total_hunks,
        "metrics": [
            {
                "metric": r.metric_name,
                "scope": r.scope.value,
                "value": r.value,
                "file": r.file_path,
                "hunk": r.hunk_index,
            }
            for r in results
        ],
        "violations": [str(v) for v in violations],
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
