from dataclasses import dataclass

from specter.config import SEVERITY_ORDER
from specter.analyzer.semgrep import SemgrepFinding
from specter.analyzer.claude import ClaudeFinding
from specter.analyzer.gemini import GeminiFinding


@dataclass
class Finding:
    filename: str
    line: int
    severity: str
    source: str  # "semgrep" | "claude" | "gemini"
    issue: str
    reason: str


@dataclass
class AuditResult:
    risk_level: str  # LOW | MEDIUM | HIGH | CRITICAL
    risk_score: int  # 0-100
    findings: list[Finding]
    summary: str
    counts: dict[str, int]


def _deduplicate(findings: list[Finding]) -> list[Finding]:
    # Only merge findings from the same source at the same line.
    # Different sources flagging the same line may have found distinct issues.
    groups: dict[tuple[str, int, str], list[Finding]] = {}
    for f in findings:
        groups.setdefault((f.filename, f.line, f.source), []).append(f)

    return [
        max(group, key=lambda f: SEVERITY_ORDER.get(f.severity, 0))
        for group in groups.values()
    ]


def _score_finding(severity: str) -> int:
    weights = {"CRITICAL": 25, "HIGH": 10, "MEDIUM": 4, "LOW": 1, "INFO": 0}
    return weights.get(severity, 0)


def _risk_label(score: int) -> str:
    if score >= 25:
        return "CRITICAL"
    if score >= 15:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"


def combine_findings(
    semgrep: list[SemgrepFinding],
    claude: list[ClaudeFinding],
    claude_summary: str,
    gemini: list[GeminiFinding] | None = None,
    gemini_summary: str = "",
) -> AuditResult:
    findings: list[Finding] = []

    for f in semgrep:
        findings.append(
            Finding(
                filename=f.filename,
                line=f.line,
                severity=f.severity,
                source="semgrep",
                issue=f.rule_id,
                reason=f.message,
            )
        )

    for f in claude:
        findings.append(
            Finding(
                filename=f.filename,
                line=f.line,
                severity=f.severity,
                source="claude",
                issue=f.issue,
                reason=f.reason,
            )
        )

    for f in gemini or []:
        findings.append(
            Finding(
                filename=f.filename,
                line=f.line,
                severity=f.severity,
                source="gemini",
                issue=f.issue,
                reason=f.reason,
            )
        )

    findings = _deduplicate(findings)
    findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 0), reverse=True)

    score = min(100, sum(_score_finding(f.severity) for f in findings))
    counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for f in findings:
        if f.severity in counts:
            counts[f.severity] += 1

    summaries = [s for s in [claude_summary, gemini_summary] if s]
    return AuditResult(
        risk_level=_risk_label(score),
        risk_score=score,
        findings=findings,
        summary=" | ".join(summaries),
        counts=counts,
    )
