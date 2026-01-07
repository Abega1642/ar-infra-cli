"""User-facing messages with beautiful formatting."""

from pathlib import Path

from rich.panel import Panel

from .console import console


class Messages:
    @staticmethod
    def success(message: str) -> None:
        console.print(f"✓ {message}", style="success")

    @staticmethod
    def error(message: str) -> None:
        console.print(f"✗ {message}", style="error")

    @staticmethod
    def warning(message: str) -> None:
        console.print(f"⚠ {message}", style="warning")

    @staticmethod
    def info(message: str) -> None:
        console.print(f"[bold cyan]i[/] {message}", style="info")

    @staticmethod
    def project_summary(
        group: str,
        artifact: str,
        version: str,
        path: Path,
        features: list[str],
    ) -> None:
        summary = f"""
[bold]Project Configuration:[/bold]

  [prompt]Group ID:[/prompt]        {group}
  [prompt]Artifact ID:[/prompt]     {artifact}
  [prompt]Version:[/prompt]         {version}
  [prompt]Location:[/prompt]        {path}
  [prompt]Features:[/prompt]        {", ".join(features) if features else "None selected"}
"""
        panel = Panel(
            summary.strip(),
            border_style="blue",
            title="[bold]Summary[/bold]",
            padding=(1, 2),
        )
        console.print(panel)
