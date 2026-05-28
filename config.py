import os
import tomllib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

_ROOT = Path(__file__).parent
try:
    with open(_ROOT / "specter.toml", "rb") as _f:
        _cfg = tomllib.load(_f)
except FileNotFoundError as e:
    raise FileNotFoundError(f"specter.toml not found; expected at {_ROOT / 'specter.toml'}") from e


# Secrets — always from environment
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


# Operational settings — from specter.toml
TIMEOUT = _cfg["global"]["timeout"]
CLAUDE_MODEL = _cfg["claude"]["model"]
CLAUDE_MAX_OUTPUT_TOKENS = _cfg["claude"]["max_output_tokens"]
GEMINI_MODEL = _cfg["gemini"]["model"]
GEMINI_MAX_OUTPUT_TOKENS = _cfg["gemini"]["max_output_tokens"]

SEMGREP_TIMEOUT = _cfg["semgrep"]["timeout"]
RULES_DIR = _ROOT / _cfg["semgrep"]["rules_dir"]

MAX_DIFF_CHARS = _cfg["scoring"]["max_diff_chars"]
SEVERITY_ORDER = _cfg["scoring"]["severity_order"]
