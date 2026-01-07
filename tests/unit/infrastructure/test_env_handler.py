"""Tests for EnvHandler."""

from pathlib import Path

import pytest

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.env_handler import EnvHandler


SAMPLE_ENV_TEMPLATE = """SPRING_RABBITMQ_HOST=rabbit_mq_host
SPRING_RABBITMQ_USERNAME=rabbit_mq_username
SPRING_RABBITMQ_PASSWORD=rabbit_mq_password
SPRING_RABBITMQ_VHOST=rabbit_mq_vhost
SPRING_RABBITMQ_QUEUE=rabbit_mq_queue
SPRING_RABBITMQ_EXCHANGE=rabbit_mq_exchange_key
SPRING_RABBITMQ_ROUTING_KEY=rabbit_mq_routing_key
SPRING_RABBITMQ_PORT=5671
APP_RABBITMQ_SSL=true

SPRING_DATASOURCE_URL=datasource_url
SPRING_DATASOURCE_USERNAME=datasource_username
SPRING_DATASOURCE_PASSWORD=data_source_password

B2_KEY_ID=b2_key_id
B2_APPLICATION_KEY=b2_app_id
B2_BUCKET_NAME=bucket_name
B2_ENDPOINT=b2_endpoint_base_url
B2_ENDPOINT_PREFIX=b2_endpoint_base_url_prefix
B2_ENDPOINT_SUFFIX=b2_endpoint_base_url_suffix
B2_REGION=b2_region

PORT=8080

SPRING_MAIL_HOST=spring_mail_host
SPRING_MAIL_USERNAME=spring_mail_username
SPRING_MAIL_PASSWORD=spring_mail_password
SPRING_MAIL_FROM_EMAIL=spring_mail_from_email
SPRING_MAIL_PORT=port
"""


