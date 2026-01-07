"""Tests for the DevelopmentArtifactCleaner class."""

import platform
import re
from pathlib import Path

import pytest

from src.ar_infra.infrastructure.template.development_artifact_remover import (
    DevelopmentArtifactCleaner,
)


@pytest.fixture
def temp_project(tmp_path: Path) -> Path:
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    (project_root / ".github").mkdir()
    (project_root / ".github" / "dependabot.yml").write_text("version: 2")
    (project_root / ".github" / "CODEOWNERS").write_text("* @owner")
    (project_root / "ar-infra-logo.png").write_bytes(b"fake image data")
    (project_root / "code_of_conduct.md").write_text("# Code of Conduct")
    (project_root / "readme.md").write_text("# README")
    (project_root / "security.md").write_text("# Security")
    (project_root / "contributing.md").write_text("# Contributing")
    (project_root / "licence").write_text("MIT License")

    # Create some files that should remain
    (project_root / "main.py").write_text("print('hello')")
    (project_root / "config.json").write_text("{}")

    return project_root


@pytest.fixture
def cleaner(temp_project: Path) -> DevelopmentArtifactCleaner:
    return DevelopmentArtifactCleaner(temp_project)


class TestDevelopmentArtifactCleanerInitialization:
    def test_init_with_valid_directory(self, temp_project: Path) -> None:
        cleaner = DevelopmentArtifactCleaner(temp_project)
        assert cleaner._project_root == temp_project.resolve()

    def test_init_with_nonexistent_directory(self, tmp_path: Path) -> None:
        nonexistent = tmp_path / "does_not_exist"
        with pytest.raises(ValueError, match="does not exist"):
            DevelopmentArtifactCleaner(nonexistent)

    def test_init_with_file_instead_of_directory(self, tmp_path: Path) -> None:
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        with pytest.raises(ValueError, match="not a directory"):
            DevelopmentArtifactCleaner(file_path)


