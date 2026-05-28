# Specter

AI-powered security auditor for LLM-generated code. Combines static analysis (semgrep) with Claude and Gemini (more pending) review to surface hallucinated APIs, security antipatterns, missing error handling, and logic errors in your git diff.

## How it works

```
git diff → semgrep → Claude / Gemini → scored findings → terminal or JSON
```

Each added line in your staged diff is analyzed by up to three sources. Findings are deduplicated per source, scored by severity, and mapped to a risk level (LOW → CRITICAL) with a CI exit code.

| Risk level | Score | CI exit code |
|---|---|---|
| LOW / MEDIUM | 0–14 | 0 |
| HIGH / CRITICAL | ≥15 / ≥25 | 2 |

## Quickstart

### Local (Python)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Add API keys
cp specter.local.toml.example specter.local.toml
# edit specter.local.toml with your keys

# Stage some changes, then:
python cli.py
```

### Local (Docker)

```bash
docker build -t specter .

docker run --rm \
  -v $(pwd):/repo \
  -w /repo \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -e GEMINI_API_KEY=$GEMINI_API_KEY \
  specter
```

## API keys

Keys are resolved in this order (highest priority first):

1. Environment variables: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`
2. `specter.local.toml` (gitignored) — see `specter.local.toml.example`
3. Error if neither is set

For CI, inject keys as environment secrets. For local use, copy `specter.local.toml.example` to `specter.local.toml` and fill in your keys.

## Usage

```bash
# Scan staged diff (default)
python cli.py

# Scan a specific file
python cli.py --file src/auth.py

# Use only one vendor
python cli.py --vendor claude
python cli.py --vendor gemini

# Skip semgrep static analysis
python cli.py --skip-semgrep

# JSON output (for CI)
python cli.py --format json
```

## Configuration

All operational settings live in `specter.toml`. Override any value locally via `specter.local.toml` (gitignored):

```toml
# specter.local.toml
[claude]
api_key = "sk-ant-..."
model = "claude-opus-4-5"      # optional override

[gemini]
api_key = "AIza..."
max_output_tokens = 8192       # optional override
```

| Key | Default | Description |
|---|---|---|
| `global.timeout` | `60000` | API timeout in ms |
| `claude.model` | `claude-sonnet-4-20250514` | Anthropic model |
| `claude.max_output_tokens` | `1024` | Max tokens in Claude response |
| `gemini.model` | `gemini-2.0-flash` | Gemini model |
| `gemini.max_output_tokens` | `4096` | Max tokens in Gemini response |
| `semgrep.timeout` | `30` | Semgrep subprocess timeout (s) |
| `semgrep.rules_dir` | `rules/llm_patterns` | Path to semgrep rules |
| `scoring.max_diff_chars` | `8000` | Max diff characters sent per hunk |

## Semgrep rules

Custom rules live in `rules/llm_patterns/` and target patterns common in LLM-generated code:

- `sql_injection.yaml` — string-interpolated queries
- `hardcoded_secrets.yaml` — inline passwords and API keys
- `error_handling.yaml` — bare `except` clauses
- `input_validation.yaml` — unvalidated input passed to `exec`/`eval`
- `deprecated_crypto.yaml` — MD5/SHA1 usage

## Development

```bash
pytest tests/        # run test suite
```
