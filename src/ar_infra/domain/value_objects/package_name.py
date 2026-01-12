from dataclasses import dataclass
from typing import final

from src.ar_infra.domain.constant import (
    DANGEROUS_CHARACTERS,
    JAVA_RESERVED_KEYWORDS,
    VALID_SEGMENT_PATTERN,
)
from src.ar_infra.domain.exceptions.validation_error import InvalidPackageNameError
from src.ar_infra.domain.value_objects.artifact_id import ArtifactId
from src.ar_infra.domain.value_objects.group_id import GroupId


@final
@dataclass(frozen=True, slots=True)
class PackageName:
    value: str

    def __post_init__(self) -> None:
        self._validate()

    @classmethod
    def from_parts(cls, group: GroupId, artifact: ArtifactId) -> "PackageName":
        artifact_cleaned = artifact.value.replace("-", "_")
        full_package = f"{group.value}.{artifact_cleaned}"
        return cls(full_package)

    def _validate(self) -> None:
        self._validate_basic_structure()
        self._validate_segments()

    def _validate_basic_structure(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidPackageNameError("Package name cannot be empty")

        if ".." in self.value or "/" in self.value or "\\" in self.value:
            raise InvalidPackageNameError(
                "Package name contains invalid path characters",
            )

        if any(char in self.value for char in DANGEROUS_CHARACTERS):
            raise InvalidPackageNameError(
                "Package name contains potentially dangerous characters",
            )

        if self.value.startswith(".") or self.value.endswith("."):
            raise InvalidPackageNameError("Package name cannot start or end with a dot")

    def _validate_segments(self) -> None:
        segments = self.value.split(".")

        if len(segments) < 3:
            raise InvalidPackageNameError(
                "Package name must have at least three segments",
            )

        for segment in segments:
            self._validate_segment(segment)

    @staticmethod
    def _validate_segment(segment: str) -> None:
        if not segment:
            raise InvalidPackageNameError("Package segments cannot be empty")

        if segment != segment.lower():
            raise InvalidPackageNameError(
                f"Package segment '{segment}' must be lowercase",
            )

        if not VALID_SEGMENT_PATTERN.match(segment):
            raise InvalidPackageNameError(
                f"Package segment '{segment}' contains invalid characters",
            )

        if segment in JAVA_RESERVED_KEYWORDS:
            raise InvalidPackageNameError(
                f"Package segment '{segment}' is a Java reserved keyword",
            )

    @property
    def segments(self) -> list[str]:
        return self.value.split(".")

    @property
    def base_package(self) -> str:
        """Return base package (all segments except last)."""
        segments = self.segments
        return ".".join(segments[:-1])

    @property
    def artifact_segment(self) -> str:
        """Return the artifact segment (last segment)."""
        return self.segments[-1]

    def to_path(self) -> str:
        return self.value.replace(".", "/")

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"PackageName('{self.value}')"

    def __hash__(self) -> int:
        return hash(self.value)
