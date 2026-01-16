"""Use case for adding dependencies to build.gradle."""

from dataclasses import dataclass
from pathlib import Path
from typing import final

from src.ar_infra.domain.entities.gradle_dependency import GradleDependency
from src.ar_infra.infrastructure.gradle import GradleWriteError, GradleWriter, MaliciousContentError
from src.ar_infra.logger import get_logger


log = get_logger(use_rich=True)


@dataclass(frozen=True)
class AddDependenciesInput:
    project_path: Path
    dependencies: list[GradleDependency]


@dataclass(frozen=True)
class AddDependenciesResult:
    success: bool
    message: str
    added_count: int
    skipped_count: int
    skipped_dependencies: list[str]


@final
class AddDependenciesUseCase:
    def __init__(self, gradle_writer: GradleWriter) -> None:
        self._gradle_writer = gradle_writer

    def execute(self, input_data: AddDependenciesInput) -> AddDependenciesResult:
        build_file = self._locate_build_gradle(input_data.project_path)

        if not build_file.exists():
            return AddDependenciesResult(
                success=False,
                message=f"build.gradle not found at {build_file}",
                added_count=0,
                skipped_count=0,
                skipped_dependencies=[],
            )

        log.info("Adding %d dependencies to %s", len(input_data.dependencies), build_file)

        added_count = 0
        skipped_count = 0
        skipped_dependencies = []

        for dependency in input_data.dependencies:
            try:
                content_before = build_file.read_text(encoding="utf-8")
                self._gradle_writer.add_dependency(build_file, dependency)
                content_after = build_file.read_text(encoding="utf-8")

                if content_before == content_after:
                    log.info("Dependency already exists, skipping: %s", str(dependency))
                    skipped_count += 1
                    skipped_dependencies.append(str(dependency))
                else:
                    log.info("Successfully added dependency: %s", str(dependency))
                    added_count += 1

            except (GradleWriteError, MaliciousContentError, OSError) as e:
                log.exception("Failed to add dependency %s", str(dependency))
                return AddDependenciesResult(
                    success=False,
                    message=f"Failed to add dependency {dependency}: {e}",
                    added_count=added_count,
                    skipped_count=skipped_count,
                    skipped_dependencies=skipped_dependencies,
                )

        message = self._build_success_message(added_count, skipped_count)

        return AddDependenciesResult(
            success=True,
            message=message,
            added_count=added_count,
            skipped_count=skipped_count,
            skipped_dependencies=skipped_dependencies,
        )

    @staticmethod
    def _locate_build_gradle(project_path: Path) -> Path:
        build_file = project_path / "build.gradle"

        if not build_file.exists():
            log.warning("build.gradle not found at %s, checking parent directories", project_path)
            current = project_path
            for _ in range(3):
                parent_build = current / "build.gradle"
                if parent_build.exists():
                    log.info("Found build.gradle at %s", parent_build)
                    return parent_build
                current = current.parent

        return build_file

    @staticmethod
    def _build_success_message(added_count: int, skipped_count: int) -> str:
        if added_count > 0 and skipped_count > 0:
            return (
                f"Successfully added {added_count} dependencies. "
                f"{skipped_count} dependencies were already present and skipped."
            )
        if added_count > 0:
            return f"Successfully added {added_count} dependencies."
        return f"All {skipped_count} dependencies were already present. No changes made."
