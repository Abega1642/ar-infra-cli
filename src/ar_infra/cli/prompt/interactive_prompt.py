"""Interactive prompts for user input."""

from pathlib import Path
from typing import Any

from questionary import (
    Style,
    checkbox,
    confirm,
    text,
)

from src.ar_infra.cli.prompt.validator import Validators


CLR = "fg:#673ab7"
PROMPT_STYLE = Style(
    [
        ("qmark", f"{CLR} bold"),
        ("question", "bold"),
        ("answer", "fg:#f44336 bold"),
        ("pointer", f"{CLR} bold"),
        ("highlighted", f"{CLR} bold"),
        ("selected", "fg:#cc5454"),
        ("separator", "fg:#cc5454"),
        ("instruction", ""),
        ("text", ""),
    ]
)


class InteractivePrompt:
    """Handles interactive CLI prompts."""

    def __init__(self) -> None:
        self.validators = Validators()

    def collect_inputs(self) -> dict[str, Any]:
        """Collect all inputs interactively."""
        group_id = text(
            "Maven Group ID:",
            default="com.example",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.group_id(val) is None,
        ).ask()

        artifact_id = text(
            "Maven Artifact ID (project name):",
            default="my-app",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.artifact_id(val) is None,
        ).ask()

        version = text(
            "Project Version:",
            default="1.0.0",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.version(val) is None,
        ).ask()

        destination = text(
            "Destination Directory:",
            default="./",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.path(val) is None,
        ).ask()

        features = checkbox(
            "Select Features to Include:",
            choices=[
                {"name": "PostgreSQL Database", "value": "postgresql"},
                {"name": "RabbitMQ Message Broker", "value": "rabbitmq"},
                {"name": "AWS S3 Storage", "value": "s3_bucket"},
                {"name": "Email Support", "value": "email"},
            ],
            style=PROMPT_STYLE,
        ).ask()

        use_cache = confirm(
            "Use cached template (faster)?",
            default=True,
            style=PROMPT_STYLE,
        ).ask()

        return {
            "group_id": group_id,
            "artifact_id": artifact_id,
            "version": version,
            "destination": Path(destination).expanduser().resolve(),
            "enabled_features": set(features),
            "use_template_cache": use_cache,
        }
