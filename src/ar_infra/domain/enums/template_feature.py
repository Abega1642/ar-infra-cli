from enum import StrEnum


class TemplateFeature(StrEnum):
    """Available features in the template."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    RABBITMQ = "rabbitmq"
    S3_BUCKET = "s3_bucket"
    EMAIL = "email"

    @classmethod
    def database_features(cls) -> set["TemplateFeature"]:
        return {cls.POSTGRESQL, cls.MYSQL}
