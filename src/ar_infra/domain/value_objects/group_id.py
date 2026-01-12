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
    value: str

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
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
        return self.value.split(".")

    def to_path(self) -> str:
        return self.value.replace(".", "/")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"GroupId('{self.value}')"

    def __hash__(self) -> int:
        return hash(self.value)
