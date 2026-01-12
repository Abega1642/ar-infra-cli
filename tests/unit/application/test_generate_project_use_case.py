"""Tests for GenerateProjectUseCase."""

from pathlib import Path
from unittest.mock import Mock, patch

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
    monkeypatch.setenv("BOT_ID", "123456")
    monkeypatch.setenv("BOT_SLUG", "ar-infra-bot")


@pytest.fixture
def use_case(template_fetcher, feature_manager, gradle_writer, package_renamer):
    fake_git_initializer = Mock()
    fake_annotation_writer = Mock()
    fake_artifact_cleaner = Mock()
    fake_format_runner = Mock()
    fake_artifact_cleaner.clean.return_value = 8
    fake_artifact_cleaner.clean_empty_parent_directories.return_value = 1

    return GenerateProjectUseCase(
        template_fetcher=template_fetcher,
        feature_manager=feature_manager,
        gradle_writer=gradle_writer,
        package_renamer=package_renamer,
        git_initializer=fake_git_initializer,
        annotation_writer=fake_annotation_writer,
        artifact_cleaner=fake_artifact_cleaner,
        format_script_runner=fake_format_runner,
    )


class TestGenerateProjectUseCase:
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

        def get_deps_for_feature(feature):
            feature_deps = {
                TemplateFeature.RABBITMQ: [
                    "org.springframework.boot:spring-boot-starter-amqp",
                    "org.testcontainers:rabbitmq",
                ],
                TemplateFeature.EMAIL: [
                    "org.springframework.boot:spring-boot-starter-mail",
                    "com.icegreen:greenmail",
                ],
            }
            return feature_deps.get(feature, [])

        manager.get_feature_dependencies.side_effect = get_deps_for_feature
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
        all_features = set(TemplateFeature)
        disabled_features = all_features - valid_input.enabled_features

        assert feature_manager.get_feature_dependencies.call_count == len(disabled_features)

        gradle_writer.remove_dependencies.assert_called_once()
        call_args = gradle_writer.remove_dependencies.call_args
        assert call_args[0][0] == valid_input.destination / "build.gradle"
        assert isinstance(call_args[0][1], list)

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

    def test_artifact_cleaner_handles_errors(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
    ) -> None:
        use_case._artifact_cleaner.clean.side_effect = OSError("Permission denied")

        result = use_case.execute(valid_input)

        assert result.success is False
        assert "Failed to clean development artifacts" in result.message

    def test_artifact_cleaner_called_before_git_init(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
    ) -> None:
        call_order = []
        use_case._artifact_cleaner.clean.side_effect = (
            lambda *args: call_order.append("cleaner") or 8
        )
        use_case._git_initializer.initialize_repository.side_effect = (
            lambda *args, **kwargs: call_order.append("git")
        )

        use_case.execute(valid_input)

        assert call_order == ["cleaner", "git"]

    def test_format_script_runner_called(
        self,
        use_case: GenerateProjectUseCase,
        valid_input: GenerateProjectInput,
    ) -> None:
        use_case.execute(valid_input)

        use_case._format_script_runner.run.assert_called_once_with(valid_input.destination)


