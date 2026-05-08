import shutil
from pathlib import Path

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.env_handler import EnvHandler
from src.ar_infra.infrastructure.template.facadeit_handler import FacadeITHandler
from src.ar_infra.infrastructure.template.feature_config import (
    FEATURE_DEPENDENCIES,
    FEATURE_FILES,
    get_all_dependencies_for_features,
)
from src.ar_infra.infrastructure.template.rest_exception_manager import (
    RestExceptionHandlerManager,
)
from src.ar_infra.infrastructure.template.swagger_handler import SwaggerHandler
from src.ar_infra.logger import get_logger


log = get_logger(use_rich=True)


class FeatureManager:
    DATABASE_FEATURES = TemplateFeature.database_features()

    def __init__(
        self,
        env_handler: EnvHandler | None = None,
        facadeit_handler: FacadeITHandler | None = None,
        rest_exception_handler: RestExceptionHandlerManager | None = None,
        swagger_handler: SwaggerHandler | None = None,
    ) -> None:
        self._env_handler = env_handler or EnvHandler()
        self._facadeit_handler = facadeit_handler or FacadeITHandler()
        self._rest_exception_handler = rest_exception_handler or RestExceptionHandlerManager()
        self._swagger_handler = swagger_handler

    def apply_feature_selection(
        self,
        template_dir: Path,
        enabled_features: set[TemplateFeature],
    ) -> None:
        all_features: set[TemplateFeature] = set(TemplateFeature)
        features_to_remove: set[TemplateFeature] = all_features - enabled_features

        # Remove specific files/directories for disabled features
        for feature in features_to_remove:
            self._remove_specific_feature_resources(template_dir, feature)

        # Remove shared resources only if no related features are enabled
        self._remove_shared_resources(template_dir, enabled_features, features_to_remove)

        self._facadeit_handler.apply_feature_selection(
            template_dir,
            enabled_features,
        )
        self._rest_exception_handler.apply_feature_selection(template_dir, enabled_features)
        self._remove_env_variables_for_disabled_features(template_dir, features_to_remove)
        self._update_swagger_documentation(template_dir, enabled_features)

    def _remove_specific_feature_resources(
        self,
        template_dir: Path,
        feature: TemplateFeature,
    ) -> None:
        feature_files = FEATURE_FILES.get(feature)
        if not feature_files:
            return

        self._remove_directories(template_dir, feature_files.specific_directories)
        self._remove_files(template_dir, feature_files.specific_files)

    def _remove_shared_resources(
        self,
        template_dir: Path,
        enabled_features: set[TemplateFeature],
        features_to_remove: set[TemplateFeature],
    ) -> None:
        shared_dirs_to_check: dict[str, set[TemplateFeature]] = {}
        shared_files_to_check: dict[str, set[TemplateFeature]] = {}

        self._collect_shared_resources(
            features_to_remove, shared_dirs_to_check, shared_files_to_check
        )
        self._remove_unused_shared_directories(template_dir, enabled_features, shared_dirs_to_check)
        self._remove_unused_shared_files(template_dir, enabled_features, shared_files_to_check)

    @staticmethod
    def _collect_shared_resources(
        features_to_remove: set[TemplateFeature],
        shared_dirs_to_check: dict[str, set[TemplateFeature]],
        shared_files_to_check: dict[str, set[TemplateFeature]],
    ) -> None:
        for feature in features_to_remove:
            feature_files = FEATURE_FILES.get(feature)
            if not feature_files:
                continue

            for directory in feature_files.shared_directories:
                if directory not in shared_dirs_to_check:
                    shared_dirs_to_check[directory] = set()
                shared_dirs_to_check[directory].add(feature)

            for file in feature_files.shared_files:
                if file not in shared_files_to_check:
                    shared_files_to_check[file] = set()
                shared_files_to_check[file].add(feature)

    def _remove_unused_shared_directories(
        self,
        template_dir: Path,
        enabled_features: set[TemplateFeature],
        shared_dirs_to_check: dict[str, set[TemplateFeature]],
    ) -> None:
        dirs_to_remove = [
            directory
            for directory, sharing_features in shared_dirs_to_check.items()
            if self._should_remove_shared_resource(sharing_features, enabled_features)
        ]
        self._remove_directories(template_dir, dirs_to_remove)

    def _remove_unused_shared_files(
        self,
        template_dir: Path,
        enabled_features: set[TemplateFeature],
        shared_files_to_check: dict[str, set[TemplateFeature]],
    ) -> None:
        files_to_remove = [
            file
            for file, sharing_features in shared_files_to_check.items()
            if self._should_remove_shared_resource(sharing_features, enabled_features)
        ]
        self._remove_files(template_dir, files_to_remove)

    def _should_remove_shared_resource(
        self,
        sharing_features: set[TemplateFeature],
        enabled_features: set[TemplateFeature],
    ) -> bool:
        if sharing_features.issubset(self.DATABASE_FEATURES):
            return not any(db_feature in enabled_features for db_feature in self.DATABASE_FEATURES)

        return not any(feature in enabled_features for feature in sharing_features)

    @staticmethod
    def _remove_directories(template_dir: Path, directories: list[str]) -> None:
        for directory in directories:
            dir_path = template_dir / directory
            if dir_path.exists():
                shutil.rmtree(dir_path)

    @staticmethod
    def _remove_files(template_dir: Path, files: list[str]) -> None:
        for file in files:
            file_path = template_dir / file
            if file_path.exists():
                file_path.unlink()

    @staticmethod
    def get_all_feature_dependencies(enabled_features: set[TemplateFeature]) -> list[str]:
        return get_all_dependencies_for_features(enabled_features)

    @staticmethod
    def get_feature_dependencies(feature: TemplateFeature) -> list[str]:
        feature_deps = FEATURE_DEPENDENCIES.get(feature)
        if not feature_deps:
            return []
        return [*feature_deps.shared, *feature_deps.specific]

    @staticmethod
    def get_feature_env_variables(feature: TemplateFeature) -> list[str]:
        feature_files = FEATURE_FILES.get(feature)
        if not feature_files:
            return []
        return [*feature_files.shared_env_variables, *feature_files.specific_env_variables]

    def _remove_env_variables_for_disabled_features(
        self,
        template_dir: Path,
        features_to_remove: set[TemplateFeature],
    ) -> None:
        env_file = template_dir / ".env.template"
        if not env_file.exists():
            return

        env_variable_mappings = {
            feature: self.get_feature_env_variables(feature) for feature in TemplateFeature
        }

        self._env_handler.remove_feature_env_variables(
            env_file, features_to_remove, env_variable_mappings
        )

    def _update_swagger_documentation(
        self,
        template_dir: Path,
        enabled_features: set[TemplateFeature],
    ) -> None:
        api_file = template_dir / "doc" / "api.yaml"

        swagger_handler = self._swagger_handler or SwaggerHandler(api_file)
        swagger_handler.update_swagger(enabled_features)
