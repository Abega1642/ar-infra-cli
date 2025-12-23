"""Secure Gradle build file writer."""

import re
import shutil
from pathlib import Path

from src.ar_infra.domain.constant import MALICIOUS_PATTERNS
from src.ar_infra.domain.entities.gradle_dependency import GradleDependency
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

        updated = re.sub(
            r"version\s*=\s*['\"][^'\"]*['\"]",
            f"version = '{version.value}'",
            content,
        )

        self._detect_malicious_content(updated)
        self._atomic_write(build_file, updated)

    def update_group_and_version(self, build_file: Path, group: GroupId, version: Version) -> None:
        self._validate_file(build_file)
        content = build_file.read_text(encoding="utf-8")

        updated = re.sub(
            r"group\s*=\s*['\"][^'\"]*['\"]",
            f"group = '{group.value}'",
            content,
        )
        updated = re.sub(
            r"version\s*=\s*['\"][^'\"]*['\"]",
            f"version = '{version.value}'",
            updated,
        )

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
