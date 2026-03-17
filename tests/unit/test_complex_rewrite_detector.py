from reviewability.diff.complex_rewrite import ComplexRewriteDetector
from reviewability.diff.similarity_calculator import DiffSimilarityCalculator
from reviewability.domain.models import Hunk, HunkRewriteKind


def before_hunk(
    removed_lines: list[str],
    *,
    start: int = 10,
    file_path: str = "policy.java",
) -> Hunk:
    return Hunk(
        file_path=file_path,
        source_start=start,
        source_length=len(removed_lines),
        target_start=start,
        target_length=0,
        removed_lines=removed_lines,
    )


def after_hunk(
    added_lines: list[str],
    *,
    start: int = 10,
    file_path: str = "policy.java",
) -> Hunk:
    return Hunk(
        file_path=file_path,
        source_start=start,
        source_length=0,
        target_start=start,
        target_length=len(added_lines),
        added_lines=added_lines,
    )


DETECTOR = ComplexRewriteDetector()
SIMILARITY_CALCULATOR = DiffSimilarityCalculator()


def test_classifies_moderately_similar_nearby_heavy_edit_as_in_place():
    before = before_hunk(
        [
            "    if (routePlan.hubHandoffRequired()) {",
            "        riskPoints += 3;",
            '        reasons.add("Hub handoff introduces coordination risk.");',
            "    }",
            "    return ReviewTier.MANDATORY;",
        ]
    )
    after = after_hunk(
        [
            "    if (routePlan.remoteCoverageRequired()) {",
            "        reviewLoad += 2;",
            '        reviewReasons.add("Remote routing requires manual confirmation.");',
            "    }",
            "    return ReviewTier.RECOMMENDED;",
        ]
    )

    assert (
        DETECTOR.classify_rewrite(before, after, SIMILARITY_CALCULATOR)
        is HunkRewriteKind.IN_PLACE_REWRITE
    )


def test_classifies_distant_heavy_edit_as_moved_rewrite():
    before = before_hunk(
        [
            "    if (routePlan.hubHandoffRequired()) {",
            "        riskPoints += 3;",
            '        reasons.add("Hub handoff introduces coordination risk.");',
            "    }",
            "    return ReviewTier.MANDATORY;",
        ],
        start=10,
    )
    after = after_hunk(
        [
            "    if (routePlan.remoteCoverageRequired()) {",
            "        reviewLoad += 2;",
            '        reviewReasons.add("Remote routing requires manual confirmation.");',
            "    }",
            "    return ReviewTier.RECOMMENDED;",
        ],
        start=20,
    )

    assert (
        DETECTOR.classify_rewrite(before, after, SIMILARITY_CALCULATOR)
        is HunkRewriteKind.MOVED_REWRITE
    )


def test_rejects_simple_high_similarity_edit():
    lines = [
        "    int riskPoints = 0;",
        "    riskPoints += 1;",
        "    riskPoints += 2;",
        "    riskPoints += 3;",
        "    return riskPoints;",
    ]
    before = before_hunk(lines)
    after = after_hunk(lines[:-1] + ["    return totalRiskPoints;"])

    assert DETECTOR.classify_rewrite(before, after, SIMILARITY_CALCULATOR) is None


def test_rejects_completely_unrelated_replacement():
    before = before_hunk(
        [
            "    int riskPoints = 0;",
            "    riskPoints += 2;",
            '    reasons.add("Hub handoff introduces coordination risk.");',
            "    return ReviewTier.MANDATORY;",
            "    }",
        ]
    )
    after = after_hunk(
        [
            "    String city = request.destination().city();",
            "    double surcharge = distanceKm * 1.4;",
            "    return baseCharge + surcharge;",
            "    }",
            "    // pricing branch",
        ]
    )

    assert DETECTOR.classify_rewrite(before, after, SIMILARITY_CALCULATOR) is None


def test_ignores_indentation_and_blank_lines():
    before = before_hunk(
        [
            "        if (routePlan.hubHandoffRequired()) {",
            "            riskPoints += 3;",
            '            reasons.add("Hub handoff introduces coordination risk.");',
            "        }",
            "        return ReviewTier.MANDATORY;",
        ]
    )
    after = after_hunk(
        [
            "    if (routePlan.remoteCoverageRequired()) {",
            "",
            "      reviewLoad += 2;",
            '      reviewReasons.add("Remote routing requires manual confirmation.");',
            "    }",
            "    return ReviewTier.RECOMMENDED;",
        ]
    )

    assert (
        DETECTOR.classify_rewrite(before, after, SIMILARITY_CALCULATOR)
        is HunkRewriteKind.IN_PLACE_REWRITE
    )
