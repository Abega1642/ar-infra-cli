"""Tests for RestExceptionHandlerManager."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.tmpdir import TempPathFactory

import pytest
from tests.fixtures.api_exception_handler_sample import API_EXCEPTION_HANDLER_SAMPLE

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.rest_exception_manager import RestExceptionHandlerManager


@pytest.fixture
def sample_exception_handler() -> str:
    """Sample ApiExceptionHandler.java content."""
    return API_EXCEPTION_HANDLER_SAMPLE


@pytest.fixture
def temp_project_dir(tmp_path_factory: TempPathFactory, sample_exception_handler: str) -> Path:
    """Create temporary project directory with ApiExceptionHandler.java."""
    project_dir = tmp_path_factory.mktemp("test_project")
    handler_dir = project_dir / "src" / "main" / "java" / "com" / "example" / "arinfra"
    handler_dir = handler_dir / "endpoint" / "rest" / "controller"
    handler_dir.mkdir(parents=True)

    handler_file = handler_dir / "ApiExceptionHandler.java"
    handler_file.write_text(sample_exception_handler, encoding="utf-8")

    return project_dir


class TestRestExceptionHandlerManager:
    """Test suite for RestExceptionHandlerManager."""

    def test_remove_bucket_exceptions_only(self, temp_project_dir: Path) -> None:
        """Test removing only S3 bucket exception handlers."""
        manager = RestExceptionHandlerManager()
        enabled_features = {TemplateFeature.EMAIL, TemplateFeature.POSTGRESQL}

        manager.apply_feature_selection(temp_project_dir, enabled_features)

        handler_file = temp_project_dir / "src" / "main" / "java" / "com" / "example"
        handler_file = handler_file / "arinfra" / "endpoint" / "rest" / "controller"
        handler_file = handler_file / "ApiExceptionHandler.java"

        content = handler_file.read_text(encoding="utf-8")

        assert "handleBucketHealthCheckException" not in content
        assert "handleBucketOperationException" not in content
        assert "handleEmailHealthCheckException" in content
        assert "handleEntityNotFoundException" in content
        assert "handleGenericException" in content

    def test_remove_email_exceptions_only(self, temp_project_dir: Path) -> None:
        """Test removing only email exception handlers."""
        manager = RestExceptionHandlerManager()
        enabled_features = {TemplateFeature.S3_BUCKET, TemplateFeature.POSTGRESQL}

        manager.apply_feature_selection(temp_project_dir, enabled_features)

        handler_file = temp_project_dir / "src" / "main" / "java" / "com" / "example"
        handler_file = handler_file / "arinfra" / "endpoint" / "rest" / "controller"
        handler_file = handler_file / "ApiExceptionHandler.java"

        content = handler_file.read_text(encoding="utf-8")

        assert "handleEmailHealthCheckException" not in content
        assert "handleBucketHealthCheckException" in content
        assert "handleEntityNotFoundException" in content

    def test_remove_postgresql_exceptions_only(self, temp_project_dir: Path) -> None:
        """Test removing only PostgreSQL exception handlers."""
        manager = RestExceptionHandlerManager()
        enabled_features = {TemplateFeature.S3_BUCKET, TemplateFeature.EMAIL}

        manager.apply_feature_selection(temp_project_dir, enabled_features)

        handler_file = temp_project_dir / "src" / "main" / "java" / "com" / "example"
        handler_file = handler_file / "arinfra" / "endpoint" / "rest" / "controller"
        handler_file = handler_file / "ApiExceptionHandler.java"

        content = handler_file.read_text(encoding="utf-8")

        assert "handleEntityNotFoundException" not in content
        assert "handleBucketHealthCheckException" in content
        assert "handleEmailHealthCheckException" in content

    def test_remove_all_feature_exceptions(self, temp_project_dir: Path) -> None:
        """Test removing all feature-specific exception handlers."""
        manager = RestExceptionHandlerManager()
        enabled_features: set[TemplateFeature] = set()

        manager.apply_feature_selection(temp_project_dir, enabled_features)

        handler_file = temp_project_dir / "src" / "main" / "java" / "com" / "example"
        handler_file = handler_file / "arinfra" / "endpoint" / "rest" / "controller"
        handler_file = handler_file / "ApiExceptionHandler.java"

        content = handler_file.read_text(encoding="utf-8")

        assert "handleBucketHealthCheckException" not in content
        assert "handleBucketOperationException" not in content
        assert "handleEmailHealthCheckException" not in content
        assert "handleEntityNotFoundException" not in content
        assert "handleGenericException" in content

    def test_keep_all_exceptions_when_all_enabled(self, temp_project_dir: Path) -> None:
        """Test keeping all exception handlers when all features are enabled."""
        manager = RestExceptionHandlerManager()
        enabled_features = {
            TemplateFeature.S3_BUCKET,
            TemplateFeature.EMAIL,
            TemplateFeature.POSTGRESQL,
        }

        manager.apply_feature_selection(temp_project_dir, enabled_features)

        handler_file = temp_project_dir / "src" / "main" / "java" / "com" / "example"
        handler_file = handler_file / "arinfra" / "endpoint" / "rest" / "controller"
        handler_file = handler_file / "ApiExceptionHandler.java"

        content = handler_file.read_text(encoding="utf-8")

        assert "handleBucketHealthCheckException" in content
        assert "handleBucketOperationException" in content
        assert "handleEmailHealthCheckException" in content
        assert "handleEntityNotFoundException" in content
        assert "handleGenericException" in content

    def test_no_exception_handler_file(self, tmp_path: Path) -> None:
        """Test handling when ApiExceptionHandler.java doesn't exist."""
        manager = RestExceptionHandlerManager()
        enabled_features = {TemplateFeature.EMAIL}

        # Should not raise an exception
        manager.apply_feature_selection(tmp_path, enabled_features)

    def test_multiple_exception_handler_files_raises_error(
        self, tmp_path: Path, sample_exception_handler: str
    ) -> None:
        """Test that multiple ApiExceptionHandler.java files raise an error."""
        dir1 = tmp_path / "src1" / "controller"
        dir2 = tmp_path / "src2" / "controller"
        dir1.mkdir(parents=True)
        dir2.mkdir(parents=True)

        (dir1 / "ApiExceptionHandler.java").write_text(sample_exception_handler, encoding="utf-8")
        (dir2 / "ApiExceptionHandler.java").write_text(sample_exception_handler, encoding="utf-8")

        manager = RestExceptionHandlerManager()
        enabled_features = {TemplateFeature.EMAIL}

        with pytest.raises(
            RuntimeError, match=re.escape("Multiple ApiExceptionHandler.java files found")
        ):
            manager.apply_feature_selection(tmp_path, enabled_features)

    def test_preserves_generic_exception_handler(self, temp_project_dir: Path) -> None:
        """Test that generic Exception handler is always preserved."""
        manager = RestExceptionHandlerManager()
        enabled_features: set[TemplateFeature] = set()

        manager.apply_feature_selection(temp_project_dir, enabled_features)

        handler_file = temp_project_dir / "src" / "main" / "java" / "com" / "example"
        handler_file = handler_file / "arinfra" / "endpoint" / "rest" / "controller"
        handler_file = handler_file / "ApiExceptionHandler.java"

        content = handler_file.read_text(encoding="utf-8")

        assert "@ExceptionHandler(Exception.class)" in content
        assert "handleGenericException" in content
