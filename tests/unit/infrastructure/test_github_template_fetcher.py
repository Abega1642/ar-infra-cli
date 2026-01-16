"""Tests for GitHubTemplateFetcher."""

import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import git.exc
import pytest

from src.ar_infra.infrastructure.template.exception import (
    InvalidTemplateError,
    SecurityViolationError,
    TemplateFetchError,
)
from src.ar_infra.infrastructure.template.github_template_fetcher import (
    GitHubTemplateFetcher,
)
from src.ar_infra.properties import TEMPLATE_VERSION


@pytest.fixture
def fetcher() -> GitHubTemplateFetcher:
    return GitHubTemplateFetcher()


@pytest.fixture
def valid_template_structure(tmp_path: Path) -> Path:
    template_dir = tmp_path / "valid_template"
    template_dir.mkdir()

    (template_dir / "build.gradle").write_text("group = 'com.example'\n")
    (template_dir / "settings.gradle").write_text("rootProject.name = 'arinfra'\n")

    src_main_java = template_dir / "src" / "main" / "java" / "com" / "example" / "arinfra"
    src_main_java.mkdir(parents=True)
    (src_main_java / "Application.java").write_text("package com.example.arinfra;\n")

    return template_dir


class TestFetchTemplate:
    @patch(
        "src.ar_infra.infrastructure.template.github_template_fetcher.GitHubTemplateFetcher._tag_exists_in_remote"
    )
    @patch("git.Repo.clone_from")
    @patch("tempfile.mkdtemp")
    def test_fetch_template_from_github_with_tag(
        self,
        mock_mkdtemp: Mock,
        mock_clone: Mock,
        mock_tag_exists: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
        valid_template_structure: Path,
    ) -> None:
        url = "https://github.com/user/ar-infra.git"
        destination = tmp_path / "template"
        temp_dir = tmp_path / "temp_clone"

        mock_mkdtemp.return_value = str(temp_dir)
        mock_tag_exists.return_value = True

        def mock_clone_side_effect(url: str, dest: str, branch: str, depth: int) -> None:
            shutil.copytree(valid_template_structure, dest)

        mock_clone.side_effect = mock_clone_side_effect

        result = fetcher.fetch(url, destination)

        assert result == "com.example.arinfra"
        assert destination.exists()
        assert (destination / "build.gradle").exists()
        mock_tag_exists.assert_called_once_with(url, TEMPLATE_VERSION)
        mock_clone.assert_called_once_with(url, str(temp_dir), branch=TEMPLATE_VERSION, depth=1)

    @patch(
        "src.ar_infra.infrastructure.template.github_template_fetcher.GitHubTemplateFetcher._tag_exists_in_remote"
    )
    @patch("git.Repo.clone_from")
    @patch("tempfile.mkdtemp")
    def test_fetch_template_falls_back_when_tag_not_found(
        self,
        mock_mkdtemp: Mock,
        mock_clone: Mock,
        mock_tag_exists: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
        valid_template_structure: Path,
    ) -> None:
        """Should fall back to default branch when tag doesn't exist."""
        url = "https://github.com/user/ar-infra.git"
        destination = tmp_path / "template"
        temp_dir = tmp_path / "temp_clone"

        mock_mkdtemp.return_value = str(temp_dir)
        mock_tag_exists.return_value = False

        def mock_clone_side_effect(url: str, dest: str, depth: int) -> None:
            shutil.copytree(valid_template_structure, dest)

        mock_clone.side_effect = mock_clone_side_effect

        result = fetcher.fetch(url, destination)

        assert result == "com.example.arinfra"
        assert destination.exists()
        mock_tag_exists.assert_called_once_with(url, TEMPLATE_VERSION)
        # Should clone without branch parameter when tag doesn't exist
        mock_clone.assert_called_once_with(url, str(temp_dir), depth=1)

    @patch("git.Repo.clone_from")
    def test_use_cached_template(
        self,
        mock_clone: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
        valid_template_structure: Path,
    ) -> None:
        url = "https://github.com/user/ar-infra.git"
        destination = tmp_path / "template"
        shutil.copytree(valid_template_structure, destination)

        result = fetcher.fetch(url, destination, use_cache=True)

        assert result == "com.example.arinfra"
        mock_clone.assert_not_called()

    @patch(
        "src.ar_infra.infrastructure.template.github_template_fetcher.GitHubTemplateFetcher._tag_exists_in_remote"
    )
    @patch("git.Repo.clone_from")
    @patch("tempfile.mkdtemp")
    def test_force_refetch_ignores_cache(
        self,
        mock_mkdtemp: Mock,
        mock_clone: Mock,
        mock_tag_exists: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
        valid_template_structure: Path,
    ) -> None:
        url = "https://github.com/user/ar-infra.git"
        destination = tmp_path / "template"
        temp_dir = tmp_path / "temp_clone"

        # Create existing destination
        shutil.copytree(valid_template_structure, destination)

        mock_mkdtemp.return_value = str(temp_dir)
        mock_tag_exists.return_value = True

        def mock_clone_side_effect(url: str, dest: str, branch: str, depth: int) -> None:
            shutil.copytree(valid_template_structure, dest)

        mock_clone.side_effect = mock_clone_side_effect

        result = fetcher.fetch(url, destination, use_cache=False)

        assert result == "com.example.arinfra"
        mock_clone.assert_called_once()

    @patch(
        "src.ar_infra.infrastructure.template.github_template_fetcher.GitHubTemplateFetcher._tag_exists_in_remote"
    )
    @patch("git.Repo.clone_from")
    @patch("tempfile.mkdtemp")
    def test_cleanup_temp_dir_on_clone_error(
        self,
        mock_mkdtemp: Mock,
        mock_clone: Mock,
        mock_tag_exists: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
    ) -> None:
        """Should clean up temporary directory when clone fails."""
        url = "https://github.com/user/repo.git"
        destination = tmp_path / "template"
        temp_dir = tmp_path / "temp_clone"
        temp_dir.mkdir()

        mock_mkdtemp.return_value = str(temp_dir)
        mock_tag_exists.return_value = True
        mock_clone.side_effect = OSError("Clone failed")

        with pytest.raises(TemplateFetchError):
            fetcher.fetch(url, destination)

        assert not temp_dir.exists()
        assert not destination.exists()

    @patch(
        "src.ar_infra.infrastructure.template.github_template_fetcher.GitHubTemplateFetcher._tag_exists_in_remote"
    )
    @patch("git.Repo.clone_from")
    @patch("tempfile.mkdtemp")
    def test_cleanup_temp_dir_on_validation_error(
        self,
        mock_mkdtemp: Mock,
        mock_clone: Mock,
        mock_tag_exists: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
    ) -> None:
        url = "https://github.com/user/repo.git"
        destination = tmp_path / "template"
        temp_dir = tmp_path / "temp_clone"

        mock_mkdtemp.return_value = str(temp_dir)
        mock_tag_exists.return_value = True

        def mock_clone_invalid(url: str, dest: str, branch: str, depth: int) -> None:
            Path(dest).mkdir(parents=True, exist_ok=True)
            (Path(dest) / "src" / "main" / "java").mkdir(parents=True)

        mock_clone.side_effect = mock_clone_invalid

        with pytest.raises(InvalidTemplateError):
            fetcher.fetch(url, destination)

        assert not temp_dir.exists()
        assert not destination.exists()


