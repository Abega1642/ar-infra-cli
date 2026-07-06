import re
from importlib.resources.abc import Traversable
from io import StringIO
from unittest.mock import MagicMock

import pytest
import yaml
from pydantic import BaseModel, ValidationError

from src.ar_infra.domain.entities.path_resolver import (
    DangerousPathError,
    PathSecurityError,
    PathSecurityValidator,
)
from src.ar_infra.infrastructure.processor.yaml_processor import (
    _MAX_FILE_SIZE_BYTES,
    YamlFileProcessor,
)


_VALID_YAML = """
name: test
value: 42
"""

_MALFORMED_YAML = """
name: [unclosed
"""

_LIST_ROOT_YAML = """
- item1
- item2
"""

_NESTED_YAML = """
label: top
inner:
  count: 7
"""

_SCALAR_YAML = """
just a string
"""

_EXTRA_FIELDS_YAML = """
name: test
value: 1
extra_field: ignored
"""


class SimpleModel(BaseModel):
    name: str
    value: int


class NestedModel(BaseModel):
    class Inner(BaseModel):
        count: int

    label: str
    inner: Inner


def _make_traversable(content: str, name: str = "config.yml") -> MagicMock:
    mock = MagicMock(spec=Traversable)
    mock.name = name
    mock.open.return_value.__enter__ = lambda s: StringIO(content)
    mock.open.return_value.__exit__ = MagicMock(return_value=False)
    return mock


def _make_processor(validator: PathSecurityValidator | None = None) -> YamlFileProcessor:
    return YamlFileProcessor(security_validator=validator)


class TestLoad:
    def test__given_valid_yml_file_when_load_then_returns_model_instance(self, tmp_path):
        f = tmp_path / "config.yml"
        f.write_text(_VALID_YAML, encoding="utf-8")
        result = _make_processor().load(f, SimpleModel)
        assert result == SimpleModel(name="test", value=42)

    def test__given_valid_yaml_extension_when_load_then_returns_model_instance(self, tmp_path):
        f = tmp_path / "config.yaml"
        f.write_text(_VALID_YAML, encoding="utf-8")
        result = _make_processor().load(f, SimpleModel)
        assert result == SimpleModel(name="test", value=42)

    def test__given_valid_traversable_when_load_then_returns_model_instance(self):
        result = _make_processor().load(_make_traversable(_VALID_YAML), SimpleModel)
        assert result == SimpleModel(name="test", value=42)

    def test__given_nested_model_when_load_then_maps_correctly(self, tmp_path):
        f = tmp_path / "nested.yml"
        f.write_text(_NESTED_YAML, encoding="utf-8")
        result = _make_processor().load(f, NestedModel)
        assert result.label == "top"
        assert result.inner.count == 7

    def test__given_injected_validator_when_load_then_uses_it(self, tmp_path):
        f = tmp_path / "config.yml"
        f.write_text(_VALID_YAML, encoding="utf-8")
        mock_validator = MagicMock(spec=PathSecurityValidator)
        mock_validator.validate_destination_path.return_value = f.resolve()
        result = _make_processor(mock_validator).load(f, SimpleModel)
        mock_validator.validate_destination_path.assert_called_once_with(str(f))
        assert result.name == "test"


