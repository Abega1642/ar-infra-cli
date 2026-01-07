"""Welcome message."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.ar_infra.cli.ui.color_properties import PRIMARY, SECONDARY


def show_welcome(console: Console) -> None:
    accent = "#b8b3e6"
    text_primary = "#e8e6f5"
    text_secondary = "#b8b5cc"

    max_width = 80
    left_pad = 2

    title = Text()
    title.append("Welcome to ", style=text_secondary)
    title.append("AR-INFRA CLI", style=f"bold {PRIMARY}")
    title.append("!", style=f"bold {SECONDARY}")

    console.print()
    console.print(title, width=max_width, overflow="fold")
    console.print()

    message = Text()
    message.append("Let's create your ", style=text_primary)
    message.append("Spring Boot project", style=f"bold {PRIMARY}")
    message.append(" together.\n", style=text_primary)
    message.append(
        "Answer a few questions, and we'll generate a ",
        style=text_secondary,
    )
    message.append("production-ready", style=f"bold {SECONDARY}")
    message.append(" codebase.", style=text_secondary)

    console.print(
        Panel(
            message,
            border_style=accent,
            padding=(1, left_pad),
            title="[bold]Quick Start[/bold]",
            title_align="left",
            width=max_width,
        )
    )
    console.print()

    credit = Text()
    credit.append("Crafted with ", style=f"dim {text_secondary}")
    credit.append("❤", style=PRIMARY)
    credit.append(" by ", style=f"dim {text_secondary}")
    credit.append("Abegà Razafindratelo", style=f"italic {SECONDARY}")

    contact = Text()
    contact.append(
        "<a.razafindratelo@gmail.com>",
        style="dim underline link=mailto:a.razafindratelo@gmail.com",
    )
    contact.append("  •  ", style=f"dim {text_secondary}")
    contact.append(
        "https://github.com/Abega1642",
        style="dim underline link=https://github.com/Abega1642",
    )

    footer = Text()
    footer.append(credit)
    footer.append("\n")
    footer.append(contact)

    console.print(footer, width=max_width)
    console.print()

    hint = Text()
    hint.append("Press ", style=f"dim {text_secondary}")
    hint.append("Ctrl+C", style=f"bold {PRIMARY}")
    hint.append(" at any time to cancel", style=f"dim {text_secondary}")

    console.print(hint, width=max_width)
    console.print()


def show_welcome_compact(console: Console) -> None:
    text = "#b8b5cc"

    message = Text()
    message.append("AR-INFRA CLI", style=f"bold {PRIMARY}")
    message.append(" • ", style=text)
    message.append("Spring Boot Project Generator", style=SECONDARY)
    message.append("\nby ", style=f"dim {text}")
    message.append("Abegà Razafindratelo", style=f"italic {SECONDARY}")

    console.print()
    console.print(message)
    console.print()
