import json
from dataclasses import dataclass

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL, MAX_DIFF_TOKENS
from parser.diff import Hunk, sanitize_diff


@dataclass
class GeminiFinding:
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


def review_hunks(hunks: list[Hunk]) -> tuple[list[GeminiFinding], str]:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set. Add it to your .env file.")

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=1024,
    )

    all_findings: list[GeminiFinding] = []
    summaries: list[str] = []

    for hunk in hunks:
        if not hunk.added_lines:
            continue

        user_msg = USER_TEMPLATE.format(
            filename=hunk.filename,
            start_line=hunk.start_line,
            diff=sanitize_diff(hunk.raw, max_chars=MAX_DIFF_TOKENS),
        )

        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_msg,
            config=config,
        )
        raw = (response.text or "").strip()

        if raw.lower().startswith("```"):
            raw = raw.split("```")[1]
            if raw.lower().startswith("json"):
                raw = raw[4:]

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            summaries.append(f"{hunk.filename}: (parse error in Gemini response)")
            continue

        for f in data.get("findings", []):
            all_findings.append(
                GeminiFinding(
                    filename=hunk.filename,
                    line=hunk.start_line + max(0, int(f.get('line') or 1) - 1),
                    severity=str(f.get("severity", "LOW")).upper(),
                    issue=f.get("issue", ""),
                    reason=f.get("reason", ""),
                )
            )

        if summary := data.get("summary", ""):
            summaries.append(f"{hunk.filename}: {summary}")

    return all_findings, " | ".join(summaries)
