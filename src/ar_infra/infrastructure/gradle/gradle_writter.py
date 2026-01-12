import re
import shutil
from pathlib import Path

from src.ar_infra.domain.constant import MALICIOUS_PATTERNS
from src.ar_infra.domain.entities.gradle_dependency import GradleDependency
from src.ar_infra.domain.value_objects import ArtifactId
from src.ar_infra.domain.value_objects.group_id import GroupId
from src.ar_infra.domain.value_objects.version import Version
from src.ar_infra.infrastructure.gradle.gradle_exception import (
    GradleWriteError,
    MaliciousContentError,
)


DEP_REG = r"(dependencies\s*\{)(.*?)(\n\})"
CONFIGURATIONS = [
    "implementation",
    "testImplementation",
    "runtimeOnly",
    "compileOnly",
    "api",
    "annotationProcessor",
    "testAnnotationProcessor",
    "testCompileOnly",
    "testRuntimeOnly",
]
DEP_PATTERN = re.compile(
    r"^\s*(implementation|testImplementation|runtimeOnly|compileOnly|api|"
    r"annotationProcessor|testAnnotationProcessor|testCompileOnly|testRuntimeOnly)\s*"
    r"[(\[]?\s*['\"]([^'\"]+)['\"]",
    re.IGNORECASE,
)
GROUP_PATTERN = re.compile(r"group\s*=\s*['\"][^'\"]*['\"]")
VERSION_PATTERN = re.compile(r"version\s*=\s*['\"][^'\"]*['\"]")
SETTINGS_NAME_PATTERN = re.compile(r"rootProject\.name\s*=\s*['\"][^'\"]*['\"]")
JAVA_BLOCK_WITH_GROUP_PATTERN = re.compile(
    r"(java\s*\{[^}]*group\s*=\s*['\"][^'\"]*['\"])",
    re.DOTALL,
)


