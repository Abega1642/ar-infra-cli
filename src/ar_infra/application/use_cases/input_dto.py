from dataclasses import dataclass
from pathlib import Path

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.domain.value_objects.artifact_id import ArtifactId
from src.ar_infra.domain.value_objects.group_id import GroupId
from src.ar_infra.domain.value_objects.version import Version


@dataclass(frozen=True)
class GenerateProjectInput:
    group_id: GroupId
    artifact_id: ArtifactId
    version: Version
    destination: Path
    enabled_features: set[TemplateFeature]
    template_url: str
    use_template_cache: bool = False
