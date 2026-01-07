"""Environment file handler for template customization."""

from pathlib import Path

from src.ar_infra.domain.enums.template_feature import TemplateFeature


class EnvHandler:
    """Handle .env.template file modifications based on enabled features."""

    def remove_feature_env_variables(
        self,
        env_file: Path,
        features_to_remove: set[TemplateFeature],
        env_variable_mappings: dict[TemplateFeature, list[str]],
    ) -> None:
        """Remove environment variables for disabled features from .env.template."""
        if not env_file.exists():
            return

        content = env_file.read_text(encoding="utf-8")
        lines = content.split("\n")

        prefixes_to_remove: set[str] = set()
        for feature in features_to_remove:
            env_vars = env_variable_mappings.get(feature, [])
            prefixes_to_remove.update(env_vars)

        filtered_lines = [
            line for line in lines if not self._should_remove_line(line, prefixes_to_remove)
        ]

        updated_content = "\n".join(filtered_lines)
        env_file.write_text(updated_content, encoding="utf-8")

    def _should_remove_line(self, line: str, prefixes_to_remove: set[str]) -> bool:
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            return False

        return any(stripped.startswith(prefix) for prefix in prefixes_to_remove)
