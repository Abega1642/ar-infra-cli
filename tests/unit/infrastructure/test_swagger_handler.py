from pathlib import Path
from typing import Any

import pytest
import yaml
from tests.fixtures.sample_swagger_api import SAMPLE_SWAGGER_API_YAML

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.swagger_handler import SwaggerHandler


class TestSwaggerHandler:
    @pytest.fixture
    def sample_swagger_data(self) -> dict[str, Any]:
        return yaml.safe_load(SAMPLE_SWAGGER_API_YAML)

    @pytest.fixture
    def temp_template_dir(self, tmp_path: Path, sample_swagger_data: dict[str, Any]) -> Path:
        template_dir = tmp_path / "template"
        doc_dir = template_dir / "doc"
        doc_dir.mkdir(parents=True)

        api_file = doc_dir / "api.yml"
        with api_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(sample_swagger_data, f)

        return template_dir

    @pytest.fixture
    def api_file_path(self, temp_template_dir: Path) -> Path:
        return temp_template_dir / "doc" / "api.yml"

    def test_update_swagger_all_features_selected(
        self, api_file_path: Path, sample_swagger_data: dict[str, Any]
    ) -> None:
        handler = SwaggerHandler(api_file_path)
        all_features = {
            TemplateFeature.POSTGRESQL,
            TemplateFeature.RABBITMQ,
            TemplateFeature.S3_BUCKET,
            TemplateFeature.EMAIL,
        }

        handler.update_swagger(all_features)

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert "/health/db" in result["paths"]
        assert "/health/message" in result["paths"]
        assert "/health/bucket" in result["paths"]
        assert "/health/email" in result["paths"]
        assert "/" in result["paths"]
        assert "/ping" in result["paths"]

        assert result["components"] == sample_swagger_data["components"]

    def test_update_swagger_no_features_selected(self, api_file_path: Path) -> None:
        handler = SwaggerHandler(api_file_path)
        no_features: set[TemplateFeature] = set()

        handler.update_swagger(no_features)

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert "/health/db" not in result["paths"]
        assert "/health/message" not in result["paths"]
        assert "/health/bucket" not in result["paths"]
        assert "/health/email" not in result["paths"]

        assert "/" in result["paths"]
        assert "/ping" in result["paths"]

        assert "components" in result
        assert "schemas" in result["components"]

    def test_update_swagger_only_postgresql(self, api_file_path: Path) -> None:
        handler = SwaggerHandler(api_file_path)
        features = {TemplateFeature.POSTGRESQL}

        handler.update_swagger(features)

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert "/health/db" in result["paths"]
        assert "/health/message" not in result["paths"]
        assert "/health/bucket" not in result["paths"]
        assert "/health/email" not in result["paths"]

        assert "/" in result["paths"]
        assert "/ping" in result["paths"]

    def test_update_swagger_only_rabbitmq(self, api_file_path: Path) -> None:
        handler = SwaggerHandler(api_file_path)
        features = {TemplateFeature.RABBITMQ}

        handler.update_swagger(features)

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert "/health/message" in result["paths"]
        assert "/health/db" not in result["paths"]
        assert "/health/bucket" not in result["paths"]
        assert "/health/email" not in result["paths"]

    def test_update_swagger_only_s3_bucket(self, api_file_path: Path) -> None:
        handler = SwaggerHandler(api_file_path)
        features = {TemplateFeature.S3_BUCKET}

        handler.update_swagger(features)

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert "/health/bucket" in result["paths"]
        assert "/health/db" not in result["paths"]
        assert "/health/message" not in result["paths"]
        assert "/health/email" not in result["paths"]

    def test_update_swagger_only_email(self, api_file_path: Path) -> None:
        handler = SwaggerHandler(api_file_path)
        features = {TemplateFeature.EMAIL}

        handler.update_swagger(features)

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert "/health/email" in result["paths"]
        assert "/health/db" not in result["paths"]
        assert "/health/message" not in result["paths"]
        assert "/health/bucket" not in result["paths"]

    def test_update_swagger_multiple_features(self, api_file_path: Path) -> None:
        handler = SwaggerHandler(api_file_path)
        features = {TemplateFeature.POSTGRESQL, TemplateFeature.EMAIL}

        handler.update_swagger(features)

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert "/health/db" in result["paths"]
        assert "/health/email" in result["paths"]

        assert "/health/message" not in result["paths"]
        assert "/health/bucket" not in result["paths"]

    def test_update_swagger_file_not_exists(self, tmp_path: Path) -> None:
        non_existent_file = tmp_path / "doc" / "does_not_exist.yml"
        handler = SwaggerHandler(non_existent_file)

        handler.update_swagger({TemplateFeature.POSTGRESQL})

        assert not non_existent_file.exists()

    def test_update_swagger_missing_paths_key(self, tmp_path: Path) -> None:
        doc_dir = tmp_path / "doc"
        doc_dir.mkdir()
        api_file = doc_dir / "api.yml"
        invalid_swagger = {"openapi": "3.1.0", "info": {"title": "Test"}}

        with api_file.open("w", encoding="utf-8") as f:
            yaml.safe_dump(invalid_swagger, f)

        handler = SwaggerHandler(api_file)
        handler.update_swagger({TemplateFeature.POSTGRESQL})

        with api_file.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert result == invalid_swagger

    def test_update_swagger_preserves_order(self, api_file_path: Path) -> None:
        handler = SwaggerHandler(api_file_path)
        features = {TemplateFeature.POSTGRESQL, TemplateFeature.S3_BUCKET}

        handler.update_swagger(features)

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        paths_keys = list(result["paths"].keys())
        assert paths_keys.index("/") < paths_keys.index("/ping")
        assert "/health/bucket" in paths_keys
        assert "/health/db" in paths_keys

    def test_update_swagger_components_unchanged(
        self, api_file_path: Path, sample_swagger_data: dict[str, Any]
    ) -> None:
        handler = SwaggerHandler(api_file_path)
        handler.update_swagger({TemplateFeature.EMAIL})

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert result["components"] == sample_swagger_data["components"]
        assert "ErrorResponse" in result["components"]["schemas"]
        assert "DateTime" in result["components"]["schemas"]
        assert "UUID" in result["components"]["schemas"]
        assert "Dummy" in result["components"]["schemas"]

    def test_get_endpoints_to_remove_all_features(self) -> None:
        handler = SwaggerHandler(Path("dummy.yml"))
        all_features = {
            TemplateFeature.POSTGRESQL,
            TemplateFeature.RABBITMQ,
            TemplateFeature.S3_BUCKET,
            TemplateFeature.EMAIL,
        }

        endpoints = handler._get_endpoints_to_remove(all_features)

        assert len(endpoints) == 0

    def test_get_endpoints_to_remove_no_features(self) -> None:
        handler = SwaggerHandler(Path("dummy.yml"))
        no_features: set[TemplateFeature] = set()

        endpoints = handler._get_endpoints_to_remove(no_features)

        assert endpoints == {
            "/health/db",
            "/health/message",
            "/health/bucket",
            "/health/email",
        }

    def test_get_endpoints_to_remove_partial_features(self) -> None:
        handler = SwaggerHandler(Path("dummy.yml"))
        features = {TemplateFeature.POSTGRESQL, TemplateFeature.EMAIL}

        endpoints = handler._get_endpoints_to_remove(features)

        assert endpoints == {"/health/message", "/health/bucket"}

    def test_forward_compatibility_mysql_feature(self, api_file_path: Path) -> None:
        handler = SwaggerHandler(api_file_path)
        features = {TemplateFeature.POSTGRESQL}

        handler.update_swagger(features)

        with api_file_path.open("r", encoding="utf-8") as f:
            result = yaml.safe_load(f)

        assert "/health/db" in result["paths"]
