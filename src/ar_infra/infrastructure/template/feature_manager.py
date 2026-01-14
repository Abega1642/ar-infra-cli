import shutil
from pathlib import Path

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.env_handler import EnvHandler
from src.ar_infra.infrastructure.template.facadeit_handler import FacadeITHandler
from src.ar_infra.infrastructure.template.feature_config import FEATURE_MAPPINGS
from src.ar_infra.infrastructure.template.rest_exception_manager import RestExceptionHandlerManager
from src.ar_infra.infrastructure.template.swagger_handler import SwaggerHandler


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
        all_features = set(TemplateFeature)
        features_to_remove = all_features - enabled_features

        safe_features_to_remove = self._get_safe_features_to_remove(
            enabled_features, features_to_remove
        )

        for feature in safe_features_to_remove:
            self.remove_feature(template_dir, feature)

        self._facadeit_handler.apply_feature_selection(
            template_dir,
            enabled_features,
        )
        self._rest_exception_handler.apply_feature_selection(template_dir, enabled_features)
        self._remove_env_variables_for_disabled_features(template_dir, features_to_remove)
        self._update_swagger_documentation(template_dir, enabled_features)

    def _get_safe_features_to_remove(
        self,
        enabled_features: set[TemplateFeature],
        features_to_remove: set[TemplateFeature],
    ) -> set[TemplateFeature]:
        """
        Determine which features can safely be removed without affecting enabled features.

        For features that share resources (e.g., PostgreSQL and MySQL share database files),
        we should only remove the shared resources if NONE of the sharing features are enabled.
        """
        safe_to_remove = set()

        for feature in features_to_remove:
            if feature in self.DATABASE_FEATURES:
                if not any(db_feature in enabled_features for db_feature in self.DATABASE_FEATURES):
                    safe_to_remove.add(feature)
            else:
                safe_to_remove.add(feature)

        return safe_to_remove

    @staticmethod
    def remove_feature(
        template_dir: Path,
        feature: TemplateFeature,
    ) -> None:
        feature_files = FEATURE_MAPPINGS.get(feature)
        if not feature_files:
            return

        for directory in feature_files.directories:
            dir_path = template_dir / directory
            if dir_path.exists():
                shutil.rmtree(dir_path)

        for file in feature_files.files:
            file_path = template_dir / file
            if file_path.exists():
                file_path.unlink()

    @staticmethod
    def get_feature_dependencies(feature: TemplateFeature) -> list[str]:
        feature_files = FEATURE_MAPPINGS.get(feature)
        return feature_files.dependencies if feature_files else []

    @staticmethod
    def get_feature_env_variables(feature: TemplateFeature) -> list[str]:
        feature_files = FEATURE_MAPPINGS.get(feature)
        return feature_files.env_variables if feature_files else []

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
