"""Feature manager for template customization."""

import shutil
from pathlib import Path

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.env_handler import EnvHandler
from src.ar_infra.infrastructure.template.facadeit_handler import FacadeITHandler
from src.ar_infra.infrastructure.template.feature_config import FEATURE_MAPPINGS
from src.ar_infra.infrastructure.template.rest_exception_manager import RestExceptionHandlerManager


class FeatureManager:
    """Manage template features - remove unwanted features and their files."""

    def __init__(
        self,
        env_handler: EnvHandler | None = None,
        facadeit_handler: FacadeITHandler | None = None,
        rest_exception_handler: RestExceptionHandlerManager | None = None,
    ) -> None:
        self._env_handler = env_handler or EnvHandler()
        self._facadeit_handler = facadeit_handler or FacadeITHandler()
        self._rest_exception_handler = rest_exception_handler or RestExceptionHandlerManager()

    def apply_feature_selection(
        self,
        template_dir: Path,
        enabled_features: set[TemplateFeature],
    ) -> None:
        """Remove all features not in enabled_features."""
        all_features = set(TemplateFeature)
        features_to_remove = all_features - enabled_features

        for feature in features_to_remove:
            self.remove_feature(template_dir, feature)

        self._facadeit_handler.apply_feature_selection(
            template_dir,
            enabled_features,
        )

        self._rest_exception_handler.apply_feature_selection(template_dir, enabled_features)

        self._remove_env_variables_for_disabled_features(template_dir, features_to_remove)

    def remove_feature(
        self,
        template_dir: Path,
        feature: TemplateFeature,
    ) -> None:
        """Remove all files and directories associated with a feature."""
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

    def get_feature_dependencies(self, feature: TemplateFeature) -> list[str]:
        """Get list of dependencies for a feature."""
        feature_files = FEATURE_MAPPINGS.get(feature)
        return feature_files.dependencies if feature_files else []

    def get_feature_env_variables(self, feature: TemplateFeature) -> list[str]:
        """Get list of environment variables for a feature."""
        feature_files = FEATURE_MAPPINGS.get(feature)
        return feature_files.env_variables if feature_files else []

    def _remove_env_variables_for_disabled_features(
        self,
        template_dir: Path,
        features_to_remove: set[TemplateFeature],
    ) -> None:
        """Remove environment variables for disabled features."""
        env_file = template_dir / ".env.template"
        if not env_file.exists():
            return

        env_variable_mappings = {
            feature: self.get_feature_env_variables(feature) for feature in TemplateFeature
        }

        self._env_handler.remove_feature_env_variables(
            env_file, features_to_remove, env_variable_mappings
        )
