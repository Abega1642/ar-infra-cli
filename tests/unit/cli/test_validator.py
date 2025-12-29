"""Tests for input validators."""

from pathlib import Path

import pytest

from src.ar_infra.cli.prompt.validator import Validators


class TestValidators:
    """Test suite for Validators class."""

    @pytest.fixture
    def validators(self) -> Validators:
        return Validators()

    def test_group_id_valid(self, validators: Validators) -> None:
        assert validators.group_id("com.example") is None
        assert validators.group_id("dev.razafindratelo") is None
        assert validators.group_id("org.springframework.boot") is None

    def test_group_id_invalid_no_dot(self, validators: Validators) -> None:
        result = validators.group_id("example")
        assert result is not None
        assert "dot-separated" in result.lower()

    def test_group_id_invalid_uppercase(self, validators: Validators) -> None:
        result = validators.group_id("Com.Example")
        assert result is not None
        assert "lowercase" in result.lower()

    def test_group_id_invalid_starts_with_number(self, validators: Validators) -> None:
        result = validators.group_id("123.example")
        assert result is not None

    def test_group_id_invalid_special_chars(self, validators: Validators) -> None:
        result = validators.group_id("com.exam-ple")
        assert result is not None

    def test_group_id_invalid_single_segment(self, validators: Validators) -> None:
        result = validators.group_id("com")
        assert result is not None

    def test_artifact_id_valid(self, validators: Validators) -> None:
        assert validators.artifact_id("my-app") is None
        assert validators.artifact_id("backend-api") is None
        assert validators.artifact_id("service123") is None
        assert validators.artifact_id("app") is None

    def test_artifact_id_invalid_uppercase(self, validators: Validators) -> None:
        result = validators.artifact_id("MyApp")
        assert result is not None
        assert "lowercase" in result.lower()

    def test_artifact_id_invalid_starts_with_number(self, validators: Validators) -> None:
        result = validators.artifact_id("123app")
        assert result is not None

    def test_artifact_id_invalid_underscore(self, validators: Validators) -> None:
        result = validators.artifact_id("my_app")
        assert result is not None

    def test_artifact_id_invalid_dot(self, validators: Validators) -> None:
        result = validators.artifact_id("my.app")
        assert result is not None

    def test_version_valid(self, validators: Validators) -> None:
        assert validators.version("1.0.0") is None
        assert validators.version("2.3.4") is None
        assert validators.version("1.0.0-SNAPSHOT") is None
        assert validators.version("1.2.3-beta1") is None
        assert validators.version("0.0.1") is None

    def test_version_invalid_two_parts(self, validators: Validators) -> None:
        result = validators.version("1.0")
        assert result is not None
        assert "semantic versioning" in result.lower()

    def test_version_invalid_four_parts(self, validators: Validators) -> None:
        result = validators.version("1.0.0.0")
        assert result is not None

    def test_version_invalid_non_numeric(self, validators: Validators) -> None:
        result = validators.version("v1.0.0")
        assert result is not None

    def test_version_invalid_letters_in_version(self, validators: Validators) -> None:
        result = validators.version("a.b.c")
        assert result is not None

    def test_path_valid_existing_dir(self, validators: Validators, tmp_path: Path) -> None:
        assert validators.path(str(tmp_path)) is None

    def test_path_valid_current_dir(self, validators: Validators) -> None:
        assert validators.path("./") is None

    def test_path_valid_home_dir(self, validators: Validators) -> None:
        assert validators.path("~/") is None

    def test_path_valid_non_existing(self, validators: Validators, tmp_path: Path) -> None:
        non_existing = tmp_path / "non-existing-path-12345"
        assert validators.path(str(non_existing)) is None

    def test_path_invalid_is_file(self, validators: Validators, tmp_path: Path) -> None:
        file = tmp_path / "file.txt"
        file.write_text("test")
        result = validators.path(str(file))
        assert result is not None
        assert "not a directory" in result.lower()

    def test_features_valid_all(self, validators: Validators) -> None:
        assert validators.features("postgresql,rabbitmq,s3_bucket,email") is None

    def test_features_valid_single(self, validators: Validators) -> None:
        assert validators.features("postgresql") is None
        assert validators.features("rabbitmq") is None
        assert validators.features("s3_bucket") is None
        assert validators.features("email") is None

    def test_features_valid_with_spaces(self, validators: Validators) -> None:
        assert validators.features("postgresql, rabbitmq, email") is None

    def test_features_valid_case_insensitive(self, validators: Validators) -> None:
        assert validators.features("PostgreSQL,RABBITMQ,Email") is None

    def test_features_invalid_unknown_feature(self, validators: Validators) -> None:
        result = validators.features("postgresql,mongodb")
        assert result is not None
        assert "mongodb" in result.lower()

    def test_features_invalid_multiple_unknown(self, validators: Validators) -> None:
        result = validators.features("postgresql,redis,mongodb")
        assert result is not None
        assert "redis" in result.lower() or "mongodb" in result.lower()

    def test_features_empty_string(self, validators: Validators) -> None:
        assert validators.features("") is None

    def test_features_whitespace_only(self, validators: Validators) -> None:
        assert validators.features("   ") is None
