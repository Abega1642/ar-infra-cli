from dataclasses import dataclass
from typing import Final

from src.ar_infra.domain.enums.template_feature import TemplateFeature


SRC_PACKAGE = "src/main/java/com/example/arinfra/"
TEST_PACKAGE = "src/test/java/com/example/arinfra/"


@dataclass(frozen=True)
class FeatureFiles:
    """Files, dependencies, and environment variables associated with a feature."""

    directories: list[str]
    files: list[str]
    dependencies: list[str]
    env_variables: list[str]


FEATURE_MAPPINGS: Final[dict[TemplateFeature, FeatureFiles]] = {
    TemplateFeature.POSTGRESQL: FeatureFiles(
        directories=[
            SRC_PACKAGE + "repository",
            "src/main/resources/db",
            TEST_PACKAGE + "service/health",
        ],
        files=[
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthRepositoryController.java",
            SRC_PACKAGE + "service/health/HealthRepositoryService.java",
            TEST_PACKAGE + "conf/PostgresConf.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthRepositoryControllerIT.java",
        ],
        dependencies=[
            "org.springframework.boot:spring-boot-starter-data-jpa",
            "org.postgresql:postgresql",
            "org.flywaydb:flyway-core",
            "org.flywaydb:flyway-database-postgresql",
            "org.testcontainers:postgresql",
        ],
        env_variables=[
            "SPRING_DATASOURCE_URL",
            "SPRING_DATASOURCE_USERNAME",
            "SPRING_DATASOURCE_PASSWORD",
        ],
    ),
    TemplateFeature.RABBITMQ: FeatureFiles(
        directories=[
            SRC_PACKAGE + "event",
            SRC_PACKAGE + "datastructure",
        ],
        files=[
            SRC_PACKAGE + "config/RabbitConfig.java",
            SRC_PACKAGE + "datastructure/ListGrouper.java",
            SRC_PACKAGE + "service/health/HealthEventService.java",
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthEventController.java",
            TEST_PACKAGE + "conf/RabbitMQConf.java",
            TEST_PACKAGE + "service/health/HealthEventServiceIT.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthEventControllerIT.java",
        ],
        dependencies=[
            "org.springframework.boot:spring-boot-starter-amqp",
            "org.springframework.amqp:spring-rabbit-test",
            "org.testcontainers:rabbitmq",
        ],
        env_variables=[
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
    ),
    TemplateFeature.S3_BUCKET: FeatureFiles(
        directories=[
            SRC_PACKAGE + "exception/bucket",
        ],
        files=[
            SRC_PACKAGE + "config/BucketConf.java",
            SRC_PACKAGE + "file/BucketComponent.java",
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthBucketController.java",
            SRC_PACKAGE + "service/health/HealthBucketService.java",
            TEST_PACKAGE + "conf/BucketConf.java",
            TEST_PACKAGE + "file/BucketComponentIT.java",
            TEST_PACKAGE + "service/health/HealthBucketServiceIT.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthBucketControllerIT.java",
        ],
        dependencies=[
            "software.amazon.awssdk:s3",
            "software.amazon.awssdk:s3-transfer-manager",
            "org.testcontainers:localstack",
        ],
        env_variables=[
            "B2_KEY_ID",
            "B2_APPLICATION_KEY",
            "B2_BUCKET_NAME",
            "B2_ENDPOINT",
            "B2_ENDPOINT_PREFIX",
            "B2_ENDPOINT_SUFFIX",
            "B2_REGION",
        ],
    ),
    TemplateFeature.EMAIL: FeatureFiles(
        directories=[
            SRC_PACKAGE + "mail",
            TEST_PACKAGE + "mail",
        ],
        files=[
            SRC_PACKAGE + "config/EmailConf.java",
            SRC_PACKAGE + "service/health/HealthEmailService.java",
            SRC_PACKAGE + "exception/EmailSendException.java",
            SRC_PACKAGE + "exception/health/EmailHealthCheckException.java",
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthEmailController.java",
            TEST_PACKAGE + "conf/EmailConf.java",
            TEST_PACKAGE + "service/health/HealthEmailServiceIT.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthEmailControllerIT.java",
        ],
        dependencies=[
            "org.springframework.boot:spring-boot-starter-mail",
            "com.icegreen:greenmail",
            "com.icegreen:greenmail-junit5",
        ],
        env_variables=[
            "SPRING_MAIL_HOST",
            "SPRING_MAIL_USERNAME",
            "SPRING_MAIL_PASSWORD",
            "SPRING_MAIL_FROM_EMAIL",
            "SPRING_MAIL_PORT",
        ],
    ),
}
