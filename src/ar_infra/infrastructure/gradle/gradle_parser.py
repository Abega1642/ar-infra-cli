"""Secure Gradle build file parser."""

import re
from pathlib import Path
from typing import Final

from src.ar_infra.domain.entities.gradle_dependency import (
    GradleConfiguration,
    GradleDependency,
)
from src.ar_infra.infrastructure.gradle.gradle_exception import (
    GradleParseError,
    MaliciousContentError,
)


MAX_FILE_SIZE: Final[int] = 5 * 1024 * 1024

MALICIOUS_PATTERNS: Final[list[re.Pattern[str]]] = [
    re.compile(r"System\.exit\("),
    re.compile(r"Runtime\.getRuntime\(\)"),
    re.compile(r"ProcessBuilder"),
    re.compile(r"\.\.\/\.\.\/"),
    re.compile(r"exec\("),
    re.compile(r"`[^`]+`"),
    re.compile(r"\$\([^\)]+\)"),
]

GROUP_PATTERN: Final[re.Pattern[str]] = re.compile(r"group\s*=\s*['\"]([^'\"]+)['\"]")
VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"version\s*=\s*['\"]([^'\"]+)['\"]",
)
JAVA_VERSION_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"sourceCompatibility\s*=\s*['\"]?(\d+)['\"]?",
)
PLUGIN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"id\s+['\"]([^'\"]+)['\"]\s*(?:version\s+['\"]([^'\"]+)['\"])?",
)
DEPENDENCY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(implementation|testImplementation|runtimeOnly|compileOnly|"
    r"annotationProcessor|testRuntimeOnly)\s*\(?\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE | re.DOTALL,
)


