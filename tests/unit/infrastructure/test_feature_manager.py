"""Tests for FeatureManager."""

from pathlib import Path

import pytest

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.feature_manager import FeatureManager


class TestFeatureManager:
    """Test suite for FeatureManager."""

    @pytest.fixture
    def manager(self) -> FeatureManager:
        return FeatureManager()

    @pytest.fixture
    def template_with_all_features(self, tmp_path: Path) -> Path:
        template = tmp_path / "template"

        (template / "src/main/java/com/example/arinfra/event").mkdir(parents=True)
        (template / "src/main/java/com/example/arinfra/mail").mkdir(parents=True)
        (template / "src/main/java/com/example/arinfra/repository").mkdir(parents=True)
        (template / "src/main/java/com/example/arinfra/config").mkdir(parents=True)

        (template / "src/main/java/com/example/arinfra/config/RabbitConfig.java").write_text(
            "rabbit"
        )
        (template / "src/main/java/com/example/arinfra/config/EmailConf.java").write_text("email")
        (template / "src/main/java/com/example/arinfra/config/BucketConf.java").write_text("bucket")

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
        self, manager: FeatureManager, template_with_all_features: Path
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

    def test_get_feature_dependencies(self, manager: FeatureManager) -> None:
        deps = manager.get_feature_dependencies(TemplateFeature.RABBITMQ)

        assert "org.springframework.boot:spring-boot-starter-amqp" in deps
        assert "org.testcontainers:rabbitmq" in deps

    def test_get_all_dependencies_for_features(self, manager: FeatureManager) -> None:
        enabled = {TemplateFeature.POSTGRESQL, TemplateFeature.EMAIL}
        deps = manager.get_dependencies_for_features(enabled)

        assert "org.springframework.boot:spring-boot-starter-data-jpa" in deps
        assert "org.postgresql:postgresql" in deps
        assert "org.springframework.boot:spring-boot-starter-mail" in deps

    def test_handle_missing_files_gracefully(self, manager: FeatureManager, tmp_path: Path) -> None:
        template = tmp_path / "template"
        template.mkdir()

        manager.remove_feature(template, TemplateFeature.RABBITMQ)
