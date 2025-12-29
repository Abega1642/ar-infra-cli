"""Init command implementation."""

import sys
from dataclasses import dataclass
from pathlib import Path

from src.ar_infra.application.use_cases.generate_project_use_case import (
    GenerateProjectUseCase,
)
from src.ar_infra.application.use_cases.input_dto import GenerateProjectInput
from src.ar_infra.cli.prompt.interactive_prompt import InteractivePrompt
from src.ar_infra.cli.ui.banner import Banner
from src.ar_infra.cli.ui.message import Messages
from src.ar_infra.cli.ui.progress import ProgressIndicator
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
    features: str | None
    no_features: str | None
    template_url: str | None
    no_cache: bool


class InitCommand:
    """Handles the init command logic."""

    DEFAULT_TEMPLATE_URL = "https://github.com/Abega1642/ar-infra-template.git"

    def __init__(self) -> None:
        self.use_case = self._create_use_case()
        self.interactive_prompt = InteractivePrompt()

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
        Banner.show()

        is_interactive = all(
            param is None
            for param in (
                args.group,
                args.artifact,
                args.version,
                args.path,
                args.features,
                args.no_features,
            )
        )

        if is_interactive:
            self._execute_interactive()
        else:
            self._execute_cli(args)

    def _execute_interactive(self) -> None:
        Messages.welcome()

        try:
            inputs = self.interactive_prompt.collect_inputs()

            project_input = GenerateProjectInput(
                group_id=GroupId(inputs["group_id"]),
                artifact_id=ArtifactId(inputs["artifact_id"]),
                version=Version(inputs["version"]),
                destination=inputs["destination"],
                enabled_features=self._convert_features(inputs["enabled_features"]),
                template_url=self.DEFAULT_TEMPLATE_URL,
                use_template_cache=inputs["use_template_cache"],
            )

            self._generate_project(project_input)

        except KeyboardInterrupt:
            Messages.warning("\n\nOperation cancelled by user.")
            sys.exit(0)
        except (InvalidGroupIdError, InvalidArtifactIdError, InvalidVersionError) as exc:
            Messages.error(f"Validation error: {exc}")
            sys.exit(1)
        except OSError as exc:
            Messages.error(f"I/O error: {exc}")
            sys.exit(1)

    def _execute_cli(self, args: InitCommandArgs) -> None:
        if not args.group:
            Messages.error("--group is required when not using interactive mode")
            sys.exit(1)

        if not args.artifact:
            Messages.error("--artifact is required when not using interactive mode")
            sys.exit(1)

        try:
            enabled_features = self._parse_features(args.features, args.no_features)

            project_input = GenerateProjectInput(
                group_id=GroupId(args.group),
                artifact_id=ArtifactId(args.artifact),
                version=Version(args.version or "1.0.0"),
                destination=Path(args.path or ".").expanduser().resolve(),
                enabled_features=self._convert_features(enabled_features),
                template_url=args.template_url or self.DEFAULT_TEMPLATE_URL,
                use_template_cache=not args.no_cache,
            )

            self._generate_project(project_input)

        except (InvalidGroupIdError, InvalidArtifactIdError, InvalidVersionError) as exc:
            Messages.error(f"Validation error: {exc}")
            sys.exit(1)
        except OSError as exc:
            Messages.error(f"I/O error: {exc}")
            sys.exit(1)

    def _generate_project(self, project_input: GenerateProjectInput) -> None:
        Messages.project_summary(
            group=project_input.group_id.value,
            artifact=project_input.artifact_id.value,
            version=project_input.version.value,
            path=project_input.destination,
            features=[f.value for f in project_input.enabled_features],
        )

        with ProgressIndicator.steps(7) as (progress, task):
            progress.update(task, description="Fetching template...")
            progress.advance(task)

            result = self.use_case.execute(project_input)

            if result.success:
                progress.update(task, completed=7, description="✓ Complete!")
                Messages.success(f"\n{result.message}")
                Messages.info(f"Project created at: {result.project_path}")
                if result.has_signature:
                    Messages.info(f"Project signature: {result.signature}")
            else:
                Messages.error(f"\n{result.message}")
                sys.exit(1)

    def _parse_features(
        self,
        features: str | None,
        no_features: str | None,
    ) -> set[str]:
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
        feature_map = {
            "postgresql": TemplateFeature.POSTGRESQL,
            "rabbitmq": TemplateFeature.RABBITMQ,
            "s3_bucket": TemplateFeature.S3_BUCKET,
            "email": TemplateFeature.EMAIL,
        }

        return {feature_map[name] for name in feature_names if name in feature_map}
