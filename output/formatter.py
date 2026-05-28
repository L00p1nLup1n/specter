import json

from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

from analyzer.scorer import AuditResult

console = Console()

SEVERITY_COLORS = {
    "CRITICAL": "bold red",
    "HIGH": "red",
    "MEDIUM": "yellow",
    "LOW": "cyan",
    "INFO": "dim",
}

RISK_COLORS = {
    "CRITICAL": "bold red",
    "HIGH": "red",
    "MEDIUM": "yellow",
    "LOW": "green",
}


def print_terminal(result: AuditResult) -> None:
    risk_color = RISK_COLORS.get(result.risk_level, "white")

    console.print()
    console.rule(style="dim")
    console.print(
        f" RISK: [{risk_color}]{result.risk_level}[/{risk_color}]  "
        f"(score: {result.risk_score}/100)",
        justify="left",
    )
    console.rule(style="dim")

    if result.findings:
        table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold",
            padding=(0, 1),
            show_lines=True
        )
        table.add_column("Location", style="dim", no_wrap=True)
        table.add_column("Severity", no_wrap=True)
        table.add_column("Source", style="dim", no_wrap=True)
        table.add_column("Issue")
        table.add_column("Detail", overflow="fold")

        for f in result.findings:
            sev_color = SEVERITY_COLORS.get(f.severity, "white")
            table.add_row(
                f"{f.filename}:{f.line}",
                Text(f.severity, style=sev_color),
                f.source,
                f.issue,
                f.reason,
            )

        console.print(table)
    else:
        console.print(" [green]No issues found.[/green]")

    console.rule(style="dim")
    counts = result.counts
    parts = []
    for label, color in RISK_COLORS.items():
        n = counts.get(label, 0)
        parts.append(f"[{color}]{n} {label.lower()}[/{color}]")
    console.print(" " + " · ".join(parts))
    console.rule(style="dim")

    if result.summary:
        console.print(f"\n[bold]Summary:[/bold] {result.summary}\n")


def print_json(result: AuditResult) -> None:
    output = {
        "risk_level": result.risk_level,
        "risk_score": result.risk_score,
        "summary": result.summary,
        "counts": result.counts,
        "findings": [
            {
                "filename": f.filename,
                "line": f.line,
                "severity": f.severity,
                "source": f.source,
                "issue": f.issue,
                "reason": f.reason,
            }
            for f in result.findings
        ],
    }
    print(json.dumps(output, indent=2))
