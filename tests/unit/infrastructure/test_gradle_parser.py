"""Tests for Gradle parser."""

from pathlib import Path

import pytest
from tests.fixtures.sample_build_gradle import (
    MALICIOUS_BUILD_GRADLE,
    SAMPLE_BUILD_GRADLE,
)

from src.ar_infra.domain.entities.gradle_dependency import GradleConfiguration
from src.ar_infra.infrastructure.gradle.gradle_exception import (
    GradleParseError,
    MaliciousContentError,
)
from src.ar_infra.infrastructure.gradle.gradle_parser import GradleParser


class TestGradleParser:
    """Test suite for GradleParser."""

    @pytest.fixture
    def parser(self) -> GradleParser:
        """Create GradleParser instance."""
        return GradleParser()

    @pytest.fixture
    def sample_build_file(self, tmp_path: Path) -> Path:
        """Create a temporary build.gradle file."""
        build_file = tmp_path / "build.gradle"
        build_file.write_text(SAMPLE_BUILD_GRADLE)
        return build_file

    def test_parse_group_and_version(
        self,
        parser: GradleParser,
        sample_build_file: Path,
    ) -> None:
        """Test parsing group and version from build.gradle."""
        group, version = parser.parse_group_and_version(sample_build_file)
        assert group == "com.example"
        assert version == "0.0.1-SNAPSHOT"

    def test_parse_dependencies(
        self,
        parser: GradleParser,
        sample_build_file: Path,
    ) -> None:
        """Test parsing dependencies from build.gradle."""
        dependencies = parser.parse_dependencies(sample_build_file)

        assert len(dependencies) >= 3

        # Check for specific dependencies
        web_dep = next(
            (d for d in dependencies if "spring-boot-starter-web" in d.name),
            None,
        )
        assert web_dep is not None
        assert web_dep.configuration == GradleConfiguration.IMPLEMENTATION

        jpa_dep = next(
            (d for d in dependencies if "spring-boot-starter-data-jpa" in d.name),
            None,
        )
        assert jpa_dep is not None

        test_dep = next(
            (d for d in dependencies if "spring-boot-starter-test" in d.name),
            None,
        )
        assert test_dep is not None
        assert test_dep.configuration == GradleConfiguration.TEST_IMPLEMENTATION

    def test_parse_java_version(
        self,
        parser: GradleParser,
        sample_build_file: Path,
    ) -> None:
        """Test parsing Java version from build.gradle."""
        java_version = parser.parse_java_version(sample_build_file)
        assert java_version == "21"

    def test_parse_plugins(
        self,
        parser: GradleParser,
        sample_build_file: Path,
    ) -> None:
        """Test parsing plugins from build.gradle."""
        plugins = parser.parse_plugins(sample_build_file)

        assert "java" in plugins
        assert "org.springframework.boot" in plugins
        assert plugins["org.springframework.boot"] == "3.2.0"

    def test_parse_nonexistent_file(self, parser: GradleParser) -> None:
        """Test parsing non-existent file raises error."""
        with pytest.raises(GradleParseError, match="does not exist"):
            parser.parse_group_and_version(Path("/nonexistent/build.gradle"))

    def test_parse_malformed_gradle_file(
        self,
        parser: GradleParser,
        tmp_path: Path,
    ) -> None:
        """Test parsing malformed Gradle file raises error."""
        malformed_file = tmp_path / "build.gradle"
        malformed_file.write_text("group = 'com.example'\nthis is not valid groovy {{")

        with pytest.raises(GradleParseError):
            parser.parse_group_and_version(malformed_file)

    def test_detect_malicious_content(
        self,
        parser: GradleParser,
        tmp_path: Path,
    ) -> None:
        """Test detection of malicious content in Gradle files."""
        malicious_file = tmp_path / "build.gradle"
        malicious_file.write_text(MALICIOUS_BUILD_GRADLE)

        with pytest.raises(MaliciousContentError, match="malicious"):
            parser.parse_group_and_version(malicious_file)

    def test_prevent_path_traversal_in_dependencies(
        self,
        parser: GradleParser,
        tmp_path: Path,
    ) -> None:
        """Test that path traversal in dependencies is detected."""
        malicious_gradle = """
        dependencies {
            implementation '../../../etc/passwd'
            implementation '../../../../malicious'
        }
        """
        malicious_file = tmp_path / "build.gradle"
        malicious_file.write_text(malicious_gradle)

        with pytest.raises(MaliciousContentError):
            parser.parse_dependencies(malicious_file)

    def test_handle_empty_dependencies_block(
        self,
        parser: GradleParser,
        tmp_path: Path,
    ) -> None:
        """Test handling of empty dependencies block."""
        gradle_content = """
        group = 'com.example'
        version = '1.0.0'

        dependencies {
        }
        """
        gradle_file = tmp_path / "build.gradle"
        gradle_file.write_text(gradle_content)

        dependencies = parser.parse_dependencies(gradle_file)
        assert len(dependencies) == 0

    def test_handle_missing_dependencies_block(
        self,
        parser: GradleParser,
        tmp_path: Path,
    ) -> None:
        """Test handling of missing dependencies block."""
        gradle_content = """
        group = 'com.example'
        version = '1.0.0'
        """
        gradle_file = tmp_path / "build.gradle"
        gradle_file.write_text(gradle_content)

        dependencies = parser.parse_dependencies(gradle_file)
        assert len(dependencies) == 0

    def test_parse_multiline_dependencies(
        self,
        parser: GradleParser,
        tmp_path: Path,
    ) -> None:
        """Test parsing multiline dependency declarations."""
        gradle_content = """
        dependencies {
            implementation(
                'org.springframework.boot:spring-boot-starter-web'
            )
            testImplementation(
                'org.springframework.boot:spring-boot-starter-test'
            ) {
                exclude group: 'org.junit.vintage', module: 'junit-vintage-engine'
            }
        }
        """
        gradle_file = tmp_path / "build.gradle"
        gradle_file.write_text(gradle_content)

        dependencies = parser.parse_dependencies(gradle_file)
        assert len(dependencies) == 2

    def test_file_size_limit(self, parser: GradleParser, tmp_path: Path) -> None:
        """Test that excessively large files are rejected (DoS prevention)."""
        large_file = tmp_path / "build.gradle"
        large_content = "// comment\n" * 500000
        large_file.write_text(large_content)

        with pytest.raises(GradleParseError, match="too large"):
            parser.parse_group_and_version(large_file)
