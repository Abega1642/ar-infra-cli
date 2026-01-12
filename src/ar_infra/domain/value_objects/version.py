import re
from dataclasses import dataclass, field
from typing import final

from src.ar_infra.domain.constant import (
    DANGEROUS_CHARACTERS,
    SEMANTIC_VERSION_PATTERN,
)
from src.ar_infra.domain.exceptions.validation_error import InvalidVersionError


_QUALIFIER_LABEL_RANK = {
    "SNAPSHOT": 0,
    "ALPHA": 1,
    "BETA": 2,
    "M": 3,
    "RC": 4,
}


@final
@dataclass(frozen=True, slots=True)
class Version:
    value: str
    _parsed: tuple[int, int, int, str | None] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._validate()
        object.__setattr__(self, "_parsed", self._parse())

    def _validate(self) -> None:
        if not self.value or not self.value.strip():
            raise InvalidVersionError("Version cannot be empty")

        if any(char in self.value for char in DANGEROUS_CHARACTERS):
            raise InvalidVersionError("Version contains potentially dangerous characters")

        if not SEMANTIC_VERSION_PATTERN.fullmatch(self.value):
            raise InvalidVersionError(
                f"Version '{self.value}' does not match semantic versioning format",
            )

    def _parse(self) -> tuple[int, int, int, str | None]:
        match = SEMANTIC_VERSION_PATTERN.fullmatch(self.value)
        if not match:
            raise InvalidVersionError("Failed to parse version")

        return (
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            match.group(4),
        )

    @property
    def major(self) -> int:
        return self._parsed[0]

    @property
    def minor(self) -> int:
        return self._parsed[1]

    @property
    def patch(self) -> int:
        return self._parsed[2]

    @property
    def qualifier(self) -> str | None:
        return self._parsed[3]

    @property
    def is_snapshot(self) -> bool:
        return self.qualifier is not None and self.qualifier.upper() == "SNAPSHOT"

    def _qualifier_key(self) -> tuple[int, int, int]:
        if self.qualifier is None:
            return 5, 0, 0

        q = self.qualifier.upper()

        if q == "SNAPSHOT":
            return 0, 0, 0

        match = re.match(r"(ALPHA|BETA|RC|M)[.-]?(\d+)?", q)
        if match:
            return (
                1,
                _QUALIFIER_LABEL_RANK[match.group(1)],
                int(match.group(2)) if match.group(2) else 0,
            )

        return 4, 0, 0

    def __lt__(self, other: "Version") -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch

        return self._qualifier_key() < other._qualifier_key()

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Version('{self.value}')"

    def __hash__(self) -> int:
        return hash(self.value)
