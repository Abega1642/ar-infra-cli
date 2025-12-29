"""User-facing messages with beautiful formatting."""

from pathlib import Path

from rich.panel import Panel

from .console import console


class Messages:
    """Handles displaying messages to users."""

    @staticmethod
    def success(message: str) -> None:
        """Display success message."""
        console.print(f"✓ {message}", style="success")

    @staticmethod
    def error(message: str) -> None:
        """Display error message."""
        console.print(f"✗ {message}", style="error")

    @staticmethod
    def warning(message: str) -> None:
        """Display warning message."""
        console.print(f"⚠ {message}", style="warning")

    @staticmethod
    def info(message: str) -> None:
        """Display info message."""
        console.print(f"[bold cyan]i[/] {message}", style="info")

    @staticmethod
    def welcome() -> None:
        """Display welcome message."""
        welcome_path = Path(__file__).parent.parent / "resources" / "welcome.txt"

        if welcome_path.exists():
            welcome_text = welcome_path.read_text(encoding="utf-8")
        else:
            welcome_text = "Welcome to AR-INFRA!\n\nLet's create your Spring Boot project."

        panel = Panel(
            welcome_text,
            border_style="green",
            title="[bold]Welcome[/bold]",
            padding=(1, 2),
        )
        console.print(panel)
        console.print()

    @staticmethod
    def project_summary(
        group: str,
        artifact: str,
        version: str,
        path: Path,
        features: list[str],
    ) -> None:
        """Display project configuration summary."""
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
