"""FacadeIT handler for feature-based integration test pruning."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from src.ar_infra.domain.enums.template_feature import TemplateFeature


if TYPE_CHECKING:
    from pathlib import Path


class FacadeITHandler:
    """Prune FacadeIT.java based on enabled infrastructure features."""

    _FEATURE_CONF_MAPPING: Final[dict[TemplateFeature, tuple[str, str]]] = {
        TemplateFeature.POSTGRESQL: ("PostgresConf", "POSTGRES_CONF"),
        TemplateFeature.RABBITMQ: ("RabbitMQConf", "RABBITMQ_CONF"),
        TemplateFeature.S3_BUCKET: ("BucketConf", "BUCKET_CONF"),
        TemplateFeature.EMAIL: ("EmailConf", "EMAIL_CONF"),
    }

    def apply_feature_selection(
        self,
        template_dir: Path,
        enabled_features: set[TemplateFeature],
    ) -> None:
        facade_path = self._find_facade_it(template_dir)
        if facade_path is None:
            return

        disabled_features = set(self._FEATURE_CONF_MAPPING) - enabled_features
        disabled_tokens = {
            token for feature in disabled_features for token in self._FEATURE_CONF_MAPPING[feature]
        }

        lines = facade_path.read_text(encoding="utf-8").splitlines()
        filtered = self._remove_disabled_feature_lines(lines, disabled_tokens)

        if not enabled_features:
            filtered = self._remove_empty_before_all(filtered)

        facade_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")

    @staticmethod
    def _find_facade_it(template_dir: Path) -> Path | None:
        matches = list(template_dir.rglob("FacadeIT.java"))
        if not matches:
            return None
        if len(matches) > 1:
            raise RuntimeError("Multiple FacadeIT.java files found")
        return matches[0]

    @staticmethod
    def _remove_disabled_feature_lines(
        lines: list[str],
        disabled_tokens: set[str],
    ) -> list[str]:
        result: list[str] = []

        for line in lines:
            stripped = line.strip()
            if any(token in stripped for token in disabled_tokens):
                continue
            result.append(line)

        return result

    @staticmethod
    def _remove_empty_before_all(lines: list[str]) -> list[str]:
        """Remove @BeforeAll annotated methods from the lines."""
        result: list[str] = []
        i = 0

        while i < len(lines):
            if lines[i].strip() == "@BeforeAll":
                i = FacadeITHandler._skip_before_all_method(lines, i)
                continue

            result.append(lines[i])
            i += 1

        return result

    @staticmethod
    def _skip_before_all_method(lines: list[str], start_index: int) -> int:
        """Skip past a @BeforeAll method and return the next index to process."""
        i = start_index + 1
        brace_depth = 0

        while i < len(lines):
            brace_depth = FacadeITHandler._update_brace_depth(lines[i], brace_depth)
            i += 1

            if brace_depth <= 0:
                break

        return i

    @staticmethod
    def _update_brace_depth(line: str, current_depth: int) -> int:
        depth = current_depth
        depth += line.count("{")
        depth -= line.count("}")
        return depth
