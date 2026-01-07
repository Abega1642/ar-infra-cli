"""Project signature generation for InfraGenerated annotation."""

import hashlib
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from src.ar_infra.domain.value_objects.artifact_id import ArtifactId
from src.ar_infra.domain.value_objects.group_id import GroupId
from src.ar_infra.domain.value_objects.version import Version
from src.ar_infra.properties import CLI_VERSION


@dataclass(frozen=True)
class ProjectSignature:
    signature: str
    version: str
    generated_at: str

    @classmethod
    def generate(
        cls,
        group_id: GroupId,
        artifact_id: ArtifactId,
        version: Version,
        cli_version: str = CLI_VERSION,
    ) -> "ProjectSignature":
        project_hash = cls._compute_project_hash(group_id, artifact_id, version)
        signature = f"ar-infra-cli:{project_hash}"
        generated_at = cls._get_iso_timestamp()

        return cls(
            signature=signature,
            version=cli_version,
            generated_at=generated_at,
        )

    @staticmethod
    def _compute_project_hash(
        group_id: GroupId,
        artifact_id: ArtifactId,
        version: Version,
    ) -> str:
        composite = f"{group_id.value}:{artifact_id.value}:{version.value}"
        digest = hashlib.sha256(composite.encode("utf-8")).hexdigest()
        return digest[:16]

    @staticmethod
    def _get_iso_timestamp() -> str:
        return datetime.now(UTC).isoformat()


class InfraGeneratedAnnotationWriter:
    """Updates InfraGenerated.java annotation with project signature."""

    _SIGNATURE_RE = re.compile(r'(String\s+signature\(\)\s*default\s*)"[^"]*"')
    _VERSION_RE = re.compile(r'(String\s+version\(\)\s*default\s*)"[^"]*"')
    _GENERATED_AT_RE = re.compile(r'(String\s+generatedAt\(\)\s*default\s*)"[^"]*"')

    def update_annotation(
        self,
        annotation_file: Path,
        signature: ProjectSignature,
    ) -> None:
        if not annotation_file.exists():
            raise FileNotFoundError(f"Annotation file not found: {annotation_file}")

        content = annotation_file.read_text(encoding="utf-8")

        updated = self._replace(self._SIGNATURE_RE, content, signature.signature, "signature()")
        updated = self._replace(self._VERSION_RE, updated, signature.version, "version()")
        updated = self._replace(
            self._GENERATED_AT_RE, updated, signature.generated_at, "generatedAt()"
        )

        annotation_file.write_text(updated, encoding="utf-8")

    @staticmethod
    def _replace(
        pattern: re.Pattern[str],
        content: str,
        value: str,
        label: str,
    ) -> str:
        if not pattern.search(content):
            raise ValueError(f"Could not find {label} default value to replace")

        return pattern.sub(rf'\1"{value}"', content)
