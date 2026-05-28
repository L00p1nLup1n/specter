import json
import pytest
from io import StringIO
from unittest.mock import patch

from specter.analyzer.scorer import AuditResult, Finding
from specter.output.formatter import print_json


def make_result(risk_level="LOW", score=0, findings=None, summary=""):
    return AuditResult(
        risk_level=risk_level,
        risk_score=score,
        findings=findings or [],
        summary=summary,
        counts={"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0},
    )


def capture_json(result):
    buf = StringIO()
    with patch("builtins.print", side_effect=lambda s: buf.write(s + "\n")):
        print_json(result)
    return json.loads(buf.getvalue())


def test_json_output_structure():
    result = make_result("HIGH", 20, summary="found issues")
    data = capture_json(result)
    assert set(data.keys()) == {"risk_level", "risk_score", "summary", "counts", "findings"}


@pytest.mark.parametrize("risk_level,score", [
    ("LOW",      0),
    ("MEDIUM",   8),
    ("HIGH",    20),
    ("CRITICAL", 30),
])
def test_json_risk_level(risk_level, score):
    data = capture_json(make_result(risk_level, score))
    assert data["risk_level"] == risk_level
    assert data["risk_score"] == score


def test_json_findings_serialization():
    finding = Finding(
        filename="src/auth.py", line=42, severity="HIGH",
        source="semgrep", issue="sql-injection", reason="raw input in query"
    )
    result = make_result("HIGH", 10, findings=[finding])
    data = capture_json(result)
    assert len(data["findings"]) == 1
    f = data["findings"][0]
    assert f["filename"] == "src/auth.py"
    assert f["line"] == 42
    assert f["severity"] == "HIGH"
    assert f["source"] == "semgrep"


def test_json_empty_findings():
    data = capture_json(make_result())
    assert data["findings"] == []
    assert data["summary"] == ""