class GradleWriter:
    def update_group(self, build_file: Path, group: GroupId) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        updated = GROUP_PATTERN.sub(f"group = '{group.value}'", content)

        self._detect_malicious_content(updated)
        self._atomic_write(build_file, updated)

    def update_version(self, build_file: Path, version: Version) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        updated = self._replace_or_insert_version(content, version.value)

        self._detect_malicious_content(updated)
        self._atomic_write(build_file, updated)

    def update_settings_gradle(self, settings_file: Path, artifact: ArtifactId) -> None:
        """Update rootProject.name in settings.gradle."""
        self._validate_file(settings_file)
        content = settings_file.read_text(encoding="utf-8")

        updated = SETTINGS_NAME_PATTERN.sub(
            f"rootProject.name = '{artifact.value}'",
            content,
        )

        self._detect_malicious_content(updated)
        self._atomic_write(settings_file, updated)

    def update_group_and_version(self, build_file: Path, group: GroupId, version: Version) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        updated = GROUP_PATTERN.sub(f"group = '{group.value}'", content)
        updated = self._replace_or_insert_version(updated, version.value)

        self._detect_malicious_content(updated)
        self._atomic_write(build_file, updated)

    def add_dependency(self, build_file: Path, dependency: GradleDependency) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        if self._dependency_exists(content, dependency):
            return

        dependency_line = self._format_dependency(dependency)

        if "dependencies {" in content:
            updated = self._add_to_existing_dependencies(content, dependency_line)
        else:
            updated = self._create_dependencies_block(content, dependency_line)

        self._detect_malicious_content(updated)
        self._atomic_write(build_file, updated)

    def remove_dependencies(self, build_file: Path, dependencies_to_remove: list[str]) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        to_remove_set = set(dependencies_to_remove)
        dependencies_pattern = re.compile(DEP_REG, re.DOTALL)

        match = dependencies_pattern.search(content)
        if not match:
            return

        opening, deps_content, closing = match.groups()
        filtered_lines = self._remove_matching_dependencies(deps_content, to_remove_set)

        updated_deps = f"{opening}{filtered_lines}{closing}"
        updated_content = content[: match.start()] + updated_deps + content[match.end() :]

        self._detect_malicious_content(updated_content)
        self._atomic_write(build_file, updated_content)

    def remove_dependency(self, build_file: Path, dependency_notation: str) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        dependencies_pattern = re.compile(DEP_REG, re.DOTALL)
        match = dependencies_pattern.search(content)
        if not match:
            return

        opening, deps_content, closing = match.groups()
        filtered_lines = [
            line for line in deps_content.split("\n") if dependency_notation not in line
        ]

        updated_deps_content = "\n".join(filtered_lines)
        updated_deps = f"{opening}{updated_deps_content}{closing}"
        updated_content = content[: match.start()] + updated_deps + content[match.end() :]

        self._detect_malicious_content(updated_content)
        self._atomic_write(build_file, updated_content)

    def _remove_matching_dependencies(self, deps_content: str, to_remove_set: set[str]) -> str:
        lines = deps_content.split("\n")
        filtered = []

        for line in lines:
            if self._is_comment_or_empty(line):
                filtered.append(line)
                continue

            if self._is_non_dependency_line(line):
                filtered.append(line)
                continue

            if not self._should_remove_dependency(line, to_remove_set):
                filtered.append(line)

        return "\n".join(filtered)

    @staticmethod
    def _should_remove_dependency(line: str, to_remove_set: set[str]) -> bool:
        match = DEP_PATTERN.match(line)
        if not match:
            return False

        full_notation = match.group(2)
        parts = full_notation.split(":")
        if len(parts) < 2:
            return False

        group_artifact = f"{parts[0]}:{parts[1]}"
        return group_artifact in to_remove_set or full_notation in to_remove_set

    @staticmethod
    def _is_non_dependency_line(line: str) -> bool:
        stripped = line.strip()
        if not stripped:
            return False
        if stripped.startswith("//"):
            return False
        return not any(conf in line for conf in CONFIGURATIONS)

    @staticmethod
    def _is_comment_or_empty(line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("//") or not stripped

    @staticmethod
    def _replace_or_insert_version(content: str, version_value: str) -> str:
        if VERSION_PATTERN.search(content):
            return VERSION_PATTERN.sub(f"version = '{version_value}'", content)

        match = JAVA_BLOCK_WITH_GROUP_PATTERN.search(content)
        if match:
            insertion_point = match.end()
            return (
                content[:insertion_point]
                + f"\n    version = '{version_value}'"
                + content[insertion_point:]
            )

        plugins_start = content.find("plugins {")
        plugins_end = content.find("}\n", plugins_start) if plugins_start != -1 else -1
        if plugins_end != -1:
            return (
                content[: plugins_end + 2]
                + f"\nversion = '{version_value}'\n"
                + content[plugins_end + 2 :]
            )

        raise GradleWriteError("Cannot find suitable location for version")

    @staticmethod
    def _dependency_exists(content: str, dependency: GradleDependency) -> bool:
        pattern = re.compile(
            rf"{dependency.configuration.value}\s+['\"].*{re.escape(dependency.name)}.*['\"]"
        )
        return pattern.search(content) is not None

    @staticmethod
    def _format_dependency(dependency: GradleDependency) -> str:
        notation = dependency.to_gradle_notation()
        return f"    {dependency.configuration.value} '{notation}'"

    @staticmethod
    def _add_to_existing_dependencies(content: str, dependency_line: str) -> str:
        dependencies_pattern = re.compile(DEP_REG, re.DOTALL)
        match = dependencies_pattern.search(content)
        if not match:
            raise GradleWriteError("Could not locate dependencies block")

        opening, deps_content, closing = match.groups()
        updated_deps = f"{opening}{deps_content}\n{dependency_line}{closing}"
        return content[: match.start()] + updated_deps + content[match.end() :]

    @staticmethod
    def _create_dependencies_block(content: str, dependency_line: str) -> str:
        return content + f"\ndependencies {{\n{dependency_line}\n}}\n"

    @staticmethod
    def _validate_file(file_path: Path) -> None:
        if not file_path.exists():
            raise GradleWriteError(f"File does not exist: {file_path}")
        if not file_path.is_file():
            raise GradleWriteError(f"Not a file: {file_path}")

    @staticmethod
    def _detect_malicious_content(content: str) -> None:
        for pattern in MALICIOUS_PATTERNS:
            if pattern.search(content):
                raise MaliciousContentError(
                    f"Potentially malicious content detected. Pattern: {pattern.pattern}",
                )

    @staticmethod
    def _atomic_write(file_path: Path, content: str) -> None:
        backup_path = file_path.with_suffix(".gradle.bak")
        try:
            shutil.copy2(file_path, backup_path)

            file_path.write_text(content, encoding="utf-8")

            backup_path.unlink()
        except OSError as e:
            if backup_path.exists():
                try:
                    shutil.copy2(backup_path, file_path)
                    backup_path.unlink()
                except OSError:
                    # Rollback failed - original error is more important to surface
                    # File may be in inconsistent state but original exception provides context
                    pass
            raise GradleWriteError(f"Failed to write file: {e}") from e
