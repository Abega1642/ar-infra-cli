"""GroupId value object - represents a Maven/Gradle group identifier."""

from dataclasses import dataclass
from typing import final

from pathvalidate import ValidationError, validate_filename

from src.ar_infra.domain.constant import (
    JAVA_RESERVED_KEYWORDS,
    MAX_GROUP_ID_LENGTH,
    MAX_SEGMENT_LENGTH,
    VALID_SEGMENT_PATTERN,
)
from src.ar_infra.domain.exceptions.validation_error import InvalidGroupIdError


def _validate_segment(segment: str) -> None:
    """
    Validate a single segment of the group ID.

    Args:
        segment: A single segment to validate.

    Raises:
        InvalidGroupIdError: If the segment is invalid.
    """
    if not segment:
        raise InvalidGroupIdError("Group ID segments cannot be empty")

    if len(segment) > MAX_SEGMENT_LENGTH:
        raise InvalidGroupIdError(
            f"Group ID segment '{segment}' is too long (max {MAX_SEGMENT_LENGTH} characters)",
        )

    if segment != segment.lower():
        raise InvalidGroupIdError(
            f"Group ID segment '{segment}' must be lowercase",
        )

    if not VALID_SEGMENT_PATTERN.match(segment):
        raise InvalidGroupIdError(
            f"Group ID segment '{segment}' contains invalid characters or format. "
            "Must start with a letter and contain only lowercase letters, numbers, "
            "and hyphens (not at start or end).",
        )

    if segment in JAVA_RESERVED_KEYWORDS:
        raise InvalidGroupIdError(
            f"Group ID segment '{segment}' is a Java reserved keyword",
        )

    try:
        validate_filename(segment, platform="auto")
    except ValidationError as e:
        raise InvalidGroupIdError(
            f"Group ID segment '{segment}' is not a valid filename: {e}",
        ) from e


@final
@dataclass(frozen=True, slots=True)
class GroupId:
    """
    Immutable value object representing a Maven/Gradle group identifier.

    A group ID must:
    - Be in reverse domain name notation (e.g., 'dev.razafindratelo')
    - Contain at least 2 segments separated by dots
    - Use only lowercase letters, numbers, and hyphens
    - Not start or end with hyphens or dots
    - Not contain consecutive dots
    - Not use Java reserved keywords
    - Be within reasonable length limits

    Security features:
    - Input sanitization to prevent path traversal
    - Command injection prevention
    - Length limits to prevent DoS
    - Reserved keyword checking
    """

    value: str

    def __post_init__(self) -> None:
        """Validate group ID after initialization."""
        self._validate()

    def _validate(self) -> None:
        """
        Validate the group ID according to Maven/Gradle conventions and security rules.

        Raises:
            InvalidGroupIdError: If the group ID is invalid.
        """
        if not self.value or not self.value.strip():
            raise InvalidGroupIdError("Group ID cannot be empty")

        if len(self.value) > MAX_GROUP_ID_LENGTH:
            raise InvalidGroupIdError(
                f"Group ID is too long (max {MAX_GROUP_ID_LENGTH} characters)",
            )

        if ".." in self.value or "/" in self.value or "\\" in self.value:
            raise InvalidGroupIdError(
                "Group ID contains invalid path characters (possible path traversal)",
            )

        dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        if any(char in self.value for char in dangerous_chars):
            raise InvalidGroupIdError(
                "Group ID contains potentially dangerous characters",
            )

        if self.value.startswith(".") or self.value.endswith("."):
            raise InvalidGroupIdError("Group ID cannot start or end with a dot")

        if ".." in self.value:
            raise InvalidGroupIdError("Group ID cannot contain consecutive dots")

        segments = self.value.split(".")

        if len(segments) < 2:
            raise InvalidGroupIdError(
                "Group ID must have at least two segments (e.g., 'dev.razafindratelo')",
            )

        for segment in segments:
            _validate_segment(segment)

    @property
    def segments(self) -> list[str]:
        """Return the segments of the group ID."""
        return self.value.split(".")

    def to_path(self) -> str:
        """
        Convert group ID to file system path.

        Returns:
            Path string with forward slashes (e.g., 'dev/razafindratelo').
        """
        return self.value.replace(".", "/")

    def __str__(self) -> str:
        """Return string representation."""
        return self.value

    def __repr__(self) -> str:
        """Return detailed representation."""
        return f"GroupId('{self.value}')"

    def __hash__(self) -> int:
        """Return hash for use in sets and dicts."""
        return hash(self.value)
