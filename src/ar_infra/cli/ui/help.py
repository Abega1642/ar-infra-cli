"""Rich-formatted help display."""

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


AR_INFRA_TEMPLATE = "https://github.com/Abega1642/ar-infra-template"


def show_help() -> None:
    console = Console()

    title = Text()
    title.append("AR-INFRA", style="bold cyan")
    title.append(" - Spring Boot Project Generator")
    console.print(title)
    console.print()

    console.print("[bold yellow]USAGE:[/bold yellow]")
    console.print("    ar-infra init [OPTIONS]")
    console.print()

    console.print("[bold yellow]DESCRIPTION:[/bold yellow]")
    console.print("    Generate a production-ready Spring Boot project with customizable features.")
    console.print("    You can use interactive mode or provide all options via command line.")
    console.print()

    console.print("[bold yellow]INTERACTIVE MODE:[/bold yellow]")
    console.print(Syntax("ar-infra init", "bash", theme="monokai", background_color="default"))
    console.print("    Guides you through project setup with beautiful prompts.")
    console.print()

    console.print("[bold yellow]COMMAND LINE MODE:[/bold yellow]")
    console.print(
        Syntax(
            "ar-infra init --group=com.example --artifact=myapp --project-version=1.0.0",
            "bash",
            theme="monokai",
            background_color="default",
        )
    )
    console.print()

    console.print("[bold yellow]EXAMPLES:[/bold yellow]")
    console.print()

    console.print("    [green]# Interactive mode (recommended for first-time users)[/green]")
    console.print(
        Syntax("ar-infra init", "bash", theme="monokai", background_color="default", padding=(0, 4))
    )
    console.print()

    console.print("    [green]# Quick start with defaults[/green]")
    console.print(
        Syntax(
            "ar-infra init --group=com.mycompany --artifact=backend-api",
            "bash",
            theme="monokai",
            background_color="default",
            padding=(0, 4),
        )
    )
    console.print()

    console.print("    [green]# Full customization[/green]")
    full_command = """ar-infra init \\
    --group=dev.razafindratelo \\
    --artifact=cool-project \\
    --project-version=2.0.0 \\
    --path=/home/user/projects \\
    --project-dir=cool-project \\
    --features=postgresql,s3_bucket"""
    console.print(
        Syntax(full_command, "bash", theme="monokai", background_color="default", padding=(0, 4))
    )
    console.print()

    console.print("    [green]# Exclude specific features[/green]")
    exclude_command = """ar-infra init \\
    --group=com.example \\
    --artifact=minimal-api \\
    --disable-features=rabbitmq,email"""
    console.print(
        Syntax(exclude_command, "bash", theme="monokai", background_color="default", padding=(0, 4))
    )
    console.print()

    console.print("[bold yellow]FEATURES:[/bold yellow]")
    features_table = Table(show_header=False, box=None, padding=(0, 2))
    features_table.add_column(style="cyan bold", width=15)
    features_table.add_column()

    features_table.add_row("postgresql", "PostgreSQL database support")
    features_table.add_row("rabbitmq", "RabbitMQ message broker")
    features_table.add_row("s3_bucket", "AWS S3-compatible (BackBlaze) integration")
    features_table.add_row("email", "Email sending capabilities")

    console.print(features_table)
    console.print()

    console.print(
        f"For more information, visit: [blue underline]{AR_INFRA_TEMPLATE}[/blue underline]"
    )
    console.print()
