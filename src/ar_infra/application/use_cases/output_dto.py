from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GenerateProjectOutput:
    success: bool
    project_path: Path
    message: str
    placeholder_package: str
    signature: str = ""

    @property
    def has_signature(self) -> bool:
        return bool(self.signature)