class TestArtifactCleanerIntegration:
    @pytest.fixture
    def template_fetcher_with_artifacts(self, tmp_path: Path) -> Mock:
        fetcher = Mock()

        def create_template_with_artifacts(url, destination, use_cache=False):
            destination.mkdir(parents=True, exist_ok=True)

            settings_file = destination / "settings.gradle"
            settings_file.write_text("rootProject.name = 'arinfra'\n", encoding="utf-8")

            build_gradle = destination / "build.gradle"
            build_gradle.write_text("group = 'com.example'\nversion = '0.0.1'\n", encoding="utf-8")

            github_dir = destination / ".github"
            github_dir.mkdir()
            (github_dir / "dependabot.yml").write_text("version: 2")
            (github_dir / "CODEOWNERS").write_text("* @owner")
            (destination / "readme.md").write_text("# README")
            (destination / "licence").write_text("MIT License")
            (destination / "contributing.md").write_text("# Contributing")
            (destination / "security.md").write_text("# Security")
            (destination / "code_of_conduct.md").write_text("# Code of Conduct")
            (destination / "ar-infra-logo.png").write_bytes(b"fake image")

            return "com.example.arinfra"

        fetcher.fetch.side_effect = create_template_with_artifacts
        return fetcher

    @pytest.fixture
    def feature_manager_simple(self) -> Mock:
        manager = Mock()
        manager.get_feature_dependencies.return_value = []
        return manager

    @pytest.fixture
    def gradle_writer_simple(self) -> Mock:
        return Mock()

    @pytest.fixture
    def package_renamer_simple(self) -> Mock:
        return Mock()

    def test_development_artifacts_are_removed_end_to_end(
        self,
        template_fetcher_with_artifacts: Mock,
        feature_manager_simple: Mock,
        gradle_writer_simple: Mock,
        package_renamer_simple: Mock,
        tmp_path: Path,
    ) -> None:
        fake_git_initializer = Mock()
        fake_annotation_writer = Mock()

        use_case = GenerateProjectUseCase(
            template_fetcher=template_fetcher_with_artifacts,
            feature_manager=feature_manager_simple,
            gradle_writer=gradle_writer_simple,
            package_renamer=package_renamer_simple,
            git_initializer=fake_git_initializer,
            annotation_writer=fake_annotation_writer,
            artifact_cleaner=None,  # Let it create a real cleaner
        )

        input_dto = GenerateProjectInput(
            group_id=GroupId("dev.razafindratelo"),
            artifact_id=ArtifactId("backend-api"),
            version=Version("1.0.0"),
            destination=tmp_path / "my-project",
            enabled_features=set(),
            template_url="https://github.com/Abega1642/ar-infra-template.git",
            use_template_cache=False,
        )

        result = use_case.execute(input_dto)

        assert result.success is True

        project_path = input_dto.destination
        assert not (project_path / ".github" / "dependabot.yml").exists()
        assert not (project_path / ".github" / "CODEOWNERS").exists()
        assert not (project_path / ".github").exists()  # Empty dir removed
        assert not (project_path / "readme.md").exists()
        assert not (project_path / "licence").exists()
        assert not (project_path / "contributing.md").exists()
        assert not (project_path / "security.md").exists()
        assert not (project_path / "code_of_conduct.md").exists()
        assert not (project_path / "ar-infra-logo.png").exists()

        assert (project_path / "build.gradle").exists()
        assert (project_path / "settings.gradle").exists()

    def test_partial_artifact_removal_succeeds(
        self,
        feature_manager_simple: Mock,
        gradle_writer_simple: Mock,
        package_renamer_simple: Mock,
        tmp_path: Path,
    ) -> None:
        fetcher = Mock()

        def create_partial_template(url, destination, use_cache=False):
            destination.mkdir(parents=True, exist_ok=True)
            (destination / "build.gradle").write_text("group = 'com.example'\n", encoding="utf-8")
            (destination / "settings.gradle").write_text(
                "rootProject.name = 'app'\n", encoding="utf-8"
            )
            (destination / "readme.md").write_text("# README")
            (destination / "licence").write_text("MIT")
            return "com.example.arinfra"

        fetcher.fetch.side_effect = create_partial_template

        fake_git_initializer = Mock()
        fake_annotation_writer = Mock()

        use_case = GenerateProjectUseCase(
            template_fetcher=fetcher,
            feature_manager=feature_manager_simple,
            gradle_writer=gradle_writer_simple,
            package_renamer=package_renamer_simple,
            git_initializer=fake_git_initializer,
            annotation_writer=fake_annotation_writer,
            artifact_cleaner=None,
        )

        input_dto = GenerateProjectInput(
            group_id=GroupId("dev.razafindratelo"),
            artifact_id=ArtifactId("backend-api"),
            version=Version("1.0.0"),
            destination=tmp_path / "my-project",
            enabled_features=set(),
            template_url="https://github.com/Abega1642/ar-infra-template.git",
            use_template_cache=False,
        )

        result = use_case.execute(input_dto)

        assert result.success is True

        project_path = input_dto.destination
        assert not (project_path / "readme.md").exists()
        assert not (project_path / "licence").exists()

        assert (project_path / "build.gradle").exists()
        assert (project_path / "settings.gradle").exists()

    def test_use_case_creates_cleaner_when_not_provided(
        self,
        template_fetcher_with_artifacts: Mock,
        feature_manager_simple: Mock,
        gradle_writer_simple: Mock,
        package_renamer_simple: Mock,
        tmp_path: Path,
    ) -> None:
        fake_git_initializer = Mock()
        fake_annotation_writer = Mock()

        use_case = GenerateProjectUseCase(
            template_fetcher=template_fetcher_with_artifacts,
            feature_manager=feature_manager_simple,
            gradle_writer=gradle_writer_simple,
            package_renamer=package_renamer_simple,
            git_initializer=fake_git_initializer,
            annotation_writer=fake_annotation_writer,
            artifact_cleaner=None,
        )

        input_dto = GenerateProjectInput(
            group_id=GroupId("dev.razafindratelo"),
            artifact_id=ArtifactId("backend-api"),
            version=Version("1.0.0"),
            destination=tmp_path / "my-project",
            enabled_features=set(),
            template_url="https://github.com/Abega1642/ar-infra-template.git",
            use_template_cache=False,
        )

        with patch(
            "src.ar_infra.application.use_cases.generate_project_use_case.DevelopmentArtifactCleaner"
        ) as mock_cleaner_class:
            mock_cleaner_instance = Mock()
            mock_cleaner_instance.clean.return_value = 8
            mock_cleaner_instance.clean_empty_parent_directories.return_value = 1
            mock_cleaner_class.return_value = mock_cleaner_instance

            result = use_case.execute(input_dto)

            assert result.success is True
            mock_cleaner_class.assert_called_with(input_dto.destination)
            mock_cleaner_instance.clean.assert_called_once()
            assert mock_cleaner_instance.clean_empty_parent_directories.call_count == 2
