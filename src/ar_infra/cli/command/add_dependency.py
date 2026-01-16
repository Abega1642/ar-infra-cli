"""Add dependency command."""

import sys
from dataclasses import dataclass
from pathlib import Path

from src.ar_infra.application.use_cases.add_dependency_use_case import (
    AddDependenciesInput,
    AddDependenciesUseCase,
)
from src.ar_infra.cli.ui.message import Messages
from src.ar_infra.domain.entities.gradle_dependency import GradleDependency
from src.ar_infra.domain.exceptions.validation_error import ValidationError
from src.ar_infra.infrastructure.gradle import GradleWriter
from src.ar_infra.infrastructure.gradle.dependency_parser import DependencyParser
from src.ar_infra.logger import get_logger


log = get_logger(use_rich=True)


@dataclass(frozen=True)
class AddDependencyCommandArgs:
    dependencies: tuple[str, ...]
    project_path: str | None


class AddDependencyCommand:
    """Command to add dependencies to build.gradle."""

    def __init__(self) -> None:
        self._parser = DependencyParser()
        self._use_case = AddDependenciesUseCase(gradle_writer=GradleWriter())

    def execute(self, args: AddDependencyCommandArgs) -> None:
        if not args.dependencies:
            Messages.error("No dependencies provided. Use --help for usage information.")
            sys.exit(1)

        try:
            project_path = self._resolve_project_path(args.project_path)
            self._validate_project_structure(project_path)

            log.info("Parsing %d dependency strings", len(args.dependencies))
            parsed_dependencies = self._parser.parse_multiple(list(args.dependencies))

            log.info("Resolved project path: %s", project_path)

            self._display_summary(parsed_dependencies, project_path)

            input_data = AddDependenciesInput(
                project_path=project_path,
                dependencies=parsed_dependencies,
            )

            result = self._use_case.execute(input_data)

            if result.success:
                Messages.success(result.message)
                if result.added_count > 0:
                    Messages.info(f"Updated: {project_path / 'build.gradle'}")
                if result.skipped_dependencies:
                    log.info("Skipped dependencies: %s", ", ".join(result.skipped_dependencies))
            else:
                Messages.error(result.message)
                sys.exit(1)

        except ValidationError as e:
            Messages.error(f"Validation error: {e}")
            sys.exit(1)
        except FileNotFoundError as e:
            Messages.error(f"File not found: {e}")
            sys.exit(1)
        except PermissionError as e:
            Messages.error(f"Permission denied: {e}")
            sys.exit(1)
        except OSError as e:
            Messages.error(f"I/O error: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            Messages.warning("Operation cancelled by user.")
            sys.exit(0)

    @staticmethod
    def _resolve_project_path(project_path: str | None) -> Path:
        if project_path is None:
            return Path.cwd().resolve()

        path = Path(project_path).resolve()

        if not path.exists():
            raise FileNotFoundError(f"Project path does not exist: {path}")

        if not path.is_dir():
            raise NotADirectoryError(f"Project path is not a directory: {path}")

        return path

    @staticmethod
    def _validate_project_structure(project_path: Path) -> None:
        build_file = project_path / "build.gradle"

        if not build_file.exists():
            parent_build = project_path.parent / "build.gradle"
            grandparent_build = project_path.parent.parent / "build.gradle"

            if not parent_build.exists() and not grandparent_build.exists():
                raise FileNotFoundError(
                    f"build.gradle not found in {project_path} or parent directories. "
                    "Please run this command from a Gradle project directory."
                )

    @staticmethod
    def _display_summary(dependencies: list[GradleDependency], project_path: Path) -> None:
        Messages.info(f"Project: {project_path}")
        Messages.info(f"Dependencies to add: {len(dependencies)}")
        for dep in dependencies:
            Messages.info(f"  - {dep}")
