import pytest
from specter.analyzer.scorer import combine_findings, AuditResult, Finding
from specter.analyzer.semgrep import SemgrepFinding
from specter.analyzer.claude import ClaudeFinding


def make_semgrep(severity="HIGH", filename="a.py", line=1):
    return SemgrepFinding(
        filename=filename, line=line, severity=severity,
        rule_id="test-rule", message="test message"
    )


def make_claude(severity="MEDIUM", filename="a.py", line=5):
    return ClaudeFinding(
        filename=filename, line=line, severity=severity,
        issue="test issue", reason="test reason"
    )


def test_empty_inputs():
    result = combine_findings([], [], "")
    assert isinstance(result, AuditResult)
    assert result.risk_level == "LOW"
    assert result.risk_score == 0
    assert result.findings == []


@pytest.mark.parametrize("semgrep_f,claude_f,expected_level", [
    ([], [],                                                                                    "LOW"),
    ([], [make_claude("MEDIUM", line=1), make_claude("MEDIUM", line=2)],                       "MEDIUM"),
    ([make_semgrep("HIGH", line=1)], [make_claude("MEDIUM", line=2), make_claude("LOW", line=3)], "HIGH"),
    ([make_semgrep("CRITICAL")], [],                                                            "CRITICAL"),
])
def test_risk_label(semgrep_f, claude_f, expected_level):
    result = combine_findings(semgrep_f, claude_f, "")
    assert result.risk_level == expected_level


def test_score_capped_at_100():
    findings = [make_semgrep("CRITICAL", line=i) for i in range(10)]
    result = combine_findings(findings, [], "")
    assert result.risk_score == 100


def test_findings_sorted_by_severity():
    sf = [make_semgrep("LOW", line=1), make_semgrep("CRITICAL", line=2), make_semgrep("HIGH", line=3)]
    result = combine_findings(sf, [], "")
    severities = [f.severity for f in result.findings]
    assert severities == ["CRITICAL", "HIGH", "LOW"]


def test_source_attribution():
    result = combine_findings([make_semgrep("HIGH")], [make_claude("MEDIUM")], "summary")
    sources = {f.source for f in result.findings}
    assert sources == {"semgrep", "claude"}


def test_summary_propagated():
    result = combine_findings([], [], "this is a summary")
    assert result.summary == "this is a summary"


def test_deduplication_same_source_keeps_highest_severity():
    sf = [make_semgrep("HIGH", line=10), make_semgrep("MEDIUM", line=10)]
    result = combine_findings(sf, [], "")
    assert len(result.findings) == 1
    assert result.findings[0].severity == "HIGH"


def test_deduplication_cross_source_same_line_kept_separately():
    sf = [make_semgrep("HIGH", line=10)]
    cf = [make_claude("MEDIUM", line=10)]
    result = combine_findings(sf, cf, "")
    assert len(result.findings) == 2
    sources = {f.source for f in result.findings}
    assert sources == {"semgrep", "claude"}


def test_deduplication_different_lines_not_merged():
    sf = [make_semgrep("HIGH", line=10)]
    cf = [make_claude("MEDIUM", line=20)]
    result = combine_findings(sf, cf, "")
    assert len(result.findings) == 2


def test_deduplication_score_counts_cross_source_separately():
    sf = [make_semgrep("HIGH", line=10)]
    cf = [make_claude("MEDIUM", line=10)]
    result = combine_findings(sf, cf, "")
    assert result.risk_score == 14  # HIGH(10) + MEDIUM(4)


def test_counts_accurate():
    sf = [make_semgrep("CRITICAL", line=1), make_semgrep("HIGH", line=2)]
    cf = [make_claude("MEDIUM", line=3), make_claude("LOW", line=4)]
    result = combine_findings(sf, cf, "")
    assert result.counts["CRITICAL"] == 1
    assert result.counts["HIGH"] == 1
    assert result.counts["MEDIUM"] == 1
    assert result.counts["LOW"] == 1
