import re
import shutil
from pathlib import Path

from src.ar_infra.domain.value_objects.package_name import PackageName
from src.ar_infra.infrastructure.processor.exception import (
    PackageRenameError,
    SecurityViolationError,
)


SRC_PKG = "src"
JAVA_PKG = "java"
MAIN_PKG = "main"
TEST_PKG = "test"


class PackageRenamer:
    def rename_package(
        self,
        project_root: Path,
        old_package: PackageName,
        new_package: PackageName,
    ) -> None:
        self._validate_project_root(project_root)

        source_dirs = [
            project_root / SRC_PKG / MAIN_PKG / JAVA_PKG,
            project_root / SRC_PKG / TEST_PKG / JAVA_PKG,
        ]

        for source_dir in source_dirs:
            if not source_dir.exists():
                continue

            old_package_dir = source_dir / old_package.to_path()
            if not old_package_dir.exists():
                if source_dir == source_dirs[0]:
                    raise PackageRenameError(
                        f"Source package directory does not exist: {old_package_dir}"
                    )
                continue

            self._check_for_symlinks(old_package_dir)

            new_package_dir = source_dir / new_package.to_path()
            self._move_package_directory(old_package_dir, new_package_dir)

        self._update_all_java_files(project_root, old_package, new_package)

        self._cleanup_empty_directories(project_root)

    @staticmethod
    def _validate_project_root(project_root: Path) -> None:
        try:
            resolved = project_root.resolve(strict=True)
            if ".." in str(resolved):
                raise SecurityViolationError("Path traversal detected in project root")
        except Exception as e:
            raise SecurityViolationError(f"Invalid or inaccessible project root: {e}") from e

    @staticmethod
    def _check_for_symlinks(directory: Path) -> None:
        for item in directory.rglob("*"):
            if item.is_symlink():
                raise SecurityViolationError(
                    f"Symlink detected: {item}. This could be a security risk."
                )

    @staticmethod
    def _move_package_directory(old_dir: Path, new_dir: Path) -> None:
        new_dir.parent.mkdir(parents=True, exist_ok=True)

        try:
            shutil.move(str(old_dir), str(new_dir))
        except Exception as e:
            raise PackageRenameError(f"Failed to move package directory: {e}") from e

    def _update_all_java_files(
        self,
        project_root: Path,
        old_package: PackageName,
        new_package: PackageName,
    ) -> None:
        java_files = list(project_root.rglob("*.java"))

        for java_file in java_files:
            self._update_java_file(java_file, old_package, new_package)

    def _update_java_file(
        self,
        java_file: Path,
        old_package: PackageName,
        new_package: PackageName,
    ) -> None:
        try:
            content = java_file.read_text(encoding="utf-8")
        except Exception as e:
            raise PackageRenameError(f"Failed to read {java_file}: {e}") from e

        content = self._update_package_declaration(content, old_package, new_package)
        content = self._update_import_statements(content, old_package, new_package)

        try:
            java_file.write_text(content, encoding="utf-8")
        except Exception as e:
            raise PackageRenameError(f"Failed to write {java_file}: {e}") from e

    @staticmethod
    def _update_package_declaration(
        content: str,
        old_package: PackageName,
        new_package: PackageName,
    ) -> str:
        pattern = re.compile(
            rf"^package\s+{re.escape(old_package.value)}(\.[a-z0-9.]+)?;",
            re.MULTILINE,
        )

        def replace_package(match: re.Match[str]) -> str:
            suffix = match.group(1) or ""
            return f"package {new_package.value}{suffix};"

        return pattern.sub(replace_package, content)

    @staticmethod
    def _update_import_statements(
        content: str,
        old_package: PackageName,
        new_package: PackageName,
    ) -> str:
        pattern = re.compile(
            rf"^import\s+(?:static\s+)?{re.escape(old_package.value)}(\.[a-zA-Z0-9.*]+)?;",
            re.MULTILINE,
        )

        def replace_import(match: re.Match[str]) -> str:
            static_keyword = "static " if "static" in match.group(0) else ""
            suffix = match.group(1) or ""
            return f"import {static_keyword}{new_package.value}{suffix};"

        return pattern.sub(replace_import, content)

    @staticmethod
    def _cleanup_empty_directories(project_root: Path) -> None:
        source_dirs = [
            project_root / SRC_PKG / MAIN_PKG / JAVA_PKG,
            project_root / SRC_PKG / TEST_PKG / JAVA_PKG,
        ]

        for source_dir in source_dirs:
            if not source_dir.exists():
                continue

            for directory in sorted(source_dir.rglob("*"), reverse=True):
                if directory.is_dir() and not any(directory.iterdir()):
                    try:
                        directory.rmdir()
                    except OSError:
                        # Best-effort cleanup - ignore if directory cannot be removed
                        # (e.g., permissions, race condition, or already removed)
                        pass
