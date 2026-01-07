from collections.abc import Iterator
from contextlib import contextmanager

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

from src.ar_infra.cli.ui.console import console


class ProgressIndicator:
    @staticmethod
    @contextmanager
    def spinner(message: str) -> Iterator[Progress]:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(description=message, total=None)
            yield progress

    @staticmethod
    @contextmanager
    def steps(total_steps: int) -> Iterator[tuple[Progress, TaskID]]:
        with Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task: TaskID = progress.add_task("Generating project...", total=total_steps)
            yield progress, task
