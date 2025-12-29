"""Helper utilities and fixtures for integration tests."""

import shutil
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest


@dataclass
class ProjectStructure:
    """Expected project structure."""

    root: Path

    @property
    def build_gradle(self) -> Path:
        return self.root / "build.gradle"

    @property
    def settings_gradle(self) -> Path:
        return self.root / "settings.gradle"

    @property
    def src_main_java(self) -> Path:
        return self.root / "src" / "main" / "java"

    @property
    def src_main_resources(self) -> Path:
        return self.root / "src" / "main" / "resources"

    @property
    def src_test_java(self) -> Path:
        return self.root / "src" / "test" / "java"

    def package_dir(self, group: str, artifact: str) -> Path:
        """Get package directory for given group and artifact."""
        parts = [*group.split("."), artifact]
        return self.src_main_java.joinpath(*parts)

    def has_feature_directory(self, group: str, artifact: str, feature_dir: str) -> bool:
        """Check if feature directory exists."""
        package = self.package_dir(group, artifact)
        return (package / feature_dir).exists()

    def get_all_java_files(self) -> list[Path]:
        """Get all Java files in the project."""
        return list(self.root.rglob("*.java"))

    def get_package_java_files(self, group: str, artifact: str) -> list[Path]:
        """Get Java files in main package."""
        package = self.package_dir(group, artifact)
        return list(package.rglob("*.java"))


class ProjectValidator:
    """Validates generated project structure and content."""

    def __init__(self, project_path: Path):
        self.structure = ProjectStructure(project_path)

    def validate_basic_structure(self) -> list[str]:
        """Validate basic project structure. Returns list of errors."""
        errors = []

        if not self.structure.build_gradle.exists():
            errors.append("Missing build.gradle")

        if not self.structure.settings_gradle.exists():
            errors.append("Missing settings.gradle")

        if not self.structure.src_main_java.exists():
            errors.append("Missing src/main/java")

        if not self.structure.src_main_resources.exists():
            errors.append("Missing src/main/resources")

        return errors

    def validate_gradle_configuration(
        self,
        expected_group: str,
        expected_artifact: str,
        expected_version: str,
    ) -> list[str]:
        """Validate Gradle configuration. Returns list of errors."""
        errors = []

        build_content = self.structure.build_gradle.read_text(encoding="utf-8")
        settings_content = self.structure.settings_gradle.read_text(encoding="utf-8")

        if expected_group not in build_content:
            errors.append(f"Group '{expected_group}' not found in build.gradle")

        if expected_version not in build_content:
            errors.append(f"Version '{expected_version}' not found in build.gradle")

        if expected_artifact not in settings_content:
            errors.append(f"Artifact '{expected_artifact}' not found in settings.gradle")

        return errors

    def validate_package_structure(
        self,
        group: str,
        artifact: str,
    ) -> list[str]:
        """Validate package structure. Returns list of errors."""
        errors = []

        package_dir = self.structure.package_dir(group, artifact)
        if not package_dir.exists():
            errors.append(f"Package directory not found: {package_dir}")
            return errors

        java_files = self.structure.get_package_java_files(group, artifact)
        if len(java_files) == 0:
            errors.append("No Java files found in package")

        expected_package = f"{group}.{artifact}"
        for java_file in java_files[:5]:
            content = java_file.read_text(encoding="utf-8")
            if f"package {expected_package}" not in content:
                errors.append(f"Wrong package declaration in {java_file.name}")

        return errors

    def validate_features_present(
        self,
        group: str,
        artifact: str,
        enabled_features: set[str],
    ) -> list[str]:
        """Validate enabled features are present. Returns list of errors."""
        errors = []

        feature_dirs = {
            "postgresql": "repository",
            "rabbitmq": "event",
            "email": "mail",
            "s3_bucket": "file",
        }

        for feature in enabled_features:
            if feature in feature_dirs and not self.structure.has_feature_directory(
                group, artifact, feature_dirs[feature]
            ):
                errors.append(f"Feature directory missing for {feature}: {feature_dirs[feature]}")

        return errors

    def validate_features_absent(
        self,
        group: str,
        artifact: str,
        disabled_features: set[str],
    ) -> list[str]:
        """Validate disabled features are absent. Returns list of errors."""
        errors = []

        feature_dirs = {
            "postgresql": "repository",
            "rabbitmq": "event",
            "email": "mail",
            "s3_bucket": "file",
        }

        for feature in disabled_features:
            if feature in feature_dirs and self.structure.has_feature_directory(
                group, artifact, feature_dirs[feature]
            ):
                errors.append(
                    f"Feature directory should not exist for {feature}: {feature_dirs[feature]}"
                )

        return errors

    def validate_dependencies(
        self,
        expected_deps: list[str],
        forbidden_deps: list[str] | None = None,
    ) -> list[str]:
        """Validate dependencies in build.gradle. Returns list of errors."""
        errors = []

        build_content = self.structure.build_gradle.read_text(encoding="utf-8").lower()

        for dep in expected_deps:
            if dep.lower() not in build_content:
                errors.append(f"Expected dependency not found: {dep}")

        if forbidden_deps:
            for dep in forbidden_deps:
                if dep.lower() in build_content:
                    errors.append(f"Forbidden dependency found: {dep}")

        return errors

    def validate_all(
        self,
        group: str,
        artifact: str,
        version: str,
        enabled_features: set[str],
    ) -> list[str]:
        """Run all validations. Returns list of all errors."""
        errors = []

        errors.extend(self.validate_basic_structure())
        errors.extend(self.validate_gradle_configuration(group, artifact, version))
        errors.extend(self.validate_package_structure(group, artifact))
        errors.extend(self.validate_features_present(group, artifact, enabled_features))

        all_features = {"postgresql", "rabbitmq", "email", "s3_bucket"}
        disabled_features = all_features - enabled_features
        errors.extend(self.validate_features_absent(group, artifact, disabled_features))

        return errors


@pytest.fixture(scope="session")
def integration_test_cache(tmp_path_factory) -> Generator[Path, Any, None]:
    """Create a session-scoped temp directory for integration test cache."""
    cache_dir = tmp_path_factory.mktemp("integration_cache")
    yield cache_dir
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


@pytest.fixture
def project_validator():
    """Factory fixture for creating ProjectValidator instances."""

    def _validator(project_path: Path) -> ProjectValidator:
        return ProjectValidator(project_path)

    return _validator


@pytest.fixture
def assert_project_valid(project_validator):
    """Helper to assert project is valid with detailed error messages."""

    def _assert_valid(
        project_path: Path,
        group: str,
        artifact: str,
        version: str,
        enabled_features: set[str],
    ):
        validator = project_validator(project_path)
        errors = validator.validate_all(group, artifact, version, enabled_features)

        if errors:
            error_msg = "\n".join(f"  - {err}" for err in errors)
            pytest.fail(f"Project validation failed:\n{error_msg}")

    return _assert_valid
