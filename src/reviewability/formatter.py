from reviewability.domain.models import Hunk, Move
from reviewability.domain.report import Analysis, AnalysisReport
from reviewability.gate import GateResult
from reviewability.rules.engine import RuleViolation


def build_output(
    report: AnalysisReport,
    violations: list[RuleViolation],
    gate_result: GateResult,
    detailed: bool,
) -> dict:
    """Serialize an analysis report and gate result into a JSON-ready dict."""
    output: dict = {
        "score": round(report.overall.score, 2),
        "passed": gate_result.passed,
        "violations": [str(v) for v in violations],
        "recommendations": [
            {
                "location": r.location,
                "metric": r.metric,
                "value": r.value,
                "remediation": r.remediation,
            }
            for r in gate_result.recommendations
        ],
    }

    if detailed:
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
        output["moves"] = [_format_move(move) for move in report.moves]
        output["hunks"] = [
            {
                "file": h.subject.file_path,
                "score": round(h.score, 2),
                "metrics": [{"name": m.name, "value": m.value} for m in h.metrics],
            }
            for h in report.hunks
        ]

    return output


def _format_move(analysis: Analysis) -> dict[str, object]:
    """Format a move analysis after validating the generic analysis subject."""
    if not isinstance(analysis.subject, Move):
        raise TypeError("Move analysis must have a Move subject")

    move = analysis.subject
    return {
        "move_id": move.move_id,
        "source": _hunk_location(move.source_hunk),
        "target": _hunk_location(move.target_hunk),
        "hunk_count": len(move.hunks),
        "score": round(analysis.score, 2),
        "alignment": _move_alignment(move),
        "residual_removed_lines": list(move.residual_removed_lines),
        "residual_added_lines": list(move.residual_added_lines),
        "metrics": [{"name": metric.name, "value": metric.value} for metric in analysis.metrics],
    }


def _hunk_location(hunk: Hunk | None) -> dict[str, int | str] | None:
    """Return a source or target hunk location for detailed move output."""
    if hunk is None:
        return None
    return {
        "file": hunk.file_path,
        "source_start": hunk.source_start or 0,
        "source_length": hunk.source_length or 0,
        "target_start": hunk.target_start or 0,
        "target_length": hunk.target_length or 0,
    }


def _move_alignment(move: Move) -> list[dict[str, object]]:
    """Align exact move correspondence and retain unmatched edits as separate rows."""
    source = move.source_hunk
    target = move.target_hunk
    if source is None or target is None:
        return []

    target_indices = _line_indices(target.added_lines)
    matched_target_indices: set[int] = set()
    alignment: list[dict[str, object]] = []

    for source_index, line in enumerate(source.removed_lines):
        candidates = target_indices.get(line, [])
        target_index = next(
            (index for index in candidates if index not in matched_target_indices), None
        )
        if target_index is None:
            alignment.append(
                {
                    "kind": "removed",
                    "source": _line_reference(source, source.source_start, source_index, line),
                }
            )
            continue

        matched_target_indices.add(target_index)
        alignment.append(
            {
                "kind": "exact_match",
                "source": _line_reference(source, source.source_start, source_index, line),
                "target": _line_reference(target, target.target_start, target_index, line),
            }
        )

    alignment.extend(
        {
            "kind": "added",
            "target": _line_reference(target, target.target_start, target_index, line),
        }
        for target_index, line in enumerate(target.added_lines)
        if target_index not in matched_target_indices
    )
    return alignment


def _line_indices(lines: list[str]) -> dict[str, list[int]]:
    indices: dict[str, list[int]] = {}
    for index, line in enumerate(lines):
        indices.setdefault(line, []).append(index)
    return indices


def _line_reference(
    hunk: Hunk, line_start: int | None, index: int, content: str
) -> dict[str, int | str]:
    return {
        "file": hunk.file_path,
        "line": (line_start or 0) + index,
        "content": content,
    }
