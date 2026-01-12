from pathlib import Path

from src.ar_infra.domain.constant import (
    DEPENDENCY_PATTERN,
    GROUP_PATTERN,
    JAVA_VERSION_PATTERN,
    MALICIOUS_PATTERNS,
    MAX_FILE_SIZE,
    PLUGIN_PATTERN,
    VERSION_PATTERN,
)
from src.ar_infra.domain.entities.gradle_dependency import (
    GradleConfiguration,
    GradleDependency,
)
from src.ar_infra.infrastructure.gradle.gradle_exception import (
    GradleParseError,
    MaliciousContentError,
)


class GradleParser:
    def parse_group_and_version(self, build_file: Path) -> tuple[str, str]:
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
        content = self._read_and_validate_file(build_file)

        match = JAVA_VERSION_PATTERN.search(content)
        if not match:
            raise GradleParseError(f"Could not find Java version in {build_file}")

        return match.group(1)

    def parse_plugins(self, build_file: Path) -> dict[str, str | None]:
        content = self._read_and_validate_file(build_file)

        plugins: dict[str, str | None] = {}

        for match in PLUGIN_PATTERN.finditer(content):
            plugin_id = match.group(1)
            version = match.group(2) if match.lastindex and match.lastindex >= 2 else None
            plugins[plugin_id] = version

        return plugins

    def _read_and_validate_file(self, file_path: Path) -> str:
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

    @staticmethod
    def _detect_malicious_content(content: str, file_path: Path) -> None:
        for pattern in MALICIOUS_PATTERNS:
            if pattern.search(content):
                raise MaliciousContentError(
                    f"Potentially malicious content detected in {file_path}. "
                    f"Pattern matched: {pattern.pattern}",
                )

    @staticmethod
    def _validate_group(group: str) -> None:
        if not group or not group.strip():
            raise GradleParseError("Group ID cannot be empty")

        if ".." in group or "/" in group or "\\" in group:
            raise GradleParseError(f"Invalid group ID: {group}")

    @staticmethod
    def _validate_version(version: str) -> None:
        if not version or not version.strip():
            raise GradleParseError("Version cannot be empty")

        if any(char in version for char in [";", "&", "|", "`", "$"]):
            raise GradleParseError(f"Invalid version: {version}")

    @staticmethod
    def _parse_configuration(config_str: str) -> GradleConfiguration:
        config_map = {
            "implementation": GradleConfiguration.IMPLEMENTATION,
            "testImplementation": GradleConfiguration.TEST_IMPLEMENTATION,
            "runtimeOnly": GradleConfiguration.RUNTIME_ONLY,
            "compileOnly": GradleConfiguration.COMPILE_ONLY,
            "annotationProcessor": GradleConfiguration.ANNOTATION_PROCESSOR,
            "testRuntimeOnly": GradleConfiguration.TEST_RUNTIME_ONLY,
        }

        return config_map.get(config_str, GradleConfiguration.IMPLEMENTATION)
