"""Path security and validation for project generation."""

import platform
from pathlib import Path
from typing import Final


class PathSecurityError(Exception):
    """Raised when a path is deemed unsafe for project generation."""


class DangerousPathError(PathSecurityError):
    """Raised when attempting to use a system-critical path."""


class PathTraversalError(PathSecurityError):
    """Raised when path traversal is detected."""


class PathSecurityValidator:
    """Validates paths for security concerns before project generation."""

    # System-critical paths that should NEVER be used (exact matches only)
    DANGEROUS_UNIX_PATHS: Final[set[str]] = {
        "/",
        "/bin",
        "/boot",
        "/dev",
        "/etc",
        "/lib",
        "/lib64",
        "/proc",
        "/root",
        "/sbin",
        "/sys",
        "/usr",
        "/var",
    }

    DANGEROUS_UNIX_PREFIXES: Final[set[str]] = {
        "/bin/",
        "/boot/",
        "/dev/",
        "/etc/",
        "/lib/",
        "/lib64/",
        "/proc/",
        "/root/",
        "/sbin/",
        "/sys/",
        "/usr/",
        "/var/",
    }

    DANGEROUS_WINDOWS_PATHS: Final[set[str]] = {
        "c:\\",
        "c:\\windows",
        "c:\\program files",
        "c:\\program files (x86)",
        "c:\\programdata",
    }

    DANGEROUS_WINDOWS_PREFIXES: Final[set[str]] = {
        "c:\\windows\\",
        "c:\\program files\\",
        "c:\\program files (x86)\\",
        "c:\\programdata\\",
    }

    DANGEROUS_MACOS_PATHS: Final[set[str]] = {
        "/System",
        "/Library",
        "/Applications",
        "/private",
    }

    DANGEROUS_MACOS_PREFIXES: Final[set[str]] = {
        "/System/",
        "/Library/",
        "/Applications/",
        "/private/etc/",
        "/private/var/",
    }

    def __init__(self) -> None:
        self._system = platform.system()

    def validate_destination_path(self, path_str: str) -> Path:
        """
        Validate and resolve destination path with security checks.

        Args:
            path_str: The path string provided by user

        Returns:
            Resolved, validated Path object

        Raises:
            PathSecurityError: If path is unsafe
            ValueError: If path is invalid
            OSError: If path resolution fails
        """
        self._validate_not_empty(path_str)
        self._check_path_traversal_in_input(path_str)
        path = Path(path_str).expanduser()
        if path.exists() and path.is_symlink():
            raise PathSecurityError(
                f"Destination path '{path}' is a symbolic link. "
                "Please provide a direct path for security reasons."
            )
        resolved = path.resolve(strict=False)
        self._check_dangerous_path(resolved)

        return resolved

    def validate_project_directory_name(self, name: str) -> str:
        """
        Validate the project directory name.

        Args:
            name: The directory name provided by user

        Returns:
            Validated directory name

        Raises:
            ValueError: If name is invalid or contains dangerous patterns
        """
        self._validate_not_empty(name)
        name = name.strip()

        self._check_path_separators(name)
        self._check_hidden_directory(name)
        self._check_valid_characters(name)
        self._check_name_length(name)

        return name

    def _validate_not_empty(self, value: str) -> None:
        """Check if value is empty or whitespace."""
        if not value or not value.strip():
            raise ValueError("Path or name cannot be empty")

    def _expand_and_check_symlink(self, path_str: str) -> Path:
        """Expand user path and check for symlinks."""
        try:
            path = Path(path_str).expanduser()
        except (RuntimeError, ValueError) as exc:
            raise ValueError(f"Invalid path format: {exc}") from exc

        if path.exists() and path.is_symlink():
            raise PathSecurityError(
                f"Destination path '{path}' is a symbolic link. "
                "Please provide a direct path for security reasons."
            )

        return path

    def _resolve_path(self, path: Path) -> Path:
        """Resolve path to absolute form."""
        try:
            return path.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            raise OSError(f"Cannot resolve path '{path}': {exc}") from exc

    def _check_path_traversal_in_input(self, path_str: str) -> None:
        try:
            parts = Path(path_str).expanduser().parts
        except (ValueError, RuntimeError) as err:
            raise ValueError("Invalid path format") from err

        if ".." in parts:
            raise PathTraversalError("path traversal detected")

    def _check_dangerous_path(self, resolved: Path) -> None:
        """Check if the resolved path is a system-critical directory."""
        path_str = str(resolved)

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

    def _is_exact_dangerous_match(self, path_str: str) -> bool:
        """Check if path exactly matches a dangerous path."""
        dangerous_paths = self._get_dangerous_paths()

        if self._system == "Windows":
            return path_str.lower() in {p.lower() for p in dangerous_paths}

        return path_str in dangerous_paths

    def _is_under_dangerous_prefix(self, path_str: str) -> bool:
        """Check if path starts with a dangerous prefix."""
        dangerous_prefixes = self._get_dangerous_prefixes()

        if self._system == "Windows":
            path_lower = path_str.lower()
            return any(path_lower.startswith(prefix.lower()) for prefix in dangerous_prefixes)

        return any(path_str.startswith(prefix) for prefix in dangerous_prefixes)

    def _get_dangerous_paths(self) -> set[str]:
        """Get dangerous paths for the current system."""
        dangerous = self.DANGEROUS_UNIX_PATHS.copy()

        if self._system == "Windows":
            dangerous.update(self.DANGEROUS_WINDOWS_PATHS)
        elif self._system == "Darwin":
            dangerous.update(self.DANGEROUS_MACOS_PATHS)

        return dangerous

    def _get_dangerous_prefixes(self) -> set[str]:
        """Get dangerous path prefixes for the current system."""
        prefixes = self.DANGEROUS_UNIX_PREFIXES.copy()

        if self._system == "Windows":
            prefixes.update(self.DANGEROUS_WINDOWS_PREFIXES)
        elif self._system == "Darwin":
            prefixes.update(self.DANGEROUS_MACOS_PREFIXES)

        return prefixes

    def _check_path_separators(self, name: str) -> None:
        """Check for path separators in directory name."""
        if ".." in name or "/" in name or "\\" in name:
            raise ValueError(
                "Project directory name cannot contain path separators or '..' sequences"
            )

    def _check_hidden_directory(self, name: str) -> None:
        """Check if directory name starts with dot."""
        if name.startswith("."):
            raise ValueError("Project directory name cannot start with '.' (hidden directory)")

    def _check_valid_characters(self, name: str) -> None:
        """Check if directory name contains only valid characters."""
        if not all(c.isalnum() or c in "-_" for c in name):
            raise ValueError(
                "Project directory name can only contain alphanumeric characters, "
                "hyphens, and underscores"
            )

    def _check_name_length(self, name: str) -> None:
        """Check if directory name is not too long."""
        if len(name) > 255:
            raise ValueError("Project directory name too long (max 255 characters)")


