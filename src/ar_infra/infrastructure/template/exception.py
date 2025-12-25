"""Template infrastructure exceptions."""


class TemplateError(Exception):
    """Base exception for template operations."""


class TemplateFetchError(TemplateError):
    """Raised when template fetching fails."""


class InvalidTemplateError(TemplateError):
    """Raised when template structure is invalid."""


class SecurityViolationError(TemplateError):
    """Raised when a security violation is detected."""
