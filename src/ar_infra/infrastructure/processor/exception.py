"""Processor infrastructure exceptions."""


class ProcessorError(Exception):
    """Base exception for processor operations."""


class PackageRenameError(ProcessorError):
    """Raised when package renaming fails."""


class SecurityViolationError(ProcessorError):
    """Raised when a security violation is detected."""


class FileProcessingError(ProcessorError):
    """Raised when file processing fails."""