class TestPathValidation:
    def test_validate_path_within_project(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        valid_path = temp_project / "readme.md"
        validated = cleaner._validate_path(valid_path)
        assert validated == valid_path.resolve()

    def test_validate_path_prevents_traversal_absolute(
        self, cleaner: DevelopmentArtifactCleaner, tmp_path: Path
    ) -> None:
        outside_path = tmp_path / "outside.txt"
        with pytest.raises(ValueError, match="outside project root"):
            cleaner._validate_path(outside_path)

    def test_validate_path_prevents_traversal_relative(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        traversal_path = temp_project / ".." / ".." / "etc" / "passwd"
        with pytest.raises(ValueError, match="outside project root"):
            cleaner._validate_path(traversal_path)

    def test_validate_path_prevents_symlink_escape(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path, tmp_path: Path
    ) -> None:
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        symlink_path = temp_project / "evil_link"

        try:
            symlink_path.symlink_to(outside_dir)
            with pytest.raises(ValueError, match="outside project root"):
                cleaner._validate_path(symlink_path)
        except OSError:
            # Symlink creation might fail on some systems
            pytest.skip("Symlink creation not supported")


class TestRemoveSingleArtifact:
    def test_remove_existing_file(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        assert (temp_project / "readme.md").exists()
        result = cleaner.remove_artifact("readme.md")
        assert result is True
        assert not (temp_project / "readme.md").exists()

    def test_remove_nonexistent_file(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        result = cleaner.remove_artifact("nonexistent.md")
        assert result is False

    def test_remove_file_in_subdirectory(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        assert (temp_project / ".github" / "dependabot.yml").exists()
        result = cleaner.remove_artifact(".github/dependabot.yml")
        assert result is True
        assert not (temp_project / ".github" / "dependabot.yml").exists()

    def test_remove_entire_directory(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        github_dir = temp_project / ".github"
        assert github_dir.exists()
        assert (github_dir / "dependabot.yml").exists()
        assert (github_dir / "CODEOWNERS").exists()

        result = cleaner.remove_artifact(".github")
        assert result is True
        assert not github_dir.exists()

    def test_remove_nested_directory_structure(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        nested_dir = temp_project / "a" / "b" / "c"
        nested_dir.mkdir(parents=True)
        (nested_dir / "file.txt").write_text("content")

        result = cleaner.remove_artifact("a")
        assert result is True
        assert not (temp_project / "a").exists()

    def test_remove_with_path_traversal_attempt(self, cleaner: DevelopmentArtifactCleaner) -> None:
        with pytest.raises(ValueError, match="outside project root"):
            cleaner.remove_artifact("../../etc/passwd")


class TestCleanMultipleArtifacts:
    def test_clean_default_artifacts(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        removed_count = cleaner.clean()

        assert not (temp_project / ".github" / "dependabot.yml").exists()
        assert not (temp_project / ".github" / "CODEOWNERS").exists()
        assert not (temp_project / "ar-infra-logo.png").exists()
        assert not (temp_project / "code_of_conduct.md").exists()
        assert not (temp_project / "readme.md").exists()
        assert not (temp_project / "security.md").exists()
        assert not (temp_project / "contributing.md").exists()
        assert not (temp_project / "licence").exists()

        assert (temp_project / "main.py").exists()
        assert (temp_project / "config.json").exists()

        assert removed_count == 8

    def test_clean_custom_artifacts(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        custom_artifacts = ["readme.md", "licence"]
        removed_count = cleaner.clean(artifacts=custom_artifacts)

        assert not (temp_project / "readme.md").exists()
        assert not (temp_project / "licence").exists()
        assert (temp_project / "security.md").exists()  # Not in custom list
        assert removed_count == 2

    def test_clean_with_nonexistent_artifacts(self, cleaner: DevelopmentArtifactCleaner) -> None:
        artifacts = ["readme.md", "nonexistent1.txt", "nonexistent2.txt"]
        removed_count = cleaner.clean(artifacts=artifacts)
        assert removed_count == 1  # Only readme.md existed

    def test_clean_empty_list(self, cleaner: DevelopmentArtifactCleaner) -> None:
        removed_count = cleaner.clean(artifacts=[])
        assert removed_count == 0


class TestCleanEmptyParentDirectories:
    def test_clean_empty_parents_after_file_removal(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        cleaner.remove_artifact(".github/dependabot.yml")
        cleaner.remove_artifact(".github/CODEOWNERS")

        assert (temp_project / ".github").exists()

        removed_count = cleaner.clean_empty_parent_directories(".github/dependabot.yml")
        assert removed_count == 1
        assert not (temp_project / ".github").exists()

    def test_clean_empty_parents_nested(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        nested_path = temp_project / "a" / "b" / "c" / "file.txt"
        nested_path.parent.mkdir(parents=True)
        nested_path.write_text("content")

        cleaner.remove_artifact("a/b/c/file.txt")
        removed_count = cleaner.clean_empty_parent_directories("a/b/c/file.txt")

        assert removed_count == 3
        assert not (temp_project / "a").exists()

    def test_clean_empty_parents_stops_at_non_empty(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        nested_path = temp_project / "a" / "b" / "file.txt"
        nested_path.parent.mkdir(parents=True)
        nested_path.write_text("content")
        (temp_project / "a" / "keeper.txt").write_text("keep me")

        cleaner.remove_artifact("a/b/file.txt")
        removed_count = cleaner.clean_empty_parent_directories("a/b/file.txt")

        assert removed_count == 1
        assert (temp_project / "a").exists()
        assert (temp_project / "a" / "keeper.txt").exists()

    def test_clean_empty_parents_does_not_remove_project_root(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        file_path = temp_project / "file.txt"
        file_path.write_text("content")

        cleaner.remove_artifact("file.txt")
        removed_count = cleaner.clean_empty_parent_directories("file.txt")

        assert removed_count == 0
        assert temp_project.exists()


class TestErrorHandling:
    @pytest.mark.skipif(platform.system() == "Windows", reason="Windows-specific tests")
    def test_remove_artifact_with_permission_error(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        if not hasattr(Path, "chmod"):
            pytest.skip("chmod not available on this platform")

        protected_file = temp_project / "protected.txt"
        protected_file.write_text("content")

        temp_project.chmod(0o444)

        try:
            error = re.escape(f"[Errno 13] Permission denied: '{protected_file}'")
            with pytest.raises(OSError, match=error):
                cleaner.remove_artifact("protected.txt")
        finally:
            temp_project.chmod(0o755)


class TestIntegrationScenarios:
    def test_full_cleanup_workflow(self, temp_project: Path) -> None:
        cleaner = DevelopmentArtifactCleaner(temp_project)

        removed_count = cleaner.clean()
        assert removed_count == 8

        cleaner.clean_empty_parent_directories(".github/dependabot.yml")

        assert not (temp_project / ".github").exists()
        assert not (temp_project / "readme.md").exists()
        assert (temp_project / "main.py").exists()
        assert (temp_project / "config.json").exists()

        removed_count_2 = cleaner.clean()
        assert removed_count_2 == 0

    def test_cleanup_with_mixed_success_and_failure(
        self, cleaner: DevelopmentArtifactCleaner, temp_project: Path
    ) -> None:
        (temp_project / "readme.md").unlink()
        (temp_project / "licence").unlink()

        removed_count = cleaner.clean()

        assert removed_count == 6
        assert not (temp_project / "security.md").exists()
        assert not (temp_project / "contributing.md").exists()
