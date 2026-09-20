from dataclasses import dataclass
from pathlib import Path

import pytest

from reviewability.config.parser import parse_config
from reviewability.diff_reader import parse_diff_text
from reviewability.domain.models import MoveType
from reviewability.factory import create_analyzer

FIXTURES = Path(__file__).parent.parent / "fixtures" / "move_semantics"
CONFIG = parse_config()


@dataclass(frozen=True)
class FixtureExpectation:
    name: str
    raw_lines: int
    unexplained_lines: int
    move_type: MoveType | None
    residual_removed_count: int = 0
    residual_added_count: int = 0


FIXTURES_TO_EXPECTATIONS = (
    FixtureExpectation("pure_cross_file", 10, 0, MoveType.PURE),
    FixtureExpectation("pure_same_file", 8, 0, MoveType.PURE),
    FixtureExpectation("pure_whitespace_normalized", 6, 0, MoveType.PURE),
    FixtureExpectation("pure_reordered_lines", 8, 0, MoveType.PURE),
    FixtureExpectation("modified_rename", 10, 2, MoveType.MODIFIED, 1, 1),
    FixtureExpectation("modified_operator", 10, 2, MoveType.MODIFIED, 1, 1),
    FixtureExpectation("modified_added_guard", 10, 2, MoveType.MODIFIED, 0, 2),
    FixtureExpectation("modified_removed_log", 9, 1, MoveType.MODIFIED, 1, 0),
    FixtureExpectation("modified_rename_and_guard", 12, 4, MoveType.MODIFIED, 1, 3),
    FixtureExpectation("modified_large_rewrite", 17, 13, MoveType.MODIFIED, 6, 7),
    FixtureExpectation("in_place_rewrite", 9, 9, None),
    FixtureExpectation("unrelated_hunks", 8, 8, None),
)


def _load(name: str) -> str:
    return (FIXTURES / f"{name}.diff").read_text()


@pytest.mark.parametrize("expectation", FIXTURES_TO_EXPECTATIONS)
def test_move_semantics_fixture(expectation: FixtureExpectation) -> None:
    diff = parse_diff_text(_load(expectation.name), CONFIG)
    report, _ = create_analyzer(CONFIG).run(diff)

    assert report.overall.metric("overall.lines_changed").value == expectation.raw_lines  # type: ignore[union-attr]
    assert report.overall.metric("overall.unexplained_lines").value == expectation.unexplained_lines  # type: ignore[union-attr]

    if expectation.move_type is None:
        assert diff.moves == []
        return

    assert len(diff.moves) == 1
    move = diff.moves[0]
    assert move.move_type is expectation.move_type
    assert len(move.residual_removed_lines) == expectation.residual_removed_count
    assert len(move.residual_added_lines) == expectation.residual_added_count


def test_score_ordering_for_move_fixture_extremes() -> None:
    pure_report, _ = create_analyzer(CONFIG).run(
        parse_diff_text(_load("pure_cross_file"), CONFIG)
    )
    small_rewrite_report, _ = create_analyzer(CONFIG).run(
        parse_diff_text(_load("modified_rename"), CONFIG)
    )
    large_rewrite_report, _ = create_analyzer(CONFIG).run(
        parse_diff_text(_load("modified_large_rewrite"), CONFIG)
    )

    assert pure_report.overall.score > small_rewrite_report.overall.score
    assert small_rewrite_report.overall.score > large_rewrite_report.overall.score
