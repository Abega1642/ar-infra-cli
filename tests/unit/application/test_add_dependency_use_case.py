"""Tests for AddDependenciesUseCase."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.ar_infra.application.use_cases.add_dependency_use_case import (
    AddDependenciesInput,
    AddDependenciesUseCase,
)
from src.ar_infra.domain.entities.gradle_dependency import (
    GradleConfiguration,
    GradleDependency,
)


class TestAddDependenciesUseCase:
    @pytest.fixture
    def mock_gradle_writer(self) -> Mock:
        return Mock()

    @pytest.fixture
    def use_case(self, mock_gradle_writer: Mock) -> AddDependenciesUseCase:
        return AddDependenciesUseCase(gradle_writer=mock_gradle_writer)

    @pytest.fixture
    def sample_dependency(self) -> GradleDependency:
        return GradleDependency(
            group="io.jsonwebtoken",
            name="jjwt-api",
            version="0.13.0",
            configuration=GradleConfiguration.IMPLEMENTATION,
        )

    def test_execute_adds_single_dependency_successfully(
        self,
        use_case: AddDependenciesUseCase,
        mock_gradle_writer: Mock,
        sample_dependency: GradleDependency,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        input_data = AddDependenciesInput(
            project_path=tmp_path,
            dependencies=[sample_dependency],
        )

        def mock_add_dependency(file: Path, dep: GradleDependency) -> None:
            content = file.read_text(encoding="utf-8")
            new_content = content.replace("}", f"    {dep}\n}}")
            file.write_text(new_content, encoding="utf-8")

        mock_gradle_writer.add_dependency.side_effect = mock_add_dependency

        result = use_case.execute(input_data)

        assert result.success is True
        assert result.added_count == 1
        assert result.skipped_count == 0
        assert "Successfully added 1 dependencies" in result.message
        mock_gradle_writer.add_dependency.assert_called_once()

    def test_execute_adds_multiple_dependencies_successfully(
        self,
        use_case: AddDependenciesUseCase,
        mock_gradle_writer: Mock,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        dependencies = [
            GradleDependency(
                group="io.jsonwebtoken",
                name="jjwt-api",
                version="0.13.0",
                configuration=GradleConfiguration.IMPLEMENTATION,
            ),
            GradleDependency(
                group="io.jsonwebtoken",
                name="jjwt-impl",
                version="0.13.0",
                configuration=GradleConfiguration.RUNTIME_ONLY,
            ),
        ]

        input_data = AddDependenciesInput(
            project_path=tmp_path,
            dependencies=dependencies,
        )

        def mock_add_dependency(file: Path, dep: GradleDependency) -> None:
            content = file.read_text(encoding="utf-8")
            new_content = content.replace("}", f"    {dep}\n}}")
            file.write_text(new_content, encoding="utf-8")

        mock_gradle_writer.add_dependency.side_effect = mock_add_dependency

        result = use_case.execute(input_data)

        assert result.success is True
        assert result.added_count == 2
        assert result.skipped_count == 0
        assert "Successfully added 2 dependencies" in result.message
        assert mock_gradle_writer.add_dependency.call_count == 2

    def test_execute_skips_existing_dependency(
        self,
        use_case: AddDependenciesUseCase,
        mock_gradle_writer: Mock,
        sample_dependency: GradleDependency,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        existing_content = (
            "dependencies {\n    implementation 'io.jsonwebtoken:jjwt-api:0.13.0'\n}\n"
        )
        build_file.write_text(existing_content, encoding="utf-8")

        input_data = AddDependenciesInput(
            project_path=tmp_path,
            dependencies=[sample_dependency],
        )

        mock_gradle_writer.add_dependency.side_effect = lambda f, d: None

        result = use_case.execute(input_data)

        assert result.success is True
        assert result.added_count == 0
        assert result.skipped_count == 1
        assert "already present" in result.message.lower()
        assert len(result.skipped_dependencies) == 1

    def test_execute_handles_mixed_new_and_existing_dependencies(
        self,
        use_case: AddDependenciesUseCase,
        mock_gradle_writer: Mock,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text(
            "dependencies {\n    implementation 'existing:dep:1.0'\n}\n", encoding="utf-8"
        )

        dependencies = [
            GradleDependency(
                group="existing",
                name="dep",
                version="1.0",
                configuration=GradleConfiguration.IMPLEMENTATION,
            ),
            GradleDependency(
                group="new",
                name="dep",
                version="2.0",
                configuration=GradleConfiguration.IMPLEMENTATION,
            ),
        ]

        input_data = AddDependenciesInput(
            project_path=tmp_path,
            dependencies=dependencies,
        )

        call_count = 0

        def mock_add_dependency(file: Path, dep: GradleDependency) -> None:
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                content = file.read_text(encoding="utf-8")
                new_content = content.replace("}", f"    {dep}\n}}")
                file.write_text(new_content, encoding="utf-8")

        mock_gradle_writer.add_dependency.side_effect = mock_add_dependency

        result = use_case.execute(input_data)

        assert result.success is True
        assert result.added_count == 1
        assert result.skipped_count == 1
        assert "1 dependencies were already present" in result.message

    def test_execute_returns_error_when_build_gradle_not_found(
        self,
        use_case: AddDependenciesUseCase,
        sample_dependency: GradleDependency,
        tmp_path: Path,
    ) -> None:
        input_data = AddDependenciesInput(
            project_path=tmp_path,
            dependencies=[sample_dependency],
        )

        result = use_case.execute(input_data)

        assert result.success is False
        assert "build.gradle not found" in result.message
        assert result.added_count == 0
        assert result.skipped_count == 0

    def test_execute_returns_error_on_write_failure(
        self,
        use_case: AddDependenciesUseCase,
        mock_gradle_writer: Mock,
        sample_dependency: GradleDependency,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("dependencies {\n}\n", encoding="utf-8")

        input_data = AddDependenciesInput(
            project_path=tmp_path,
            dependencies=[sample_dependency],
        )

        mock_gradle_writer.add_dependency.side_effect = OSError("Write failed")

        result = use_case.execute(input_data)

        assert result.success is False
        assert "Failed to add dependency" in result.message
        assert "Write failed" in result.message

    def test_locate_build_gradle_in_project_root(
        self,
        use_case: AddDependenciesUseCase,
        tmp_path: Path,
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text("", encoding="utf-8")

        located = use_case._locate_build_gradle(tmp_path)

        assert located == build_file

    def test_locate_build_gradle_in_parent_directory(
        self,
        use_case: AddDependenciesUseCase,
        tmp_path: Path,
    ) -> None:
        parent_build = tmp_path / "build.gradle"
        parent_build.write_text("", encoding="utf-8")

        subdir = tmp_path / "subdir"
        subdir.mkdir()

        with patch("src.ar_infra.application.use_cases.add_dependency_use_case.log"):
            located = use_case._locate_build_gradle(subdir)

        assert located == parent_build

    def test_locate_build_gradle_returns_expected_path_when_not_found(
        self,
        use_case: AddDependenciesUseCase,
        tmp_path: Path,
    ) -> None:
        with patch("src.ar_infra.application.use_cases.add_dependency_use_case.log"):
            located = use_case._locate_build_gradle(tmp_path)

        assert located == tmp_path / "build.gradle"

    def test_build_success_message_with_only_added(
        self,
        use_case: AddDependenciesUseCase,
    ) -> None:
        message = use_case._build_success_message(added_count=3, skipped_count=0)

        assert "Successfully added 3 dependencies" in message
        assert "skipped" not in message.lower()

    def test_build_success_message_with_only_skipped(
        self,
        use_case: AddDependenciesUseCase,
    ) -> None:
        message = use_case._build_success_message(added_count=0, skipped_count=2)

        assert "All 2 dependencies were already present" in message
        assert "No changes made" in message

    def test_build_success_message_with_mixed_results(
        self,
        use_case: AddDependenciesUseCase,
    ) -> None:
        message = use_case._build_success_message(added_count=3, skipped_count=2)

        assert "Successfully added 3 dependencies" in message
        assert "2 dependencies were already present and skipped" in message
