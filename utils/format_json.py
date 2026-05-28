from __future__ import annotations

import anthropic
from google.genai import errors as genai_errors
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console(stderr=True)

_ANTHROPIC_STATUS_LABELS = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    422: "Unprocessable Entity",
    429: "Rate Limited",
    500: "Internal Server Error",
    503: "Service Unavailable",
}

_ANTHROPIC_HINTS = {
    401: "Check that ANTHROPIC_API_KEY is set correctly.",
    429: "You have exceeded your rate limit. Wait before retrying.",
    500: "Anthropic server error. Try again shortly.",
    503: "Anthropic is overloaded. Try again shortly.",
}

_GOOGLE_STATUS_LABELS = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    429: "Rate Limited",
    500: "Internal Server Error",
    503: "Service Unavailable",
}

# Keyed by gRPC status string (exc.status)
_GOOGLE_HINTS = {
    "UNAUTHENTICATED": "Check that GEMINI_API_KEY is set correctly.",
    "PERMISSION_DENIED": "The API key does not have access to this resource.",
    "RESOURCE_EXHAUSTED": "Gemini quota exceeded. Wait before retrying.",
    "INVALID_ARGUMENT": "The request contained an invalid argument.",
    "INTERNAL": "Google server error. Try again shortly.",
    "UNAVAILABLE": "Gemini is temporarily unavailable.",
}


def _anthropic_table(exc: anthropic.APIError) -> Table:
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column(style="dim", no_wrap=True)
    table.add_column()

    if isinstance(exc, anthropic.APIStatusError):
        label = _ANTHROPIC_STATUS_LABELS.get(exc.status_code, "HTTP Error")
        table.add_row("Status", f"[bold]{exc.status_code}[/bold] {label}")
        body = exc.body or {}
        if isinstance(body, dict) and "error" in body:
            err = body["error"]
            table.add_row("Type", str(err.get("type", "")))
            table.add_row("Message", str(err.get("message", exc.message)))
        else:
            table.add_row("Message", exc.message)
        hint = _ANTHROPIC_HINTS.get(exc.status_code)
    elif isinstance(exc, anthropic.APIConnectionError):
        table.add_row("Type", "Connection Error")
        table.add_row("Message", str(exc))
        hint = "Check your network connection."
    elif isinstance(exc, anthropic.APITimeoutError):
        table.add_row("Type", "Timeout")
        table.add_row("Message", "Request timed out.")
        hint = "The request took too long. Try again or reduce the diff size."
    else:
        table.add_row("Message", str(exc))
        hint = None

    if hint:
        table.add_row("Hint", f"[dim]{hint}[/dim]")

    return table


def _google_table(exc: genai_errors.APIError) -> Table:
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    table.add_column(style="dim", no_wrap=True)
    table.add_column()

    label = _GOOGLE_STATUS_LABELS.get(exc.code, "API Error")
    table.add_row("Status", f"[bold]{exc.code}[/bold] {label}")
    if exc.status:
        table.add_row("Type", exc.status)
    if exc.message:
        table.add_row("Message", exc.message)

    fallback = f"Unexpected Gemini error (status: {exc.status or 'unknown'}). Check the Gemini API status page."
    hint = _GOOGLE_HINTS.get(exc.status or "", fallback)
    table.add_row("Hint", f"[dim]{hint}[/dim]")


    return table


def print_api_error(exc: Exception, vendor: str = "") -> None:
    if isinstance(exc, anthropic.APIError):
        vendor = vendor or "Claude"
        table = _anthropic_table(exc)
    elif isinstance(exc, genai_errors.APIError):
        vendor = vendor or "Gemini"
        table = _google_table(exc)
    else:
        vendor = vendor or "API"
        table = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        table.add_column(style="dim")
        table.add_column()
        table.add_row("Error", str(exc))

    console.print(Panel(table, title=f"[red]{vendor} Error[/red]", border_style="red"))
