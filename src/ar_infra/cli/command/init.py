"""Init command implementation with enhanced security."""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import NoReturn

from src.ar_infra.application.use_cases.generate_project_use_case import (
    GenerateProjectUseCase,
)
from src.ar_infra.application.use_cases.input_dto import GenerateProjectInput
from src.ar_infra.cli.prompt.interactive_prompt import InteractivePrompt
from src.ar_infra.cli.ui.banner import Banner
from src.ar_infra.cli.ui.message import Messages
from src.ar_infra.cli.ui.progress import ProgressIndicator
from src.ar_infra.domain.entities.path_resolver import (
    DangerousPathError,
    PathSecurityError,
    PathSecurityValidator,
    SafeProjectPathResolver,
)
from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.domain.exceptions.validation_error import (
    InvalidArtifactIdError,
    InvalidGroupIdError,
    InvalidVersionError,
)
from src.ar_infra.domain.value_objects.artifact_id import ArtifactId
from src.ar_infra.domain.value_objects.group_id import GroupId
from src.ar_infra.domain.value_objects.version import Version
from src.ar_infra.infrastructure.gradle import GradleWriter
from src.ar_infra.infrastructure.processor import GitRepositoryInitializer, PackageRenamer
from src.ar_infra.infrastructure.template import FeatureManager, GitHubTemplateFetcher
from src.ar_infra.infrastructure.template.project_signature import (
    InfraGeneratedAnnotationWriter,
)


@dataclass(frozen=True)
class InitCommandArgs:
    """Arguments for init command to avoid too many parameters."""

    group: str | None
    artifact: str | None
    version: str | None
    path: str | None
    project_dir: str | None
    features: str | None
    no_features: str | None
    no_cache: bool


