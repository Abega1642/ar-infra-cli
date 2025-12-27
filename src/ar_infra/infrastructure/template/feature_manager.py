"""Feature manager for template customization."""

import shutil
from pathlib import Path

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.feature_config import FEATURE_MAPPINGS


class FeatureManager:
    """Manage template features - remove unwanted features and their files."""

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

    def get_dependencies_for_features(
        self,
        enabled_features: set[TemplateFeature],
    ) -> list[str]:
        """Get all dependencies for enabled features."""
        all_deps: list[str] = []
        for feature in enabled_features:
            all_deps.extend(self.get_feature_dependencies(feature))
        return all_deps
