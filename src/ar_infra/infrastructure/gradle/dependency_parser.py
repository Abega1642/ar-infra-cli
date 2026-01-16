"""Parse dependency strings into GradleDependency objects."""

import re
from typing import ClassVar, final

from src.ar_infra.domain.entities.gradle_dependency import (
    GradleConfiguration,
    GradleDependency,
)
from src.ar_infra.domain.exceptions.validation_error import ValidationError


@final
class DependencyParser:
    DEPENDENCY_PATTERN = re.compile(
        r"^\s*(implementation|testImplementation|runtimeOnly|compileOnly|"
        r"annotationProcessor|testRuntimeOnly|api|testAnnotationProcessor|"
        r"testCompileOnly)\s+"
        r"['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    )

    CONFIGURATION_MAP: ClassVar[dict[str, GradleConfiguration]] = {
        "implementation": GradleConfiguration.IMPLEMENTATION,
        "testimplementation": GradleConfiguration.TEST_IMPLEMENTATION,
        "runtimeonly": GradleConfiguration.RUNTIME_ONLY,
        "compileonly": GradleConfiguration.COMPILE_ONLY,
        "annotationprocessor": GradleConfiguration.ANNOTATION_PROCESSOR,
        "testruntimeonly": GradleConfiguration.TEST_RUNTIME_ONLY,
    }

    def parse(self, dependency_string: str) -> GradleDependency:
        if not dependency_string or not dependency_string.strip():
            raise ValidationError("Dependency string cannot be empty")

        match = self.DEPENDENCY_PATTERN.match(dependency_string.strip())
        if not match:
            raise ValidationError(
                f"Invalid dependency format: \n====>\t{dependency_string}.\n\n"
                f"Expected format: 'configuration \"group:name:version\"'\n"
                f"Please check the configuration keywords or the dependency syntax.\n"
            )

        config_str = match.group(1).lower()
        notation = match.group(2)

        configuration = self._parse_configuration(config_str, dependency_string)
        group, name, version = self._parse_notation(notation, dependency_string)

        return GradleDependency(
            group=group,
            name=name,
            version=version,
            configuration=configuration,
        )

    def parse_multiple(self, dependency_strings: list[str]) -> list[GradleDependency]:
        if not dependency_strings:
            raise ValidationError("No dependencies provided")

        dependencies = []
        for dep_str in dependency_strings:
            dependencies.append(self.parse(dep_str))

        return dependencies

    def _parse_configuration(
        self,
        config_str: str,
        original_string: str,
    ) -> GradleConfiguration:
        config = self.CONFIGURATION_MAP.get(config_str)
        if not config:
            raise ValidationError(
                f"Unknown configuration type '{config_str}' in: {original_string}"
            )
        return config

    def _parse_notation(
        self,
        notation: str,
        original_string: str,
    ) -> tuple[str, str, str | None]:
        """Parse Maven notation (group:name:version)."""
        self._validate_notation_security(notation, original_string)

        parts = notation.split(":")
        if len(parts) < 2:
            raise ValidationError(
                f"Invalid dependency notation '{notation}' in: {original_string}. "
                f"Expected format: 'group:name' or 'group:name:version'"
            )

        group = parts[0].strip()
        name = parts[1].strip()
        version = parts[2].strip() if len(parts) >= 3 else None

        if not group:
            raise ValidationError(f"Group ID cannot be empty in: {original_string}")
        if not name:
            raise ValidationError(f"Artifact name cannot be empty in: {original_string}")

        return group, name, version

    @staticmethod
    def _validate_notation_security(notation: str, original_string: str) -> None:
        dangerous_chars = ["..", "/", "\\", ";", "&", "|", "`", "$", "\n", "\r"]

        for char in dangerous_chars:
            if char in notation:
                raise ValidationError(
                    f"Suspicious character '{char}' detected in dependency notation: "
                    f"{original_string}"
                )
