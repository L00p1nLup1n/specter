"""Smoke-tests that specter.toml is valid and all required keys are present."""
import specter.config as config


def test_claude_config():
    assert isinstance(config.CLAUDE_MODEL, str) and config.CLAUDE_MODEL
    assert isinstance(config.CLAUDE_MAX_OUTPUT_TOKENS, int) and config.CLAUDE_MAX_OUTPUT_TOKENS > 0


def test_gemini_config():
    assert isinstance(config.GEMINI_MODEL, str) and config.GEMINI_MODEL
    assert isinstance(config.GEMINI_MAX_OUTPUT_TOKENS, int) and config.GEMINI_MAX_OUTPUT_TOKENS > 0


def test_semgrep_config():
    assert isinstance(config.SEMGREP_TIMEOUT, int) and config.SEMGREP_TIMEOUT > 0
    assert config.RULES_DIR is not None


def test_scoring_config():
    assert isinstance(config.MAX_DIFF_CHARS, int) and config.MAX_DIFF_CHARS > 0
    assert isinstance(config.SEVERITY_ORDER, dict)
    assert set(config.SEVERITY_ORDER.keys()) == {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}


def test_global_config():
    assert isinstance(config.TIMEOUT, int) and config.TIMEOUT > 0