class TestExtensionValidation:
    def test__given_toml_extension_when_load_then_raises_value_error(self, tmp_path):
        f = tmp_path / "config.toml"
        f.write_text("[section]\nkey = 'value'\n", encoding="utf-8")
        with pytest.raises(ValueError, match=re.escape("extension '.toml' is not allowed")):
            _make_processor().load(f, SimpleModel)

    def test__given_json_extension_when_load_then_raises_value_error(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text("{}", encoding="utf-8")
        with pytest.raises(ValueError, match=re.escape("extension '.json' is not allowed")):
            _make_processor().load(f, SimpleModel)

    def test__given_no_extension_when_load_then_raises_value_error(self, tmp_path):
        f = tmp_path / "noext"
        f.write_text(_VALID_YAML, encoding="utf-8")
        with pytest.raises(ValueError, match=re.escape("extension '' is not allowed")):
            _make_processor().load(f, SimpleModel)

    def test__given_uppercase_yml_extension_when_load_then_accepts_it(self, tmp_path):
        f = tmp_path / "config.YML"
        f.write_text(_VALID_YAML, encoding="utf-8")
        result = _make_processor().load(f, SimpleModel)
        assert result.name == "test"

    def test__given_traversable_with_wrong_extension_when_load_then_raises_value_error(self):
        with pytest.raises(ValueError, match=re.escape("extension '.json' is not allowed")):
            _make_processor().load(_make_traversable(_VALID_YAML, name="config.json"), SimpleModel)


class TestPathSecurity:
    def test__given_path_traversal_when_load_then_raises_from_validator(self, tmp_path):
        mock_validator = MagicMock(spec=PathSecurityValidator)
        mock_validator.validate_destination_path.side_effect = ValueError(
            "path traversal sequence '..' detected"
        )
        with pytest.raises(ValueError, match="path traversal"):
            _make_processor(mock_validator).load(tmp_path / ".." / "config.yml", SimpleModel)

    def test__given_dangerous_system_path_when_load_then_raises_from_validator(self, tmp_path):
        mock_validator = MagicMock(spec=PathSecurityValidator)
        mock_validator.validate_destination_path.side_effect = DangerousPathError(
            "Cannot use system directory"
        )
        with pytest.raises(DangerousPathError):
            _make_processor(mock_validator).load(tmp_path / "config.yml", SimpleModel)

    def test__given_symlink_when_load_then_raises_from_validator(self, tmp_path):
        mock_validator = MagicMock(spec=PathSecurityValidator)
        mock_validator.validate_destination_path.side_effect = PathSecurityError("symbolic link")
        with pytest.raises(PathSecurityError, match="symbolic link"):
            _make_processor(mock_validator).load(tmp_path / "link.yml", SimpleModel)

    def test__given_valid_path_when_load_then_validator_called_with_string(self, tmp_path):
        f = tmp_path / "config.yml"
        f.write_text(_VALID_YAML, encoding="utf-8")
        mock_validator = MagicMock(spec=PathSecurityValidator)
        mock_validator.validate_destination_path.return_value = f.resolve()
        _make_processor(mock_validator).load(f, SimpleModel)
        mock_validator.validate_destination_path.assert_called_once_with(str(f))

    def test__given_traversable_when_load_then_validator_is_not_called(self):
        mock_validator = MagicMock(spec=PathSecurityValidator)
        _make_processor(mock_validator).load(_make_traversable(_VALID_YAML), SimpleModel)
        mock_validator.validate_destination_path.assert_not_called()


class TestFileSizeGuard:
    def test__given_oversized_path_file_when_load_then_raises_value_error(self, tmp_path):
        f = tmp_path / "large.yml"
        f.write_bytes(b"x" * (_MAX_FILE_SIZE_BYTES + 1))
        with pytest.raises(ValueError, match="exceeds the limit"):
            _make_processor().load(f, SimpleModel)

    def test__given_file_at_exact_limit_when_load_then_does_not_raise_size_error(self, tmp_path):
        f = tmp_path / "atlimit.yml"
        f.write_bytes(b"x" * _MAX_FILE_SIZE_BYTES)
        with pytest.raises(TypeError):
            _make_processor().load(f, SimpleModel)

    def test__given_oversized_traversable_when_load_then_raises_value_error(self):
        oversized_content = "x" * (_MAX_FILE_SIZE_BYTES + 1)
        with pytest.raises(ValueError, match=re.escape("exceeds the limit")):
            _make_processor().load(_make_traversable(oversized_content), SimpleModel)


class TestYamlContentValidation:
    def test__given_malformed_yaml_when_load_then_raises_yaml_error(self, tmp_path):
        f = tmp_path / "malformed.yml"
        f.write_text(_MALFORMED_YAML, encoding="utf-8")
        with pytest.raises(yaml.YAMLError):
            _make_processor().load(f, SimpleModel)

    def test__given_yaml_root_is_list_when_load_then_raises_value_error(self, tmp_path):
        f = tmp_path / "list_root.yml"
        f.write_text(_LIST_ROOT_YAML, encoding="utf-8")
        with pytest.raises(TypeError, match=re.escape("Expected a YAML mapping")):
            _make_processor().load(f, SimpleModel)

    def test__given_yaml_root_is_scalar_when_load_then_raises_value_error(self, tmp_path):
        f = tmp_path / "scalar.yml"
        f.write_text(_SCALAR_YAML, encoding="utf-8")
        with pytest.raises(TypeError, match=re.escape("Expected a YAML mapping")):
            _make_processor().load(f, SimpleModel)

    def test__given_empty_yaml_file_when_load_then_raises_value_error(self, tmp_path):
        f = tmp_path / "empty.yml"
        f.write_text("", encoding="utf-8")
        with pytest.raises(TypeError, match=re.escape("Expected a YAML mapping")):
            _make_processor().load(f, SimpleModel)


class TestSchemaValidation:
    def test__given_missing_required_field_when_load_then_raises_validation_error(self, tmp_path):
        f = tmp_path / "missing_field.yml"
        f.write_text("name: only_name\n", encoding="utf-8")
        with pytest.raises(ValidationError) as exc_info:
            _make_processor().load(f, SimpleModel)
        assert any(e["loc"] == ("value",) for e in exc_info.value.errors())

    def test__given_wrong_field_type_when_load_then_raises_validation_error(self, tmp_path):
        f = tmp_path / "wrong_type.yml"
        f.write_text("name: test\nvalue: not_an_int\n", encoding="utf-8")
        with pytest.raises(ValidationError) as exc_info:
            _make_processor().load(f, SimpleModel)
        assert any(e["loc"] == ("value",) for e in exc_info.value.errors())

    def test__given_extra_fields_in_yaml_when_load_then_ignores_them_by_default(self, tmp_path):
        f = tmp_path / "extra.yml"
        f.write_text(_EXTRA_FIELDS_YAML, encoding="utf-8")
        result = _make_processor().load(f, SimpleModel)
        assert result == SimpleModel(name="test", value=1)
