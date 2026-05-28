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
CLAUDE_MODEL = _cfg["claude"]["model"]
GEMINI_MODEL = _cfg["gemini"]["model"]

SEMGREP_TIMEOUT = _cfg["semgrep"]["timeout"]
RULES_DIR = _ROOT / _cfg["semgrep"]["rules_dir"]

MAX_DIFF_TOKENS = _cfg["scoring"]["max_tokens"]
SEVERITY_ORDER = _cfg["scoring"]["severity_order"]
