import os
from importlib.resources import files as _pkg_files
from pathlib import Path

import tomllib
from dotenv import load_dotenv

load_dotenv()

_pkg_data = _pkg_files("specter.data")


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], val)
        else:
            result[key] = val
    return result


with (_pkg_data / "specter.toml").open("rb") as _f:
    _cfg = tomllib.load(_f)

# User-global config at ~/.config/specter/specter.toml
_global = Path.home() / ".config" / "specter" / "specter.toml"
if _global.exists():
    with open(_global, "rb") as _f:
        _cfg = _deep_merge(_cfg, tomllib.load(_f))

# Per-project override via specter.local.toml in the working directory
_local = Path.cwd() / "specter.local.toml"
if _local.exists():
    with open(_local, "rb") as _f:
        _cfg = _deep_merge(_cfg, tomllib.load(_f))

# Secrets — env var takes priority, then specter.local.toml [claude/gemini] api_key
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY") or _cfg.get("claude", {}).get("api_key", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or _cfg.get("gemini", {}).get("api_key", "")

# Operational settings — from specter.toml (overridable via specter.local.toml)
TIMEOUT = _cfg["global"]["timeout"]
CLAUDE_MODEL = _cfg["claude"]["model"]
CLAUDE_MAX_OUTPUT_TOKENS = _cfg["claude"]["max_output_tokens"]
GEMINI_MODEL = _cfg["gemini"]["model"]
GEMINI_MAX_OUTPUT_TOKENS = _cfg["gemini"]["max_output_tokens"]

SEMGREP_TIMEOUT = _cfg["semgrep"]["timeout"]
RULES_DIR = Path(str(_pkg_data)) / _cfg["semgrep"]["rules_dir"]

MAX_DIFF_CHARS = _cfg["scoring"]["max_diff_chars"]
SEVERITY_ORDER = _cfg["scoring"]["severity_order"]
