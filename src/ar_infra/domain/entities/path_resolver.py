"""Path security and validation for project generation.

This module provides cross-platform path validation and security checking
for project generation. It handles platform-specific path formats and
dangerous system directories across Linux, macOS, and Windows.
"""

import platform
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Final

from src.ar_infra.domain.entities.path_constant import (
    DANGEROUS_MACOS_EXACT_PATHS,
    DANGEROUS_MACOS_PREFIX_PATHS,
    DANGEROUS_UNIX_EXACT_PATHS,
    DANGEROUS_UNIX_PREFIX_PATHS,
    DANGEROUS_WINDOWS_EXACT_PATHS,
    DANGEROUS_WINDOWS_PREFIX_PATHS,
    SAFE_MACOS_PATHS,
    SAFE_MACOS_PREFIX_PATHS,
    SAFE_UNIX_PATHS,
    SAFE_UNIX_PREFIX_PATHS,
)


class PathSecurityError(Exception):
    """Raised when a path is deemed unsafe for project generation."""


class DangerousPathError(PathSecurityError):
    """Raised when attempting to use a system-critical path."""


class PathTraversalError(PathSecurityError):
    """Raised when path traversal causes project to escape destination."""


class PathSecurityValidator:
    def __init__(self) -> None:
        self._system: Final[str] = platform.system()

    def validate_destination_path(self, path_str: str) -> Path:
        self._validate_not_empty(path_str)

        try:
            path = Path(path_str).expanduser()
        except (ValueError, RuntimeError) as err:
            raise ValueError(f"Invalid path format: {err}") from err

        resolved = path.resolve(strict=False)

        self._check_dangerous_path(resolved)

        # After confirming it's not a dangerous system path, check if it's a symlink
        # We reject user-provided symlinks for security, but only after confirming
        # they don't point to dangerous locations
        if path.exists() and path.is_symlink():
            raise PathSecurityError(
                f"Destination path '{path}' is a symbolic link. "
                "Please provide a direct path for security reasons."
            )

        return resolved

    def validate_project_directory_name(self, name: str) -> str:
        self._validate_not_empty(name)
        name = name.strip()

        self._check_path_separators(name)
        self._check_hidden_directory(name)
        self._check_valid_characters(name)
        self._check_name_length(name)

        return name

    def _validate_not_empty(self, value: str) -> None:
        if not value or not value.strip():
            raise ValueError("Path or name cannot be empty")

    def _check_dangerous_path(self, resolved: Path) -> None:
        path_str = self._normalize_path_for_comparison(resolved)

        if self._is_safe_path(path_str):
            return

        if self._is_exact_dangerous_match(path_str):
            raise DangerousPathError(
                f"Cannot use system directory '{resolved}' as destination. "
                "This is a critical system path that should not be modified."
            )

        if self._is_under_dangerous_prefix(path_str):
            raise DangerousPathError(
                f"Cannot use path '{resolved}' as it is under a system directory. "
                "This is a critical system path that should not be modified."
            )

    def _normalize_path_for_comparison(self, path: Path) -> str:
        path_str = str(path)

        if self._system == "Windows":
            # Convert to lowercase for case-insensitive comparison
            # Normalize slashes to backslashes for Windows
            path_str = path_str.lower().replace("/", "\\")

            # Handle Windows short names (e.g., RUNNER~1)
            # Try to get the long path name if possible
            if path.exists():
                try:
                    path_str = str(path.resolve()).lower().replace("/", "\\")
                except (OSError, RuntimeError):
                    # If we can't resolve the path (e.g., broken symlink, permission issue),
                    # fall back to using the original normalized path
                    pass
        else:
            # For Unix/Linux/macOS, use forward slashes
            path_str = path_str.replace("\\", "/")

        return path_str

    def _is_safe_path(self, path_str: str) -> bool:
        if self._system == "Darwin":
            if path_str in SAFE_MACOS_PATHS:
                return True
            for prefix in SAFE_MACOS_PREFIX_PATHS:
                if path_str.startswith(prefix):
                    return True

        if self._system in ("Linux", "Darwin"):
            if path_str in SAFE_UNIX_PATHS:
                return True
            for prefix in SAFE_UNIX_PREFIX_PATHS:
                if path_str.startswith(prefix):
                    return True

        return False

    def _is_exact_dangerous_match(self, path_str: str) -> bool:
        dangerous_paths = self._get_dangerous_exact_paths()

        if self._system == "Windows":
            return path_str in dangerous_paths

        return path_str in dangerous_paths

    def _is_under_dangerous_prefix(self, path_str: str) -> bool:
        dangerous_prefixes = self._get_dangerous_prefix_paths()

        return any(path_str.startswith(prefix) for prefix in dangerous_prefixes)

    def _get_dangerous_exact_paths(self) -> frozenset[str]:
        if self._system == "Windows":
            return DANGEROUS_WINDOWS_EXACT_PATHS
        if self._system == "Darwin":
            return DANGEROUS_MACOS_EXACT_PATHS | DANGEROUS_UNIX_EXACT_PATHS
        # Linux and other Unix-like systems
        return DANGEROUS_UNIX_EXACT_PATHS

    def _get_dangerous_prefix_paths(self) -> frozenset[str]:
        if self._system == "Windows":
            return DANGEROUS_WINDOWS_PREFIX_PATHS
        if self._system == "Darwin":
            return DANGEROUS_MACOS_PREFIX_PATHS | DANGEROUS_UNIX_PREFIX_PATHS
        # Linux and other Unix-like systems
        return DANGEROUS_UNIX_PREFIX_PATHS

    def _check_path_separators(self, name: str) -> None:
        if ".." in name or "/" in name or "\\" in name:
            raise ValueError(
                "Project directory name cannot contain path separators or '..' sequences"
            )

    def _check_hidden_directory(self, name: str) -> None:
        if name.startswith("."):
            raise ValueError("Project directory name cannot start with '.' (hidden directory)")

    def _check_valid_characters(self, name: str) -> None:
        if not all(c.isalnum() or c in "-_" for c in name):
            raise ValueError(
                "Project directory name can only contain alphanumeric characters, "
                "hyphens, and underscores"
            )

    def _check_name_length(self, name: str) -> None:
        if len(name) > 255:
            raise ValueError("Project directory name too long (max 255 characters)")


