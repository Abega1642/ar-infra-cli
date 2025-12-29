"""Output DTO for project generation."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GenerateProjectOutput:
    """Output data transfer object for project generation result."""

    success: bool
    project_path: Path
    message: str
    placeholder_package: str
    signature: str = ""

    @property
    def has_signature(self) -> bool:
        """Check if signature was generated."""
        return bool(self.signature)
