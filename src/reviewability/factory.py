from reviewability.analyzer import Analyzer
from reviewability.config.models import ReviewabilityConfig
from reviewability.metrics.engine import MetricEngine
from reviewability.metrics.file import FileLinesChanged
from reviewability.metrics.hunk import (
    HunkAddedLines,
    HunkChangeBalance,
    HunkContextLines,
    HunkInterleaving,
    HunkLinesChanged,
    HunkRemovedLines,
)
from reviewability.metrics.move import MoveEditComplexity
from reviewability.metrics.overall import (
    OverallAddedLines,
    OverallFilesChanged,
    OverallLinesChanged,
    OverallMeanInterleaving,
    OverallProblematicFileCount,
    OverallProblematicHunkCount,
    OverallProblematicMoveCount,
    OverallScatterFactor,
)
from reviewability.metrics.registry import MetricRegistry
from reviewability.rules.definitions import hunk_rules, overall_rules
from reviewability.rules.engine import RuleEngine
from reviewability.scoring.weighted import DefaultScorer


def create_analyzer(config: ReviewabilityConfig) -> Analyzer:
    """Build a fully configured ``Analyzer`` from a ``ReviewabilityConfig``."""
    registry = MetricRegistry()
    for metric in [
        HunkLinesChanged(),
        HunkAddedLines(),
        HunkRemovedLines(),
        HunkContextLines(),
        HunkChangeBalance(),
        HunkInterleaving(),
        FileLinesChanged(),
        OverallFilesChanged(),
        OverallLinesChanged(),
        OverallAddedLines(),
        OverallProblematicHunkCount(config.hunk_score_threshold),
        OverallProblematicMoveCount(config.hunk_score_threshold),
        OverallProblematicFileCount(config.file_score_threshold),
        OverallScatterFactor(),
        OverallMeanInterleaving(),
        MoveEditComplexity(config.max_move_lines, config.move_similarity_penalty),
    ]:
        registry.add(metric)

    scorer = DefaultScorer(
        max_hunk_lines=float(config.max_hunk_lines),
        max_diff_lines=float(config.max_diff_lines),
    )

    return Analyzer(
        engine=MetricEngine(registry, scorer),
        hunk_rule_engine=RuleEngine(hunk_rules(config)),
        overall_rule_engine=RuleEngine(overall_rules(config)),
    )
