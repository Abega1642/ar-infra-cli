from pathlib import Path
from typing import Any, cast

from questionary import (
    checkbox,
    confirm,
    select,
    text,
)

from src.ar_infra.cli.prompt.validator import Validators
from src.ar_infra.cli.ui.color_properties import PROMPT_STYLE
from src.ar_infra.cli.ui.message import Messages
from src.ar_infra.domain.entities.path_resolver import (
    DangerousPathError,
    PathSecurityError,
    PathSecurityValidator,
)
from src.ar_infra.infrastructure.processor.github_app import GitHubAppHandler


class InteractivePrompt:
    def __init__(self) -> None:
        self.validators = Validators()
        self.security_validator = PathSecurityValidator()
        self.github_app_handler = GitHubAppHandler()

    def collect_inputs(self, *, skip_github_app: bool = False) -> dict[str, Any]:
        while True:
            inputs = self._collect_all_prompts()

            if self._confirm_and_proceed(inputs):
                if not skip_github_app:
                    try:
                        self.github_app_handler.prompt_installation()
                    except KeyboardInterrupt as exc:
                        canceled_message_pref = "GitHub App installation was cancelled."
                        canceled_message_suf = "Continue with project generation anyway?"
                        continue_anyway = confirm(
                            f"\n{canceled_message_pref} {canceled_message_suf}",
                            default=True,
                            style=PROMPT_STYLE,
                        ).ask()

                        if continue_anyway is None or not cast("bool", continue_anyway):
                            raise KeyboardInterrupt("Operation cancelled by user") from exc

                return inputs

            if not self._ask_to_start_over():
                raise KeyboardInterrupt("Configuration cancelled by user") from None

            print("\n")

    def _collect_all_prompts(self) -> dict[str, Any]:
        group_id = self._prompt_group_id()
        artifact_id = self._prompt_artifact_id()
        version = self._prompt_version()

        while True:
            destination = self._prompt_destination_path()
            project_dir_name = self._prompt_project_directory_name(artifact_id)

            conflict_action = self._handle_existing_directory(destination, project_dir_name)

            if conflict_action == "proceed":
                break
            if conflict_action == "rename":
                print()
                continue
            if conflict_action == "change_dest":
                print()
                continue
            print("\nOperation cancelled.\n")
            raise KeyboardInterrupt("Operation cancelled by user") from None

        features = self._prompt_features()
        use_cache = self._prompt_use_cache()

        return {
            "group_id": group_id,
            "artifact_id": artifact_id,
            "version": version,
            "destination": destination,
            "project_dir_name": project_dir_name,
            "enabled_features": set(features),
            "use_template_cache": use_cache,
        }

    def _prompt_group_id(self) -> str:
        result = text(
            "Gradle/Maven Group ID:",
            default="com.example",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.group_id(val) is None,
        ).ask()
        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None
        return cast("str", result)

    def _prompt_artifact_id(self) -> str:
        result = text(
            "Gradle/Maven Artifact ID (project name):",
            default="my-app",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.artifact_id(val) is None,
        ).ask()
        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None
        return cast("str", result)

    def _prompt_version(self) -> str:
        result = text(
            "Project Version:",
            default="1.0.0",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.version(val) is None,
        ).ask()
        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None
        return cast("str", result)

    def _prompt_features(self) -> list[str]:
        result = checkbox(
            "Select Features to Include:",
            choices=[
                {"name": "PostgreSQL Database", "value": "postgresql"},
                {"name": "RabbitMQ Message Broker", "value": "rabbitmq"},
                {"name": "AWS S3 Storage", "value": "s3_bucket"},
                {"name": "Email Support", "value": "email"},
            ],
            style=PROMPT_STYLE,
        ).ask()
        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None
        return cast("list[str]", result)

    def _prompt_use_cache(self) -> bool:
        result = confirm(
            "Use cached template (faster)?",
            default=True,
            style=PROMPT_STYLE,
        ).ask()
        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None
        return cast("bool", result)

    def _confirm_and_proceed(self, inputs: dict[str, Any]) -> bool:
        Messages.project_summary(
            group=inputs["group_id"],
            artifact=inputs["artifact_id"],
            version=inputs["version"],
            path=inputs["destination"] / inputs["project_dir_name"],
            features=list(inputs["enabled_features"]) if inputs["enabled_features"] else [],
        )

        result = confirm(
            "Would you like to proceed with this configuration?",
            default=True,
            style=PROMPT_STYLE,
        ).ask()
        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None
        return cast("bool", result)

    def _ask_to_start_over(self) -> bool:
        result = confirm(
            "Would you like to start over with different values?",
            default=True,
            style=PROMPT_STYLE,
        ).ask()
        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None
        return cast("bool", result)

    def _prompt_destination_path(self) -> Path:
        while True:
            path_str = self._ask_for_destination_path()
            try:
                validated_path = self.security_validator.validate_destination_path(path_str)
                return self._handle_validated_path(validated_path)
            except (DangerousPathError, PathSecurityError) as exc:
                error_type = (
                    "SECURITY WARNING" if isinstance(exc, DangerousPathError) else "Security Error"
                )
                if not self._handle_security_exception(exc, error_type):
                    raise
            except (ValueError, OSError) as exc:
                if not self._handle_general_error(exc):
                    raise

    def _ask_for_destination_path(self) -> str:
        result = text(
            "Destination Directory (where to create the project folder):",
            default="./",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.path(val) is None,
        ).ask()
        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None
        return cast("str", result)

    def _handle_validated_path(self, validated_path: Path) -> Path:
        if not validated_path.exists():
            return self._handle_nonexistent_path(validated_path)

        if not validated_path.is_dir():
            self._print_directory_error(validated_path)
            raise ValueError(f"'{validated_path}' exists but is not a directory.")

        return validated_path

    def _handle_nonexistent_path(self, path: Path) -> Path:
        create = confirm(
            f"Directory '{path}' does not exist. Create it?",
            default=True,
            style=PROMPT_STYLE,
        ).ask()
        if create is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None

        if not cast("bool", create):
            print("\nPlease provide an existing directory.\n")

            retry = confirm(
                "Would you like to try a different path?",
                default=True,
                style=PROMPT_STYLE,
            ).ask()
            if retry is None:
                raise KeyboardInterrupt("Operation cancelled by user") from None

            if not cast("bool", retry):
                raise KeyboardInterrupt("Operation cancelled by user") from None

            return self._prompt_destination_path()

        return self._create_directory(path)

    def _create_directory(self, path: Path) -> Path:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            print(f"\nError: Cannot create directory: {exc}\nPlease choose a different path.\n")
            raise
        return path

    def _handle_security_exception(self, exc: Exception, error_type: str) -> bool:
        print(f"\n{error_type}: {exc}\n")
        return self._ask_retry("Would you like to choose a different path?")

    def _handle_general_error(self, exc: Exception) -> bool:
        print(f"\nError: {exc}\n")
        return self._ask_retry("Would you like to try again?")

    def _ask_retry(self, message: str) -> bool:
        result = confirm(
            message,
            default=True,
            style=PROMPT_STYLE,
        ).ask()
        if result is None:
            raise KeyboardInterrupt("Operation cancelled by user") from None
        return cast("bool", result)

    def _print_directory_error(self, path: Path) -> None:
        print(
            f"\nError: '{path}' exists but is not a directory.\nPlease choose a different path.\n"
        )

    def _prompt_project_directory_name(self, default_name: str) -> str:
        while True:
            dir_name = text(
                "Project Directory Name (folder name for the project):",
                default=default_name,
                style=PROMPT_STYLE,
            ).ask()
            if dir_name is None:
                raise KeyboardInterrupt("Operation cancelled by user") from None

            try:
                return self.security_validator.validate_project_directory_name(
                    cast("str", dir_name)
                )
            except ValueError as exc:
                print(f"\nError: {exc}\n")
                retry = confirm(
                    "Would you like to try a different name?",
                    default=True,
                    style=PROMPT_STYLE,
                ).ask()
                if retry is None:
                    raise KeyboardInterrupt("Operation cancelled by user") from None

                if not cast("bool", retry):
                    raise

    def _handle_existing_directory(self, destination: Path, project_dir_name: str) -> str:
        project_path = destination / project_dir_name

        conflict_result = self._check_path_conflicts(project_path)
        if conflict_result is not None:
            return conflict_result

        empty_dir_result = self._handle_empty_directory(project_path)
        if empty_dir_result is not None:
            return empty_dir_result

        return self._ask_directory_conflict_resolution(project_path)

    def _check_path_conflicts(self, project_path: Path) -> str | None:
        if not project_path.exists():
            return "proceed"

        if not project_path.is_dir():
            print(
                f"\nError: '{project_path}' exists but is not a directory.\n"
                "Please choose a different name or destination.\n"
            )
            return "rename"

        return None

    def _handle_empty_directory(self, project_path: Path) -> str | None:
        try:
            has_content = any(project_path.iterdir())
        except OSError as exc:
            print(f"\nError: Cannot access directory '{project_path}': {exc}\n")
            return "cancel"

        if has_content:
            return None

        use_empty = confirm(
            f"Directory '{project_path}' exists but is empty. Use it?",
            default=True,
            style=PROMPT_STYLE,
        ).ask()

        if use_empty is None or not cast("bool", use_empty):
            return "cancel" if use_empty is None else "rename"

        return "proceed"

    def _ask_directory_conflict_resolution(self, project_path: Path) -> str:
        print(f"\nWarning: Directory '{project_path}' already exists and contains files.\n")

        action = select(
            "What would you like to do?",
            choices=[
                {"name": "Choose a different project name", "value": "rename"},
                {"name": "Choose a different destination", "value": "change_dest"},
                {"name": "Cancel operation", "value": "cancel"},
            ],
            style=PROMPT_STYLE,
        ).ask()

        return "cancel" if action is None else cast("str", action)
