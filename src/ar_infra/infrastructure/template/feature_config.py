"""Feature configuration mapping."""

from dataclasses import dataclass
from typing import Final

from src.ar_infra.domain.enums.template_feature import TemplateFeature


SRC_PACKAGE = "src/main/java/com/example/arinfra/"
TEST_PACKAGE = "src/test/java/com/example/arinfra/"


@dataclass(frozen=True)
class FeatureFiles:
    """Files and dependencies associated with a feature."""

    directories: list[str]
    files: list[str]
    dependencies: list[str]


FEATURE_MAPPINGS: Final[dict[TemplateFeature, FeatureFiles]] = {
    TemplateFeature.POSTGRESQL: FeatureFiles(
        directories=[
            SRC_PACKAGE + "repository",
            "src/main/resources/db",
            TEST_PACKAGE + "service/health",
        ],
        files=[
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthRepositoryController.java",
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
    ),
    TemplateFeature.RABBITMQ: FeatureFiles(
        directories=[
            SRC_PACKAGE + "event",
        ],
        files=[
            SRC_PACKAGE + "config/RabbitConfig.java",
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthEventController.java",
            TEST_PACKAGE + "conf/RabbitMQConf.java",
            TEST_PACKAGE + "service/health/HealthEventService.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthEventControllerIT.java",
        ],
        dependencies=[
            "org.springframework.boot:spring-boot-starter-amqp",
            "org.springframework.amqp:spring-rabbit-test",
            "org.testcontainers:rabbitmq",
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
            TEST_PACKAGE + "conf/BucketConf.java",
            TEST_PACKAGE + "file/BucketComponentIT.java",
            SRC_PACKAGE + "service/health/HealthBucketService.java",
            TEST_PACKAGE + "service/health/HealthBucketServiceIT.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthBucketControllerIT.java",
        ],
        dependencies=[
            "software.amazon.awssdk:s3",
            "software.amazon.awssdk:s3-transfer-manager",
            "org.testcontainers:localstack",
        ],
    ),
    TemplateFeature.EMAIL: FeatureFiles(
        directories=[
            SRC_PACKAGE + "mail",
            TEST_PACKAGE + "mail",
        ],
        files=[
            SRC_PACKAGE + "config/EmailConf.java",
            SRC_PACKAGE + "exception/EmailSendException.java",
            SRC_PACKAGE + "exception/health/EmailHealthCheckException.java",
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthEmailController.java",
            TEST_PACKAGE + "conf/EmailConf.java",
            TEST_PACKAGE + "service/health/HealthEmailService.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthEmailControllerIT.java",
        ],
        dependencies=[
            "org.springframework.boot:spring-boot-starter-mail",
            "com.icegreen:greenmail",
            "com.icegreen:greenmail-junit5",
        ],
    ),
}
