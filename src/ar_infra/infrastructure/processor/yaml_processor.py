from importlib.resources.abc import (
    Traversable,  # nosemgrep: python.lang.compatibility.python37.python37-compatibility-importlib2
)
from pathlib import Path
from typing import Any, TypeVar

import yaml
from pydantic import BaseModel

from src.ar_infra.domain.entities.path_resolver import PathSecurityValidator


T = TypeVar("T", bound=BaseModel)

_ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".yml", ".yaml"})
_MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB


class YamlFileProcessor:
    def __init__(self, security_validator: PathSecurityValidator | None = None) -> None:
        self._security_validator = security_validator or PathSecurityValidator()

    def load(self, path: Traversable | Path, model: type[T]) -> T:
        """
        Load a YAML file and validate its content against a Pydantic model.

        :param path: Traversable (package resource) or Path (filesystem).
        :param model: Pydantic BaseModel subclass to validate against.
        :return: Validated instance of model.
        :raises ValueError: On security constraint violations.
        :raises yaml.YAMLError: On malformed YAML.
        :raises pydantic.ValidationError: On schema mismatch.
        """
        safe_path = self._validate_path(path)
        raw: dict[str, Any] = self._read(safe_path)
        return self._parse(raw, model)

    def _validate_path(self, path: Traversable | Path) -> Traversable | Path:
        self._check_extension(path.name)
        if isinstance(path, Path):
            return self._validate_filesystem_path(path)
        return path

    def _check_extension(self, name: str) -> None:
        suffix = Path(name).suffix.lower()
        if suffix not in _ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Rejected file '{name}': extension '{suffix}' is not allowed. "
                f"Accepted: {_ALLOWED_EXTENSIONS}"
            )

    def _validate_filesystem_path(self, path: Path) -> Path:
        resolved = self._security_validator.validate_destination_path(str(path))

        size = resolved.stat().st_size
        if size > _MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"Rejected file '{path.name}': size {size} bytes exceeds "
                f"the limit of {_MAX_FILE_SIZE_BYTES} bytes."
            )

        return resolved

    def _read(self, path: Traversable | Path) -> dict[str, Any]:
        # Python objects, enabling RCE.
        # Reference: https://pyyaml.org/wiki/PyYAMLDocumentation#loading-yaml
        with path.open("r", encoding="utf-8") as f:
            # Secondary size guard for Traversable (no stat() available).
            content = f.read(_MAX_FILE_SIZE_BYTES + 1)
            if len(content) > _MAX_FILE_SIZE_BYTES:
                raise ValueError(
                    f"Rejected file '{path.name}': content exceeds "
                    f"the limit of {_MAX_FILE_SIZE_BYTES} bytes."
                )
            data = yaml.safe_load(content)

        if not isinstance(data, dict):
            raise TypeError(
                f"Expected a YAML mapping at the root of '{path.name}', got {type(data).__name__}."
            )

        return data

    def _parse(self, raw: dict[str, Any], model: type[T]) -> T:
        result = model.model_validate(raw)
        assert isinstance(result, model)
        return result
