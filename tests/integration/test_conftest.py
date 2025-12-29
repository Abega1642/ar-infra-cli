"""Shared pytest fixtures and configuration for AR-INFRA tests."""

import shutil
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest
import requests
from click.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    """Provide Click CLI test runner."""
    return CliRunner()


@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """Cleanup test artifacts after all tests."""
    return


@pytest.fixture
def mock_github_unavailable(monkeypatch):
    """Mock GitHub being unavailable for testing error handling."""

    def mock_get(*args, **kwargs):
        raise requests.ConnectionError("GitHub unavailable")

    monkeypatch.setattr(requests, "get", mock_get)
    return mock_get


@pytest.fixture(scope="session")
def integration_test_cache(tmp_path_factory) -> Generator[Path, Any, None]:
    """Create a session-scoped temp directory for integration test cache."""
    cache_dir = tmp_path_factory.mktemp("integration_cache")
    yield cache_dir
    if cache_dir.exists():
        shutil.rmtree(cache_dir)


@pytest.fixture
def test_output_dir(tmp_path: Path) -> Generator[Path, Any, None]:
    """Create a temporary directory for test outputs."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(parents=True, exist_ok=True)
    yield output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)


@pytest.fixture
def mock_template_repository(tmp_path: Path) -> Path:
    """Create a mock template repository structure for testing."""
    template_dir = tmp_path / "mock_template"
    template_dir.mkdir(parents=True, exist_ok=True)

    (template_dir / "build.gradle").write_text("group = '{{GROUP_ID}}'\nversion = '{{VERSION}}'\n")
    (template_dir / "settings.gradle").write_text("rootProject.name = '{{ARTIFACT_ID}}'\n")

    src_dir = template_dir / "src" / "main" / "java" / "com" / "example" / "template"
    src_dir.mkdir(parents=True, exist_ok=True)

    (src_dir / "Application.java").write_text(
        "package com.example.template;\n\n@SpringBootApplication\npublic class Application {}\n"
    )

    return template_dir


@pytest.fixture
def sample_features() -> dict:
    """Provide sample feature configurations for testing."""
    return {
        "postgresql": {
            "dependencies": ["org.postgresql:postgresql"],
            "directories": ["repository"],
        },
        "rabbitmq": {
            "dependencies": ["spring-boot-starter-amqp"],
            "directories": ["event"],
        },
        "email": {
            "dependencies": ["spring-boot-starter-mail"],
            "directories": ["mail"],
        },
        "s3_bucket": {
            "dependencies": ["aws-java-sdk-s3"],
            "directories": ["file"],
        },
    }


@pytest.fixture
def valid_project_config() -> dict:
    """Provide a valid project configuration for testing."""
    return {
        "group": "com.example",
        "artifact": "test-app",
        "version": "1.0.0",
        "features": ["postgresql", "email"],
    }


@pytest.fixture
def invalid_project_configs() -> list:
    """Provide invalid project configurations for testing validation."""
    return [
        {"group": "InvalidGroup", "artifact": "test-app", "reason": "uppercase in group"},
        {"group": "com.example", "artifact": "Invalid_App", "reason": "underscore in artifact"},
        {"group": "com..example", "artifact": "test-app", "reason": "double dot in group"},
        {"group": "", "artifact": "test-app", "reason": "empty group"},
        {"group": "com.example", "artifact": "", "reason": "empty artifact"},
    ]
