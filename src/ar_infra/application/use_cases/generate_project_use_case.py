from pathlib import Path
from typing import Protocol

from src.ar_infra.application.use_cases.exception import GenerateProjectError
from src.ar_infra.application.use_cases.input_dto import GenerateProjectInput
from src.ar_infra.application.use_cases.output_dto import GenerateProjectOutput
from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.domain.value_objects.package_name import PackageName
from src.ar_infra.infrastructure.gradle import GradleWriter
from src.ar_infra.infrastructure.processor import GitRepositoryInitializer, PackageRenamer
from src.ar_infra.infrastructure.processor.format_script_runner import FormatScriptRunner
from src.ar_infra.infrastructure.template import FeatureManager, GitHubTemplateFetcher
from src.ar_infra.infrastructure.template.development_artifact_remover import (
    DevelopmentArtifactCleaner,
)
from src.ar_infra.infrastructure.template.project_signature import (
    InfraGeneratedAnnotationWriter,
    ProjectSignature,
)
from src.ar_infra.logger import get_logger
from src.ar_infra.properties import CLI_VERSION


log = get_logger(use_rich=True)


class ProgressReporter(Protocol):
    def update_step(self, step_name: str, *, completed: bool = False) -> None: ...


class GenerateProjectUseCase:
    """Orchestrates the entire project generation workflow."""

    def __init__(
        self,
        template_fetcher: GitHubTemplateFetcher,
        feature_manager: FeatureManager,
        gradle_writer: GradleWriter,
        package_renamer: PackageRenamer,
        git_initializer: GitRepositoryInitializer | None = None,
        annotation_writer: InfraGeneratedAnnotationWriter | None = None,
        artifact_cleaner: DevelopmentArtifactCleaner | None = None,
        format_script_runner: FormatScriptRunner | None = None,
    ) -> None:
        self._template_fetcher = template_fetcher
        self._feature_manager = feature_manager
        self._gradle_writer = gradle_writer
        self._package_renamer = package_renamer
        self._git_initializer = git_initializer or GitRepositoryInitializer()
        self._annotation_writer = annotation_writer or InfraGeneratedAnnotationWriter()
        self._artifact_cleaner = artifact_cleaner
        self._format_script_runner = format_script_runner or FormatScriptRunner()

    def execute(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None = None
    ) -> GenerateProjectOutput:
        try:
            placeholder_package = self._fetch_template(input_dto, progress)
            self._apply_features(input_dto, progress)
            self._remove_unwanted_dependencies(input_dto, progress)

            # We need to format immediately after feature removal if no features selected
            # This handles the case where Google Java Format needs two passes
            # to fully clean up unused imports (e.g., static imports from removed @BeforeAll)
            if not input_dto.enabled_features:
                log.info("SCRIPT FORMATTING ACTIVATED. First run of the Format Script ...")
                self._run_formatter(input_dto, progress)

            self._update_build_gradle(input_dto, progress)
            self._rename_packages(input_dto, placeholder_package, progress)
            self._update_settings_gradle(input_dto, progress)
            signature = self._update_infra_generated_annotation(input_dto, progress)
            self._clean_development_artifacts(input_dto, progress)
            self._run_formatter(input_dto, progress)
            self._initialize_git_repository(input_dto, progress)

            if progress:
                progress.update_step("Complete!", completed=True)

            return GenerateProjectOutput(
                success=True,
                project_path=input_dto.destination,
                message="Project generated successfully",
                placeholder_package=placeholder_package,
                signature=signature.signature,
            )

        except GenerateProjectError as exc:
            return GenerateProjectOutput(
                success=False,
                project_path=input_dto.destination,
                message=f"Project generation failed: {exc}",
                placeholder_package="",
            )

    def _fetch_template(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None
    ) -> str:
        if progress:
            progress.update_step("Fetching template...")

        try:
            result = self._template_fetcher.fetch(
                input_dto.template_url,
                input_dto.destination,
                use_cache=input_dto.use_template_cache,
            )
        except Exception as exc:
            raise GenerateProjectError("Failed to fetch template") from exc

        if progress:
            progress.update_step("Fetching template...", completed=True)
        return result

    def _apply_features(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None
    ) -> None:
        if progress:
            progress.update_step("Applying features...")

        try:
            self._feature_manager.apply_feature_selection(
                input_dto.destination,
                input_dto.enabled_features,
            )

            if progress:
                progress.update_step("Applying features...", completed=True)
        except Exception as exc:
            raise GenerateProjectError("Failed to apply features") from exc

    def _remove_unwanted_dependencies(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None
    ) -> None:
        if progress:
            progress.update_step("Removing dependencies...")

        all_features = set(TemplateFeature)
        features_to_remove = all_features - input_dto.enabled_features

        dependencies_to_remove = []
        for feature in features_to_remove:
            dependencies_to_remove.extend(self._feature_manager.get_feature_dependencies(feature))

        if dependencies_to_remove:
            build_gradle = input_dto.destination / "build.gradle"
            self._gradle_writer.remove_dependencies(build_gradle, dependencies_to_remove)

        if progress:
            progress.update_step("Removing dependencies...", completed=True)

    def _update_build_gradle(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None
    ) -> None:
        if progress:
            progress.update_step("Configuring build...")

        build_gradle = input_dto.destination / "build.gradle"
        self._gradle_writer.update_group_and_version(
            build_gradle,
            input_dto.group_id,
            input_dto.version,
        )

        if progress:
            progress.update_step("Configuring build...", completed=True)

    def _rename_packages(
        self,
        input_dto: GenerateProjectInput,
        placeholder_package: str,
        progress: ProgressReporter | None,
    ) -> None:
        if progress:
            progress.update_step("Renaming packages...")

        old_package = PackageName(placeholder_package)
        new_package = PackageName.from_parts(input_dto.group_id, input_dto.artifact_id)

        try:
            self._package_renamer.rename_package(
                input_dto.destination,
                old_package,
                new_package,
            )

            if progress:
                progress.update_step("Renaming packages...", completed=True)
        except Exception as exc:
            raise GenerateProjectError("Failed to rename packages") from exc

    def _update_settings_gradle(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None
    ) -> None:
        if progress:
            progress.update_step("Updating settings...")

        settings_file = input_dto.destination / "settings.gradle"
        if settings_file.exists():
            self._gradle_writer.update_settings_gradle(settings_file, input_dto.artifact_id)
        else:
            settings_file.write_text(
                f"rootProject.name = '{input_dto.artifact_id.value}'\n",
                encoding="utf-8",
            )

        if progress:
            progress.update_step("Updating settings...", completed=True)

    def _update_infra_generated_annotation(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None = None
    ) -> ProjectSignature:
        if progress:
            progress.update_step("Updating annotations...")

        signature = ProjectSignature.generate(
            group_id=input_dto.group_id,
            artifact_id=input_dto.artifact_id,
            version=input_dto.version,
            cli_version=CLI_VERSION,
        )
        annotation_file = self._find_infra_generated_annotation(input_dto.destination)
        if annotation_file:
            self._annotation_writer.update_annotation(annotation_file, signature)

        if progress:
            progress.update_step("Updating annotations...", completed=True)

        return signature

    def _find_infra_generated_annotation(self, project_path: Path) -> Path | None:
        java_dir = project_path / "src" / "main" / "java"
        if not java_dir.exists():
            return None
        for annotation_file in java_dir.rglob("InfraGenerated.java"):
            return annotation_file
        return None

    def _clean_development_artifacts(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None
    ) -> None:
        if progress:
            progress.update_step("Cleaning artifacts...")

        try:
            cleaner = self._artifact_cleaner or DevelopmentArtifactCleaner(input_dto.destination)
            cleaner.clean()
            cleaner.clean_empty_parent_directories(".github/dependabot.yml")
            cleaner.clean_empty_parent_directories(".github/CODEOWNERS")

            if progress:
                progress.update_step("Cleaning artifacts...", completed=True)
        except Exception as exc:
            raise GenerateProjectError("Failed to clean development artifacts") from exc

    def _run_formatter(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None
    ) -> None:
        if progress:
            progress.update_step("Formatting code...")

        try:
            if progress and hasattr(progress, "pause"):
                progress.pause()

            self._format_script_runner.run(input_dto.destination)

            if progress and hasattr(progress, "resume"):
                progress.resume()

            if progress:
                progress.update_step("Formatting code...", completed=True)
        except Exception as exc:
            if progress and hasattr(progress, "resume"):
                progress.resume()
            raise GenerateProjectError("Failed to format generated project") from exc

    def _initialize_git_repository(
        self, input_dto: GenerateProjectInput, progress: ProgressReporter | None
    ) -> None:
        if progress:
            progress.update_step("Initializing git...")

        self._git_initializer.initialize_repository(
            project_path=input_dto.destination,
            initial_branch="preprod",
            commit_message=f"infra: ar-infra[v{CLI_VERSION}]: generate ar-infra project",
        )

        if progress:
            progress.update_step("Initializing git...", completed=True)
