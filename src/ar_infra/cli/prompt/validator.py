import re
from pathlib import Path


class Validators:
    """Collection of input validators."""

    @staticmethod
    def group_id(value: str) -> str | None:
        pattern = r"^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)+$"
        if not re.match(pattern, value):
            return "Invalid group ID. Must be lowercase, dot-separated (e.g., com.example)"
        return None

    @staticmethod
    def artifact_id(value: str) -> str | None:
        pattern = r"^[a-z][a-z0-9-]*$"
        if not re.match(pattern, value):
            return "Invalid artifact ID. Must be lowercase, can contain hyphens (e.g., my-app)"
        return None

    @staticmethod
    def version(value: str) -> str | None:
        pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$"
        if not re.match(pattern, value):
            return "Invalid version. Must follow semantic versioning (e.g., 1.0.0)"
        return None

    @staticmethod
    def path(value: str) -> str | None:
        try:
            resolved = Path(value).expanduser().resolve()
        except (OSError, ValueError) as exc:
            return f"Invalid path: {exc}"

        if resolved.exists() and not resolved.is_dir():
            return "Path exists but is not a directory"

        return None

    @staticmethod
    def features(value: str) -> str | None:
        valid_features = {"postgresql", "rabbitmq", "s3_bucket", "email"}

        features = [f.strip().lower() for f in value.split(",") if f.strip()]
        invalid = [f for f in features if f not in valid_features]

        if invalid:
            return f"Invalid features: {', '.join(invalid)}"
        return None
