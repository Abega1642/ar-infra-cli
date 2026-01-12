from typing import Final


class ValidationError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message: Final[str] = message


class InvalidGroupIdError(ValidationError):
    """Raised when a group ID is invalid."""


class InvalidArtifactIdError(ValidationError):
    """Raised when an artifact ID is invalid."""


class InvalidPackageNameError(ValidationError):
    """Raised when a package name is invalid."""


class InvalidVersionError(ValidationError):
    """Raised when a version string is invalid."""


class InvalidDependencyError(ValidationError):
    """Raised when a dependency specification is invalid."""
