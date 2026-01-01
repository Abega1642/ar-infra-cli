"""Interactive prompts for user input with enhanced security."""

from pathlib import Path
from typing import Any

from questionary import (
    Style,
    checkbox,
    confirm,
    select,
    text,
)

from src.ar_infra.cli.prompt.validator import Validators
from src.ar_infra.domain.entities.path_resolver import (
    DangerousPathError,
    PathSecurityError,
    PathSecurityValidator,
)


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
        self.security_validator = PathSecurityValidator()

    def collect_inputs(self) -> dict[str, Any]:
        """Collect all inputs interactively with security checks."""
        group_id = text(
            "Gradle/Maven Group ID:",
            default="com.example",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.group_id(val) is None,
        ).ask()

        artifact_id = text(
            "Gradle/Maven Artifact ID (project name):",
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

        destination = self._prompt_destination_path()
        project_dir_name = self._prompt_project_directory_name(artifact_id)
        self._handle_existing_directory(destination, project_dir_name)

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
            "destination": destination,
            "project_dir_name": project_dir_name,
            "enabled_features": set(features),
            "use_template_cache": use_cache,
        }

    def _prompt_destination_path(self) -> Path:
        """
        Prompt for destination path with security validation.

        Returns:
            Validated destination path
        """
        while True:
            path_str = self._ask_for_destination_path()
            try:
                validated_path = self.security_validator.validate_destination_path(path_str)
                return self._handle_validated_path(validated_path)
            except DangerousPathError as exc:
                if not self._handle_security_exception(exc, "SECURITY WARNING"):
                    raise
            except PathSecurityError as exc:
                if not self._handle_security_exception(exc, "Security Error"):
                    raise
            except (ValueError, OSError) as exc:
                if not self._handle_general_error(exc):
                    raise

    def _ask_for_destination_path(self) -> str:
        """Prompt user for destination path."""
        result: str = text(
            "Destination Directory (where to create the project folder):",
            default="./",
            style=PROMPT_STYLE,
            validate=lambda val: self.validators.path(val) is None,
        ).ask()
        return result

    def _handle_validated_path(self, validated_path: Path) -> Path:
        """Handle validated path (create if needed, validate directory)."""
        if not validated_path.exists():
            return self._handle_nonexistent_path(validated_path)

        if not validated_path.is_dir():
            self._print_directory_error(validated_path)
            raise ValueError(f"'{validated_path}' exists but is not a directory.")

        return validated_path

    def _handle_nonexistent_path(self, path: Path) -> Path:
        """Handle case where path doesn't exist."""
        create = confirm(
            f"Directory '{path}' does not exist. Create it?",
            default=True,
            style=PROMPT_STYLE,
        ).ask()

        if not create:
            print("\nPlease provide an existing directory.\n")
            raise ValueError("User declined to create directory.")

        return self._create_directory(path)

    def _create_directory(self, path: Path) -> Path:
        """Create directory at given path."""
        try:
            path.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as exc:
            print(f"\nError: Cannot create directory: {exc}\nPlease choose a different path.\n")
            raise

        return path

    def _handle_security_exception(self, exc: Exception, error_type: str) -> bool:
        """Handle security-related exceptions."""
        print(f"\n{error_type}: {exc}\n")
        return self._ask_retry("Would you like to choose a different path?")

    def _handle_general_error(self, exc: Exception) -> bool:
        """Handle general validation/OS errors."""
        print(f"\nError: {exc}\n")
        return self._ask_retry("Would you like to try again?")

    def _ask_retry(self, message: str) -> bool:
        """Ask user if they want to retry."""
        result: bool = confirm(
            message,
            default=True,
            style=PROMPT_STYLE,
        ).ask()
        return result

    def _print_directory_error(self, path: Path) -> None:
        """Print error message for non-directory paths."""
        print(
            f"\nError: '{path}' exists but is not a directory.\nPlease choose a different path.\n"
        )

    def _prompt_project_directory_name(self, default_name: str) -> str:
        """
        Prompt for project directory name with validation.

        Args:
            default_name: Default directory name (artifact_id)

        Returns:
            Validated project directory name
        """
        while True:
            dir_name = text(
                "Project Directory Name (folder name for the project):",
                default=default_name,
                style=PROMPT_STYLE,
            ).ask()

            try:
                return self.security_validator.validate_project_directory_name(dir_name)
            except ValueError as exc:
                print(f"\nError: {exc}\n")
                retry = confirm(
                    "Would you like to try a different name?",
                    default=True,
                    style=PROMPT_STYLE,
                ).ask()
                if not retry:
                    raise

    def _handle_existing_directory(self, destination: Path, project_dir_name: str) -> Path:
        """
        Handle the case where project directory already exists.

        Args:
            destination: Destination path
            project_dir_name: Project directory name

        Returns:
            Final destination path to use
        """
        project_path = destination / project_dir_name

        if not project_path.exists():
            return destination

        if not project_path.is_dir():
            raise ValueError(
                f"'{project_path}' exists but is not a directory. Please choose a different name."
            )

        try:
            has_content = any(project_path.iterdir())
        except (OSError, PermissionError) as exc:
            raise PermissionError(f"Cannot access directory '{project_path}': {exc}") from exc

        if not has_content:
            use_empty = confirm(
                f"Directory '{project_path}' exists but is empty. Use it?",
                default=True,
                style=PROMPT_STYLE,
            ).ask()

            if use_empty:
                return destination
            raise FileExistsError(
                f"Directory '{project_path}' already exists. "
                "Please choose a different name or destination."
            )

        print(f"\nWarning: Directory '{project_path}' already exists and contains files.\n")

        action = select(
            "What would you like to do?",
            choices=[
                {
                    "name": "Choose a different project name",
                    "value": "rename",
                },
                {
                    "name": "Choose a different destination",
                    "value": "change_dest",
                },
                {
                    "name": "Cancel operation",
                    "value": "cancel",
                },
            ],
            style=PROMPT_STYLE,
        ).ask()

        if action == "cancel":
            raise KeyboardInterrupt("Operation cancelled by user")
        if action == "rename":
            raise FileExistsError("Please provide a different project name")
        raise FileExistsError("Please provide a different destination")
