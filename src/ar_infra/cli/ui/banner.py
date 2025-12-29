"""Banner display utilities."""

from pathlib import Path

from rich.panel import Panel
from rich.text import Text

from .console import console


class Banner:
    """Handles banner display."""

    @staticmethod
    def show() -> None:
        """Display the AR-INFRA banner."""
        banner_path = Path(__file__).parent.parent / "resources" / "banner.txt"

        if banner_path.exists():
            banner_text = banner_path.read_text(encoding="utf-8")
        else:
            banner_text = "AR-INFRA\nSpring Boot Project Generator 🚀"

        text = Text(banner_text, style="bold cyan", justify="center")
        panel = Panel(
            text,
            border_style="blue",
            padding=(1, 2),
        )
        console.print(panel)
        console.print()
