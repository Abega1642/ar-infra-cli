from dataclasses import dataclass
from typing import Final

from src.ar_infra.domain.enums.template_feature import TemplateFeature


SRC_PACKAGE = "src/main/java/com/example/arinfra/"
TEST_PACKAGE = "src/test/java/com/example/arinfra/"


@dataclass(frozen=True)
class FeatureFiles:
    shared_directories: list[str]
    specific_directories: list[str]
    shared_files: list[str]
    specific_files: list[str]
    shared_env_variables: list[str]
    specific_env_variables: list[str]


@dataclass(frozen=True)
class FeatureDependencies:
    shared: list[str]
    specific: list[str]


# Database shared resources (common to all database features)
DATABASE_SHARED_DIRECTORIES: list[str] = [
    SRC_PACKAGE + "repository",
    "src/main/resources/db",
]

DATABASE_SHARED_FILES: list[str] = [
    SRC_PACKAGE + "endpoint/rest/controller/health/HealthRepositoryController.java",
    SRC_PACKAGE + "service/health/HealthRepositoryService.java",
    TEST_PACKAGE + "endpoint/rest/controller/health/HealthRepositoryControllerIT.java",
]

DATABASE_SHARED_ENV_VARIABLES: list[str] = [
    "SPRING_DATASOURCE_URL",
    "SPRING_DATASOURCE_USERNAME",
    "SPRING_DATASOURCE_PASSWORD",
]

DATABASE_SHARED_DEPENDENCIES: list[str] = [
    "org.springframework.boot:spring-boot-starter-data-jpa",
    "org.flywaydb:flyway-core",
]

FEATURE_FILES: Final[dict[TemplateFeature, FeatureFiles]] = {
    TemplateFeature.POSTGRESQL: FeatureFiles(
        shared_directories=[*DATABASE_SHARED_DIRECTORIES, TEST_PACKAGE + "conf/db"],
        specific_directories=[],
        shared_files=DATABASE_SHARED_FILES,
        specific_files=[TEST_PACKAGE + "conf/db/PostgresConf.java"],
        shared_env_variables=DATABASE_SHARED_ENV_VARIABLES,
        specific_env_variables=[],
    ),
    TemplateFeature.MYSQL: FeatureFiles(
        shared_directories=[*DATABASE_SHARED_DIRECTORIES, TEST_PACKAGE + "conf/db"],
        specific_directories=[],
        shared_files=DATABASE_SHARED_FILES,
        specific_files=[TEST_PACKAGE + "conf/db/MysqlConf.java"],
        shared_env_variables=DATABASE_SHARED_ENV_VARIABLES,
        specific_env_variables=[],
    ),
    TemplateFeature.RABBITMQ: FeatureFiles(
        shared_directories=[],
        specific_directories=[
            SRC_PACKAGE + "event",
            SRC_PACKAGE + "datastructure",
        ],
        shared_files=[],
        specific_files=[
            SRC_PACKAGE + "config/RabbitConf.java",
            SRC_PACKAGE + "datastructure/ListGrouper.java",
            SRC_PACKAGE + "service/health/HealthEventService.java",
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthEventController.java",
            TEST_PACKAGE + "conf/RabbitMQConf.java",
            TEST_PACKAGE + "service/health/HealthEventServiceIT.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthEventControllerIT.java",
        ],
        shared_env_variables=[],
        specific_env_variables=[
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
        shared_directories=[],
        specific_directories=[
            SRC_PACKAGE + "exception/bucket",
        ],
        shared_files=[],
        specific_files=[
            SRC_PACKAGE + "config/BucketConf.java",
            SRC_PACKAGE + "file/BucketComponent.java",
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthBucketController.java",
            SRC_PACKAGE + "service/health/HealthBucketService.java",
            TEST_PACKAGE + "conf/BucketConf.java",
            TEST_PACKAGE + "file/BucketComponentIT.java",
            TEST_PACKAGE + "service/health/HealthBucketServiceIT.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthBucketControllerIT.java",
        ],
        shared_env_variables=[],
        specific_env_variables=[
            "CLOUD_STORAGE_KEY_ID",
            "CLOUD_STORAGE_APPLICATION_KEY",
            "CLOUD_STORAGE_BUCKET_NAME",
            "CLOUD_STORAGE_FULL_ENDPOINT",
            "CLOUD_STORAGE_REGION",
        ],
    ),
    TemplateFeature.EMAIL: FeatureFiles(
        shared_directories=[],
        specific_directories=[
            SRC_PACKAGE + "mail",
            TEST_PACKAGE + "mail",
        ],
        shared_files=[],
        specific_files=[
            SRC_PACKAGE + "config/EmailConf.java",
            SRC_PACKAGE + "service/health/HealthEmailService.java",
            SRC_PACKAGE + "exception/EmailSendException.java",
            SRC_PACKAGE + "exception/health/EmailHealthCheckException.java",
            SRC_PACKAGE + "endpoint/rest/controller/health/HealthEmailController.java",
            TEST_PACKAGE + "conf/EmailConf.java",
            TEST_PACKAGE + "service/health/HealthEmailServiceIT.java",
            TEST_PACKAGE + "endpoint/rest/controller/health/HealthEmailControllerIT.java",
        ],
        shared_env_variables=[],
        specific_env_variables=[
            "SPRING_MAIL_HOST",
            "SPRING_MAIL_USERNAME",
            "SPRING_MAIL_PASSWORD",
            "SPRING_MAIL_FROM_EMAIL",
            "SPRING_MAIL_PORT",
        ],
    ),
}

FEATURE_DEPENDENCIES: Final[dict[TemplateFeature, FeatureDependencies]] = {
    TemplateFeature.POSTGRESQL: FeatureDependencies(
        shared=DATABASE_SHARED_DEPENDENCIES,
        specific=[
            "org.postgresql:postgresql",
            "org.flywaydb:flyway-database-postgresql",
            "org.testcontainers:postgresql",
        ],
    ),
    TemplateFeature.MYSQL: FeatureDependencies(
        shared=DATABASE_SHARED_DEPENDENCIES,
        specific=[
            "com.mysql:mysql-connector-j",
            "org.flywaydb:flyway-mysql",
            "org.testcontainers:mysql",
        ],
    ),
    TemplateFeature.RABBITMQ: FeatureDependencies(
        shared=[],
        specific=[
            "org.springframework.boot:spring-boot-starter-amqp",
            "org.springframework.amqp:spring-rabbit-test",
            "org.testcontainers:rabbitmq",
        ],
    ),
    TemplateFeature.S3_BUCKET: FeatureDependencies(
        shared=[],
        specific=[
            "software.amazon.awssdk:s3",
            "software.amazon.awssdk:s3-transfer-manager",
            "org.testcontainers:localstack",
        ],
    ),
    TemplateFeature.EMAIL: FeatureDependencies(
        shared=[],
        specific=[
            "org.springframework.boot:spring-boot-starter-mail",
            "com.icegreen:greenmail",
            "com.icegreen:greenmail-junit5",
        ],
    ),
}


def get_all_dependencies_for_features(enabled_features: set[TemplateFeature]) -> list[str]:
    all_deps = set()

    for feature in enabled_features:
        feature_deps = FEATURE_DEPENDENCIES.get(feature)
        if feature_deps:
            all_deps.update(feature_deps.shared)
            all_deps.update(feature_deps.specific)

    return sorted(all_deps)
