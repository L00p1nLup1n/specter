import pytest
from specter.analyzer.semgrep import _normalize_severity


@pytest.mark.parametrize("input_sev,expected", [
    ("ERROR",   "CRITICAL"),
    ("WARNING",  "HIGH"),
    ("INFO",    "MEDIUM"),
    ("NOTE",    "LOW"),
    ("CRITICAL", "CRITICAL"),
    ("HIGH",    "HIGH"),
    ("UNKNOWN", "UNKNOWN"),
])
def test_normalize_severity(input_sev, expected):
    assert _normalize_severity(input_sev) == expected