class GradleParser:
    """
    Secure parser for Gradle build files.

    Features:
    - Input validation and sanitization
    - Malicious content detection
    - File size limits (DoS prevention)
    - Path traversal protection
    - Command injection prevention
    """

    def parse_group_and_version(self, build_file: Path) -> tuple[str, str]:
        """
        Parse group and version from build.gradle.

        Args:
            build_file: Path to build.gradle file.

        Returns:
            Tuple of (group, version).

        Raises:
            GradleParseError: If parsing fails.
            MaliciousContentError: If malicious content is detected.
        """
        content = self._read_and_validate_file(build_file)

        group_match = GROUP_PATTERN.search(content)
        if not group_match:
            raise GradleParseError(f"Could not find group in {build_file}")
        group = group_match.group(1)

        version_match = VERSION_PATTERN.search(content)
        if not version_match:
            raise GradleParseError(f"Could not find version in {build_file}")
        version = version_match.group(1)

        self._validate_group(group)
        self._validate_version(version)

        return group, version

    def parse_dependencies(self, build_file: Path) -> list[GradleDependency]:
        """
        Parse dependencies from build.gradle.

        Args:
            build_file: Path to build.gradle file.

        Returns:
            List of GradleDependency objects.

        Raises:
            GradleParseError: If parsing fails.
            MaliciousContentError: If malicious content is detected.
        """
        content = self._read_and_validate_file(build_file)

        dependencies: list[GradleDependency] = []

        for match in DEPENDENCY_PATTERN.finditer(content):
            config_str = match.group(1)
            dependency_str = match.group(2)

            if ".." in dependency_str or "/" in dependency_str or "\\" in dependency_str:
                raise MaliciousContentError(
                    f"Suspicious dependency path detected: {dependency_str}",
                )

            config = self._parse_configuration(config_str)

            parts = dependency_str.split(":")
            if len(parts) < 2:
                continue

            group = parts[0]
            name = parts[1]
            version = parts[2] if len(parts) >= 3 else None

            dependencies.append(
                GradleDependency(
                    group=group,
                    name=name,
                    version=version,
                    configuration=config,
                ),
            )

        return dependencies

    def parse_java_version(self, build_file: Path) -> str:
        """
        Parse Java version from build.gradle.

        Args:
            build_file: Path to build.gradle file.

        Returns:
            Java version as string (e.g., "21").

        Raises:
            GradleParseError: If parsing fails.
        """
        content = self._read_and_validate_file(build_file)

        match = JAVA_VERSION_PATTERN.search(content)
        if not match:
            raise GradleParseError(f"Could not find Java version in {build_file}")

        return match.group(1)

    def parse_plugins(self, build_file: Path) -> dict[str, str | None]:
        """
        Parse plugins from build.gradle.

        Args:
            build_file: Path to build.gradle file.

        Returns:
            Dictionary of plugin_id -> version (or None if no version).

        Raises:
            GradleParseError: If parsing fails.
        """
        content = self._read_and_validate_file(build_file)

        plugins: dict[str, str | None] = {}

        for match in PLUGIN_PATTERN.finditer(content):
            plugin_id = match.group(1)
            version = match.group(2) if match.lastindex and match.lastindex >= 2 else None
            plugins[plugin_id] = version

        return plugins

    def _read_and_validate_file(self, file_path: Path) -> str:
        """
        Read and validate Gradle file with security checks.

        Args:
            file_path: Path to file.

        Returns:
            File content as string.

        Raises:
            GradleParseError: If file is invalid.
            MaliciousContentError: If malicious content is detected.
        """
        if not file_path.exists():
            raise GradleParseError(f"File does not exist: {file_path}")

        if not file_path.is_file():
            raise GradleParseError(f"Not a file: {file_path}")

        file_size = file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise GradleParseError(
                f"File is too large ({file_size} bytes, max {MAX_FILE_SIZE})",
            )

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise GradleParseError(f"File encoding error: {e}") from e
        except Exception as e:
            raise GradleParseError(f"Failed to read file: {e}") from e

        self._detect_malicious_content(content, file_path)

        return content

    def _detect_malicious_content(self, content: str, file_path: Path) -> None:
        """
        Detect potentially malicious content in Gradle files.

        Args:
            content: File content.
            file_path: Path to file (for error messages).

        Raises:
            MaliciousContentError: If malicious content is detected.
        """
        for pattern in MALICIOUS_PATTERNS:
            if pattern.search(content):
                raise MaliciousContentError(
                    f"Potentially malicious content detected in {file_path}. "
                    f"Pattern matched: {pattern.pattern}",
                )

    def _validate_group(self, group: str) -> None:
        """
        Validate group ID.

        Args:
            group: Group ID to validate.

        Raises:
            GradleParseError: If group is invalid.
        """
        if not group or not group.strip():
            raise GradleParseError("Group ID cannot be empty")

        if ".." in group or "/" in group or "\\" in group:
            raise GradleParseError(f"Invalid group ID: {group}")

    def _validate_version(self, version: str) -> None:
        """
        Validate version string.

        Args:
            version: Version to validate.

        Raises:
            GradleParseError: If version is invalid.
        """
        if not version or not version.strip():
            raise GradleParseError("Version cannot be empty")

        if any(char in version for char in [";", "&", "|", "`", "$"]):
            raise GradleParseError(f"Invalid version: {version}")

    def _parse_configuration(self, config_str: str) -> GradleConfiguration:
        """
        Parse configuration string to enum.

        Args:
            config_str: Configuration string (e.g., "implementation").

        Returns:
            GradleConfiguration enum value.
        """
        config_map = {
            "implementation": GradleConfiguration.IMPLEMENTATION,
            "testImplementation": GradleConfiguration.TEST_IMPLEMENTATION,
            "runtimeOnly": GradleConfiguration.RUNTIME_ONLY,
            "compileOnly": GradleConfiguration.COMPILE_ONLY,
            "annotationProcessor": GradleConfiguration.ANNOTATION_PROCESSOR,
            "testRuntimeOnly": GradleConfiguration.TEST_RUNTIME_ONLY,
        }

        return config_map.get(config_str, GradleConfiguration.IMPLEMENTATION)
