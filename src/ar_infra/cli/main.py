"""Main CLI entry point."""

import click

from src.ar_infra.cli.command.init import InitCommand, InitCommandArgs
from src.ar_infra.cli.resources.documentation import (
    ARTIFACT_OPTION_HELP,
    FEATURES_OPTION_HELP,
    GROUP_OPTION_HELP,
    NO_CACHE_OPTION_HELP,
    NO_FEATURES_OPTION_HELP,
    PATH_OPTION_HELP,
    PROJECT_DIR_OPTION_HELP,
    VERSION_OPTION_HELP,
)
from src.ar_infra.cli.resources.help import HELP_TEXT
from src.ar_infra.cli.ui.banner import Banner
from src.ar_infra.properties import CLI_VERSION


@click.group(
    invoke_without_command=True,
    add_help_option=False,
)
@click.version_option(version=CLI_VERSION, prog_name="ar-infra-cli")
@click.option(
    "--help",
    is_flag=True,
    expose_value=False,
    help="Show this help message and exit.",
)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Ar-infra cli."""
    if ctx.invoked_subcommand is None:
        Banner.show()
        click.echo(HELP_TEXT)
        ctx.exit()


@cli.command(help=HELP_TEXT)
@click.option("--group", type=str, help=GROUP_OPTION_HELP)
@click.option("--artifact", type=str, help=ARTIFACT_OPTION_HELP)
@click.option("--project-version", type=str, help=VERSION_OPTION_HELP)
@click.option("--path", type=str, help=PATH_OPTION_HELP)
@click.option("--project-dir", type=str, help=PROJECT_DIR_OPTION_HELP)
@click.option("--features", type=str, help=FEATURES_OPTION_HELP)
@click.option("--disable-features", type=str, help=NO_FEATURES_OPTION_HELP)
@click.option("--no-cache", "no_cache", is_flag=True, help=NO_CACHE_OPTION_HELP)
def init(
    group: str | None,
    artifact: str | None,
    project_version: str | None,
    path: str | None,
    project_dir: str | None,
    features: str | None,
    disable_features: str | None,
    *,
    no_cache: bool,
) -> None:
    """Initialize a new Spring Boot project."""
    command = InitCommand()
    args = InitCommandArgs(
        group=group,
        artifact=artifact,
        version=project_version,
        path=path,
        project_dir=project_dir,
        features=features,
        no_features=disable_features,
        no_cache=no_cache,
    )
    command.execute(args)


if __name__ == "__main__":
    cli()  # pylint: disable=no-value-for-parameter
