import subprocess
import json
import tempfile
import os
from pathlib import Path
from dataclasses import dataclass

from specter.config import RULES_DIR, SEMGREP_TIMEOUT
from specter.parser.diff import Hunk


@dataclass
class SemgrepFinding:
    filename: str
    line: int
    severity: str
    rule_id: str
    message: str


def run_semgrep(hunks: list[Hunk]) -> list[SemgrepFinding]:
    if not hunks:
        return []

    file_map: dict[str, list[tuple[int, str]]] = {}
    for hunk in hunks:
        if hunk.filename not in file_map:
            file_map[hunk.filename] = []
        for i, line in enumerate(hunk.added_lines):
            file_map[hunk.filename].append((hunk.start_line + i, line))

    rules_path = str(RULES_DIR)
    if not os.path.isdir(rules_path) or not list(Path(rules_path).glob("*.yaml")):
        return []

    findings: list[SemgrepFinding] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        temp_files: dict[str, str] = {}

        for i, (filename, lines) in enumerate(file_map.items()):
            ext = Path(filename).suffix or ".py"
            tmp_path = os.path.join(tmpdir, f"scan_{i}{ext}")
            with open(tmp_path, "w") as f:
                f.write("\n".join(eachline for _, eachline in lines))
            temp_files[filename] = tmp_path

        for original_name, tmp_path in temp_files.items():
            result = subprocess.run(
                [
                    "semgrep",
                    "--config", rules_path,
                    "--disable-nosem",
                    "--json",
                    tmp_path,
                ],
                capture_output=True,
                text=True,
                timeout=SEMGREP_TIMEOUT,
                cwd=tmpdir,
            )

            if result.returncode not in (0, 1):
                continue

            try:
                data = json.loads(result.stdout)
            except json.JSONDecodeError:
                continue

            for r in data.get("results", []):
                idx = r.get("start", {}).get("line", 1) - 1
                line_num = (
                    file_map[original_name][idx][0]
                    if 0 <= idx < len(file_map[original_name])
                    else 0
                )
                severity = r.get("extra", {}).get("severity", "WARNING").upper()
                severity = _normalize_severity(severity)
                findings.append(
                    SemgrepFinding(
                        filename=original_name,
                        line=line_num,
                        severity=severity,
                        rule_id=r.get("check_id", "unknown"),
                        message=r.get("extra", {}).get("message", ""),
                    )
                )

    return findings


def _normalize_severity(s: str) -> str:
    mapping = {
        "ERROR": "CRITICAL",
        "WARNING": "HIGH",
        "INFO": "MEDIUM",
        "NOTE": "LOW",
    }
    return mapping.get(s, s)
