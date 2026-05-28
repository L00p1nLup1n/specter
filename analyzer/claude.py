import json
from dataclasses import dataclass

import anthropic
from anthropic.types import TextBlock

from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, MAX_DIFF_TOKENS
from parser.diff import Hunk, sanitize_diff


@dataclass
class ClaudeFinding:
    filename: str
    line: int
    severity: str
    issue: str
    reason: str


SYSTEM_PROMPT = (
    "You are a code security auditor specializing in LLM-generated code. "
    "You identify: hallucinated APIs, missing error handling, security antipatterns, "
    "edge case failures, outdated patterns, and logic that ignores codebase context."
)

USER_TEMPLATE = """Audit this code diff. Return JSON only:
{{ "findings": [{{ "line": <int, 1-indexed offset from start of this diff>, "severity": "LOW|MEDIUM|HIGH|CRITICAL", "issue": "<short title>", "reason": "<explanation>" }}], "summary": "<one sentence>" }}

File: {filename}
Diff (line 1 = file line {start_line}):
```
{diff}
```"""


def review_hunks(hunks: list[Hunk]) -> tuple[list[ClaudeFinding], str]:
    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set. Add it to your .env file.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    all_findings: list[ClaudeFinding] = []
    summaries: list[str] = []

    for hunk in hunks:
        if not hunk.added_lines:
            continue

        user_msg = USER_TEMPLATE.format(
            filename=hunk.filename,
            start_line=hunk.start_line,
            diff=sanitize_diff(hunk.raw, max_chars=MAX_DIFF_TOKENS),
        )

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )

        block = response.content[0]
        if not isinstance(block, TextBlock):
            summaries.append(f"{hunk.filename}: (unexpected response type)")
            continue
        raw = block.text.strip()
        # Strip markdown fences if present
        if raw.lower().startswith("```"):
            raw = raw.split("```")[1]
            if raw.lower().startswith("json"):
                raw = raw[4:]

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            summaries.append(f"{hunk.filename}: (parse error in Claude response)")
            continue

        for f in data.get("findings", []):
            all_findings.append(
                ClaudeFinding(
                    filename=hunk.filename,
                    line=hunk.start_line + max(0, int(f.get("line") or 1) - 1),
                    severity=str(f.get("severity", "LOW")).upper(),
                    issue=f.get("issue", ""),
                    reason=f.get("reason", ""),
                )
            )

        if summary := data.get("summary", ""):
            summaries.append(f"{hunk.filename}: {summary}")

    return all_findings, " | ".join(summaries)
