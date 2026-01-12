"""Gradle dependency entity and configuration enum."""

from dataclasses import dataclass
from enum import Enum
from typing import final


class GradleConfiguration(str, Enum):
    IMPLEMENTATION = "implementation"
    TEST_IMPLEMENTATION = "testImplementation"
    RUNTIME_ONLY = "runtimeOnly"
    COMPILE_ONLY = "compileOnly"
    ANNOTATION_PROCESSOR = "annotationProcessor"
    TEST_RUNTIME_ONLY = "testRuntimeOnly"


@final
@dataclass(frozen=True, slots=True)
class GradleDependency:
    """
    Represents a Gradle dependency.

    Attributes:
        group: Maven group ID (e.g., 'org.springframework.boot').
        name: Artifact name (e.g., 'spring-boot-starter-web').
        version: Version (optional, may be managed by BOM).
        configuration: Gradle configuration (e.g., implementation, testImplementation).
    """

    group: str
    name: str
    version: str | None
    configuration: GradleConfiguration

    def to_gradle_notation(self) -> str:
        """
        Convert to Gradle notation.

        Returns:
            String like "org.springframework.boot:spring-boot-starter-web:3.2.0"
            or "org.springframework.boot:spring-boot-starter-web" (if no version).
        """
        if self.version:
            return f"{self.group}:{self.name}:{self.version}"
        return f"{self.group}:{self.name}"

    def __str__(self) -> str:
        return f"{self.configuration.value} '{self.to_gradle_notation()}'"
