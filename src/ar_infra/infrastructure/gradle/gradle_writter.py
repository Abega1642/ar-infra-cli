"""Secure Gradle build file writer."""

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


class GradleWriter:
    """Secure writer for modifying Gradle build files."""

    def update_group(self, build_file: Path, group: GroupId) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        updated = re.sub(
            r"group\s*=\s*['\"][^'\"]*['\"]",
            f"group = '{group.value}'",
            content,
        )

        self._detect_malicious_content(updated)
        self._atomic_write(build_file, updated)

    def update_version(self, build_file: Path, version: Version) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        pattern = r"version\s*=\s*['\"][^'\"]*['\"]"
        if re.search(pattern, content):
            updated = re.sub(pattern, f"version = '{version.value}'", content)
        else:
            java_block_pattern = r"(java\s*\{[^}]*group\s*=\s*['\"][^'\"]*['\"])"
            match = re.search(java_block_pattern, content, re.DOTALL)

            if match:
                insertion_point = match.end()
                updated = (
                    content[:insertion_point]
                    + f"\n    version = '{version.value}'"
                    + content[insertion_point:]
                )
            else:
                plugins_end = content.find("}\n", content.find("plugins {"))
                if plugins_end != -1:
                    updated = (
                        content[: plugins_end + 2]
                        + f"\nversion = '{version.value}'\n"
                        + content[plugins_end + 2 :]
                    )
                else:
                    raise GradleWriteError("Cannot find suitable location for version")

        self._detect_malicious_content(updated)
        self._atomic_write(build_file, updated)

    def update_settings_gradle(self, settings_file: Path, artifact: ArtifactId) -> None:
        """Update rootProject.name in settings.gradle ."""
        self._validate_file(settings_file)
        content = settings_file.read_text(encoding="utf-8")

        updated = re.sub(
            r"rootProject\.name\s*=\s*['\"][^'\"]*['\"]",
            f"rootProject.name = '{artifact.value}'",
            content,
        )

        self._detect_malicious_content(updated)
        self._atomic_write(settings_file, updated)

    def update_group_and_version(self, build_file: Path, group: GroupId, version: Version) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        updated = re.sub(
            r"group\s*=\s*['\"][^'\"]*['\"]",
            f"group = '{group.value}'",
            content,
        )

        version_pattern = r"version\s*=\s*['\"][^'\"]*['\"]"
        if re.search(version_pattern, updated):
            updated = re.sub(version_pattern, f"version = '{version.value}'", updated)
        else:
            java_block_pattern = r"(java\s*\{[^}]*group\s*=\s*['\"][^'\"]*['\"])"
            match = re.search(java_block_pattern, updated, re.DOTALL)

            if match:
                insertion_point = match.end()
                updated = (
                    updated[:insertion_point]
                    + f"\n    version = '{version.value}'"
                    + updated[insertion_point:]
                )
            else:
                plugins_end = updated.find("}\n", updated.find("plugins {"))
                if plugins_end != -1:
                    updated = (
                        updated[: plugins_end + 2]
                        + f"\nversion = '{version.value}'\n"
                        + updated[plugins_end + 2 :]
                    )
                else:
                    raise GradleWriteError("Cannot find suitable location for version")

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

    def remove_dependencies_except(self, build_file: Path, allowed_dependencies: list[str]) -> None:
        """Remove all dependencies except those in the allowed list.

        Args:
            build_file: Path to build.gradle file
            allowed_dependencies: List of dependency notations (e.g., 'org.postgresql:postgresql')
        """
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        allowed_set = set(allowed_dependencies)

        dependencies_pattern = re.compile(
            r"(dependencies\s*\{)(.*?)(\n\})",
            re.DOTALL,
        )

        match = dependencies_pattern.search(content)
        if not match:
            return

        opening = match.group(1)
        deps_content = match.group(2)
        closing = match.group(3)

        filtered_lines = self._filter_dependency_lines(deps_content, allowed_set)

        if filtered_lines:
            updated_deps = f"{opening}\n{filtered_lines}{closing}"
        else:
            updated_deps = f"{opening}{closing}"

        updated_content = content[: match.start()] + updated_deps + content[match.end() :]

        self._detect_malicious_content(updated_content)
        self._atomic_write(build_file, updated_content)

    def _filter_dependency_lines(self, deps_content: str, allowed_set: set[str]) -> str:
        """Filter dependency lines, keeping only allowed ones."""
        lines = deps_content.split("\n")
        filtered = []

        dep_pattern = re.compile(
            r"^\s*(implementation|testImplementation|runtimeOnly|compileOnly|api)\s*"
            r"[\(\[]?\s*['\"]([^'\"]+)['\"]",
            re.IGNORECASE,
        )

        for line in lines:
            match = dep_pattern.match(line)
            if match:
                full_notation = match.group(2)
                parts = full_notation.split(":")
                if len(parts) >= 2:
                    group_artifact = f"{parts[0]}:{parts[1]}"

                    if group_artifact in allowed_set or full_notation in allowed_set:
                        filtered.append(line)
            elif line.strip() and not line.strip().startswith("//"):
                if not any(
                    conf in line
                    for conf in [
                        "implementation",
                        "testImplementation",
                        "runtimeOnly",
                        "compileOnly",
                        "api",
                    ]
                ):
                    filtered.append(line)
            elif line.strip().startswith("//") or not line.strip():
                filtered.append(line)

        return "\n".join(filtered)

    def remove_dependency(self, build_file: Path, dependency_notation: str) -> None:
        """Remove a specific dependency from build.gradle.

        Args:
            build_file: Path to build.gradle file
            dependency_notation: Dependency notation (e.g., 'org.postgresql:postgresql')
        """
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        dependencies_pattern = re.compile(
            r"(dependencies\s*\{)(.*?)(\n\})",
            re.DOTALL,
        )

        match = dependencies_pattern.search(content)
        if not match:
            return

        opening = match.group(1)
        deps_content = match.group(2)
        closing = match.group(3)

        lines = deps_content.split("\n")
        filtered_lines = []

        for line in lines:
            if dependency_notation not in line:
                filtered_lines.append(line)
            else:
                continue

        updated_deps_content = "\n".join(filtered_lines)
        updated_deps = f"{opening}{updated_deps_content}{closing}"

        updated_content = content[: match.start()] + updated_deps + content[match.end() :]

        self._detect_malicious_content(updated_content)
        self._atomic_write(build_file, updated_content)

    def _dependency_exists(self, content: str, dependency: GradleDependency) -> bool:
        pattern = re.compile(
            rf"{dependency.configuration.value}\s+['\"].*{re.escape(dependency.name)}.*['\"]"
        )
        return pattern.search(content) is not None

    def _format_dependency(self, dependency: GradleDependency) -> str:
        notation = dependency.to_gradle_notation()
        return f"    {dependency.configuration.value} '{notation}'"

    def _add_to_existing_dependencies(self, content: str, dependency_line: str) -> str:
        dependencies_pattern = re.compile(
            r"(dependencies\s*\{)(.*?)(\n\})",
            re.DOTALL,
        )

        match = dependencies_pattern.search(content)
        if not match:
            raise GradleWriteError("Could not locate dependencies block")

        opening = match.group(1)
        deps_content = match.group(2)
        closing = match.group(3)

        updated_deps = f"{opening}{deps_content}\n{dependency_line}{closing}"

        return content[: match.start()] + updated_deps + content[match.end() :]

    def _create_dependencies_block(self, content: str, dependency_line: str) -> str:
        dependencies_block = f"\ndependencies {{\n{dependency_line}\n}}\n"
        return content + dependencies_block

    def _validate_file(self, file_path: Path) -> None:
        if not file_path.exists():
            raise GradleWriteError(f"File does not exist: {file_path}")

        if not file_path.is_file():
            raise GradleWriteError(f"Not a file: {file_path}")

    def _detect_malicious_content(self, content: str) -> None:
        for pattern in MALICIOUS_PATTERNS:
            if pattern.search(content):
                raise MaliciousContentError(
                    f"Potentially malicious content detected. Pattern: {pattern.pattern}",
                )

    def _atomic_write(self, file_path: Path, content: str) -> None:
        backup_path = file_path.with_suffix(".gradle.bak")

        try:
            shutil.copy2(file_path, backup_path)

            file_path.write_text(content, encoding="utf-8")

            backup_path.unlink()
        except Exception as e:
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
                backup_path.unlink()
            raise GradleWriteError(f"Failed to write file: {e}") from e
