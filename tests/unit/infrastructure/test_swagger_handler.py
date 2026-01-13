from pathlib import Path
from typing import Any

import pytest
import yaml
from tests.fixtures.sample_swagger_api import SAMPLE_SWAGGER_API

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.swagger_handler import SwaggerHandler


@pytest.fixture
def sample_swagger_data() -> dict[str, Any]:
    return SAMPLE_SWAGGER_API


@pytest.fixture
def temp_api_file(tmp_path: Path, sample_swagger_data: dict[str, Any]) -> Path:
    api_file = tmp_path / "api.yml"
    with api_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(sample_swagger_data, f)
    return api_file


def test_update_swagger_all_features_selected(
    temp_api_file: Path, sample_swagger_data: dict[str, Any]
) -> None:
    handler = SwaggerHandler(temp_api_file)
    all_features = {
        TemplateFeature.POSTGRESQL,
        TemplateFeature.RABBITMQ,
        TemplateFeature.S3_BUCKET,
        TemplateFeature.EMAIL,
    }

    handler.update_swagger(all_features)

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert "/health/db" in result["paths"]
    assert "/health/message" in result["paths"]
    assert "/health/bucket" in result["paths"]
    assert "/health/email" in result["paths"]
    assert "/" in result["paths"]
    assert "/ping" in result["paths"]

    assert result["components"] == sample_swagger_data["components"]


def test_update_swagger_no_features_selected(temp_api_file: Path) -> None:
    handler = SwaggerHandler(temp_api_file)
    no_features: set[TemplateFeature] = set()

    handler.update_swagger(no_features)

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert "/health/db" not in result["paths"]
    assert "/health/message" not in result["paths"]
    assert "/health/bucket" not in result["paths"]
    assert "/health/email" not in result["paths"]

    assert "/" in result["paths"]
    assert "/ping" in result["paths"]

    assert "components" in result
    assert "schemas" in result["components"]


def test_update_swagger_only_postgresql(temp_api_file: Path) -> None:
    handler = SwaggerHandler(temp_api_file)
    features = {TemplateFeature.POSTGRESQL}

    handler.update_swagger(features)

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert "/health/db" in result["paths"]
    assert "/health/message" not in result["paths"]
    assert "/health/bucket" not in result["paths"]
    assert "/health/email" not in result["paths"]

    assert "/" in result["paths"]
    assert "/ping" in result["paths"]


def test_update_swagger_only_rabbitmq(temp_api_file: Path) -> None:
    handler = SwaggerHandler(temp_api_file)
    features = {TemplateFeature.RABBITMQ}

    handler.update_swagger(features)

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert "/health/message" in result["paths"]
    assert "/health/db" not in result["paths"]
    assert "/health/bucket" not in result["paths"]
    assert "/health/email" not in result["paths"]


def test_update_swagger_only_s3_bucket(temp_api_file: Path) -> None:
    handler = SwaggerHandler(temp_api_file)
    features = {TemplateFeature.S3_BUCKET}

    handler.update_swagger(features)

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert "/health/bucket" in result["paths"]
    assert "/health/db" not in result["paths"]
    assert "/health/message" not in result["paths"]
    assert "/health/email" not in result["paths"]


def test_update_swagger_only_email(temp_api_file: Path) -> None:
    handler = SwaggerHandler(temp_api_file)
    features = {TemplateFeature.EMAIL}

    handler.update_swagger(features)

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert "/health/email" in result["paths"]
    assert "/health/db" not in result["paths"]
    assert "/health/message" not in result["paths"]
    assert "/health/bucket" not in result["paths"]


def test_update_swagger_multiple_features(temp_api_file: Path) -> None:
    handler = SwaggerHandler(temp_api_file)
    features = {TemplateFeature.POSTGRESQL, TemplateFeature.EMAIL}

    handler.update_swagger(features)

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert "/health/db" in result["paths"]
    assert "/health/email" in result["paths"]

    assert "/health/message" not in result["paths"]
    assert "/health/bucket" not in result["paths"]


def test_update_swagger_file_not_exists(tmp_path: Path) -> None:
    non_existent_file = tmp_path / "does_not_exist.yml"
    handler = SwaggerHandler(non_existent_file)

    handler.update_swagger({TemplateFeature.POSTGRESQL})

    assert not non_existent_file.exists()


def test_update_swagger_missing_paths_key(tmp_path: Path) -> None:
    api_file = tmp_path / "api.yml"
    invalid_swagger = {"openapi": "3.1.0", "info": {"title": "Test"}}

    with api_file.open("w", encoding="utf-8") as f:
        yaml.safe_dump(invalid_swagger, f)

    handler = SwaggerHandler(api_file)
    handler.update_swagger({TemplateFeature.POSTGRESQL})

    with api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert result == invalid_swagger


def test_update_swagger_preserves_order(temp_api_file: Path) -> None:
    handler = SwaggerHandler(temp_api_file)
    features = {TemplateFeature.POSTGRESQL, TemplateFeature.S3_BUCKET}

    handler.update_swagger(features)

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    paths_keys = list(result["paths"].keys())
    assert paths_keys.index("/") < paths_keys.index("/ping")
    assert "/health/bucket" in paths_keys
    assert "/health/db" in paths_keys


def test_update_swagger_components_unchanged(
    temp_api_file: Path, sample_swagger_data: dict[str, Any]
) -> None:
    handler = SwaggerHandler(temp_api_file)
    handler.update_swagger({TemplateFeature.EMAIL})

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert result["components"] == sample_swagger_data["components"]
    assert "ErrorResponse" in result["components"]["schemas"]
    assert "DateTime" in result["components"]["schemas"]
    assert "UUID" in result["components"]["schemas"]
    assert "Dummy" in result["components"]["schemas"]


def test_get_endpoints_to_remove_all_features() -> None:
    handler = SwaggerHandler(Path("dummy.yml"))
    all_features = {
        TemplateFeature.POSTGRESQL,
        TemplateFeature.RABBITMQ,
        TemplateFeature.S3_BUCKET,
        TemplateFeature.EMAIL,
    }

    endpoints = handler._get_endpoints_to_remove(all_features)

    assert len(endpoints) == 0


def test_get_endpoints_to_remove_no_features() -> None:
    handler = SwaggerHandler(Path("dummy.yml"))
    no_features: set[TemplateFeature] = set()

    endpoints = handler._get_endpoints_to_remove(no_features)

    assert endpoints == {
        "/health/db",
        "/health/message",
        "/health/bucket",
        "/health/email",
    }


def test_get_endpoints_to_remove_partial_features() -> None:
    handler = SwaggerHandler(Path("dummy.yml"))
    features = {TemplateFeature.POSTGRESQL, TemplateFeature.EMAIL}

    endpoints = handler._get_endpoints_to_remove(features)

    assert endpoints == {"/health/message", "/health/bucket"}


def test_forward_compatibility_mysql_feature(temp_api_file: Path) -> None:
    handler = SwaggerHandler(temp_api_file)
    features = {TemplateFeature.POSTGRESQL}

    handler.update_swagger(features)

    with temp_api_file.open("r", encoding="utf-8") as f:
        result = yaml.safe_load(f)

    assert "/health/db" in result["paths"]