class TestTagExistsCheck:
    @patch("git.cmd.Git")
    def test_tag_exists_in_remote_returns_true_when_tag_found(
        self, mock_git_class: Mock, fetcher: GitHubTemplateFetcher
    ) -> None:
        mock_git_instance = Mock()
        mock_git_class.return_value = mock_git_instance
        mock_git_instance.ls_remote.return_value = "abc123\trefs/tags/v0.1.0"

        result = fetcher._tag_exists_in_remote("https://github.com/user/repo.git", "v0.1.0")

        assert result is True
        mock_git_instance.ls_remote.assert_called_once_with(
            "--tags", "https://github.com/user/repo.git", "v0.1.0"
        )

    @patch("git.cmd.Git")
    def test_tag_exists_in_remote_returns_false_when_tag_not_found(
        self, mock_git_class: Mock, fetcher: GitHubTemplateFetcher
    ) -> None:
        mock_git_instance = Mock()
        mock_git_class.return_value = mock_git_instance
        mock_git_instance.ls_remote.return_value = ""

        result = fetcher._tag_exists_in_remote("https://github.com/user/repo.git", "v0.1.0")

        assert result is False

    @patch("git.cmd.Git")
    def test_tag_exists_in_remote_returns_false_on_git_error(
        self, mock_git_class: Mock, fetcher: GitHubTemplateFetcher
    ) -> None:
        mock_git_instance = Mock()
        mock_git_class.return_value = mock_git_instance
        mock_git_instance.ls_remote.side_effect = git.exc.GitCommandError("ls-remote", 128)

        result = fetcher._tag_exists_in_remote("https://github.com/user/repo.git", "v0.1.0")

        assert result is False