class SafeProjectPathResolver:
    def __init__(
        self,
        destination_path: str,
        project_dir_name: str,
        security_validator: PathSecurityValidator | None = None,
    ) -> None:
        self._validator = security_validator or PathSecurityValidator()
        self._system: Final[str] = platform.system()

        self.destination = self._validator.validate_destination_path(destination_path)
        self.project_name = self._validator.validate_project_directory_name(project_dir_name)

    def resolve(self) -> Path:
        project_dir = self._construct_project_path()
        self._verify_path_containment(project_dir)
        self._check_destination_validity()
        self._check_project_not_exists(project_dir)
        self._check_write_permissions()

        return project_dir

    def check_existing_directory(self) -> tuple[bool, bool]:
        project_dir = self.destination / self.project_name

        if not project_dir.exists():
            return False, False

        if not project_dir.is_dir():
            return True, False

        return True, self._directory_has_content(project_dir)

    def _construct_project_path(self) -> Path:
        project_dir = self.destination / self.project_name

        try:
            return project_dir.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            raise OSError(f"Cannot resolve project path: {exc}") from exc

    def _verify_path_containment(self, project_dir: Path) -> None:
        try:
            resolved_project = project_dir.resolve(strict=False)
            resolved_destination = self.destination.resolve(strict=False)

            if self._system == "Windows":
                is_contained = self._check_windows_path_containment(
                    resolved_project, resolved_destination
                )
            else:
                is_contained = self._check_unix_path_containment(
                    resolved_project, resolved_destination
                )

            if not is_contained:
                raise PathTraversalError(
                    f"Project directory '{resolved_project}' is not under "
                    f"destination '{resolved_destination}'. "
                    "This may indicate a path traversal attack."
                )
        except (ValueError, TypeError) as exc:
            raise PathSecurityError(f"Cannot verify project path safety: {exc}") from exc

    def _check_windows_path_containment(self, project_path: Path, dest_path: Path) -> bool:
        """Check path containment on Windows (case-insensitive)."""
        project_str = str(project_path).lower().replace("/", "\\")
        dest_str = str(dest_path).lower().replace("/", "\\")

        project_pure_win = PureWindowsPath(project_str)
        dest_pure_win = PureWindowsPath(dest_str)

        try:
            project_pure_win.relative_to(dest_pure_win)
        except ValueError:
            return False
        return True

    def _check_unix_path_containment(self, project_path: Path, dest_path: Path) -> bool:
        """Check path containment on Unix-like systems."""
        project_str = str(project_path)
        dest_str = str(dest_path)

        project_pure_posix = PurePosixPath(project_str)
        dest_pure_posix = PurePosixPath(dest_str)

        # Python 3.9+ has is_relative_to
        if hasattr(project_pure_posix, "is_relative_to"):
            return project_pure_posix.is_relative_to(dest_pure_posix)

        # Fallback for Python 3.8
        try:
            project_pure_posix.relative_to(dest_pure_posix)
        except ValueError:
            return False
        return True

    def _check_destination_validity(self) -> None:
        if not self.destination.exists():
            raise ValueError(
                f"Destination directory '{self.destination}' does not exist. "
                "Please create it first or choose an existing directory."
            )

        if not self.destination.is_dir():
            raise ValueError(f"Destination path '{self.destination}' exists but is not a directory")

    def _check_project_not_exists(self, project_dir: Path) -> None:
        if project_dir.exists():
            raise FileExistsError(
                f"Directory '{project_dir}' already exists. "
                "Please choose a different project name or destination."
            )

    def _check_write_permissions(self) -> None:
        test_file = None
        try:
            test_file = self.destination / ".ar_infra_write_test"
            test_file.write_text("", encoding="utf-8")
        except OSError as err:
            raise PermissionError(
                f"No write permission for destination directory '{self.destination}'"
            ) from err
        finally:
            if test_file and test_file.exists():
                test_file.unlink(missing_ok=True)

    def _directory_has_content(self, directory: Path) -> bool:
        try:
            return any(directory.iterdir())
        except OSError:
            return True  # Assume has content if we can't check