class SafeProjectPathResolver:
    """
    Safely resolve and validate the complete project directory path.

    This class ensures that:
    1. The destination path is safe and not system-critical
    2. The project directory name is valid
    3. The final project path is within the destination
    4. No path traversal attacks are possible
    """

    def __init__(
        self,
        destination_path: str,
        project_dir_name: str,
        security_validator: PathSecurityValidator | None = None,
    ) -> None:
        """
        Initialize the resolver.

        Args:
            destination_path: Base destination directory path
            project_dir_name: Name of the project directory to create
            security_validator: Optional custom security validator
        """
        self._validator = security_validator or PathSecurityValidator()

        self.destination = self._validator.validate_destination_path(destination_path)
        self.project_name = self._validator.validate_project_directory_name(project_dir_name)

    def resolve(self) -> Path:
        """
        Resolve and validate the complete project directory path.

        Returns:
            Safe, validated project directory path

        Raises:
            PathSecurityError: If the resolved path is unsafe
            FileExistsError: If the project directory already exists
            ValueError: If path validation fails
        """
        project_dir = self._construct_project_path()
        self._verify_path_containment(project_dir)
        self._check_destination_validity()
        self._check_project_not_exists(project_dir)
        self._check_write_permissions()

        return project_dir

    def check_existing_directory(self) -> tuple[bool, bool]:
        """
        Check if project directory exists and if it has content.

        Returns:
            Tuple of (exists, has_content)
        """
        project_dir = self.destination / self.project_name

        if not project_dir.exists():
            return (False, False)

        if not project_dir.is_dir():
            return (True, False)

        return (True, self._directory_has_content(project_dir))

    def _construct_project_path(self) -> Path:
        """Construct and resolve the project directory path."""
        project_dir = self.destination / self.project_name

        try:
            return project_dir.resolve(strict=False)
        except (OSError, RuntimeError) as exc:
            raise OSError(f"Cannot resolve project path: {exc}") from exc

    def _verify_path_containment(self, project_dir: Path) -> None:
        """Verify that project directory is contained within destination."""
        try:
            if hasattr(project_dir, "is_relative_to"):
                is_contained = project_dir.is_relative_to(self.destination)
            else:
                try:
                    project_dir.relative_to(self.destination)
                    is_contained = True
                except ValueError:
                    is_contained = False

            if not is_contained:
                raise PathTraversalError(
                    f"Project directory '{project_dir}' is not under "
                    f"destination '{self.destination}'. This may indicate a path traversal attack."
                )
        except (ValueError, TypeError) as exc:
            raise PathSecurityError(f"Cannot verify project path safety: {exc}") from exc

    def _check_destination_validity(self) -> None:
        """Check that destination exists and is a directory."""
        if not self.destination.exists():
            raise ValueError(
                f"Destination directory '{self.destination}' does not exist. "
                "Please create it first or choose an existing directory."
            )

        if not self.destination.is_dir():
            raise ValueError(f"Destination path '{self.destination}' exists but is not a directory")

    def _check_project_not_exists(self, project_dir: Path) -> None:
        """Check that project directory doesn't already exist."""
        if project_dir.exists():
            raise FileExistsError(
                f"Directory '{project_dir}' already exists. "
                "Please choose a different project name or destination."
            )

    def _check_write_permissions(self) -> None:
        test_file = None
        try:
            test_file = self.destination / ".ar_infra_write_test"
            with Path.open(test_file, "w", encoding="utf-8"):
                pass
        except OSError as err:
            raise PermissionError(
                f"No write permission for destination directory '{self.destination}'"
            ) from err
        finally:
            if test_file and test_file.exists():
                try:
                    test_file.unlink()
                except OSError:
                    pass

    def _directory_has_content(self, directory: Path) -> bool:
        """Check if directory has any content."""
        try:
            return any(directory.iterdir())
        except (OSError, PermissionError):
            return True  # Assume has content if we can't check
