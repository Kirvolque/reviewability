from reviewability.domain.report import AnalysisReport
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

    return output