class TestEnvHandler:
    @pytest.fixture
    def handler(self) -> EnvHandler:
        return EnvHandler()

    @pytest.fixture
    def env_file(self, tmp_path: Path) -> Path:
        env_path = tmp_path / ".env.template"
        env_path.write_text(SAMPLE_ENV_TEMPLATE, encoding="utf-8")
        return env_path

    def test_remove_rabbitmq_variables(self, handler: EnvHandler, env_file: Path) -> None:
        mappings = {
            TemplateFeature.RABBITMQ: [
                "SPRING_RABBITMQ_HOST",
                "SPRING_RABBITMQ_USERNAME",
                "SPRING_RABBITMQ_PASSWORD",
                "SPRING_RABBITMQ_VHOST",
                "SPRING_RABBITMQ_QUEUE",
                "SPRING_RABBITMQ_EXCHANGE",
                "SPRING_RABBITMQ_ROUTING_KEY",
                "SPRING_RABBITMQ_PORT",
                "APP_RABBITMQ_SSL",
            ]
        }

        handler.remove_feature_env_variables(env_file, {TemplateFeature.RABBITMQ}, mappings)

        content = env_file.read_text(encoding="utf-8")

        assert "SPRING_RABBITMQ_HOST" not in content
        assert "APP_RABBITMQ_SSL" not in content
        assert "SPRING_DATASOURCE_URL" in content
        assert "B2_KEY_ID" in content
        assert "SPRING_MAIL_HOST" in content
        assert "PORT=8080" in content

    def test_remove_postgresql_variables(self, handler: EnvHandler, env_file: Path) -> None:
        mappings = {
            TemplateFeature.POSTGRESQL: [
                "SPRING_DATASOURCE_URL",
                "SPRING_DATASOURCE_USERNAME",
                "SPRING_DATASOURCE_PASSWORD",
            ]
        }

        handler.remove_feature_env_variables(env_file, {TemplateFeature.POSTGRESQL}, mappings)

        content = env_file.read_text(encoding="utf-8")

        assert "SPRING_DATASOURCE_URL" not in content
        assert "SPRING_DATASOURCE_USERNAME" not in content
        assert "SPRING_DATASOURCE_PASSWORD" not in content
        assert "SPRING_RABBITMQ_HOST" in content
        assert "B2_KEY_ID" in content

    def test_remove_s3_bucket_variables(self, handler: EnvHandler, env_file: Path) -> None:
        mappings = {
            TemplateFeature.S3_BUCKET: [
                "B2_KEY_ID",
                "B2_APPLICATION_KEY",
                "B2_BUCKET_NAME",
                "B2_ENDPOINT",
                "B2_ENDPOINT_PREFIX",
                "B2_ENDPOINT_SUFFIX",
                "B2_REGION",
            ]
        }

        handler.remove_feature_env_variables(env_file, {TemplateFeature.S3_BUCKET}, mappings)

        content = env_file.read_text(encoding="utf-8")

        assert "B2_KEY_ID" not in content
        assert "B2_ENDPOINT" not in content
        assert "SPRING_DATASOURCE_URL" in content
        assert "SPRING_MAIL_HOST" in content

    def test_remove_email_variables(self, handler: EnvHandler, env_file: Path) -> None:
        mappings = {
            TemplateFeature.EMAIL: [
                "SPRING_MAIL_HOST",
                "SPRING_MAIL_USERNAME",
                "SPRING_MAIL_PASSWORD",
                "SPRING_MAIL_FROM_EMAIL",
                "SPRING_MAIL_PORT",
            ]
        }

        handler.remove_feature_env_variables(env_file, {TemplateFeature.EMAIL}, mappings)

        content = env_file.read_text(encoding="utf-8")

        assert "SPRING_MAIL_HOST" not in content
        assert "SPRING_MAIL_FROM_EMAIL" not in content
        assert "SPRING_DATASOURCE_URL" in content
        assert "B2_KEY_ID" in content

    def test_remove_multiple_features(self, handler: EnvHandler, env_file: Path) -> None:
        mappings = {
            TemplateFeature.RABBITMQ: [
                "SPRING_RABBITMQ_HOST",
                "SPRING_RABBITMQ_USERNAME",
                "SPRING_RABBITMQ_PASSWORD",
                "SPRING_RABBITMQ_VHOST",
                "SPRING_RABBITMQ_QUEUE",
                "SPRING_RABBITMQ_EXCHANGE",
                "SPRING_RABBITMQ_ROUTING_KEY",
                "SPRING_RABBITMQ_PORT",
                "APP_RABBITMQ_SSL",
            ],
            TemplateFeature.EMAIL: [
                "SPRING_MAIL_HOST",
                "SPRING_MAIL_USERNAME",
                "SPRING_MAIL_PASSWORD",
                "SPRING_MAIL_FROM_EMAIL",
                "SPRING_MAIL_PORT",
            ],
        }

        handler.remove_feature_env_variables(
            env_file, {TemplateFeature.RABBITMQ, TemplateFeature.EMAIL}, mappings
        )

        content = env_file.read_text(encoding="utf-8")

        assert "SPRING_RABBITMQ_HOST" not in content
        assert "SPRING_MAIL_HOST" not in content
        assert "SPRING_DATASOURCE_URL" in content
        assert "B2_KEY_ID" in content
        assert "PORT=8080" in content

    def test_preserve_non_feature_variables(self, handler: EnvHandler, env_file: Path) -> None:
        mappings = {
            TemplateFeature.RABBITMQ: ["SPRING_RABBITMQ_HOST"],
        }

        handler.remove_feature_env_variables(env_file, {TemplateFeature.RABBITMQ}, mappings)

        content = env_file.read_text(encoding="utf-8")

        assert "PORT=8080" in content

    def test_handle_missing_env_file(self, handler: EnvHandler, tmp_path: Path) -> None:
        non_existent = tmp_path / "missing.env"
        mappings = {TemplateFeature.RABBITMQ: ["SPRING_RABBITMQ_HOST"]}

        handler.remove_feature_env_variables(non_existent, {TemplateFeature.RABBITMQ}, mappings)

        assert not non_existent.exists()

    def test_preserve_empty_lines_and_comments(self, handler: EnvHandler, tmp_path: Path) -> None:
        env_with_comments = tmp_path / ".env.template"
        env_with_comments.write_text(
            """# Database config
SPRING_DATASOURCE_URL=url

# RabbitMQ config
SPRING_RABBITMQ_HOST=host

# Other
PORT=8080
""",
            encoding="utf-8",
        )

        mappings = {TemplateFeature.RABBITMQ: ["SPRING_RABBITMQ_HOST"]}

        handler.remove_feature_env_variables(
            env_with_comments, {TemplateFeature.RABBITMQ}, mappings
        )

        content = env_with_comments.read_text(encoding="utf-8")

        assert "# Database config" in content
        assert "SPRING_RABBITMQ_HOST" not in content
        assert "PORT=8080" in content
