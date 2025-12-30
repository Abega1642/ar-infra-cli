"""Banner display utilities."""

from pathlib import Path

from rich.panel import Panel
from rich.text import Text

from src.ar_infra.cli.ui.console import console


DEFAULT_BANNER = """
╔══════════════════════════════════════════════╗
║              AR-INFRA CLI                    ║
║     Spring Boot Application Generator        ║
╚══════════════════════════════════════════════╝
"""


class Banner:
    """Handles banner display with oh-my-logo integration."""

    @staticmethod
    def _load_banner() -> str:
        """Load the generated banner from text file.

        Returns:
            str: Banner text with ANSI color codes, or default banner if not found.
        """
        banner_path = Path(__file__).parent.parent / "resources" / "banner.txt"

        if banner_path.exists():
            try:
                banner = banner_path.read_text(encoding="utf-8")
                if banner and "\x1b[" in banner:
                    return banner
                console.print(
                    "[yellow]Warning: Generated banner exists but has no color codes[/yellow]"
                )
                return banner if banner else DEFAULT_BANNER.strip()
            except (OSError, UnicodeDecodeError) as e:
                console.print(f"[yellow]Warning: Could not load banner: {e}[/yellow]")
                return DEFAULT_BANNER.strip()

        else:
            console.print(
                "[dim]Note: Using default banner "
                "(run 'make setup-banner' to generate colored version)[/dim]"
            )

            return DEFAULT_BANNER.strip()

    @classmethod
    def show(cls) -> None:
        """Display the AR-INFRA banner with welcome message."""
        logo = cls._load_banner()

        primary = "#B9BDC6"
        secondary = "#8A8F99"
        border = "#5E646E"

        console.print(
            Panel.fit(
                Text(
                    " Welcome to AR-INFRA Generator ",
                    style=f"bold {primary}",
                ),
                border_style=border,
                padding=(0, 1),
            )
        )
        console.print()

        console.print(Text.from_ansi(logo))

        console.print()

        console.print(
            Text(
                "Production-ready Spring Boot infrastructure.\n"
                "Designed for clean architecture and enterprise systems.",
                style=secondary,
            )
        )
        console.print()

        console.print(
            Text(
                "Press Enter to continue…",
                style="#6F7480",
            )
        )
