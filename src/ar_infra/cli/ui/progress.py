from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass

from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

from src.ar_infra.cli.ui.console import console


@dataclass
class ProgressStep:
    name: str
    weight: int = 1


class StepProgress:
    def __init__(self, steps: list[ProgressStep]):
        self.steps = steps
        self.total_weight = sum(step.weight for step in steps)
        self.current_step_index = 0
        self.accumulated_weight = 0

        self.progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        )
        self.task_id: TaskID | None = None
        self.live: Live | None = None
        self._is_active = False

    def start(self) -> None:
        self.task_id = self.progress.add_task("Initializing...", total=self.total_weight)
        self.live = Live(
            self.progress,
            console=console,
            refresh_per_second=10,
        )
        self.live.start()
        self._is_active = True

    def update_step(self, step_name: str, *, completed: bool = False) -> None:
        if self.task_id is None or not self._is_active:
            return

        if completed and self.current_step_index < len(self.steps):
            current_step = self.steps[self.current_step_index]
            self.accumulated_weight += current_step.weight
            self.current_step_index += 1

        self.progress.update(self.task_id, description=step_name, completed=self.accumulated_weight)

    def pause(self) -> None:
        if self.live and self._is_active:
            self.live.stop()
            self._is_active = False

    def resume(self) -> None:
        if self.live and not self._is_active:
            self.live.start()
            self._is_active = True

    def complete(self) -> None:
        if self.task_id is None:
            return

        self.progress.update(self.task_id, description="Complete!", completed=self.total_weight)

    def stop(self) -> None:
        if self.live and self._is_active:
            self.live.stop()
            self._is_active = False


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
    def steps(steps: list[ProgressStep]) -> Iterator[StepProgress]:
        step_progress = StepProgress(steps)
        try:
            step_progress.start()
            yield step_progress
        finally:
            step_progress.stop()


PROJECT_GENERATION_STEPS = [
    ProgressStep("Fetching template...", weight=3),
    ProgressStep("Applying features...", weight=2),
    ProgressStep("Removing dependencies...", weight=1),
    ProgressStep("Configuring build...", weight=1),
    ProgressStep("Renaming packages...", weight=2),
    ProgressStep("Updating settings...", weight=1),
    ProgressStep("Updating annotations...", weight=1),
    ProgressStep("Cleaning artifacts...", weight=1),
    ProgressStep("Formatting code...", weight=2),
    ProgressStep("Initializing git...", weight=1),
]
