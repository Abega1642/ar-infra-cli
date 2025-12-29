"""Main CLI entry point."""

from pathlib import Path

import click

from src.ar_infra.cli.command.init import InitCommand, InitCommandArgs


def load_help_text() -> str:
    """Load help text from file."""
    help_path = Path(__file__).parent / "resources" / "help.txt"
    if help_path.exists():
        return help_path.read_text(encoding="utf-8")
    return "AR-INFRA - Spring Boot Project Generator"


@click.group()
@click.version_option(version="1.0.0", prog_name="ar-infra")
def cli() -> None:
    """AR-INFRA - Spring Boot Project Generator with Superpowers."""


@cli.command(help=load_help_text())
@click.option("--group", type=str, help="Gradle group ID")
@click.option("--artifact", type=str, help="Gradle artifact ID")
@click.option("--version", type=str, help="Project version")
@click.option("--path", type=str, help="Destination directory")
@click.option("--features", type=str, help="Comma-separated features to enable")
@click.option("--no-features", type=str, help="Comma-separated features to disable")
@click.option("--template-url", type=str, help="Custom template repository URL")
@click.option("--no-cache", "no_cache", is_flag=True, help="Don't use cached template")
def init(
    group: str | None,
    artifact: str | None,
    version: str | None,
    path: str | None,
    features: str | None,
    no_features: str | None,
    template_url: str | None,
    *,
    no_cache: bool,
) -> None:
    """Initialize a new Spring Boot project."""
    command = InitCommand()

    args = InitCommandArgs(
        group=group,
        artifact=artifact,
        version=version,
        path=path,
        features=features,
        no_features=no_features,
        template_url=template_url,
        no_cache=no_cache,
    )

    command.execute(args)


if __name__ == "__main__":
    cli()
