"""Tests for AddDependencyCommand."""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.ar_infra.application.use_cases.add_dependency_use_case import (
    AddDependenciesResult,
)
from src.ar_infra.cli.command.add_dependency import (
    AddDependencyCommand,
    AddDependencyCommandArgs,
)


class TestAddDependencyCommand:
    @pytest.fixture
    def command(self) -> AddDependencyCommand:
        return AddDependencyCommand()

    @pytest.fixture
    def success_result(self) -> AddDependenciesResult:
        return AddDependenciesResult(
            success=True,
            message="Successfully added 1 dependencies.",
            added_count=1,
            skipped_count=0,
            skipped_dependencies=[],
        )

    def test_execute_with_valid_single_dependency(
        self,
        command: AddDependencyCommand,
        success_result: AddDependenciesResult,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        args = AddDependencyCommandArgs(
            dependencies=("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",),
            project_path=str(tmp_path),
        )

        with patch.object(command._use_case, "execute", return_value=success_result):
            command.execute(args)

    def test_execute_with_valid_multiple_dependencies(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        args = AddDependencyCommandArgs(
            dependencies=(
                "implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",
                "runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.13.0'",
            ),
            project_path=str(tmp_path),
        )

        result = AddDependenciesResult(
            success=True,
            message="Successfully added 2 dependencies.",
            added_count=2,
            skipped_count=0,
            skipped_dependencies=[],
        )

        with patch.object(command._use_case, "execute", return_value=result):
            command.execute(args)

    def test_execute_exits_when_no_dependencies_provided(
        self,
        command: AddDependencyCommand,
    ) -> None:
        args = AddDependencyCommandArgs(
            dependencies=(),
            project_path=None,
        )

        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        assert exc_info.value.code == 1

    def test_execute_exits_on_validation_error(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        args = AddDependencyCommandArgs(
            dependencies=("invalid dependency",),
            project_path=str(tmp_path),
        )

        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        assert exc_info.value.code == 1

    def test_execute_exits_on_file_not_found(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        args = AddDependencyCommandArgs(
            dependencies=("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",),
            project_path=str(tmp_path / "nonexistent"),
        )

        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        assert exc_info.value.code == 1

    def test_execute_exits_on_use_case_failure(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        args = AddDependencyCommandArgs(
            dependencies=("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",),
            project_path=str(tmp_path),
        )

        failure_result = AddDependenciesResult(
            success=False,
            message="Failed to add dependency",
            added_count=0,
            skipped_count=0,
            skipped_dependencies=[],
        )

        with patch.object(command._use_case, "execute", return_value=failure_result):
            with pytest.raises(SystemExit) as exc_info:
                command.execute(args)

            assert exc_info.value.code == 1

    def test_execute_handles_keyboard_interrupt(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        args = AddDependencyCommandArgs(
            dependencies=("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",),
            project_path=str(tmp_path),
        )

        with patch.object(command._use_case, "execute", side_effect=KeyboardInterrupt):
            with pytest.raises(SystemExit) as exc_info:
                command.execute(args)

            assert exc_info.value.code == 0

    def test_resolve_project_path_uses_current_directory_when_none(
        self,
        command: AddDependencyCommand,
    ) -> None:
        path = command._resolve_project_path(None)

        assert path == Path.cwd().resolve()

    def test_resolve_project_path_resolves_relative_path(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        path = command._resolve_project_path(str(subdir))

        assert path == subdir.resolve()
        assert path.is_absolute()

    def test_resolve_project_path_raises_error_when_path_not_exists(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError, match="does not exist"):
            command._resolve_project_path(str(nonexistent))

    def test_resolve_project_path_raises_error_when_path_is_file(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        file_path = tmp_path / "file.txt"
        file_path.write_text("content", encoding="utf-8")

        with pytest.raises(NotADirectoryError, match="not a directory"):
            command._resolve_project_path(str(file_path))

    def test_validate_project_structure_succeeds_when_build_gradle_exists(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("", encoding="utf-8")

        command._validate_project_structure(tmp_path)

    def test_validate_project_structure_succeeds_when_build_gradle_in_parent(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("", encoding="utf-8")

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        command._validate_project_structure(subdir)

    def test_validate_project_structure_raises_error_when_no_build_gradle(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        with pytest.raises(FileNotFoundError, match="build.gradle not found"):
            command._validate_project_structure(tmp_path)

    def test_display_summary_shows_project_and_dependencies(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        from src.ar_infra.domain.entities.gradle_dependency import (
            GradleConfiguration,
            GradleDependency,
        )

        dependencies = [
            GradleDependency(
                group="io.jsonwebtoken",
                name="jjwt-api",
                version="0.13.0",
                configuration=GradleConfiguration.IMPLEMENTATION,
            ),
        ]

        with patch("src.ar_infra.cli.command.add_dependency.Messages") as mock_messages:
            command._display_summary(dependencies, tmp_path)

            assert mock_messages.info.call_count >= 3

    def test_execute_with_skipped_dependencies_logs_info(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        args = AddDependencyCommandArgs(
            dependencies=("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",),
            project_path=str(tmp_path),
        )

        result = AddDependenciesResult(
            success=True,
            message="All 1 dependencies were already present.",
            added_count=0,
            skipped_count=1,
            skipped_dependencies=["implementation 'io.jsonwebtoken:jjwt-api:0.13.0'"],
        )

        with patch.object(command._use_case, "execute", return_value=result) and patch(
            "src.ar_infra.cli.command.add_dependency.log"
        ) as mock_log:
            command.execute(args)
            mock_log.info.assert_called()

    def test_execute_handles_permission_error(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        args = AddDependencyCommandArgs(
            dependencies=("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",),
            project_path=str(tmp_path),
        )

        with patch.object(
            command._use_case, "execute", side_effect=PermissionError("Access denied")
        ):
            with pytest.raises(SystemExit) as exc_info:
                command.execute(args)

            assert exc_info.value.code == 1

    def test_execute_handles_os_error(
        self,
        command: AddDependencyCommand,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        args = AddDependencyCommandArgs(
            dependencies=("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",),
            project_path=str(tmp_path),
        )

        with patch.object(command._use_case, "execute", side_effect=OSError("I/O error")):
            with pytest.raises(SystemExit) as exc_info:
                command.execute(args)

            assert exc_info.value.code == 1
