"""Handler for updating OpenAPI/Swagger documentation based on selected features."""

from pathlib import Path
from typing import Any, ClassVar

import yaml

from src.ar_infra.domain.enums.template_feature import TemplateFeature


class SwaggerHandler:
    FEATURE_ENDPOINTS: ClassVar[dict[TemplateFeature, str]] = {
        TemplateFeature.POSTGRESQL: "/health/db",
        TemplateFeature.RABBITMQ: "/health/message",
        TemplateFeature.S3_BUCKET: "/health/bucket",
        TemplateFeature.EMAIL: "/health/email",
    }

    def __init__(self, api_file_path: Path) -> None:
        self.api_file_path = api_file_path

    def update_swagger(self, selected_features: set[TemplateFeature]) -> None:
        if not self.api_file_path.exists():
            return

        with self.api_file_path.open("r", encoding="utf-8") as f:
            swagger_data: dict[str, Any] = yaml.safe_load(f)

        if "paths" not in swagger_data:
            return

        endpoints_to_remove = self._get_endpoints_to_remove(selected_features)

        for endpoint in endpoints_to_remove:
            swagger_data["paths"].pop(endpoint, None)

        with self.api_file_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                swagger_data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def _get_endpoints_to_remove(self, selected_features: set[TemplateFeature]) -> set[str]:
        endpoints_to_remove = set()

        for feature, endpoint in self.FEATURE_ENDPOINTS.items():
            if feature not in selected_features:
                endpoints_to_remove.add(endpoint)

        return endpoints_to_remove
