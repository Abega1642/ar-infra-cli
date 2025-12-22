"""ArtifactId value object - represents a Maven/Gradle artifact identifier."""

from dataclasses import dataclass
from typing import final

from pathvalidate import ValidationError, validate_filename

from src.ar_infra.domain.constant import (
    JAVA_RESERVED_KEYWORDS,
    MAX_ARTIFACT_ID_LENGTH,
    MIN_ARTIFACT_ID_LENGTH,
    VALID_ARTIFACT_ID_PATTERN,
)
from src.ar_infra.domain.exceptions.validation_error import InvalidArtifactIdError


@final
@dataclass(frozen=True, slots=True)
class ArtifactId:
    """Immutable value object representing a Maven/Gradle artifact identifier."""

    value: str

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidArtifactIdError("Artifact ID cannot be empty")

        if len(self.value) > MAX_ARTIFACT_ID_LENGTH:
            raise InvalidArtifactIdError(
                f"Artifact ID is too long (max {MAX_ARTIFACT_ID_LENGTH} characters)",
            )

        if len(self.value) < MIN_ARTIFACT_ID_LENGTH:
            raise InvalidArtifactIdError(
                f"Artifact ID is too short (min {MIN_ARTIFACT_ID_LENGTH} characters)",
            )

        if ".." in self.value or "/" in self.value or "\\" in self.value:
            raise InvalidArtifactIdError(
                "Artifact ID contains invalid path characters (possible path traversal)",
            )

        dangerous_chars = [";", "&", "|", "`", "$", "(", ")", "<", ">", "\n", "\r"]
        if any(char in self.value for char in dangerous_chars):
            raise InvalidArtifactIdError(
                "Artifact ID contains potentially dangerous characters",
            )

        if self.value != self.value.lower():
            raise InvalidArtifactIdError("Artifact ID must be lowercase")

        if not VALID_ARTIFACT_ID_PATTERN.match(self.value):
            raise InvalidArtifactIdError(
                f"Artifact ID '{self.value}' contains invalid characters or format",
            )

        if self.value in JAVA_RESERVED_KEYWORDS:
            raise InvalidArtifactIdError(
                f"Artifact ID '{self.value}' is a Java reserved keyword",
            )

        try:
            validate_filename(self.value, platform="auto")
        except ValidationError as e:
            raise InvalidArtifactIdError(
                f"Artifact ID '{self.value}' is not a valid filename: {e}",
            ) from e

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"ArtifactId('{self.value}')"

    def __hash__(self) -> int:
        return hash(self.value)
