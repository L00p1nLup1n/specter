import os
from pathlib import Path

import tomllib
from dotenv import load_dotenv

load_dotenv()

_ROOT = Path(__file__).parent


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


try:
    with open(_ROOT / "specter.toml", "rb") as _f:
        _cfg = tomllib.load(_f)
except FileNotFoundError as e:
    raise FileNotFoundError(
        f"specter.toml not found; expected at {_ROOT / 'specter.toml'}"
    ) from e

_local = _ROOT / "specter.local.toml"
if _local.exists():
    with open(_local, "rb") as _f:
        _cfg = _deep_merge(_cfg, tomllib.load(_f))

# Secrets — env var takes priority, then specter.local.toml [claude/gemini] api_key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or _cfg.get("claude", {}).get(
    "api_key", ""
)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or _cfg.get("gemini", {}).get(
    "api_key", ""
)

# Operational settings — from specter.toml (overridable via specter.local.toml)
TIMEOUT = _cfg["global"]["timeout"]
CLAUDE_MODEL = _cfg["claude"]["model"]
CLAUDE_MAX_OUTPUT_TOKENS = _cfg["claude"]["max_output_tokens"]
GEMINI_MODEL = _cfg["gemini"]["model"]
GEMINI_MAX_OUTPUT_TOKENS = _cfg["gemini"]["max_output_tokens"]

SEMGREP_TIMEOUT = _cfg["semgrep"]["timeout"]
RULES_DIR = _ROOT / _cfg["semgrep"]["rules_dir"]

MAX_DIFF_CHARS = _cfg["scoring"]["max_diff_chars"]
SEVERITY_ORDER = _cfg["scoring"]["severity_order"]
