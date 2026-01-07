"""Tests for project signature generation."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
from tests.fixtures.sample_infra_generated import INFRA_GENERATED_SAMPLE

from src.ar_infra.domain.value_objects.artifact_id import ArtifactId
from src.ar_infra.domain.value_objects.group_id import GroupId
from src.ar_infra.domain.value_objects.version import Version
from src.ar_infra.infrastructure.template.project_signature import (
    InfraGeneratedAnnotationWriter,
    ProjectSignature,
)
from src.ar_infra.properties import CLI_VERSION


class TestProjectSignature:
    def test_generate_signature_creates_unique_hash(self) -> None:
        signature = ProjectSignature.generate(
            group_id=GroupId("com.example"),
            artifact_id=ArtifactId("test-app"),
            version=Version("1.0.0"),
        )

        assert signature.signature.startswith("ar-infra-cli:")
        hash_part = signature.signature.split(":")[1]
        assert len(hash_part) == 16
        assert all(c in "0123456789abcdef" for c in hash_part)

    def test_generate_signature_is_deterministic(self) -> None:
        sig1 = ProjectSignature.generate(
            group_id=GroupId("dev.razafindratelo"),
            artifact_id=ArtifactId("backend-api"),
            version=Version("2.0.0"),
        )

        sig2 = ProjectSignature.generate(
            group_id=GroupId("dev.razafindratelo"),
            artifact_id=ArtifactId("backend-api"),
            version=Version("2.0.0"),
        )

        assert sig1.signature == sig2.signature

    def test_generate_signature_differs_for_different_projects(self) -> None:
        sig1 = ProjectSignature.generate(
            group_id=GroupId("com.example"),
            artifact_id=ArtifactId("app1"),
            version=Version("1.0.0"),
        )

        sig2 = ProjectSignature.generate(
            group_id=GroupId("com.example"),
            artifact_id=ArtifactId("app2"),
            version=Version("1.0.0"),
        )

        assert sig1.signature != sig2.signature

    def test_version_is_set_correctly(self) -> None:
        signature = ProjectSignature.generate(
            group_id=GroupId("com.test"),
            artifact_id=ArtifactId("myapp"),
            version=Version("1.0.0"),
            cli_version="2.5.0",
        )

        assert signature.version == "2.5.0"

    def test_default_cli_version(self) -> None:
        signature = ProjectSignature.generate(
            group_id=GroupId("com.test"),
            artifact_id=ArtifactId("myapp"),
            version=Version("1.0.0"),
        )

        assert signature.version == CLI_VERSION

    def test_generated_at_is_iso_format(self) -> None:
        """Test that generated_at is in ISO 8601 format."""
        signature = ProjectSignature.generate(
            group_id=GroupId("com.test"),
            artifact_id=ArtifactId("myapp"),
            version=Version("1.0.0"),
        )

        parsed = datetime.fromisoformat(signature.generated_at)
        assert parsed.tzinfo is not None

    def test_generated_at_is_recent(self) -> None:
        before = datetime.now(UTC)

        signature = ProjectSignature.generate(
            group_id=GroupId("com.test"),
            artifact_id=ArtifactId("myapp"),
            version=Version("1.0.0"),
        )

        after = datetime.now(UTC)
        generated = datetime.fromisoformat(signature.generated_at)

        assert before <= generated <= after

    def test_signature_is_immutable(self) -> None:
        """Test that ProjectSignature is immutable."""
        signature = ProjectSignature.generate(
            group_id=GroupId("com.test"),
            artifact_id=ArtifactId("myapp"),
            version=Version("1.0.0"),
        )

        with pytest.raises(AttributeError):
            signature.signature = "modified"  # type: ignore[assignment]


class TestInfraGeneratedAnnotationWriter:
    @pytest.fixture
    def annotation_content(self) -> str:
        return INFRA_GENERATED_SAMPLE

    @pytest.fixture
    def annotation_file(self, tmp_path: Path, annotation_content: str) -> Path:
        file_path = tmp_path / "InfraGenerated.java"
        file_path.write_text(annotation_content, encoding="utf-8")
        return file_path

    @pytest.fixture
    def writer(self) -> InfraGeneratedAnnotationWriter:
        return InfraGeneratedAnnotationWriter()

    @pytest.fixture
    def test_signature(self) -> ProjectSignature:
        return ProjectSignature(
            signature="ar-infra-cli:abc123def4567890",
            version="2.0.0",
            generated_at="2025-12-29T10:30:00+00:00",
        )

    def test_update_annotation_replaces_all_values(
        self,
        writer: InfraGeneratedAnnotationWriter,
        annotation_file: Path,
        test_signature: ProjectSignature,
    ) -> None:
        writer.update_annotation(annotation_file, test_signature)

        content = annotation_file.read_text(encoding="utf-8")

        assert 'String signature() default "ar-infra-cli:abc123def4567890"' in content
        assert 'String version() default "2.0.0"' in content
        assert 'String generatedAt() default "2025-12-29T10:30:00+00:00"' in content

    def test_update_annotation_preserves_structure(
        self,
        writer: InfraGeneratedAnnotationWriter,
        annotation_file: Path,
        test_signature: ProjectSignature,
    ) -> None:
        writer.update_annotation(annotation_file, test_signature)

        content = annotation_file.read_text(encoding="utf-8")

        assert "package com.example.arinfra;" in content
        assert "@interface InfraGenerated" in content
        assert "import static java.lang.annotation.ElementType.*;" in content

    def test_update_annotation_file_not_found(
        self,
        writer: InfraGeneratedAnnotationWriter,
        tmp_path: Path,
        test_signature: ProjectSignature,
    ) -> None:
        non_existent = tmp_path / "NotFound.java"

        with pytest.raises(FileNotFoundError, match="Annotation file not found"):
            writer.update_annotation(non_existent, test_signature)

    def test_update_annotation_invalid_structure_signature(
        self,
        writer: InfraGeneratedAnnotationWriter,
        tmp_path: Path,
        test_signature: ProjectSignature,
    ) -> None:
        """Test error when signature() is not found."""
        invalid_file = tmp_path / "Invalid.java"
        invalid_file.write_text("public @interface Invalid {}", encoding="utf-8")

        with pytest.raises(ValueError, match="Could not find signature\\(\\)"):
            writer.update_annotation(invalid_file, test_signature)

    def test_update_annotation_invalid_structure_version(
        self,
        writer: InfraGeneratedAnnotationWriter,
        tmp_path: Path,
        test_signature: ProjectSignature,
    ) -> None:
        """Test error when version() is not found."""
        invalid_file = tmp_path / "Invalid.java"
        invalid_file.write_text(
            'public @interface Invalid { String signature() default "test"; }',
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="Could not find version\\(\\)"):
            writer.update_annotation(invalid_file, test_signature)

    def test_update_annotation_handles_different_spacing(
        self,
        writer: InfraGeneratedAnnotationWriter,
        tmp_path: Path,
        test_signature: ProjectSignature,
    ) -> None:
        """Test that different spacing in annotation is handled."""
        content = """
public @interface InfraGenerated {
  String   signature()   default   "old-sig";
  String version() default"1.0.0";
  String generatedAt()default"";
}
"""
        file_path = tmp_path / "Spaced.java"
        file_path.write_text(content, encoding="utf-8")

        writer.update_annotation(file_path, test_signature)

        updated = file_path.read_text(encoding="utf-8")

        assert test_signature.signature in updated
        assert test_signature.version in updated
        assert test_signature.generated_at in updated

    def test_update_annotation_is_idempotent(
        self,
        writer: InfraGeneratedAnnotationWriter,
        annotation_file: Path,
        test_signature: ProjectSignature,
    ) -> None:
        writer.update_annotation(annotation_file, test_signature)
        content_after_first = annotation_file.read_text(encoding="utf-8")

        writer.update_annotation(annotation_file, test_signature)
        content_after_second = annotation_file.read_text(encoding="utf-8")

        assert content_after_first == content_after_second
