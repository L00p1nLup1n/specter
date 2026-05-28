#!/usr/bin/env python3
from pathlib import Path
from typing import List, Optional

import anthropic
import typer
from google.genai import errors as genai_errors
from rich.console import Console

from analyzer.claude import review_hunks as claude_review
from analyzer.gemini import review_hunks as gemini_review
from analyzer.scorer import combine_findings
from analyzer.semgrep import run_semgrep
from output.formatter import print_json, print_terminal
from parser.diff import (
    get_file_content,
    get_staged_diff,
    parse_diff,
    parse_file_as_hunk,
)
from utils.available_vendors import available_vendors
from utils.format_json import print_api_error

app = typer.Typer(
    name="aiaudit",
    help="AI-powered code auditor for LLM-generated code.",
    add_completion=False,
)
console = Console(stderr=True)


@app.command()
def scan(
    file: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Path to a specific file to audit."
    ),
    format: str = typer.Option(
        "terminal", "--format", help="Output format: terminal | json"
    ),
    skip_semgrep: bool = typer.Option(
        False, "--skip-semgrep", help="Skip semgrep static analysis."
    ),
    vendor: List[str] = typer.Option(
        available_vendors,
        "--vendor",
        help="AI vendor(s) to use for review:. Pass once per vendor.",
    ),
) -> None:
    """Audit staged git diff or a specific file for security issues."""

    # 1. Gather hunks
    if file:
        try:
            content = get_file_content(str(file))
        except (ValueError, OSError) as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

        if content is None:
            console.print(f"[red]Error:[/red] File not found: {file}")
            raise typer.Exit(1)
        hunks = parse_file_as_hunk(str(file), content)
        if format == "terminal":
            console.print(f"[dim]Scanning file:[/dim] {file}")
    else:
        diff_text = get_staged_diff()
        if not diff_text:
            console.print(
                "[yellow]No diff found.[/yellow] Stage some changes with "
                "[bold]git add[/bold] or pass [bold]--file[/bold]."
            )
            raise typer.Exit(0)
        hunks = parse_diff(diff_text)
        if not hunks:
            console.print("[green]No added lines to audit.[/green]")
            raise typer.Exit(0)
        if format == "terminal":
            console.print(
                f"[dim]Scanning {len(hunks)} hunk(s) across {len({h.filename for h in hunks})} file(s)...[/dim]"
            )

    # 2. Static analysis
    semgrep_findings = []
    if not skip_semgrep:
        try:
            if format == "terminal":
                console.print("[dim]Running semgrep...[/dim]")
            semgrep_findings = run_semgrep(hunks)
        except FileNotFoundError:
            console.print(
                "[yellow]semgrep not found - skipping static analysis.[/yellow]"
            )
        except Exception as e:
            console.print(
                f"[yellow]semgrep error: {e} - skipping static analysis [/yellow]"
            )

    # 3. AI reviews — run whichever vendors were requested
    vendors = {v.lower() for v in vendor}
    if not all(v in available_vendors for v in vendors):
        console.print("[red]Requested vendor is not available[/red]")
        raise typer.Exit(1)

    claude_findings = []
    claude_summary = ""
    claude_ok = False
    if "claude" in vendors:
        try:
            if format == "terminal":
                console.print("[dim]Sending to Claude for review...[/dim]")
            claude_findings, claude_summary = claude_review(hunks)
            claude_ok = True
        except RuntimeError as e:
            console.print(f"[yellow]Claude skipped:[/yellow] {e}")
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError) as e:
            print_api_error(e, vendor="Claude")
            raise typer.Exit(1)
        except Exception as e:
            print_api_error(e, vendor="Claude")

    gemini_findings = []
    gemini_summary = ""
    gemini_ok = False
    if "gemini" in vendors:
        try:
            if format == "terminal":
                console.print("[dim]Sending to Gemini for review...[/dim]")
            gemini_findings, gemini_summary = gemini_review(hunks)
            gemini_ok = True
        except RuntimeError as e:
            console.print(f"[yellow]Gemini skipped:[/yellow] {e}")
        except genai_errors.ClientError as e:
            print_api_error(e, vendor="Gemini")
            if e.status in ("UNAUTHENTICATED", "PERMISSION_DENIED"):
                raise typer.Exit(1)
        except Exception as e:
            print_api_error(e, vendor="Gemini")

    # Warn if every requested AI vendor failed — result would be a false negative
    ai_requested = vendors & {"claude", "gemini"}
    ai_succeeded = {
        v
        for v, ok in [("claude", claude_ok), ("gemini", gemini_ok)]
        if ok and v in vendors
    }
    if ai_requested and not ai_succeeded:
        console.print("[red]All AI backends failed. Results may be incomplete.[/red]")
        raise typer.Exit(1)

    # 5. Score and output
    result = combine_findings(
        semgrep_findings,
        claude_findings,
        claude_summary,
        gemini_findings,
        gemini_summary,
    )

    if format == "json":
        print_json(result)
    else:
        print_terminal(result)

    # Exit with non-zero code if HIGH or CRITICAL for CI integration
    if result.risk_level in ("HIGH", "CRITICAL"):
        raise typer.Exit(2)


if __name__ == "__main__":
    app()
