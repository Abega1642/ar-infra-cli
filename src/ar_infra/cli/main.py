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
from src.ar_infra.cli.ui.banner import Banner
from src.ar_infra.cli.ui.help import show_help
from src.ar_infra.properties import CLI_VERSION


@click.group(
    invoke_without_command=True,
    add_help_option=False,
)
@click.version_option(version=CLI_VERSION, prog_name="ar-infra-cli")
@click.option(
    "--help",
    "show_help_flag",
    is_flag=True,
    help="Show this message and exit.",
)
@click.pass_context
def cli(ctx: click.Context, *, show_help_flag: bool = False) -> None:
    if show_help_flag:
        show_help()
        ctx.exit()

    if ctx.invoked_subcommand is None:
        Banner.show()
        show_help()
        ctx.exit()


def _show_help_and_exit(
    ctx: click.Context,
    _param: click.Parameter,
    value: bool,  # noqa: FBT001
) -> None:
    if value:
        show_help()
        ctx.exit()


@cli.command(context_settings={"max_content_width": 120})
@click.option("--group", type=str, help=GROUP_OPTION_HELP)
@click.option("--artifact", type=str, help=ARTIFACT_OPTION_HELP)
@click.option("--project-version", type=str, help=VERSION_OPTION_HELP)
@click.option("--path", type=str, help=PATH_OPTION_HELP)
@click.option("--project-dir", type=str, help=PROJECT_DIR_OPTION_HELP)
@click.option("--features", type=str, help=FEATURES_OPTION_HELP)
@click.option("--disable-features", type=str, help=NO_FEATURES_OPTION_HELP)
@click.option("--no-cache", "no_cache", is_flag=True, help=NO_CACHE_OPTION_HELP)
@click.option(
    "--help",
    "-h",
    is_flag=True,
    expose_value=False,
    is_eager=True,
    callback=_show_help_and_exit,
    help="Show this message and exit.",
)
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
