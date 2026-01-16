"""Rich-formatted help display."""

from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from src.ar_infra.cli.resources.documentation import (
    ADD_DEPENDENCY_PROJECT_PATH_HELP,
    ARTIFACT_OPTION_HELP,
    FEATURES_OPTION_HELP,
    GROUP_OPTION_HELP,
    NO_CACHE_OPTION_HELP,
    NO_FEATURES_OPTION_HELP,
    PATH_OPTION_HELP,
    PROJECT_DIR_OPTION_HELP,
    SKIP_COMMAND,
    VERSION_OPTION_HELP,
)
from src.ar_infra.properties import AR_INFRA_TEMPLATE


def show_add_deps_header(console: Console) -> None:
    console.print("    ar-infra add-dependency [OPTIONS] DEPENDENCIES...")
    console.print()

    console.print("[bold yellow]COMMANDS:[/bold yellow]")
    commands_table = Table(show_header=False, box=None, padding=(0, 2))
    commands_table.add_column(style="cyan bold", width=20)
    commands_table.add_column()

    commands_table.add_row("init", "Generate a new Spring Boot project")
    commands_table.add_row("add-dependency", "Add dependencies to build.gradle")

    console.print(commands_table)
    console.print()


def show_add_deps_body(console: Console) -> None:
    console.print("[bold yellow]ADD-DEPENDENCY COMMAND:[/bold yellow]")
    console.print("    Add Gradle dependencies to an existing project's build.gradle file.")
    console.print()

    console.print("[bold yellow]ADD-DEPENDENCY EXAMPLES:[/bold yellow]")
    console.print()

    console.print("    [green]# Add a single dependency[/green]")
    console.print(
        Syntax(
            "ar-infra add-dependency \"implementation 'io.jsonwebtoken:jjwt-api:0.13.0'\"",
            "bash",
            theme="monokai",
            background_color="default",
            padding=(0, 4),
        )
    )
    console.print()

    console.print("    [green]# Add multiple dependencies[/green]")
    add_multiple_command = """ar-infra add-dependency \\
        "implementation 'io.jsonwebtoken:jjwt-api:0.13.0'" \\
        "runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.13.0'" \\
        "runtimeOnly 'io.jsonwebtoken:jjwt-jackson:0.13.0'\""""
    console.print(
        Syntax(
            add_multiple_command,
            "bash",
            theme="monokai",
            background_color="default",
            padding=(0, 4),
        )
    )
    console.print()

    console.print("    [green]# Add dependency to specific project[/green]")
    add_with_path_command = """ar-infra add-dependency \\
        --project-path /path/to/project \\
        "implementation 'org.springframework.boot:spring-boot-starter-data-jpa'\""""
    console.print(
        Syntax(
            add_with_path_command,
            "bash",
            theme="monokai",
            background_color="default",
            padding=(0, 4),
        )
    )
    console.print()


def show_feature_list(console: Console) -> None:
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


def show_init_command_example(console: Console) -> None:
    console.print("[bold yellow]INIT EXAMPLES:[/bold yellow]")
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


def show_init_command_body(console: Console) -> None:
    console.print("[bold yellow]INIT COMMAND:[/bold yellow]")
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
            "ar-infra init --group=com.example --artifact=myapp --no-feature",
            "bash",
            theme="monokai",
            background_color="default",
        )
    )
    console.print()


def show_init_options(console: Console) -> None:
    console.print("[bold yellow]INIT OPTIONS:[/bold yellow]")
    options_table = Table(show_header=False, box=None, padding=(0, 2))
    options_table.add_column(style="cyan bold", width=20)
    options_table.add_column()

    options_table.add_row("--group", GROUP_OPTION_HELP.strip())
    options_table.add_row("--artifact", ARTIFACT_OPTION_HELP.strip())
    options_table.add_row("--project-version", VERSION_OPTION_HELP.strip())
    options_table.add_row("--path", PATH_OPTION_HELP.strip())
    options_table.add_row("--project-dir", PROJECT_DIR_OPTION_HELP.strip())
    options_table.add_row("--features", FEATURES_OPTION_HELP.strip())
    options_table.add_row("--disable-features", NO_FEATURES_OPTION_HELP.strip())
    options_table.add_row("--no-feature", "Generate project without any features")
    options_table.add_row("--no-cache", NO_CACHE_OPTION_HELP.strip())
    options_table.add_row("--skip-github-app", SKIP_COMMAND.strip())

    console.print(options_table)
    console.print()


def show_add_deps_options(console: Console) -> None:
    console.print("[bold yellow]ADD-DEPENDENCY OPTIONS:[/bold yellow]")
    options_table = Table(show_header=False, box=None, padding=(0, 2))
    options_table.add_column(style="cyan bold", width=20)
    options_table.add_column()

    options_table.add_row(
        "DEPENDENCIES...", "One or more Gradle dependency strings to add (required)."
    )

    options_table.add_row("--project-path", ADD_DEPENDENCY_PROJECT_PATH_HELP.strip())
    options_table.add_row("--help, -h", "Show this message and exit.")

    console.print(options_table)
    console.print()


def show_help() -> None:
    console = Console()

    title = Text()
    title.append("AR-INFRA", style="bold cyan")
    title.append(" - Spring Boot Project Generator")
    console.print(title)
    console.print()

    console.print("[bold yellow]USAGE:[/bold yellow]")
    console.print("    ar-infra init [OPTIONS]")

    show_add_deps_header(console)
    show_add_deps_options(console)
    show_init_command_body(console)
    show_init_options(console)
    show_init_command_example(console)
    show_add_deps_body(console)
    show_feature_list(console)

    console.print(
        f"For more information, visit: [blue underline]{AR_INFRA_TEMPLATE}[/blue underline]"
    )
    console.print()