class InitCommand:
    """Handles the init command logic."""

    DEFAULT_TEMPLATE_URL = "https://github.com/Abega1642/ar-infra-template.git"

    def __init__(self) -> None:
        self.use_case = self._create_use_case()
        self.interactive_prompt = InteractivePrompt()
        self.security_validator = PathSecurityValidator()

    def _create_use_case(self) -> GenerateProjectUseCase:
        return GenerateProjectUseCase(
            template_fetcher=GitHubTemplateFetcher(),
            feature_manager=FeatureManager(),
            gradle_writer=GradleWriter(),
            package_renamer=PackageRenamer(),
            git_initializer=GitRepositoryInitializer(),
            annotation_writer=InfraGeneratedAnnotationWriter(),
        )

    def execute(self, args: InitCommandArgs) -> None:
        """Execute the init command."""
        is_interactive = all(
            param is None
            for param in (
                args.group,
                args.artifact,
                args.version,
                args.path,
                args.project_dir,
                args.features,
                args.no_features,
            )
        )

        if is_interactive:
            self._execute_interactive()
        else:
            self._execute_cli(args)

    def _execute_interactive(self) -> None:
        """Execute interactive mode."""
        Banner.show(wait_for_enter=True)
        Messages.welcome()
        try:
            inputs = self.interactive_prompt.collect_inputs()

            self._execute_common(
                group_id=inputs["group_id"],
                artifact_id=inputs["artifact_id"],
                version=inputs["version"],
                destination=str(inputs["destination"]),
                project_dir_name=inputs["project_dir_name"],
                enabled_features=set(inputs["enabled_features"] or []),
                template_url=self.DEFAULT_TEMPLATE_URL,
                use_template_cache=inputs["use_template_cache"],
            )

        except KeyboardInterrupt:
            Messages.warning("\n\nOperation cancelled by user.")
            sys.exit(0)

    def _generate_project(self, project_input: GenerateProjectInput) -> None:
        """Generate the project with proper error handling."""
        with ProgressIndicator.steps(7) as (progress, task):
            progress.update(task, description="Fetching template...")
            progress.advance(task)

            result = self.use_case.execute(project_input)

            if result.success:
                progress.update(task, completed=7, description="Complete!")
                Messages.success(f"\n{result.message}")
                Messages.info(f"Project created at: {result.project_path}")
                if result.has_signature:
                    Messages.info(f"Project signature: {result.signature}")
            else:
                Messages.error(f"\n{result.message}")
                sys.exit(1)

    def _execute_cli(self, args: InitCommandArgs) -> None:
        """Execute CLI mode with enhanced security."""
        if not args.group:
            self._abort("--group is required when not using interactive mode")
        if not args.artifact:
            self._abort("--artifact is required when not using interactive mode")
        if not args.project_dir:
            self._abort(
                "--project-dir is required when not using interactive mode. "
                "This is the name of the directory where your project will be generated."
            )

        assert args.group is not None
        assert args.artifact is not None
        assert args.project_dir is not None

        try:
            enabled_features = self._parse_features(args.features, args.no_features)

            destination_path = Path(args.path or ".").resolve()
            project_path = destination_path / args.project_dir

            Messages.project_summary(
                group=args.group,
                artifact=args.artifact,
                version=args.version or "1.0.0",
                path=project_path,
                features=list(enabled_features),
            )

            self._execute_common(
                group_id=args.group,
                artifact_id=args.artifact,
                version=args.version or "1.0.0",
                destination=args.path or ".",
                project_dir_name=args.project_dir,
                enabled_features=enabled_features,
                template_url=self.DEFAULT_TEMPLATE_URL,
                use_template_cache=not args.no_cache,
            )

        except KeyboardInterrupt:
            Messages.warning("\n\nOperation cancelled by user.")
            sys.exit(0)

    def _execute_common(
        self,
        group_id: str,
        artifact_id: str,
        version: str,
        destination: str,
        project_dir_name: str,
        enabled_features: set[str],
        template_url: str,
        *,
        use_template_cache: bool,
    ) -> None:
        """Shared execution logic for CLI and interactive modes."""
        try:
            validated_destination = self._validate_destination_path(destination)
            validated_project_name = self._validate_project_directory_name(project_dir_name)

            if not validated_destination.exists():
                self._abort(
                    f"Destination directory '{validated_destination}' does not exist.\n"
                    "Please create it first or use an existing directory."
                )

            project_dir = self._resolve_project_dir(validated_destination, validated_project_name)

            project_input = GenerateProjectInput(
                group_id=GroupId(group_id),
                artifact_id=ArtifactId(artifact_id),
                version=Version(version),
                destination=project_dir,
                enabled_features=self._convert_features(enabled_features),
                template_url=template_url,
                use_template_cache=use_template_cache,
            )

            self._generate_project(project_input)

        except (InvalidGroupIdError, InvalidArtifactIdError, InvalidVersionError) as exc:
            self._abort(f"Validation error: {exc}")
        except OSError as exc:
            self._abort(f"I/O error: {exc}")

    def _abort(self, message: str) -> NoReturn:
        """Abort execution with error message."""
        Messages.error(message)
        raise SystemExit(1)

    def _validate_destination_path(self, destination_path: str) -> Path:
        """Validate destination path with security checks."""
        try:
            return self.security_validator.validate_destination_path(destination_path)
        except DangerousPathError as exc:
            Messages.error(
                f"SECURITY WARNING: {exc}\n"
                "Cannot proceed with this destination for security reasons."
            )
            raise SystemExit(1) from exc
        except PathSecurityError as exc:
            Messages.error(f"Security error: {exc}")
            raise SystemExit(1) from exc

    def _validate_project_directory_name(self, project_dir_name: str) -> str:
        """Validate project directory name."""
        try:
            return self.security_validator.validate_project_directory_name(project_dir_name)
        except ValueError as exc:
            Messages.error(f"Invalid project directory name: {exc}")
            raise SystemExit(1) from exc

    def _resolve_project_dir(
        self, validated_destination: Path, validated_project_name: str
    ) -> Path:
        """Resolve and validate complete project path."""
        try:
            resolver = SafeProjectPathResolver(
                destination_path=str(validated_destination),
                project_dir_name=validated_project_name,
                security_validator=self.security_validator,
            )
            return resolver.resolve()
        except PathSecurityError as exc:
            Messages.error(f"Security error: {exc}")
            raise SystemExit(1) from exc
        except (ValueError, FileExistsError, PermissionError) as exc:
            Messages.error(str(exc))
            raise SystemExit(1) from exc

    def _parse_features(
        self,
        features: str | None,
        no_features: str | None,
    ) -> set[str]:
        """Parse feature flags from command line arguments."""
        all_features = {"postgresql", "rabbitmq", "s3_bucket", "email"}

        if features is not None:
            if features == "":
                return set()
            return {f.strip().lower() for f in features.split(",") if f.strip()}

        if no_features:
            excluded = {f.strip().lower() for f in no_features.split(",") if f.strip()}
            return all_features - excluded

        return all_features

    def _convert_features(self, feature_names: set[str]) -> set[TemplateFeature]:
        """Convert feature name strings to TemplateFeature enums."""
        feature_map = {
            "postgresql": TemplateFeature.POSTGRESQL,
            "rabbitmq": TemplateFeature.RABBITMQ,
            "s3_bucket": TemplateFeature.S3_BUCKET,
            "email": TemplateFeature.EMAIL,
        }

        return {feature_map[name] for name in feature_names if name in feature_map}
