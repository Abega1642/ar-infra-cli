import importlib.resources
from dataclasses import dataclass
from functools import cache
from typing import Final

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.processor.yaml_processor import YamlFileProcessor
from src.ar_infra.infrastructure.template.feature_config_schema import (
    FeatureConfigSchema,
    FeatureSchema,
)


@dataclass(frozen=True)
class FeatureFiles:
    shared_directories: list[str]
    specific_directories: list[str]
    shared_files: list[str]
    specific_files: list[str]
    shared_env_variables: list[str]
    specific_env_variables: list[str]


@dataclass(frozen=True)
class FeatureDependencies:
    shared: list[str]
    specific: list[str]


@cache
def _load_config() -> FeatureConfigSchema:
    path = importlib.resources.files("src.ar_infra.cli.resources") / "feature-conf.yml"
    return YamlFileProcessor().load(path, FeatureConfigSchema)


def _resolve(template: str, src: str, test: str) -> str:
    return template.format(src_package=src, test_package=test)


def _resolve_list(items: list[str], src: str, test: str) -> list[str]:
    return [_resolve(item, src, test) for item in items]


def _to_feature_files(schema: FeatureSchema, src: str, test: str) -> FeatureFiles:
    f = schema.files

    def r(items: list[str]) -> list[str]:
        return _resolve_list(items, src, test)

    return FeatureFiles(
        shared_directories=r(f.shared_directories),
        specific_directories=r(f.specific_directories),
        shared_files=r(f.shared_files),
        specific_files=r(f.specific_files),
        shared_env_variables=f.shared_env_variables,
        specific_env_variables=f.specific_env_variables,
    )


def _to_feature_dependencies(schema: FeatureSchema) -> FeatureDependencies:
    return FeatureDependencies(
        shared=schema.dependencies.shared,
        specific=schema.dependencies.specific,
    )


def _to_enum(key: str) -> TemplateFeature:
    return TemplateFeature[key]


def _build_feature_files() -> dict[TemplateFeature, FeatureFiles]:
    cfg = _load_config()
    return {
        _to_enum(key): _to_feature_files(schema, cfg.src_package, cfg.test_package)
        for key, schema in cfg.features.items()
    }


def _build_feature_dependencies() -> dict[TemplateFeature, FeatureDependencies]:
    cfg = _load_config()
    return {_to_enum(key): _to_feature_dependencies(schema) for key, schema in cfg.features.items()}


FEATURE_FILES: Final[dict[TemplateFeature, FeatureFiles]] = _build_feature_files()
FEATURE_DEPENDENCIES: Final[dict[TemplateFeature, FeatureDependencies]] = (
    _build_feature_dependencies()
)


def get_all_dependencies_for_features(enabled_features: set[TemplateFeature]) -> list[str]:
    all_deps = set()

    for feature in enabled_features:
        feature_deps = FEATURE_DEPENDENCIES.get(feature)
        if feature_deps:
            all_deps.update(feature_deps.shared)
            all_deps.update(feature_deps.specific)

    return sorted(all_deps)
