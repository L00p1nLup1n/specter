import pytest
from analyzer.semgrep import _normalize_severity


@pytest.mark.parametrize("input_sev,expected", [
    ("ERROR",   "CRITICAL"),
    ("WARNING",  "HIGH"),
    ("INFO",    "MEDIUM"),
    ("NOTE",    "LOW"),
    ("CRITICAL", "CRITICAL"),  # already-normalized values pass through
    ("HIGH",    "HIGH"),
    ("UNKNOWN", "UNKNOWN"),    # unknown strings pass through unchanged
])
def test_normalize_severity(input_sev, expected):
    assert _normalize_severity(input_sev) == expected
