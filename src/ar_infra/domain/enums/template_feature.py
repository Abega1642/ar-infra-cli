from enum import Enum


class TemplateFeature(str, Enum):
    """Available features in the template."""

    POSTGRESQL = "postgresql"
    RABBITMQ = "rabbitmq"
    S3_BUCKET = "s3_bucket"
    EMAIL = "email"
