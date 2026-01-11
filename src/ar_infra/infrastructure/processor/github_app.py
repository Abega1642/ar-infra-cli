"""GitHub App installation handler."""

import webbrowser
from dataclasses import dataclass
from typing import cast

from questionary import select
from rich.panel import Panel

from src.ar_infra.cli.ui.color_properties import PROMPT_STYLE
from src.ar_infra.cli.ui.console import console
from src.ar_infra.logger import get_logger


log = get_logger()


@dataclass(frozen=True)
class GitHubAppConfig:
    app_name: str
    app_url: str
    installation_url: str


class GitHubAppHandler:
    DEFAULT_APP_CONFIG = GitHubAppConfig(
        app_name="ar-infra-bot",
        app_url="https://github.com/apps/ar-infra-bot",
        installation_url="https://github.com/apps/ar-infra-bot/installations/new",
    )

    def __init__(self, app_config: GitHubAppConfig | None = None):
        self.app_config = app_config or self.DEFAULT_APP_CONFIG

    def prompt_installation(self) -> bool:
        self._show_installation_info()

        choice = self._prompt_user_choice()

        if choice == "install":
            return self._handle_install_flow()
        if choice == "skip":
            self._show_skip_warning()
            return False
        console.print(f"\nGreat! {self.app_config.app_name} is ready to use.", style="success")
        log.info("User indicated %s is already installed", self.app_config.app_name)
        return True

    def _show_installation_info(self) -> None:
        info_content = f"""
[bold cyan]GitHub App:[/bold cyan] {self.app_config.app_name}

[bold]Features enabled by this app:[/bold]
  • Code scanning (CodeQL) on the initial commit
  • Security analysis (Semgrep) on the initial commit
  • Automated code quality checks

[bold yellow]Note:[/bold yellow] Without this app, security scanning features will not work.

[dim]App URL:[/dim] {self.app_config.app_url}
"""
        panel = Panel(
            info_content.strip(),
            border_style="cyan",
            title="[bold]GitHub App Installation[/bold]",
            padding=(1, 2),
        )
        console.print("\n")
        console.print(panel)

    def _prompt_user_choice(self) -> str:
        result = select(
            "\nWhat would you like to do?",
            choices=[
                {"name": "Install the app now (opens in browser)", "value": "install"},
                {"name": "Skip - I'll install it later", "value": "skip"},
                {"name": "Already installed - Continue", "value": "already_installed"},
            ],
            style=PROMPT_STYLE,
        ).ask()

        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user")

        return cast("str", result)

    def _handle_install_flow(self) -> bool:
        self._open_installation_page()
        return self._confirm_installation_completed()

    def _open_installation_page(self) -> None:
        console.print(
            f"\nOpening [bold cyan]{self.app_config.app_name}[/bold cyan] "
            "installation page in your browser...",
            style="info",
        )

        try:
            webbrowser.open(self.app_config.installation_url)
            log.info("Opened GitHub App installation page: %s", self.app_config.installation_url)
        except OSError as e:
            log.warning("Could not open browser automatically: %s", e)
            console.print("\nCould not open browser automatically.", style="warning")
            message_prefix = "Please visit this URL manually"
            console.print(
                f"\n{message_prefix}:\n[bold cyan]{self.app_config.installation_url}[/bold cyan]"
            )

        self._show_installation_steps()

    def _show_installation_steps(self) -> None:
        steps = """
[bold]Installation Steps:[/bold]

  [cyan]1.[/cyan] Select the repositories you want to grant access to
  [cyan]2.[/cyan] Click [bold]'Install'[/bold] to complete the installation
  [cyan]3.[/cyan] Return to this terminal once installation is complete
"""
        panel = Panel(
            steps.strip(),
            border_style="cyan",
            title="[bold]How to Install[/bold]",
            padding=(1, 2),
        )
        console.print("\n")
        console.print(panel)

    def _confirm_installation_completed(self) -> bool:
        console.print("\n" + "─" * 80)

        result = select(
            "Have you completed the installation?",
            choices=[
                {"name": "Yes - Installation complete", "value": "yes"},
                {"name": "No - Skip for now", "value": "no"},
            ],
            style=PROMPT_STYLE,
        ).ask()

        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user")

        if result == "yes":
            console.print(
                f"\nGreat! {self.app_config.app_name} is now available for your repository.",
                style="success",
            )
            log.info("User confirmed %s installation completed", self.app_config.app_name)
            return True
        self._show_skip_warning()
        return False

    def _show_skip_warning(self) -> None:
        warning_content = f"""
[bold yellow]GitHub App Not Installed[/bold yellow]

You have chosen to skip installing [bold]{self.app_config.app_name}[/bold].

[bold red]Features that will NOT work:[/bold red]
  ❌ CodeQL security analysis on your initial commit
  ❌ Semgrep code scanning on your initial commit
  ❌ Automated code quality checks

[bold cyan]You can install the app later:[/bold cyan]
  {self.app_config.installation_url}

Once installed, these features will work on future commits.
"""
        panel = Panel(
            warning_content.strip(),
            border_style="yellow",
            title="[bold yellow]Warning[/bold yellow]",
            padding=(1, 2),
        )
        console.print("\n")
        console.print(panel)
        log.warning("User skipped %s installation", self.app_config.app_name)

    def check_installation_optional(self, *, skip_prompt: bool = False) -> bool:
        if skip_prompt:
            return False

        return self.prompt_installation()
