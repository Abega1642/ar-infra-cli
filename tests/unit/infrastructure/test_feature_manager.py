"""Tests for FeatureManager."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.feature_manager import FeatureManager


SAMPLE_ENV_CONTENT = """SPRING_RABBITMQ_HOST=host
SPRING_DATASOURCE_URL=url
B2_KEY_ID=key
SPRING_MAIL_HOST=mail
PORT=8080
"""


class TestFeatureManager:
    @pytest.fixture
    def mock_env_handler(self) -> Mock:
        return Mock()

    @pytest.fixture
    def manager(self, mock_env_handler: Mock) -> FeatureManager:
        return FeatureManager(env_handler=mock_env_handler)

    @pytest.fixture
    def template_with_all_features(self, tmp_path: Path) -> Path:
        template = tmp_path / "template"

        (template / "src/main/java/com/example/arinfra/event").mkdir(parents=True)
        (template / "src/main/java/com/example/arinfra/mail").mkdir(parents=True)
        (template / "src/main/java/com/example/arinfra/repository").mkdir(parents=True)
        (template / "src/main/java/com/example/arinfra/config").mkdir(parents=True)

        (template / "src/main/java/com/example/arinfra/config/RabbitConfig.java").write_text(
            "rabbit", encoding="utf-8"
        )
        (template / "src/main/java/com/example/arinfra/config/EmailConf.java").write_text(
            "email", encoding="utf-8"
        )
        (template / "src/main/java/com/example/arinfra/config/BucketConf.java").write_text(
            "bucket", encoding="utf-8"
        )

        env_file = template / ".env.template"
        env_file.write_text(SAMPLE_ENV_CONTENT, encoding="utf-8")

        return template

    def test_remove_rabbitmq_feature(
        self, manager: FeatureManager, template_with_all_features: Path
    ) -> None:
        manager.remove_feature(template_with_all_features, TemplateFeature.RABBITMQ)

        assert not (template_with_all_features / "src/main/java/com/example/arinfra/event").exists()
        assert not (
            template_with_all_features
            / "src/main/java/com/example/arinfra/config/RabbitConfig.java"
        ).exists()

    def test_remove_email_feature(
        self, manager: FeatureManager, template_with_all_features: Path
    ) -> None:
        manager.remove_feature(template_with_all_features, TemplateFeature.EMAIL)

        assert not (template_with_all_features / "src/main/java/com/example/arinfra/mail").exists()
        assert not (
            template_with_all_features / "src/main/java/com/example/arinfra/config/EmailConf.java"
        ).exists()

    def test_keep_selected_features(
        self,
        manager: FeatureManager,
        template_with_all_features: Path,
        mock_env_handler: Mock,
    ) -> None:
        enabled = {TemplateFeature.POSTGRESQL, TemplateFeature.S3_BUCKET}
        manager.apply_feature_selection(template_with_all_features, enabled)

        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/repository"
        ).exists()
        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/config/BucketConf.java"
        ).exists()

        assert not (template_with_all_features / "src/main/java/com/example/arinfra/event").exists()
        assert not (template_with_all_features / "src/main/java/com/example/arinfra/mail").exists()

        mock_env_handler.remove_feature_env_variables.assert_called_once()

    def test_get_feature_dependencies(self, manager: FeatureManager) -> None:
        deps = manager.get_feature_dependencies(TemplateFeature.RABBITMQ)

        assert "org.springframework.boot:spring-boot-starter-amqp" in deps
        assert "org.testcontainers:rabbitmq" in deps

    def test_get_feature_env_variables(self, manager: FeatureManager) -> None:
        env_vars = manager.get_feature_env_variables(TemplateFeature.RABBITMQ)

        assert "SPRING_RABBITMQ_HOST" in env_vars
        assert "APP_RABBITMQ_SSL" in env_vars

    def test_handle_missing_files_gracefully(self, manager: FeatureManager, tmp_path: Path) -> None:
        template = tmp_path / "template"
        template.mkdir()

        manager.remove_feature(template, TemplateFeature.RABBITMQ)

    def test_apply_feature_selection_removes_env_variables(
        self,
        manager: FeatureManager,
        template_with_all_features: Path,
        mock_env_handler: Mock,
    ) -> None:
        enabled = {TemplateFeature.POSTGRESQL}
        manager.apply_feature_selection(template_with_all_features, enabled)

        mock_env_handler.remove_feature_env_variables.assert_called_once()
        call_args = mock_env_handler.remove_feature_env_variables.call_args

        env_file_arg = call_args[0][0]
        features_to_remove_arg = call_args[0][1]

        assert env_file_arg == template_with_all_features / ".env.template"
        assert TemplateFeature.RABBITMQ in features_to_remove_arg
        assert TemplateFeature.EMAIL in features_to_remove_arg
        assert TemplateFeature.S3_BUCKET in features_to_remove_arg
        assert TemplateFeature.POSTGRESQL not in features_to_remove_arg