class TestURLValidation:
    def test_accept_valid_github_urls(self, fetcher: GitHubTemplateFetcher) -> None:
        valid_urls = [
            "https://github.com/user/repo.git",
            "https://github.com/org/project",
            "git@github.com:user/repo.git",
        ]

        for url in valid_urls:
            fetcher._validate_url(url)  # Should not raise

    def test_reject_non_github_urls(self, fetcher: GitHubTemplateFetcher) -> None:
        invalid_urls = [
            "https://gitlab.com/user/repo.git",
            "https://bitbucket.org/user/repo",
            "https://example.com/repo",
        ]

        for url in invalid_urls:
            with pytest.raises(SecurityViolationError, match="Only GitHub URLs are allowed"):
                fetcher._validate_url(url)

    def test_reject_malicious_urls(self, fetcher: GitHubTemplateFetcher) -> None:
        malicious_urls = [
            "file:///etc/passwd",
            "http://localhost:8080/repo",
            "http://127.0.0.1/repo",
            "http://169.254.169.254/metadata",
            "ftp://evil.com/repo",
        ]

        for url in malicious_urls:
            with pytest.raises(SecurityViolationError):
                fetcher._validate_url(url)


class TestTemplateValidation:
    def test_validate_correct_template_structure(
        self, fetcher: GitHubTemplateFetcher, valid_template_structure: Path
    ) -> None:
        fetcher._validate_template_structure(valid_template_structure)

    def test_reject_template_without_build_gradle(
        self, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "src" / "main" / "java").mkdir(parents=True)

        with pytest.raises(InvalidTemplateError, match=r"build\.gradle not found"):
            fetcher._validate_template_structure(template_dir)

    def test_reject_template_without_src_structure(
        self, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        template_dir = tmp_path / "template"
        template_dir.mkdir()
        (template_dir / "build.gradle").write_text("test")

        with pytest.raises(InvalidTemplateError, match=r"src/main/java directory not found"):
            fetcher._validate_template_structure(template_dir)


class TestPackageDetection:
    def test_detect_placeholder_package(
        self, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        template_dir = tmp_path / "template"
        src_dir = template_dir / "src" / "main" / "java" / "com" / "example" / "arinfra"
        src_dir.mkdir(parents=True)
        (src_dir / "Application.java").write_text("package com.example.arinfra;\n")

        result = fetcher._detect_placeholder_package(template_dir)

        assert result == "com.example.arinfra"

    def test_detect_deep_nested_package(
        self, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        template_dir = tmp_path / "template"
        src_dir = template_dir / "src" / "main" / "java" / "com" / "mycompany" / "project" / "app"
        src_dir.mkdir(parents=True)
        (src_dir / "Main.java").write_text("package com.mycompany.project.app;\n")

        result = fetcher._detect_placeholder_package(template_dir)

        assert result == "com.mycompany.project.app"

    def test_reject_template_without_package(
        self, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        template_dir = tmp_path / "template"
        (template_dir / "src" / "main" / "java").mkdir(parents=True)

        with pytest.raises(InvalidTemplateError, match="Could not detect placeholder package"):
            fetcher._detect_placeholder_package(template_dir)


class TestErrorHandling:
    @patch(
        "src.ar_infra.infrastructure.template.github_template_fetcher.GitHubTemplateFetcher._tag_exists_in_remote"
    )
    @patch("git.Repo.clone_from")
    @patch("tempfile.mkdtemp")
    def test_provide_helpful_error_for_network_issues(
        self,
        mock_mkdtemp: Mock,
        mock_clone: Mock,
        mock_tag_exists: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
    ) -> None:
        url = "https://github.com/user/repo.git"
        destination = tmp_path / "template"
        temp_dir = tmp_path / "temp_clone"

        mock_mkdtemp.return_value = str(temp_dir)
        mock_tag_exists.return_value = True

        error = git.exc.GitCommandError("clone", 128)
        error.stderr = "fatal: could not resolve host github.com"
        mock_clone.side_effect = error

        with pytest.raises(TemplateFetchError, match="Network/DNS issue"):
            fetcher.fetch(url, destination)

    @patch(
        "src.ar_infra.infrastructure.template.github_template_fetcher.GitHubTemplateFetcher._tag_exists_in_remote"
    )
    @patch("git.Repo.clone_from")
    @patch("tempfile.mkdtemp")
    def test_provide_helpful_error_for_permission_issues(
        self,
        mock_mkdtemp: Mock,
        mock_clone: Mock,
        mock_tag_exists: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
    ) -> None:
        url = "https://github.com/user/repo.git"
        destination = tmp_path / "template"
        temp_dir = tmp_path / "temp_clone"

        mock_mkdtemp.return_value = str(temp_dir)
        mock_tag_exists.return_value = True

        error = git.exc.GitCommandError("clone", 128)
        error.stderr = "fatal: permission denied"
        mock_clone.side_effect = error

        with pytest.raises(TemplateFetchError, match="Permission issue"):
            fetcher.fetch(url, destination)
