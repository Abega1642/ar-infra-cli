"""Tests for GitHubTemplateFetcher."""

import shutil
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.ar_infra.infrastructure.template.exception import (
    InvalidTemplateError,
    SecurityViolationError,
    TemplateFetchError,
)
from src.ar_infra.infrastructure.template.github_template_fetcher import (
    GitHubTemplateFetcher,
)


class TestGitHubTemplateFetcher:
    """Test suite for GitHubTemplateFetcher."""

    @pytest.fixture
    def fetcher(self) -> GitHubTemplateFetcher:
        return GitHubTemplateFetcher()

    @pytest.fixture
    def valid_template_structure(self, tmp_path: Path) -> Path:
        template_dir = tmp_path / "valid_template"
        template_dir.mkdir()

        (template_dir / "build.gradle").write_text("group = 'com.example'\n")
        (template_dir / "settings.gradle").write_text("rootProject.name = 'arinfra'\n")

        src_main_java = template_dir / "src" / "main" / "java" / "com" / "example" / "arinfra"
        src_main_java.mkdir(parents=True)
        (src_main_java / "Application.java").write_text("package com.example.arinfra;\n")

        return template_dir

    @patch("git.Repo.clone_from")
    def test_fetch_template_from_github(
        self,
        mock_clone: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
        valid_template_structure: Path,
    ) -> None:
        url = "https://github.com/user/ar-infra.git"
        destination = tmp_path / "template"

        def mock_clone_side_effect(url: str, dest: str, depth: int) -> None:
            shutil.copytree(valid_template_structure, dest)

        mock_clone.side_effect = mock_clone_side_effect

        fetcher.fetch(url, destination)

        mock_clone.assert_called_once_with(url, str(destination), depth=1)

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

        fetcher.fetch(url, destination, use_cache=True)

        mock_clone.assert_not_called()

    @patch("git.Repo.clone_from")
    def test_force_refetch_ignores_cache(
        self,
        mock_clone: Mock,
        fetcher: GitHubTemplateFetcher,
        tmp_path: Path,
        valid_template_structure: Path,
    ) -> None:
        url = "https://github.com/user/ar-infra.git"
        destination = tmp_path / "template"
        shutil.copytree(valid_template_structure, destination)

        def mock_clone_side_effect(url: str, dest: str, depth: int) -> None:
            dest_path = Path(dest)
            if dest_path.exists():
                shutil.rmtree(dest_path)
            shutil.copytree(valid_template_structure, dest)

        mock_clone.side_effect = mock_clone_side_effect

        fetcher.fetch(url, destination, use_cache=False)

        mock_clone.assert_called_once()

    def test_validate_template_structure(
        self, fetcher: GitHubTemplateFetcher, valid_template_structure: Path
    ) -> None:
        fetcher._validate_template_structure(valid_template_structure)

    def test_reject_template_without_build_gradle(
        self, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        template_dir = tmp_path / "template"
        template_dir.mkdir()

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

    def test_reject_malicious_urls(self, fetcher: GitHubTemplateFetcher, tmp_path: Path) -> None:
        malicious_urls = [
            "file:///etc/passwd",
            "http://localhost:8080/repo",
            "http://127.0.0.1/repo",
            "http://169.254.169.254/metadata",
            "ftp://evil.com/repo",
        ]

        for malicious_url in malicious_urls:
            with pytest.raises(SecurityViolationError):
                fetcher.fetch(malicious_url, tmp_path)

    def test_validate_github_url(self, fetcher: GitHubTemplateFetcher) -> None:
        valid_urls = [
            "https://github.com/user/repo.git",
            "https://github.com/org/project",
            "git@github.com:user/repo.git",
        ]

        for valid_url in valid_urls:
            fetcher._validate_url(valid_url)

    def test_reject_non_github_urls(self, fetcher: GitHubTemplateFetcher) -> None:
        invalid_urls = [
            "https://gitlab.com/user/repo.git",
            "https://bitbucket.org/user/repo",
            "https://example.com/repo",
        ]

        for invalid_url in invalid_urls:
            with pytest.raises(SecurityViolationError, match="Only GitHub URLs are allowed"):
                fetcher._validate_url(invalid_url)

    @patch("git.Repo.clone_from")
    def test_handle_clone_error(
        self, mock_clone: Mock, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        mock_clone.side_effect = Exception("Clone failed")
        url = "https://github.com/user/repo.git"
        destination = tmp_path / "template"

        with pytest.raises(TemplateFetchError, match="Failed to fetch template"):
            fetcher.fetch(url, destination)

    def test_detect_placeholder_package(
        self, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        template_dir = tmp_path / "template"
        src_dir = template_dir / "src" / "main" / "java" / "com" / "example" / "arinfra"
        src_dir.mkdir(parents=True)
        (src_dir / "Application.java").write_text("package com.example.arinfra;\n")

        result = fetcher._detect_placeholder_package(template_dir)
        assert result == "com.example.arinfra"

    def test_detect_placeholder_package_not_found(
        self, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        template_dir = tmp_path / "template"
        (template_dir / "src" / "main" / "java").mkdir(parents=True)

        with pytest.raises(InvalidTemplateError, match="Could not detect placeholder package"):
            fetcher._detect_placeholder_package(template_dir)

    @patch("git.Repo.clone_from")
    def test_cleanup_on_error(
        self, mock_clone: Mock, fetcher: GitHubTemplateFetcher, tmp_path: Path
    ) -> None:
        mock_clone.side_effect = Exception("Clone failed")
        url = "https://github.com/user/repo.git"
        destination = tmp_path / "template"

        with pytest.raises(TemplateFetchError):
            fetcher.fetch(url, destination)

        assert not destination.exists()
