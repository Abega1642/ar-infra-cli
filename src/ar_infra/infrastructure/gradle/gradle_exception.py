"""Gradle infrastructure exceptions."""


class GradleError(Exception):
    """Base exception for Gradle operations."""


class GradleParseError(GradleError):
    """Raised when Gradle file parsing fails."""


class GradleWriteError(GradleError):
    """Raised when writing Gradle file fails."""


class MaliciousContentError(GradleError):
    """Raised when malicious content is detected in Gradle files."""
