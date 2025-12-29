"""Tests for GenerateProjectUseCase."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from src.ar_infra.application.use_cases.generate_project_use_case import GenerateProjectUseCase
from src.ar_infra.application.use_cases.input_dto import GenerateProjectInput
from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.domain.value_objects.artifact_id import ArtifactId
from src.ar_infra.domain.value_objects.group_id import GroupId
from src.ar_infra.domain.value_objects.package_name import PackageName
from src.ar_infra.domain.value_objects.version import Version


@pytest.fixture(autouse=True)
def mock_bot_env(monkeypatch):
    """Prevent GitHub API calls by setting bot env vars."""
    monkeypatch.setenv("BOT_ID", "123456")
    monkeypatch.setenv("BOT_SLUG", "ar-infra-bot")


@pytest.fixture
def use_case(template_fetcher, feature_manager, gradle_writer, package_renamer):
    fake_git_initializer = Mock()
    fake_annotation_writer = Mock()
    return GenerateProjectUseCase(
        template_fetcher=template_fetcher,
        feature_manager=feature_manager,
        gradle_writer=gradle_writer,
        package_renamer=package_renamer,
        git_initializer=fake_git_initializer,
        annotation_writer=fake_annotation_writer,
    )


class TestGenerateProjectUseCase:
    """Test suite for GenerateProjectUseCase."""

    @pytest.fixture
    def template_fetcher(self, tmp_path: Path) -> Mock:
        fetcher = Mock()

        def create_template_files(url, destination, use_cache=False):
            destination.mkdir(parents=True, exist_ok=True)

            settings_file = destination / "settings.gradle"
            settings_file.write_text("rootProject.name = 'arinfra'\n", encoding="utf-8")

            build_gradle = destination / "build.gradle"
            build_gradle.write_text("group = 'com.example'\nversion = '0.0.1'\n", encoding="utf-8")

            return "com.example.arinfra"

        fetcher.fetch.side_effect = create_template_files
        return fetcher

    @pytest.fixture
    def feature_manager(self) -> Mock:
        manager = Mock()
        manager.get_dependencies_for_features.return_value = [
            "org.postgresql:postgresql",
            "software.amazon.awssdk:s3",
        ]
        return manager

    @pytest.fixture
    def gradle_writer(self) -> Mock:
        return Mock()

    @pytest.fixture
    def package_renamer(self) -> Mock:
        return Mock()

    @pytest.fixture
    def valid_input(self, tmp_path: Path) -> GenerateProjectInput:
        return GenerateProjectInput(
            group_id=GroupId("dev.razafindratelo"),
            artifact_id=ArtifactId("backend-api"),
            version=Version("1.0.0"),
            destination=tmp_path / "my-project",
            enabled_features={TemplateFeature.POSTGRESQL, TemplateFeature.S3_BUCKET},
            template_url="https://github.com/Abega1642/ar-infra-template.git",
            use_template_cache=False,
        )

    def test_execute_success(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        template_fetcher: Mock,
    ) -> None:
        result = use_case.execute(valid_input)

        assert result.success is True
        assert result.project_path == valid_input.destination
        assert "successfully" in result.message.lower()

    def test_fetch_template(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        template_fetcher: Mock,
    ) -> None:
        use_case.execute(valid_input)

        template_fetcher.fetch.assert_called_once_with(
            valid_input.template_url,
            valid_input.destination,
            use_cache=valid_input.use_template_cache,
        )

    def test_apply_feature_selection(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        feature_manager: Mock,
    ) -> None:
        use_case.execute(valid_input)

        feature_manager.apply_feature_selection.assert_called_once_with(
            valid_input.destination,
            valid_input.enabled_features,
        )

    def test_remove_unwanted_dependencies(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        feature_manager: Mock,
        gradle_writer: Mock,
    ) -> None:
        use_case.execute(valid_input)

        feature_manager.get_dependencies_for_features.assert_called_once_with(
            valid_input.enabled_features
        )

        gradle_writer.remove_dependencies_except.assert_called_once_with(
            valid_input.destination / "build.gradle",
            [
                "org.postgresql:postgresql",
                "software.amazon.awssdk:s3",
            ],
        )

    def test_update_build_gradle(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        gradle_writer: Mock,
    ) -> None:
        use_case.execute(valid_input)

        build_gradle = valid_input.destination / "build.gradle"
        gradle_writer.update_group_and_version.assert_called_once_with(
            build_gradle,
            valid_input.group_id,
            valid_input.version,
        )

    def test_rename_packages(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        template_fetcher: Mock,
        package_renamer: Mock,
    ) -> None:
        use_case.execute(valid_input)

        expected_old = PackageName("com.example.arinfra")
        expected_new = PackageName.from_parts(
            valid_input.group_id,
            valid_input.artifact_id,
        )

        package_renamer.rename_package.assert_called_once_with(
            valid_input.destination,
            expected_old,
            expected_new,
        )

    def test_update_settings_gradle(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        gradle_writer: Mock,
    ) -> None:
        use_case.execute(valid_input)

        settings_file = valid_input.destination / "settings.gradle"
        assert settings_file.exists()

        # Since gradle_writer is mocked, we assert the collaboration (call),
        # not the file content change performed by the mock.
        gradle_writer.update_settings_gradle.assert_called_once_with(
            settings_file,
            valid_input.artifact_id,
        )

    def test_handle_template_fetch_error(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        template_fetcher: Mock,
    ) -> None:
        template_fetcher.fetch.side_effect = Exception("Fetch failed")

        result = use_case.execute(valid_input)

        assert result.success is False
        assert "failed" in result.message.lower()

    def test_handle_feature_removal_error(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        feature_manager: Mock,
    ) -> None:
        feature_manager.apply_feature_selection.side_effect = Exception("Feature error")

        result = use_case.execute(valid_input)

        assert result.success is False

    def test_handle_package_rename_error(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
        package_renamer: Mock,
    ) -> None:
        package_renamer.rename_package.side_effect = Exception("Rename failed")

        result = use_case.execute(valid_input)

        assert result.success is False
