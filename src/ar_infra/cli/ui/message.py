from pathlib import Path

from rich.panel import Panel
from rich.text import Text

from src.ar_infra.cli.ui.console import console


class Messages:
    @staticmethod
    def success(message: str) -> None:
        text = Text.assemble(
            ("✔ [SUCCESS] ", "bold green"),
            (message, "green"),
        )
        console.print(text)

    @staticmethod
    def error(message: str) -> None:
        text = Text.assemble(
            ("✘ [ERROR] ", "bold red"),
            (message, "red"),
        )
        console.print(text)

    @staticmethod
    def warning(message: str) -> None:
        text = Text.assemble(
            ("⚠ [WARNING] ", "bold yellow"),
            (message, "yellow"),
        )
        console.print(text)

    @staticmethod
    def info(message: str) -> None:
        text = Text.assemble(
            ("i [INFO] ", "bold cyan"),
            (message, "cyan"),
        )
        console.print(text)

    @staticmethod
    def project_summary(
        group: str,
        artifact: str,
        version: str,
        path: Path,
        features: list[str],
    ) -> None:
        summary = f"""
[bold]Project Configuration[/bold]

  [prompt]Group ID:[/prompt]     [bold]{group}[/bold]
  [prompt]Artifact ID:[/prompt]  [bold]{artifact}[/bold]
  [prompt]Version:[/prompt]      [bold]{version}[/bold]
  [prompt]Location:[/prompt]     [italic]{path}[/italic]
  [prompt]Features:[/prompt]     {", ".join(features) if features else "[dim]None selected[/dim]"}
"""
        panel = Panel(
            summary.strip(),
            border_style="bright_blue",
            title="[bold cyan]Summary[/bold cyan]",
            padding=(1, 2),
        )
        console.print(panel)
