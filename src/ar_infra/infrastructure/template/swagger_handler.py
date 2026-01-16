"""Handler for updating OpenAPI/Swagger documentation based on selected features."""

from pathlib import Path
from typing import Any, ClassVar

import yaml

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.logger import get_logger


log = get_logger(use_rich=True)


class SwaggerHandler:
    FEATURE_ENDPOINTS: ClassVar[dict[TemplateFeature, str]] = {
        TemplateFeature.POSTGRESQL: "/health/db",
        TemplateFeature.MYSQL: "/health/db",
        TemplateFeature.RABBITMQ: "/health/message",
        TemplateFeature.S3_BUCKET: "/health/bucket",
        TemplateFeature.EMAIL: "/health/email",
    }

    def __init__(self, api_file_path: Path) -> None:
        self.api_file_path = api_file_path
        log.debug("Initialized SwaggerHandler with api_file_path: %s", api_file_path)

    def update_swagger(self, selected_features: set[TemplateFeature]) -> None:
        log.info(
            "Updating Swagger documentation with selected features: %s",
            [f.value for f in selected_features],
        )

        if not self.api_file_path.exists():
            log.warning("API file does not exist: %s", self.api_file_path)
            return

        swagger_data = self._load_swagger_data()
        if swagger_data is None:
            return

        endpoints_to_remove = self._get_endpoints_to_remove(selected_features)
        self._log_removal_summary(endpoints_to_remove)
        self._remove_endpoints(swagger_data, endpoints_to_remove)
        self._save_swagger_data(swagger_data)

        log.info("Swagger documentation updated successfully")

    def _load_swagger_data(self) -> dict[str, Any] | None:
        log.debug("Loading Swagger file from: %s", self.api_file_path)
        with self.api_file_path.open("r", encoding="utf-8") as f:
            swagger_data: dict[str, Any] = yaml.safe_load(f)

        if "paths" not in swagger_data:
            log.warning("Swagger file does not contain 'paths' key, skipping update")
            return None

        return swagger_data

    @staticmethod
    def _log_removal_summary(endpoints_to_remove: set[str]) -> None:
        if endpoints_to_remove:
            log.info(
                "Removing %d unused health endpoints: %s",
                len(endpoints_to_remove),
                endpoints_to_remove,
            )
        else:
            log.info("No endpoints to remove, all features are selected")

    @staticmethod
    def _remove_endpoints(swagger_data: dict[str, Any], endpoints_to_remove: set[str]) -> None:
        for endpoint in endpoints_to_remove:
            if endpoint in swagger_data["paths"]:
                log.debug("Removing endpoint: %s", endpoint)
                swagger_data["paths"].pop(endpoint, None)

    def _save_swagger_data(self, swagger_data: dict[str, Any]) -> None:
        log.debug("Writing updated Swagger file to: %s", self.api_file_path)
        with self.api_file_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                swagger_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def _get_endpoints_to_remove(self, selected_features: set[TemplateFeature]) -> set[str]:
        endpoint_to_features: dict[str, set[TemplateFeature]] = {}
        for feature, endpoint in self.FEATURE_ENDPOINTS.items():
            if endpoint not in endpoint_to_features:
                endpoint_to_features[endpoint] = set()
            endpoint_to_features[endpoint].add(feature)

        endpoints_to_remove = set()
        for endpoint, features in endpoint_to_features.items():
            if not any(feature in selected_features for feature in features):
                endpoints_to_remove.add(endpoint)

        log.debug(
            "Identified %d endpoints to remove based on feature selection", len(endpoints_to_remove)
        )
        return endpoints_to_remove
