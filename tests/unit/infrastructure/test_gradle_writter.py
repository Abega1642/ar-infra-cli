"""Tests for GradleWriter."""

from pathlib import Path

import pytest
from tests.fixtures.sample_build_gradle import (
    BUILD_GRADLE_WITHOUT_DEPENDENCIES,
    SAMPLE_BUILD_GRADLE,
)

from src.ar_infra.domain.entities.gradle_dependency import (
    GradleConfiguration,
    GradleDependency,
)
from src.ar_infra.domain.exceptions.validation_error import InvalidGroupIdError
from src.ar_infra.domain.value_objects.group_id import GroupId
from src.ar_infra.domain.value_objects.version import Version
from src.ar_infra.infrastructure.gradle.gradle_exception import (
    GradleWriteError,
    MaliciousContentError,
)
from src.ar_infra.infrastructure.gradle.gradle_writter import GradleWriter


class TestGradleWriter:
    """Test suite for GradleWriter."""

    @pytest.fixture
    def writer(self) -> GradleWriter:
        return GradleWriter()

    @pytest.fixture
    def sample_build_file(self, tmp_path: Path) -> Path:
        build_file = tmp_path / "build.gradle"
        build_file.write_text(SAMPLE_BUILD_GRADLE)
        return build_file

    def test_update_group(self, writer: GradleWriter, sample_build_file: Path) -> None:
        new_group = GroupId("dev.razafindratelo")
        writer.update_group(sample_build_file, new_group)

        content = sample_build_file.read_text()
        assert "group = 'dev.razafindratelo'" in content
        assert "group = 'com.example'" not in content

    def test_update_version(self, writer: GradleWriter, sample_build_file: Path) -> None:
        new_version = Version("1.2.3")
        writer.update_version(sample_build_file, new_version)

        content = sample_build_file.read_text()
        assert "version = '1.2.3'" in content
        assert "version = '0.0.1-SNAPSHOT'" not in content

    def test_update_group_and_version(self, writer: GradleWriter, sample_build_file: Path) -> None:
        new_group = GroupId("com.company")
        new_version = Version("2.0.0")
        writer.update_group_and_version(sample_build_file, new_group, new_version)

        content = sample_build_file.read_text()
        assert "group = 'com.company'" in content
        assert "version = '2.0.0'" in content

    def test_add_dependency_to_existing_block(
        self, writer: GradleWriter, sample_build_file: Path
    ) -> None:
        dependency = GradleDependency(
            group="org.postgresql",
            name="postgresql",
            version=None,
            configuration=GradleConfiguration.IMPLEMENTATION,
        )

        writer.add_dependency(sample_build_file, dependency)

        content = sample_build_file.read_text()
        assert "implementation 'org.postgresql:postgresql'" in content

    def test_add_dependency_with_version(
        self, writer: GradleWriter, sample_build_file: Path
    ) -> None:
        dependency = GradleDependency(
            group="redis.clients",
            name="jedis",
            version="4.3.0",
            configuration=GradleConfiguration.IMPLEMENTATION,
        )

        writer.add_dependency(sample_build_file, dependency)

        content = sample_build_file.read_text()
        assert "implementation 'redis.clients:jedis:4.3.0'" in content

    def test_add_test_dependency(self, writer: GradleWriter, sample_build_file: Path) -> None:
        dependency = GradleDependency(
            group="org.testcontainers",
            name="postgresql",
            version="1.19.0",
            configuration=GradleConfiguration.TEST_IMPLEMENTATION,
        )

        writer.add_dependency(sample_build_file, dependency)

        content = sample_build_file.read_text()
        assert "testImplementation 'org.testcontainers:postgresql:1.19.0'" in content

    def test_add_dependency_creates_block_if_missing(
        self, writer: GradleWriter, tmp_path: Path
    ) -> None:
        build_file = tmp_path / "build.gradle"
        build_file.write_text(BUILD_GRADLE_WITHOUT_DEPENDENCIES)

        dependency = GradleDependency(
            group="org.postgresql",
            name="postgresql",
            version=None,
            configuration=GradleConfiguration.IMPLEMENTATION,
        )

        writer.add_dependency(build_file, dependency)

        content = build_file.read_text()
        assert "dependencies {" in content
        assert "implementation 'org.postgresql:postgresql'" in content
        assert "}" in content

    def test_add_multiple_dependencies(self, writer: GradleWriter, sample_build_file: Path) -> None:
        deps = [
            GradleDependency(
                "org.postgresql", "postgresql", None, GradleConfiguration.IMPLEMENTATION
            ),
            GradleDependency("redis.clients", "jedis", "4.3.0", GradleConfiguration.IMPLEMENTATION),
        ]

        for dep in deps:
            writer.add_dependency(sample_build_file, dep)

        content = sample_build_file.read_text()
        assert "implementation 'org.postgresql:postgresql'" in content
        assert "implementation 'redis.clients:jedis:4.3.0'" in content

    def test_prevent_duplicate_dependencies(
        self, writer: GradleWriter, sample_build_file: Path
    ) -> None:
        dependency = GradleDependency(
            group="org.springframework.boot",
            name="spring-boot-starter-web",
            version=None,
            configuration=GradleConfiguration.IMPLEMENTATION,
        )

        writer.add_dependency(sample_build_file, dependency)

        content = sample_build_file.read_text()
        count = content.count("spring-boot-starter-web")
        assert count == 1

    def test_domain_validation_prevents_malicious_group(
        self, writer: GradleWriter, sample_build_file: Path
    ) -> None:
        with pytest.raises(InvalidGroupIdError):
            GroupId("com.example'; System.exit(0); //'")

    def test_writer_detects_malicious_patterns(self, writer: GradleWriter, tmp_path: Path) -> None:
        build_file = tmp_path / "build.gradle"
        malicious_content = """
plugins {
    id 'java'
}

group = 'com.example'
version = '1.0.0'

task dangerous {
    doLast {
        // This should trigger the System.exit( pattern
        System.exit(0)
    }
}

dependencies {
    implementation 'org.springframework.boot:spring-boot-starter-web'
}
"""
        build_file.write_text(malicious_content)

        with pytest.raises(MaliciousContentError):
            writer.update_version(build_file, Version("2.0.0"))

    def test_write_preserves_formatting(
        self, writer: GradleWriter, sample_build_file: Path
    ) -> None:
        original = sample_build_file.read_text()
        original_line_count = len(original.split("\n"))

        writer.update_group(sample_build_file, GroupId("dev.razafindratelo"))

        updated = sample_build_file.read_text()
        updated_line_count = len(updated.split("\n"))

        assert abs(original_line_count - updated_line_count) <= 2

    def test_handle_nonexistent_file(self, writer: GradleWriter) -> None:
        with pytest.raises(GradleWriteError, match="does not exist"):
            writer.update_group(Path("/nonexistent/build.gradle"), GroupId("com.example"))
