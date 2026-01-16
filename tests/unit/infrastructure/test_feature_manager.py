"""Tests for FeatureManager."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from tests.fixtures.sample_env_template import SAMPLE_ENV_CONTENT

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.feature_manager import FeatureManager


class TestFeatureManager:
    @pytest.fixture
    def mock_env_handler(self) -> Mock:
        return Mock()

    @pytest.fixture
    def mock_facadeit_handler(self) -> Mock:
        return Mock()

    @pytest.fixture
    def mock_rest_exception_handler(self) -> Mock:
        return Mock()

    @pytest.fixture
    def mock_swagger_handler(self) -> Mock:
        return Mock()

    @pytest.fixture
    def manager(
        self,
        mock_env_handler: Mock,
        mock_facadeit_handler: Mock,
        mock_rest_exception_handler: Mock,
        mock_swagger_handler: Mock,
    ) -> FeatureManager:
        return FeatureManager(
            env_handler=mock_env_handler,
            facadeit_handler=mock_facadeit_handler,
            rest_exception_handler=mock_rest_exception_handler,
            swagger_handler=mock_swagger_handler,
        )

    @pytest.fixture
    def template_with_all_features(self, tmp_path: Path) -> Path:
        template = tmp_path / "template"

        # Create shared database directories
        (template / "src/main/java/com/example/arinfra/repository").mkdir(parents=True)
        (template / "src/main/resources/db").mkdir(parents=True)

        # Create specific database test conf directory
        (template / "src/test/java/com/example/arinfra/conf/db").mkdir(parents=True)

        # Create other feature directories
        (template / "src/main/java/com/example/arinfra/event").mkdir(parents=True)
        (template / "src/main/java/com/example/arinfra/mail").mkdir(parents=True)
        (template / "src/main/java/com/example/arinfra/exception/bucket").mkdir(parents=True)
        (template / "src/main/java/com/example/arinfra/config").mkdir(parents=True)

        # Create feature-specific files
        (template / "src/main/java/com/example/arinfra/config/RabbitConfig.java").write_text(
            "rabbit", encoding="utf-8"
        )
        (template / "src/main/java/com/example/arinfra/config/EmailConf.java").write_text(
            "email", encoding="utf-8"
        )
        (template / "src/main/java/com/example/arinfra/config/BucketConf.java").write_text(
            "bucket", encoding="utf-8"
        )

        # Create database-specific config files
        (template / "src/test/java/com/example/arinfra/conf/db/PostgresConf.java").write_text(
            "postgres", encoding="utf-8"
        )
        (template / "src/test/java/com/example/arinfra/conf/db/MysqlConf.java").write_text(
            "mysql", encoding="utf-8"
        )

        env_file = template / ".env.template"
        env_file.write_text(SAMPLE_ENV_CONTENT, encoding="utf-8")

        return template

    def test_remove_rabbitmq_feature_only_removes_specific_resources(
        self, manager: FeatureManager, template_with_all_features: Path
    ) -> None:
        enabled = {TemplateFeature.POSTGRESQL, TemplateFeature.EMAIL, TemplateFeature.S3_BUCKET}
        manager.apply_feature_selection(template_with_all_features, enabled)

        # RabbitMQ specific resources should be removed
        assert not (template_with_all_features / "src/main/java/com/example/arinfra/event").exists()
        assert not (
            template_with_all_features
            / "src/main/java/com/example/arinfra/config/RabbitConfig.java"
        ).exists()

        # Other features should remain
        assert (template_with_all_features / "src/main/java/com/example/arinfra/mail").exists()
        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/repository"
        ).exists()

    def test_remove_email_feature_only_removes_specific_resources(
        self, manager: FeatureManager, template_with_all_features: Path
    ) -> None:
        enabled = {TemplateFeature.POSTGRESQL, TemplateFeature.RABBITMQ, TemplateFeature.S3_BUCKET}
        manager.apply_feature_selection(template_with_all_features, enabled)

        # Email specific resources should be removed
        assert not (template_with_all_features / "src/main/java/com/example/arinfra/mail").exists()
        assert not (
            template_with_all_features / "src/main/java/com/example/arinfra/config/EmailConf.java"
        ).exists()

        # Other features should remain
        assert (template_with_all_features / "src/main/java/com/example/arinfra/event").exists()
        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/repository"
        ).exists()

    def test_keep_only_postgresql_removes_mysql_specific_but_keeps_shared(
        self, manager: FeatureManager, template_with_all_features: Path
    ) -> None:
        enabled = {TemplateFeature.POSTGRESQL}
        manager.apply_feature_selection(template_with_all_features, enabled)

        # Shared database resources should remain
        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/repository"
        ).exists()
        assert (template_with_all_features / "src/main/resources/db").exists()

        # PostgreSQL specific should remain
        assert (
            template_with_all_features
            / "src/test/java/com/example/arinfra/conf/db/PostgresConf.java"
        ).exists()

        # MySQL specific should be removed
        assert not (
            template_with_all_features / "src/test/java/com/example/arinfra/conf/db/MysqlConf.java"
        ).exists()

    def test_keep_only_mysql_removes_postgresql_specific_but_keeps_shared(
        self, manager: FeatureManager, template_with_all_features: Path
    ) -> None:
        enabled = {TemplateFeature.MYSQL}
        manager.apply_feature_selection(template_with_all_features, enabled)

        # Shared database resources should remain
        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/repository"
        ).exists()
        assert (template_with_all_features / "src/main/resources/db").exists()

        # MySQL specific should remain
        assert (
            template_with_all_features / "src/test/java/com/example/arinfra/conf/db/MysqlConf.java"
        ).exists()

        # PostgreSQL specific should be removed
        assert not (
            template_with_all_features
            / "src/test/java/com/example/arinfra/conf/db/PostgresConf.java"
        ).exists()

    def test_keep_both_databases_keeps_all_database_resources(
        self, manager: FeatureManager, template_with_all_features: Path
    ) -> None:
        enabled = {TemplateFeature.POSTGRESQL, TemplateFeature.MYSQL}
        manager.apply_feature_selection(template_with_all_features, enabled)

        # Shared database resources should remain
        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/repository"
        ).exists()
        assert (template_with_all_features / "src/main/resources/db").exists()

        # Both specific configs should remain
        assert (
            template_with_all_features
            / "src/test/java/com/example/arinfra/conf/db/PostgresConf.java"
        ).exists()
        assert (
            template_with_all_features / "src/test/java/com/example/arinfra/conf/db/MysqlConf.java"
        ).exists()

    def test_remove_all_databases_removes_shared_resources(
        self, manager: FeatureManager, template_with_all_features: Path
    ) -> None:
        enabled = {TemplateFeature.RABBITMQ, TemplateFeature.EMAIL}
        manager.apply_feature_selection(template_with_all_features, enabled)

        # Shared database resources should be removed
        assert not (
            template_with_all_features / "src/main/java/com/example/arinfra/repository"
        ).exists()
        assert not (template_with_all_features / "src/main/resources/db").exists()

        # Both specific configs should be removed
        assert not (
            template_with_all_features
            / "src/test/java/com/example/arinfra/conf/db/PostgresConf.java"
        ).exists()
        assert not (
            template_with_all_features / "src/test/java/com/example/arinfra/conf/db/MysqlConf.java"
        ).exists()

    def test_keep_selected_features_postgresql(
        self,
        manager: FeatureManager,
        template_with_all_features: Path,
        mock_env_handler: Mock,
        mock_facadeit_handler: Mock,
        mock_rest_exception_handler: Mock,
        mock_swagger_handler: Mock,
    ) -> None:
        enabled = {TemplateFeature.POSTGRESQL, TemplateFeature.S3_BUCKET}
        manager.apply_feature_selection(template_with_all_features, enabled)

        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/config/BucketConf.java"
        ).exists()
        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/repository"
        ).exists()

        assert not (template_with_all_features / "src/main/java/com/example/arinfra/event").exists()
        assert not (template_with_all_features / "src/main/java/com/example/arinfra/mail").exists()

        mock_env_handler.remove_feature_env_variables.assert_called_once()
        mock_facadeit_handler.apply_feature_selection.assert_called_once_with(
            template_with_all_features, enabled
        )
        mock_rest_exception_handler.apply_feature_selection.assert_called_once_with(
            template_with_all_features, enabled
        )
        mock_swagger_handler.update_swagger.assert_called_once_with(enabled)

    def test_keep_selected_features_mysql(
        self,
        manager: FeatureManager,
        template_with_all_features: Path,
        mock_env_handler: Mock,
        mock_facadeit_handler: Mock,
        mock_rest_exception_handler: Mock,
        mock_swagger_handler: Mock,
    ) -> None:
        enabled = {TemplateFeature.MYSQL, TemplateFeature.EMAIL}
        manager.apply_feature_selection(template_with_all_features, enabled)

        assert (template_with_all_features / "src/main/java/com/example/arinfra/mail").exists()
        assert (
            template_with_all_features / "src/main/java/com/example/arinfra/repository"
        ).exists()

        assert not (template_with_all_features / "src/main/java/com/example/arinfra/event").exists()
        assert not (
            template_with_all_features / "src/main/java/com/example/arinfra/config/BucketConf.java"
        ).exists()

        mock_env_handler.remove_feature_env_variables.assert_called_once()
        mock_facadeit_handler.apply_feature_selection.assert_called_once_with(
            template_with_all_features, enabled
        )
        mock_rest_exception_handler.apply_feature_selection.assert_called_once_with(
            template_with_all_features, enabled
        )
        mock_swagger_handler.update_swagger.assert_called_once_with(enabled)

    def test_get_feature_dependencies_postgresql(self, manager: FeatureManager) -> None:
        deps = manager.get_feature_dependencies(TemplateFeature.POSTGRESQL)

        assert "org.springframework.boot:spring-boot-starter-data-jpa" in deps
        assert "org.postgresql:postgresql" in deps
        assert "org.flywaydb:flyway-core" in deps
        assert "org.flywaydb:flyway-database-postgresql" in deps
        assert "org.testcontainers:postgresql" in deps

    def test_get_feature_dependencies_mysql(self, manager: FeatureManager) -> None:
        deps = manager.get_feature_dependencies(TemplateFeature.MYSQL)

        assert "org.springframework.boot:spring-boot-starter-data-jpa" in deps
        assert "com.mysql:mysql-connector-j" in deps
        assert "org.flywaydb:flyway-core" in deps
        assert "org.flywaydb:flyway-mysql" in deps
        assert "org.testcontainers:mysql" in deps

    def test_get_feature_dependencies_rabbitmq(self, manager: FeatureManager) -> None:
        deps = manager.get_feature_dependencies(TemplateFeature.RABBITMQ)

        assert "org.springframework.boot:spring-boot-starter-amqp" in deps
        assert "org.testcontainers:rabbitmq" in deps

    def test_get_feature_env_variables_rabbitmq(self, manager: FeatureManager) -> None:
        env_vars = manager.get_feature_env_variables(TemplateFeature.RABBITMQ)

        assert "SPRING_RABBITMQ_HOST" in env_vars
        assert "APP_RABBITMQ_SSL" in env_vars

    def test_get_feature_env_variables_postgresql(self, manager: FeatureManager) -> None:
        env_vars = manager.get_feature_env_variables(TemplateFeature.POSTGRESQL)

        assert "SPRING_DATASOURCE_URL" in env_vars
        assert "SPRING_DATASOURCE_USERNAME" in env_vars
        assert "SPRING_DATASOURCE_PASSWORD" in env_vars

    def test_get_feature_env_variables_mysql(self, manager: FeatureManager) -> None:
        env_vars = manager.get_feature_env_variables(TemplateFeature.MYSQL)

        assert "SPRING_DATASOURCE_URL" in env_vars
        assert "SPRING_DATASOURCE_USERNAME" in env_vars
        assert "SPRING_DATASOURCE_PASSWORD" in env_vars

    def test_handle_missing_files_gracefully(self, manager: FeatureManager, tmp_path: Path) -> None:
        """Test that the manager handles missing directories/files gracefully."""
        template = tmp_path / "template"
        template.mkdir()
        (template / ".env.template").write_text("", encoding="utf-8")

        # Should not raise any errors even with missing files
        enabled = {TemplateFeature.POSTGRESQL}
        manager.apply_feature_selection(template, enabled)

    def test_apply_feature_selection_removes_env_variables_postgresql(
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
        env_variable_mappings_arg = call_args[0][2]

        assert env_file_arg == template_with_all_features / ".env.template"
        assert TemplateFeature.RABBITMQ in features_to_remove_arg
        assert TemplateFeature.EMAIL in features_to_remove_arg
        assert TemplateFeature.S3_BUCKET in features_to_remove_arg
        assert TemplateFeature.MYSQL in features_to_remove_arg
        assert TemplateFeature.POSTGRESQL not in features_to_remove_arg
        assert isinstance(env_variable_mappings_arg, dict)

    def test_apply_feature_selection_removes_env_variables_mysql(
        self,
        manager: FeatureManager,
        template_with_all_features: Path,
        mock_env_handler: Mock,
    ) -> None:
        enabled = {TemplateFeature.MYSQL}
        manager.apply_feature_selection(template_with_all_features, enabled)

        mock_env_handler.remove_feature_env_variables.assert_called_once()
        call_args = mock_env_handler.remove_feature_env_variables.call_args

        env_file_arg = call_args[0][0]
        features_to_remove_arg = call_args[0][1]
        env_variable_mappings_arg = call_args[0][2]

        assert env_file_arg == template_with_all_features / ".env.template"
        assert TemplateFeature.RABBITMQ in features_to_remove_arg
        assert TemplateFeature.EMAIL in features_to_remove_arg
        assert TemplateFeature.S3_BUCKET in features_to_remove_arg
        assert TemplateFeature.POSTGRESQL in features_to_remove_arg
        assert TemplateFeature.MYSQL not in features_to_remove_arg
        assert isinstance(env_variable_mappings_arg, dict)

    def test_apply_feature_selection_calls_all_handlers(
        self,
        manager: FeatureManager,
        template_with_all_features: Path,
        mock_env_handler: Mock,
        mock_facadeit_handler: Mock,
        mock_rest_exception_handler: Mock,
        mock_swagger_handler: Mock,
    ) -> None:
        enabled = {TemplateFeature.POSTGRESQL, TemplateFeature.RABBITMQ}
        manager.apply_feature_selection(template_with_all_features, enabled)

        mock_env_handler.remove_feature_env_variables.assert_called_once()
        mock_facadeit_handler.apply_feature_selection.assert_called_once_with(
            template_with_all_features, enabled
        )
        mock_rest_exception_handler.apply_feature_selection.assert_called_once_with(
            template_with_all_features, enabled
        )
        mock_swagger_handler.update_swagger.assert_called_once_with(enabled)
