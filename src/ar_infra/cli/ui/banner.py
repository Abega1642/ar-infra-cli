"""Banner display utilities."""

import sys
from pathlib import Path

from rich.panel import Panel
from rich.text import Text

from src.ar_infra.cli.ui.color_properties import PRIMARY, SECONDARY
from src.ar_infra.cli.ui.console import console
from src.ar_infra.cli.ui.welcome import show_welcome


DEFAULT_BANNER = """
╔══════════════════════════════════════════════╗
║              AR-INFRA CLI                    ║
║     Spring Boot Application Generator        ║
╚══════════════════════════════════════════════╝
"""


class Banner:
    """Handles banner display with oh-my-logo integration."""

    @staticmethod
    def _get_resource_path() -> Path:
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]  # pylint: disable=protected-access
            return base_path / "ar_infra" / "cli" / "resources"
        return Path(__file__).parent.parent / "resources"

    @staticmethod
    def _load_banner() -> str:
        banner_path = Banner._get_resource_path() / "banner.txt"

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
    def show(cls, *, wait_for_enter: bool = True, show_welcome_message: bool = True) -> None:
        logo = cls._load_banner()
        border = "#b8b3e6"

        console.print(
            Panel.fit(
                Text(
                    " AR-INFRA CLI - Spring boot app generator ",
                    style=f"bold {PRIMARY}",
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
                style=SECONDARY,
            )
        )
        console.print()

        if show_welcome_message:
            show_welcome(console)

        if wait_for_enter:
            hint = Text("Press Enter to continue…", style="#9d97d9")
            console.print(hint)

            try:
                input()
            except (KeyboardInterrupt, EOFError) as exc:
                console.print("\n[yellow]Operation cancelled.[/yellow]")
                raise KeyboardInterrupt("Banner display cancelled by user") from exc

            console.print()
