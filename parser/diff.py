from dataclasses import dataclass, field
from typing import Optional
import subprocess
import re

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
_CONTROL_RE = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')


def sanitize_diff(text: str, max_chars: int = 8000) -> str:
    text = _ANSI_RE.sub('', text)
    text = _CONTROL_RE.sub('', text)
    return text[:max_chars]


@dataclass
class Hunk:
    filename: str
    start_line: int
    added_lines: list[str] = field(default_factory=list)
    raw: str = ""


def get_staged_diff() -> Optional[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--unified=5"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        result = subprocess.run(
            ["git", "diff", "HEAD", "--unified=5"],
            capture_output=True,
            text=True,
        )
    return result.stdout if result.stdout.strip() else None


def get_file_content(path: str) -> Optional[str]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except FileNotFoundError:
        return None


def parse_diff(diff_text: str) -> list[Hunk]:
    hunks: list[Hunk] = []
    current_file = ""
    current_hunk: Optional[Hunk] = None

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("@@ "):
            match = re.search(r"\+(\d+)", line)
            start = int(match.group(1)) if match else 0
            if current_hunk:
                hunks.append(current_hunk)
            current_hunk = Hunk(filename=current_file, start_line=start)
        elif current_hunk is not None:
            current_hunk.raw += line + "\n"
            if line.startswith("+") and not line.startswith("+++"):
                current_hunk.added_lines.append(line[1:])

    if current_hunk:
        hunks.append(current_hunk)

    return [h for h in hunks if h.added_lines]


def parse_file_as_hunk(path: str, content: str) -> list[Hunk]:
    lines = content.splitlines()
    return [
        Hunk(
            filename=path,
            start_line=1,
            added_lines=lines,
            raw="\n".join(f"+{eachline}" for eachline in lines),
        )
    ]
