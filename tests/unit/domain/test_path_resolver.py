"""Unit tests for path security validation."""

import platform
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from src.ar_infra.domain.entities.path_resolver import (
    DangerousPathError,
    PathSecurityError,
    PathSecurityValidator,
    PathTraversalError,
    SafeProjectPathResolver,
)


class TestPathSecurityValidator:
    """Test suite for PathSecurityValidator."""

    @pytest.fixture
    def validator(self) -> PathSecurityValidator:
        """Create a validator instance."""
        return PathSecurityValidator()

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, Any, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_validate_valid_destination_path(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        """Test validation of a valid destination path."""
        result = validator.validate_destination_path(str(temp_dir))
        assert result == temp_dir.resolve()
        assert result.is_absolute()

    def test_validate_user_home_expansion(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        """Test that ~ is properly expanded to user home."""
        # Create a test directory in user's home that we can safely test with
        home = Path.home()
        test_dir = home / "test_ar_infra_temp"
        test_dir.mkdir(exist_ok=True)

        try:
            result = validator.validate_destination_path("~/test_ar_infra_temp")
            assert "~" not in str(result)
            assert result.is_absolute()
            assert result == test_dir.resolve()
        finally:
            test_dir.rmdir()

    def test_reject_empty_path(self, validator: PathSecurityValidator) -> None:
        """Test that empty paths are rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            validator.validate_destination_path("")

        with pytest.raises(ValueError, match="cannot be empty"):
            validator.validate_destination_path("   ")

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific path validation")
    def test_reject_root_directory_unix(self, validator: PathSecurityValidator) -> None:
        """Test that root directory is rejected on Unix systems."""
        with pytest.raises(DangerousPathError, match="system directory"):
            validator.validate_destination_path("/")

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific path validation")
    def test_reject_system_directories_unix(self, validator: PathSecurityValidator) -> None:
        """Test that system directories are rejected on Unix."""
        # Test exact matches of dangerous paths
        dangerous_paths = ["/etc", "/usr", "/var", "/sys"]

        for path in dangerous_paths:
            with pytest.raises(DangerousPathError, match="system directory"):
                validator.validate_destination_path(path)

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific path validation")
    def test_reject_subdirectories_of_system_paths(self, validator: PathSecurityValidator) -> None:
        """Test that subdirectories of system paths are rejected."""
        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("/etc/config")

        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("/bin/tools")

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific path validation")
    def test_allow_tmp_directory(self, validator: PathSecurityValidator) -> None:
        """Test that /tmp and user directories are allowed."""
        # /tmp should be allowed (not in dangerous paths)
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validator.validate_destination_path(tmpdir)
            assert result.is_absolute()

    def test_allow_user_home_directory(self, validator: PathSecurityValidator) -> None:
        """Test that user home directory is allowed."""
        home = Path.home()
        test_dir = home / "test_projects"
        test_dir.mkdir(exist_ok=True)

        try:
            result = validator.validate_destination_path(str(test_dir))
            assert result.is_absolute()
            assert result == test_dir.resolve()
        finally:
            test_dir.rmdir()

    def test_reject_path_traversal_patterns(self, validator: PathSecurityValidator) -> None:
        """Test that path traversal patterns are detected."""
        traversal_patterns = [
            "../../../etc",
            "/tmp/../../../etc",  # noqa: S108
            "foo/../../bar",
        ]

        for pattern in traversal_patterns:
            with pytest.raises(PathTraversalError, match="path traversal"):
                validator.validate_destination_path(pattern)

    @pytest.mark.skipif(
        platform.system() == "Windows", reason="Symlinks behave differently on Windows"
    )
    def test_reject_symlink_destination(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        """Test that symlinks are rejected as destination."""
        real_dir = temp_dir / "real"
        real_dir.mkdir()
        symlink = temp_dir / "link"
        symlink.symlink_to(real_dir)

        with pytest.raises(PathSecurityError, match="symbolic link"):
            validator.validate_destination_path(str(symlink))

    def test_validate_valid_project_directory_name(self, validator: PathSecurityValidator) -> None:
        """Test validation of valid project directory names."""
        valid_names = [
            "my-project",
            "my_project",
            "myproject123",
            "Project-Name-123",
        ]

        for name in valid_names:
            result = validator.validate_project_directory_name(name)
            assert result == name

    def test_reject_invalid_project_directory_names(self, validator: PathSecurityValidator) -> None:
        """Test rejection of invalid project directory names."""
        invalid_names = [
            "",
            "   ",
            "my/project",
            "my\\project",
            "../project",
            ".hidden",
            "project with spaces",
            "project@name",
            "project#name",
        ]

        for name in invalid_names:
            with pytest.raises(
                ValueError,
                match=r"(cannot be empty|path separators|cannot start with|can only contain)",
            ):
                validator.validate_project_directory_name(name)

    def test_reject_path_traversal_in_project_name(self, validator: PathSecurityValidator) -> None:
        """Test that path traversal in project name is rejected."""
        with pytest.raises(ValueError, match="path separators"):
            validator.validate_project_directory_name("../project")

        with pytest.raises(ValueError, match="path separators"):
            validator.validate_project_directory_name("foo/../bar")

    def test_reject_excessively_long_project_name(self, validator: PathSecurityValidator) -> None:
        """Test that excessively long names are rejected."""
        long_name = "a" * 256

        with pytest.raises(ValueError, match="too long"):
            validator.validate_project_directory_name(long_name)

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific path validation")
    def test_reject_windows_system_paths(self, validator: PathSecurityValidator) -> None:
        """Test that Windows system paths are rejected."""
        with pytest.raises(DangerousPathError, match="system directory"):
            validator.validate_destination_path("C:\\Windows")

    @pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific path validation")
    def test_reject_windows_system_subdirectories(self, validator: PathSecurityValidator) -> None:
        """Test that Windows system subdirectories are rejected."""
        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("C:\\Windows\\System32")


class TestSafeProjectPathResolver:
    """Test suite for SafeProjectPathResolver."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, Any, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_resolve_valid_project_path(self, temp_dir: Path) -> None:
        """Test resolution of a valid project path."""
        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="my-project",
        )

        result = resolver.resolve()
        expected = temp_dir / "my-project"

        assert result == expected.resolve()
        assert result.is_absolute()

    def test_reject_existing_project_directory(self, temp_dir: Path) -> None:
        """Test that existing project directories are rejected."""
        existing_dir = temp_dir / "existing-project"
        existing_dir.mkdir()

        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="existing-project",
        )

        with pytest.raises(FileExistsError, match="already exists"):
            resolver.resolve()

    def test_reject_nonexistent_destination(self, temp_dir: Path) -> None:
        """Test that non-existent destination is rejected."""
        nonexistent = temp_dir / "does-not-exist"

        resolver = SafeProjectPathResolver(
            destination_path=str(nonexistent),
            project_dir_name="my-project",
        )

        with pytest.raises(ValueError, match="does not exist"):
            resolver.resolve()

    def test_verify_path_containment(self, temp_dir: Path) -> None:
        """Test that project path is verified to be within destination."""
        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="valid-name",
        )

        result = resolver.resolve()

        # Verify result is actually under temp_dir
        if hasattr(result, "is_relative_to"):
            assert result.is_relative_to(temp_dir)
        else:
            # Python 3.8 compatibility
            try:
                result.relative_to(temp_dir)
            except ValueError:
                pytest.fail("Project path is not under destination")

    def test_reject_destination_file_not_directory(self, temp_dir: Path) -> None:
        """Test that file paths are rejected as destination."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("test")

        resolver = SafeProjectPathResolver(
            destination_path=str(file_path),
            project_dir_name="my-project",
        )

        with pytest.raises(ValueError, match="not a directory"):
            resolver.resolve()

    def test_check_existing_directory_not_exists(self, temp_dir: Path) -> None:
        """Test checking non-existent directory."""
        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="new-project",
        )

        exists, has_content = resolver.check_existing_directory()

        assert not exists
        assert not has_content

    def test_check_existing_directory_empty(self, temp_dir: Path) -> None:
        """Test checking existing but empty directory."""
        project_dir = temp_dir / "empty-project"
        project_dir.mkdir()

        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="empty-project",
        )

        exists, has_content = resolver.check_existing_directory()

        assert exists
        assert not has_content

    def test_check_existing_directory_with_content(self, temp_dir: Path) -> None:
        """Test checking existing directory with content."""
        project_dir = temp_dir / "full-project"
        project_dir.mkdir()
        (project_dir / "file.txt").write_text("content")

        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="full-project",
        )

        exists, has_content = resolver.check_existing_directory()

        assert exists
        assert has_content

    @pytest.mark.skipif(platform.system() == "Windows", reason="Unix-specific path validation")
    def test_reject_dangerous_system_path(self) -> None:
        """Test that dangerous system paths are rejected."""
        with pytest.raises(DangerousPathError):
            SafeProjectPathResolver(
                destination_path="/etc",
                project_dir_name="my-project",
            )

    def test_security_validator_integration(self, temp_dir: Path) -> None:
        """Test that custom security validator is used."""
        custom_validator = PathSecurityValidator()

        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="my-project",
            security_validator=custom_validator,
        )

        assert resolver._validator is custom_validator


class TestSecurityIntegration:
    """Integration tests for security features."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, Any, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_full_validation_flow(self, temp_dir: Path) -> None:
        """Test the complete validation flow."""
        destination = temp_dir / "projects"
        destination.mkdir()

        resolver = SafeProjectPathResolver(
            destination_path=str(destination),
            project_dir_name="my-secure-project",
        )

        project_path = resolver.resolve()

        assert project_path == (destination / "my-secure-project").resolve()
        assert project_path.parent == destination.resolve()
        assert not project_path.exists()

    def test_prevent_directory_escape(self, temp_dir: Path) -> None:
        """Test that directory escape attempts are prevented."""
        destination = temp_dir / "safe-zone"
        destination.mkdir()

        malicious_names = [
            "..",
            "../..",
            "foo/..",
        ]

        for name in malicious_names:
            with pytest.raises(ValueError, match="path separators"):
                SafeProjectPathResolver(
                    destination_path=str(destination),
                    project_dir_name=name,
                )

    def test_cyclomatic_complexity_reduction(self, temp_dir: Path) -> None:
        """Test that refactored code maintains functionality."""
        validator = PathSecurityValidator()

        result = validator.validate_destination_path(str(temp_dir))
        assert result == temp_dir.resolve()

        name = validator.validate_project_directory_name("my-project")
        assert name == "my-project"
