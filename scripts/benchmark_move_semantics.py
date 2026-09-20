"""Compare correspondence signals for the synthetic move-semantics fixtures.

The report records raw observations from Reviewability and Git. It deliberately
does not convert them into an accuracy score: the fixture expectations remain in
the functional test, while external tools expose different correspondence models.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from unidiff import PatchSet

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviewability.config.parser import parse_config  # noqa: E402
from reviewability.diff_reader import parse_diff_text  # noqa: E402
from reviewability.factory import create_analyzer  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "move_semantics"
EXPECTATIONS = FIXTURES / "expectations.json"
_MOVED_COLOR = re.compile(r"\x1b\[1;(?:35|36)m")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the JSON report to this path instead of standard output.",
    )
    parser.add_argument(
        "--refactoring-miner",
        type=Path,
        help="Path to a RefactoringMiner CLI executable to evaluate as an external baseline.",
    )
    parser.add_argument(
        "--java-home",
        type=Path,
        help="Java home used for RefactoringMiner; requires bin/java when the baseline is enabled.",
    )
    args = parser.parse_args()
    if args.refactoring_miner is not None and not args.refactoring_miner.is_file():
        parser.error(f"RefactoringMiner executable does not exist: {args.refactoring_miner}")
    if args.java_home is not None and not (args.java_home / "bin" / "java").is_file():
        parser.error(f"Java home does not contain bin/java: {args.java_home}")

    config = parse_config()
    expectations = json.loads(EXPECTATIONS.read_text())
    fixtures = [
        _benchmark_fixture(path, config, args.refactoring_miner, args.java_home)
        for path in sorted(FIXTURES.glob("*.diff"))
    ]
    report = {
        "fixture_count": len(fixtures),
        "git_version": _git_version(),
        "refactoring_miner": _refactoring_miner_status(args.refactoring_miner, args.java_home),
        "fixtures": fixtures,
        "evaluation": _evaluate(fixtures, expectations),
    }
    output = json.dumps(report, indent=2) + "\n"

    if args.output is None:
        print(output, end="")
    else:
        args.output.write_text(output)

    return 0


def _benchmark_fixture(
    path: Path,
    config: Any,
    refactoring_miner: Path | None,
    java_home: Path | None,
) -> dict[str, Any]:
    diff_text = path.read_text()
    diff = parse_diff_text(diff_text, config)
    analysis, _ = create_analyzer(config).run(diff)

    return {
        "name": path.stem,
        "reviewability": {
            "lines_changed": _metric_value(analysis.overall, "overall.lines_changed"),
            "unexplained_lines": _metric_value(analysis.overall, "overall.unexplained_lines"),
            "moves": [
                {
                    "type": move.move_type.value,
                    "similarity": move.similarity,
                    "source": _hunk_location(move.source_hunk),
                    "target": _hunk_location(move.target_hunk),
                    "residual_removed_lines": list(move.residual_removed_lines),
                    "residual_added_lines": list(move.residual_added_lines),
                }
                for move in diff.moves
            ],
        },
        **_external_signals(diff_text, refactoring_miner, java_home),
    }


def _metric_value(analysis: Any, name: str) -> int:
    metric = analysis.metric(name)
    if metric is None:
        raise ValueError(f"Benchmark metric is not registered: {name}")
    return metric.value


def _evaluate(fixtures: list[dict[str, Any]], expectations: dict[str, Any]) -> dict[str, Any]:
    expected_pairs = {
        fixture["name"]: {
            (move["source"], move["target"])
            for move in expectations[fixture["name"]]["moves"]
        }
        for fixture in fixtures
    }
    reviewability_pairs = {
        fixture["name"]: {
            (move["source"]["file"], move["target"]["file"])
            for move in fixture["reviewability"]["moves"]
        }
        for fixture in fixtures
    }
    git_pairs = {
        fixture["name"]: {
            (rename["source"], rename["target"])
            for rename in fixture["git"]["renames"]
        }
        for fixture in fixtures
    }
    return {
        "reviewability_file_pair": _pair_metrics(expected_pairs, reviewability_pairs),
        "git_file_rename": _pair_metrics(expected_pairs, git_pairs),
        "refactoring_miner_fixture_claim": _refactoring_miner_claim_metrics(
            fixtures, expected_pairs
        ),
    }


def _pair_metrics(
    expected_by_fixture: dict[str, set[tuple[str, str]]],
    predicted_by_fixture: dict[str, set[tuple[str, str]]],
) -> dict[str, float | int]:
    true_positive = sum(
        len(expected_by_fixture[name] & predicted_by_fixture[name])
        for name in expected_by_fixture
    )
    false_positive = sum(
        len(predicted_by_fixture[name] - expected_by_fixture[name])
        for name in expected_by_fixture
    )
    false_negative = sum(
        len(expected_by_fixture[name] - predicted_by_fixture[name])
        for name in expected_by_fixture
    )
    return _classification_metrics(true_positive, false_positive, false_negative)


def _refactoring_miner_claim_metrics(
    fixtures: list[dict[str, Any]], expected_pairs: dict[str, set[tuple[str, str]]]
) -> dict[str, float | int | str]:
    statuses = {fixture["refactoring_miner"]["status"] for fixture in fixtures}
    if statuses == {"not_requested"}:
        return {"status": "not_requested"}

    true_positive = sum(
        bool(expected_pairs[fixture["name"]])
        and bool(fixture["refactoring_miner"]["refactorings"])
        for fixture in fixtures
    )
    false_positive = sum(
        not expected_pairs[fixture["name"]]
        and bool(fixture["refactoring_miner"]["refactorings"])
        for fixture in fixtures
    )
    false_negative = sum(
        bool(expected_pairs[fixture["name"]])
        and not bool(fixture["refactoring_miner"]["refactorings"])
        for fixture in fixtures
    )
    return {
        "status": "completed_with_fixture_level_claims",
        **_classification_metrics(true_positive, false_positive, false_negative),
    }


def _classification_metrics(
    true_positive: int, false_positive: int, false_negative: int
) -> dict[str, float | int]:
    precision_denominator = true_positive + false_positive
    recall_denominator = true_positive + false_negative
    precision = true_positive / precision_denominator if precision_denominator else 1.0
    recall = true_positive / recall_denominator if recall_denominator else 1.0
    f1_denominator = precision + recall
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(2 * precision * recall / f1_denominator, 3) if f1_denominator else 0.0,
    }


def _hunk_location(hunk: Any) -> dict[str, int | str | None] | None:
    if hunk is None:
        return None
    return {
        "file": hunk.file_path,
        "source_start": hunk.source_start,
        "target_start": hunk.target_start,
    }


def _external_signals(
    diff_text: str, refactoring_miner: Path | None, java_home: Path | None
) -> dict[str, Any]:
    """Materialize the fixture in a temporary repository and query Git signals."""
    with tempfile.TemporaryDirectory(prefix="reviewability-benchmark-") as temp_dir:
        repository = Path(temp_dir)
        before, after = _materialize_trees(diff_text)
        _write_tree(repository, before)
        _run_git(repository, "init", "--quiet")
        _run_git(repository, "add", ".")
        _run_git(
            repository,
            "-c",
            "user.name=Benchmark",
            "-c",
            "user.email=benchmark@example.test",
            "commit",
            "--quiet",
            "--allow-empty",
            "-m",
            "before",
        )

        _clear_worktree(repository)
        _write_tree(repository, after)
        _run_git(repository, "add", "--all")

        name_status = _run_git(repository, "diff", "--cached", "--name-status", "-M")
        moved_diff = _run_git(
            repository,
            "diff",
            "--cached",
            "--color=always",
            "--color-moved=plain",
        )
        refactoring_miner_signals = _run_refactoring_miner(
            repository, refactoring_miner, java_home
        )

    return {
        "git": {
            "renames": _parse_renames(name_status),
            "moved_line_highlights": len(_MOVED_COLOR.findall(moved_diff)),
        },
        "refactoring_miner": refactoring_miner_signals,
    }


def _materialize_trees(diff_text: str) -> tuple[dict[Path, str], dict[Path, str]]:
    """Build minimal before/after trees from fixture hunk content.

    The fixtures are intentionally self-contained; omitted unchanged regions are
    irrelevant to Git's rename and moved-line signals used by this benchmark.
    """
    before: dict[Path, str] = {}
    after: dict[Path, str] = {}
    for patched_file in PatchSet(diff_text):
        source_path = _patch_path(patched_file.source_file)
        target_path = _patch_path(patched_file.target_file)
        old_content = "".join(
            str(line.value)
            for hunk in patched_file
            for line in hunk
            if not line.is_added
        )
        new_content = "".join(
            str(line.value)
            for hunk in patched_file
            for line in hunk
            if not line.is_removed
        )
        if source_path is not None and old_content:
            before[source_path] = old_content
        if target_path is not None and new_content:
            after[target_path] = new_content
    return before, after


def _patch_path(path: str) -> Path | None:
    if path == "/dev/null":
        return None
    return Path(path.removeprefix("a/").removeprefix("b/"))


def _write_tree(root: Path, files: dict[Path, str]) -> None:
    for path, content in files.items():
        destination = root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)


def _clear_worktree(repository: Path) -> None:
    for path in repository.iterdir():
        if path.name == ".git":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def _run_git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _run_git_status(repository: Path, *arguments: str) -> int:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        capture_output=True,
        text=True,
    ).returncode


def _parse_renames(name_status: str) -> list[dict[str, str | int]]:
    renames = []
    for line in name_status.splitlines():
        status, *paths = line.split("\t")
        if status.startswith("R") and len(paths) == 2:
            renames.append(
                {
                    "similarity": int(status.removeprefix("R")),
                    "source": paths[0],
                    "target": paths[1],
                }
            )
    return renames


def _run_refactoring_miner(
    repository: Path, executable: Path | None, java_home: Path | None
) -> dict[str, Any]:
    if executable is None:
        return {"status": "not_requested", "refactorings": []}
    if _run_git_status(repository, "diff", "--cached", "--quiet") == 0:
        return {"status": "skipped_no_git_change", "refactorings": []}

    _run_git(
        repository,
        "-c",
        "user.name=Benchmark",
        "-c",
        "user.email=benchmark@example.test",
        "commit",
        "--quiet",
        "-m",
        "after",
    )
    output_path = repository / "refactorings.json"
    result = subprocess.run(
        [str(executable), "-c", str(repository), "HEAD", "-json", str(output_path)],
        capture_output=True,
        env=_refactoring_miner_environment(java_home),
        text=True,
    )
    if result.returncode != 0:
        return {"status": "failed", "error": result.stderr.strip(), "refactorings": []}

    data = json.loads(output_path.read_text())
    refactorings = [
        {
            "type": refactoring["type"],
            "description": refactoring["description"],
        }
        for commit in data.get("commits", [])
        for refactoring in commit.get("refactorings", [])
    ]
    return {"status": "completed", "refactorings": refactorings}


def _refactoring_miner_environment(java_home: Path | None) -> dict[str, str] | None:
    if java_home is None:
        return None
    return os.environ | {
        "JAVA_HOME": str(java_home),
        "PATH": f"{java_home / 'bin'}:{os.environ['PATH']}",
    }


def _git_version() -> str:
    return subprocess.run(
        ["git", "--version"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _refactoring_miner_status(
    executable: Path | None, java_home: Path | None
) -> dict[str, str | None]:
    return {
        "status": "requested" if executable else "not_requested",
        "executable": str(executable) if executable else None,
        "java_home": str(java_home) if java_home else None,
        "reason": None
        if executable
        else "Pass --refactoring-miner with a pinned CLI executable to run this baseline.",
    }


if __name__ == "__main__":
    raise SystemExit(main())
