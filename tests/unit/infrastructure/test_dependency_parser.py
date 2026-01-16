"""Tests for DependencyParser."""

import pytest

from src.ar_infra.domain.entities.gradle_dependency import GradleConfiguration
from src.ar_infra.domain.exceptions.validation_error import ValidationError
from src.ar_infra.infrastructure.gradle.dependency_parser import DependencyParser


class TestDependencyParser:
    @pytest.fixture
    def parser(self) -> DependencyParser:
        return DependencyParser()

    def test_parse_implementation_with_version(self, parser: DependencyParser) -> None:
        dep = parser.parse("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'")

        assert dep.group == "io.jsonwebtoken"
        assert dep.name == "jjwt-api"
        assert dep.version == "0.13.0"
        assert dep.configuration == GradleConfiguration.IMPLEMENTATION

    def test_parse_runtime_only_with_version(self, parser: DependencyParser) -> None:
        dep = parser.parse("runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.13.0'")

        assert dep.group == "io.jsonwebtoken"
        assert dep.name == "jjwt-impl"
        assert dep.version == "0.13.0"
        assert dep.configuration == GradleConfiguration.RUNTIME_ONLY

    def test_parse_implementation_without_version(self, parser: DependencyParser) -> None:
        dep = parser.parse("implementation 'org.springframework.boot:spring-boot-starter-web'")

        assert dep.group == "org.springframework.boot"
        assert dep.name == "spring-boot-starter-web"
        assert dep.version is None
        assert dep.configuration == GradleConfiguration.IMPLEMENTATION

    def test_parse_test_implementation(self, parser: DependencyParser) -> None:
        dep = parser.parse("testImplementation 'org.junit.jupiter:junit-jupiter:5.9.0'")

        assert dep.group == "org.junit.jupiter"
        assert dep.name == "junit-jupiter"
        assert dep.version == "5.9.0"
        assert dep.configuration == GradleConfiguration.TEST_IMPLEMENTATION

    def test_parse_compile_only(self, parser: DependencyParser) -> None:
        dep = parser.parse("compileOnly 'org.projectlombok:lombok:1.18.30'")

        assert dep.configuration == GradleConfiguration.COMPILE_ONLY

    def test_parse_annotation_processor(self, parser: DependencyParser) -> None:
        dep = parser.parse("annotationProcessor 'org.mapstruct:mapstruct-processor:1.6.3'")

        assert dep.configuration == GradleConfiguration.ANNOTATION_PROCESSOR

    def test_parse_test_runtime_only(self, parser: DependencyParser) -> None:
        dep = parser.parse("testRuntimeOnly 'org.junit.platform:junit-platform-launcher'")

        assert dep.configuration == GradleConfiguration.TEST_RUNTIME_ONLY

    def test_parse_with_double_quotes(self, parser: DependencyParser) -> None:
        dep = parser.parse('implementation "io.jsonwebtoken:jjwt-api:0.13.0"')

        assert dep.group == "io.jsonwebtoken"
        assert dep.name == "jjwt-api"
        assert dep.version == "0.13.0"

    def test_parse_with_extra_whitespace(self, parser: DependencyParser) -> None:
        dep = parser.parse("  implementation   'io.jsonwebtoken:jjwt-api:0.13.0'  ")

        assert dep.group == "io.jsonwebtoken"
        assert dep.name == "jjwt-api"
        assert dep.version == "0.13.0"

    def test_parse_case_insensitive_configuration(self, parser: DependencyParser) -> None:
        dep = parser.parse("IMPLEMENTATION 'io.jsonwebtoken:jjwt-api:0.13.0'")

        assert dep.configuration == GradleConfiguration.IMPLEMENTATION

    def test_parse_multiple_dependencies(self, parser: DependencyParser) -> None:
        deps = parser.parse_multiple(
            [
                "implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",
                "runtimeOnly 'io.jsonwebtoken:jjwt-impl:0.13.0'",
                "testImplementation 'org.junit.jupiter:junit-jupiter:5.9.0'",
            ]
        )

        assert len(deps) == 3
        assert deps[0].configuration == GradleConfiguration.IMPLEMENTATION
        assert deps[1].configuration == GradleConfiguration.RUNTIME_ONLY
        assert deps[2].configuration == GradleConfiguration.TEST_IMPLEMENTATION

    def test_parse_empty_string_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Dependency string cannot be empty"):
            parser.parse("")

    def test_parse_whitespace_only_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Dependency string cannot be empty"):
            parser.parse("   ")

    def test_parse_invalid_format_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Invalid dependency format"):
            parser.parse("invalid dependency string")

    def test_parse_missing_configuration_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Invalid dependency format"):
            parser.parse("'io.jsonwebtoken:jjwt-api:0.13.0'")

    def test_parse_missing_group_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Invalid dependency notation"):
            parser.parse("implementation 'jjwt-api'")

    def test_parse_empty_group_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Group ID cannot be empty"):
            parser.parse("implementation ':jjwt-api:0.13.0'")

    def test_parse_empty_name_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Artifact name cannot be empty"):
            parser.parse("implementation 'io.jsonwebtoken::0.13.0'")

    def test_parse_path_traversal_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation '../malicious:package:1.0'")

    def test_parse_forward_slash_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation 'io/jsonwebtoken:jjwt-api:0.13.0'")

    def test_parse_backslash_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation 'io\\jsonwebtoken:jjwt-api:0.13.0'")

    def test_parse_semicolon_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation 'io.jsonwebtoken:jjwt-api;malicious:0.13.0'")

    def test_parse_ampersand_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation 'io.jsonwebtoken:jjwt-api&malicious:0.13.0'")

    def test_parse_pipe_raises_validation_error(self, parser: DependencyParser) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation 'io.jsonwebtoken:jjwt-api|malicious:0.13.0'")

    def test_parse_backtick_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation 'io.jsonwebtoken:jjwt-api`:0.13.0'")

    def test_parse_dollar_sign_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation 'io.jsonwebtoken:jjwt-api$malicious:0.13.0'")

    def test_parse_newline_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation 'io.jsonwebtoken:jjwt-api\nmalicious:0.13.0'")

    def test_parse_carriage_return_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="Suspicious character"):
            parser.parse("implementation 'io.jsonwebtoken:jjwt-api\rmalicious:0.13.0'")

    def test_parse_multiple_empty_list_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError, match="No dependencies provided"):
            parser.parse_multiple([])

    def test_parse_multiple_with_invalid_dependency_raises_validation_error(
        self,
        parser: DependencyParser,
    ) -> None:
        with pytest.raises(ValidationError):
            parser.parse_multiple(
                [
                    "implementation 'io.jsonwebtoken:jjwt-api:0.13.0'",
                    "invalid dependency",
                ]
            )

    def test_to_gradle_notation_with_version(self, parser: DependencyParser) -> None:
        dep = parser.parse("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'")

        assert dep.to_gradle_notation() == "io.jsonwebtoken:jjwt-api:0.13.0"

    def test_to_gradle_notation_without_version(self, parser: DependencyParser) -> None:
        dep = parser.parse("implementation 'io.jsonwebtoken:jjwt-api'")

        assert dep.to_gradle_notation() == "io.jsonwebtoken:jjwt-api"

    def test_str_representation(self, parser: DependencyParser) -> None:
        dep = parser.parse("implementation 'io.jsonwebtoken:jjwt-api:0.13.0'")

        assert str(dep) == "implementation 'io.jsonwebtoken:jjwt-api:0.13.0'"
