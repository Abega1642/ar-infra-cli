"""Unit tests for path security validation - Cross-platform."""

import os
import platform
import re
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from src.ar_infra.domain.entities.path_resolver import (
    DangerousPathError,
    PathSecurityError,
    PathSecurityValidator,
    SafeProjectPathResolver,
)


@pytest.fixture
def validator() -> PathSecurityValidator:
    return PathSecurityValidator()


@pytest.fixture
def temp_dir() -> Generator[Path, Any, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# ===>  Platform-Agnostic Tests


class TestPathSecurityValidatorCommon:
    def test_reject_empty_path(self, validator: PathSecurityValidator) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            validator.validate_destination_path("")

        with pytest.raises(ValueError, match="cannot be empty"):
            validator.validate_destination_path("   ")

    def test_validate_user_home_expansion(self, validator: PathSecurityValidator) -> None:
        """Test that ~ is properly expanded to user home."""
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

    def test_allow_user_home_directory(self, validator: PathSecurityValidator) -> None:
        home = Path.home()
        test_dir = home / "test_projects"
        test_dir.mkdir(exist_ok=True)

        try:
            result = validator.validate_destination_path(str(test_dir))
            assert result.is_absolute()
            assert result == test_dir.resolve()
        finally:
            test_dir.rmdir()

    def test_validate_valid_project_directory_name(self, validator: PathSecurityValidator) -> None:
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
        with pytest.raises(ValueError, match="path separators"):
            validator.validate_project_directory_name("../project")

        with pytest.raises(ValueError, match="path separators"):
            validator.validate_project_directory_name("foo/../bar")

    def test_reject_excessively_long_project_name(self, validator: PathSecurityValidator) -> None:
        long_name = "a" * 256

        with pytest.raises(ValueError, match="too long"):
            validator.validate_project_directory_name(long_name)

    def test_validate_valid_temp_destination_path(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        result = validator.validate_destination_path(str(temp_dir))
        assert result.is_absolute()

    def test_allow_legitimate_relative_paths_to_safe_locations(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        subdir = temp_dir / "subdir"
        nested = subdir / "nested"
        nested.mkdir(parents=True)

        original_cwd = Path.cwd()
        try:
            os.chdir(nested)
            result = validator.validate_destination_path("../..")
            assert result.resolve() == temp_dir.resolve()
        finally:
            os.chdir(original_cwd)


# ===>  Linux-Specific Tests


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific tests")
class TestPathSecurityValidatorLinux:
    """Test suite for PathSecurityValidator - Linux-specific tests."""

    def test_reject_root_directory(self, validator: PathSecurityValidator) -> None:
        with pytest.raises(DangerousPathError, match="system directory"):
            validator.validate_destination_path("/")

    def test_reject_system_directories(self, validator: PathSecurityValidator) -> None:
        dangerous_paths = ["/bin", "/sbin", "/usr", "/sys", "/proc", "/boot", "/dev", "/lib"]

        for path in dangerous_paths:
            # These paths may be symlinks (e.g., /bin -> /usr/bin on modern systems)
            # but should still be rejected. They could raise DangerousPathError
            # (if resolved path is dangerous) or PathSecurityError (if it's a
            # dangerous symlink caught before resolution completes)
            with pytest.raises(PathSecurityError):
                validator.validate_destination_path(path)

    def test_reject_subdirectories_of_system_paths(self, validator: PathSecurityValidator) -> None:
        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("/etc/config")

        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("/bin/tools")

        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("/usr/bin/local")

    def test_allow_tmp_directory(self, validator: PathSecurityValidator) -> None:
        """Test that /tmp is allowed on Linux."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validator.validate_destination_path(tmpdir)
            assert result.is_absolute()
            assert "/tmp/" in str(result) or str(result) == "/tmp"  # noqa: S108

    def test_allow_var_tmp_directory(self, validator: PathSecurityValidator) -> None:
        """Test that /var/tmp is allowed on Linux."""
        with tempfile.TemporaryDirectory(dir="/var/tmp") as tmpdir:
            result = validator.validate_destination_path(tmpdir)
            assert result.is_absolute()
            assert "/var/tmp/" in str(result)  # noqa: S108

    def test_allow_relative_navigation_to_safe_paths(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        projects = temp_dir / "projects"
        myapp = projects / "myapp"
        myapp.mkdir(parents=True)

        original_cwd = Path.cwd()
        try:
            os.chdir(myapp)
            result = validator.validate_destination_path("../")
            assert result.resolve() == projects.resolve()

            result = validator.validate_destination_path("../../")
            assert result.resolve() == temp_dir.resolve()
        finally:
            os.chdir(original_cwd)

    def test_reject_symlink_destination(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        real_dir = temp_dir / "real"
        real_dir.mkdir()
        symlink = temp_dir / "link"
        symlink.symlink_to(real_dir)

        # Should reject symlinks even if they point to safe locations
        with pytest.raises(PathSecurityError, match="symbolic link"):
            validator.validate_destination_path(str(symlink))


# ===>  macOS-Specific Tests


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific tests")
class TestPathSecurityValidatorMacOS:
    """Test suite for PathSecurityValidator - macOS-specific tests."""

    def test_reject_root_directory(self, validator: PathSecurityValidator) -> None:
        with pytest.raises(DangerousPathError, match="system directory"):
            validator.validate_destination_path("/")

    def test_reject_system_directories(self, validator: PathSecurityValidator) -> None:
        dangerous_paths = [
            "/System",
            "/Library",
            "/Applications",
            "/bin",
            "/sbin",
            "/usr",
        ]

        for path in dangerous_paths:
            # Some of these may be symlinks, but all should be rejected
            with pytest.raises(PathSecurityError):  # DangerousPathError is a subclass
                validator.validate_destination_path(path)

    def test_reject_subdirectories_of_system_paths(self, validator: PathSecurityValidator) -> None:
        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("/System/Library")

        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("/Library/Frameworks")

        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("/Applications/Utilities")

    def test_allow_tmp_directory(self, validator: PathSecurityValidator) -> None:
        """Test that /tmp is allowed on macOS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validator.validate_destination_path(tmpdir)
            assert result.is_absolute()
            # On macOS, /tmp is often a symlink to /private/tmp
            resolved_str = str(result)
            assert "/tmp" in resolved_str or "/private/tmp" in resolved_str  # noqa: S108

    def test_allow_var_tmp_directory(self, validator: PathSecurityValidator) -> None:
        """Test that /var/tmp is allowed on macOS."""
        # On macOS, check if /var/tmp exists before testing
        var_tmp = Path("/var/tmp")  # noqa: S108
        if var_tmp.exists():
            with tempfile.TemporaryDirectory(dir="/var/tmp") as tmpdir:
                result = validator.validate_destination_path(tmpdir)
                assert result.is_absolute()

    def test_allow_private_var_folders(self, validator: PathSecurityValidator) -> None:
        """Test that /private/var/folders (temp dir structure) is allowed on macOS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validator.validate_destination_path(tmpdir)
            assert result.is_absolute()
            # Should not raise an error for /private/var/folders/

    def test_reject_private_etc_directory(self, validator: PathSecurityValidator) -> None:
        """Test that /private/etc is rejected on macOS."""
        with pytest.raises(DangerousPathError):
            validator.validate_destination_path("/private/etc")

    def test_allow_relative_navigation_to_safe_paths(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        projects = temp_dir / "projects"
        myapp = projects / "myapp"
        myapp.mkdir(parents=True)

        original_cwd = Path.cwd()
        try:
            os.chdir(myapp)
            result = validator.validate_destination_path("../")
            assert result.resolve() == projects.resolve()
        finally:
            os.chdir(original_cwd)

    def test_reject_symlink_destination(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        real_dir = temp_dir / "real"
        real_dir.mkdir()
        symlink = temp_dir / "link"
        symlink.symlink_to(real_dir)

        with pytest.raises(PathSecurityError, match="symbolic link"):
            validator.validate_destination_path(str(symlink))


# ===> Windows-Specific Tests


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific tests")
class TestPathSecurityValidatorWindows:
    def test_reject_c_drive_root(self, validator: PathSecurityValidator) -> None:
        """Test that C:\\ drive root is rejected on Windows."""
        with pytest.raises(DangerousPathError, match="system directory"):
            validator.validate_destination_path("C:\\")

        with pytest.raises(DangerousPathError, match="system directory"):
            validator.validate_destination_path("c:/")

    def test_reject_windows_system_paths(self, validator: PathSecurityValidator) -> None:
        dangerous_paths = [
            "C:\\Windows",
            "c:/windows",
            "C:\\Program Files",
            "c:/program files",
            "C:\\Program Files (x86)",
            "C:\\ProgramData",
        ]

        for path in dangerous_paths:
            with pytest.raises(DangerousPathError, match="system directory"):
                validator.validate_destination_path(path)

    def test_reject_windows_system_subdirectories(self, validator: PathSecurityValidator) -> None:
        expected = "Cannot use system directory 'C:\\Windows\\System32' as destination. This is a critical system path that should not be modified."

        with pytest.raises(DangerousPathError, match=re.escape(expected)):
            validator.validate_destination_path("C:\\Windows\\System32")

        with pytest.raises(DangerousPathError, match="under a system directory"):
            validator.validate_destination_path("C:\\Program Files\\Common Files")

    def test_case_insensitive_path_validation(self, validator: PathSecurityValidator) -> None:
        with pytest.raises(DangerousPathError):
            validator.validate_destination_path("c:\\WINDOWS")

        with pytest.raises(DangerousPathError):
            validator.validate_destination_path("C:\\windows")

        with pytest.raises(DangerousPathError):
            validator.validate_destination_path("C:\\WiNdOwS")

    def test_forward_slash_paths(self, validator: PathSecurityValidator) -> None:
        with pytest.raises(DangerousPathError):
            validator.validate_destination_path("C:/Windows")

        with pytest.raises(DangerousPathError):
            validator.validate_destination_path("C:/Program Files")

    def test_allow_user_temp_directory(self, validator: PathSecurityValidator) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validator.validate_destination_path(tmpdir)
            assert result.is_absolute()

    def test_reject_paths_resolving_to_system_directories(
        self, validator: PathSecurityValidator
    ) -> None:
        # C:\Temp\..\Windows resolves to C:\Windows (dangerous)
        with pytest.raises(DangerousPathError, match="system directory"):
            validator.validate_destination_path("C:\\Temp\\..\\Windows")

        # C:\Users\..\Program Files resolves to C:\Program Files (dangerous)
        with pytest.raises(DangerousPathError, match="system directory"):
            validator.validate_destination_path("C:\\Users\\..\\Program Files")

        with pytest.raises(DangerousPathError, match="system directory"):
            validator.validate_destination_path("C:/Temp/../Windows")

    def test_allow_relative_navigation_to_safe_paths(
        self, validator: PathSecurityValidator, temp_dir: Path
    ) -> None:
        projects = temp_dir / "projects"
        myapp = projects / "myapp"
        myapp.mkdir(parents=True)

        original_cwd = Path.cwd()
        try:
            os.chdir(myapp)
            result = validator.validate_destination_path("..\\")
            assert result.resolve() == projects.resolve()
        finally:
            os.chdir(original_cwd)


# ===>  SafeProjectPathResolver - Common Tests


class TestSafeProjectPathResolverCommon:
    def test_resolve_valid_project_path(self, temp_dir: Path) -> None:
        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="my-project",
        )

        result = resolver.resolve()
        expected = temp_dir / "my-project"

        assert result == expected.resolve()
        assert result.is_absolute()

    def test_reject_existing_project_directory(self, temp_dir: Path) -> None:
        existing_dir = temp_dir / "existing-project"
        existing_dir.mkdir()

        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="existing-project",
        )

        with pytest.raises(FileExistsError, match="already exists"):
            resolver.resolve()

    def test_reject_nonexistent_destination(self, temp_dir: Path) -> None:
        nonexistent = temp_dir / "does-not-exist"

        resolver = SafeProjectPathResolver(
            destination_path=str(nonexistent),
            project_dir_name="my-project",
        )

        with pytest.raises(ValueError, match="does not exist"):
            resolver.resolve()

    def test_reject_destination_file_not_directory(self, temp_dir: Path) -> None:
        file_path = temp_dir / "file.txt"
        file_path.write_text("test")

        resolver = SafeProjectPathResolver(
            destination_path=str(file_path),
            project_dir_name="my-project",
        )

        with pytest.raises(ValueError, match="not a directory"):
            resolver.resolve()

    def test_check_existing_directory_not_exists(self, temp_dir: Path) -> None:
        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="new-project",
        )

        exists, has_content = resolver.check_existing_directory()

        assert not exists
        assert not has_content

    def test_check_existing_directory_empty(self, temp_dir: Path) -> None:
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

    def test_security_validator_integration(self, temp_dir: Path) -> None:
        custom_validator = PathSecurityValidator()

        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="my-project",
            security_validator=custom_validator,
        )

        assert resolver._validator is custom_validator

    def test_verify_path_containment(self, temp_dir: Path) -> None:
        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="valid-name",
        )

        result = resolver.resolve()

        # Verify result is actually under temp_dir
        # This should work across all platforms now
        assert result.parent == temp_dir.resolve()


# ===> SafeProjectPathResolver - Linux-Specific Tests


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific tests")
class TestSafeProjectPathResolverLinux:
    def test_reject_dangerous_system_path(self) -> None:
        with pytest.raises(DangerousPathError):
            SafeProjectPathResolver(
                destination_path="/etc",
                project_dir_name="my-project",
            )

    def test_full_validation_flow(self, temp_dir: Path) -> None:
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

    def test_prevent_directory_escape_via_project_name(self, temp_dir: Path) -> None:
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


# ===>  SafeProjectPathResolver - macOS-Specific Tests


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific tests")
class TestSafeProjectPathResolverMacOS:
    """Test suite for SafeProjectPathResolver - macOS-specific tests."""

    def test_reject_dangerous_system_path(self) -> None:
        with pytest.raises(DangerousPathError):
            SafeProjectPathResolver(
                destination_path="/System",
                project_dir_name="my-project",
            )

    def test_full_validation_flow(self, temp_dir: Path) -> None:
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

    def test_prevent_directory_escape_via_project_name(self, temp_dir: Path) -> None:
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


# ===>  SafeProjectPathResolver - Windows-Specific Tests


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific tests")
class TestSafeProjectPathResolverWindows:
    """Test suite for SafeProjectPathResolver - Windows-specific tests."""

    def test_reject_dangerous_system_path(self) -> None:
        with pytest.raises(DangerousPathError):
            SafeProjectPathResolver(
                destination_path="C:\\Windows",
                project_dir_name="my-project",
            )

    def test_full_validation_flow(self, temp_dir: Path) -> None:
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

    def test_prevent_directory_escape_via_project_name(self, temp_dir: Path) -> None:
        destination = temp_dir / "safe-zone"
        destination.mkdir()

        malicious_names = [
            "..",
            "..\\..",
            "foo\\..",
        ]

        for name in malicious_names:
            with pytest.raises(ValueError, match="path separators"):
                SafeProjectPathResolver(
                    destination_path=str(destination),
                    project_dir_name=name,
                )

    def test_handle_short_names(self, temp_dir: Path) -> None:
        # Windows may use short names like RUNNER~1
        # The path containment check should still work
        resolver = SafeProjectPathResolver(
            destination_path=str(temp_dir),
            project_dir_name="test-project",
        )

        result = resolver.resolve()

        # Should not raise PathTraversalError due to short name mismatch
        assert result.is_absolute()
        assert result.parent == temp_dir.resolve()
