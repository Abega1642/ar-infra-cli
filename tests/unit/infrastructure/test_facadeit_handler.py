"""Tests for FacadeITHandler."""

from pathlib import Path

import pytest
from tests.fixtures.sample_FacadeIT import FACADE_CONTENT

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.facadeit_handler import FacadeITHandler


class TestFacadeITHandler:
    @pytest.fixture
    def facade_path(self, tmp_path: Path) -> Path:
        path = tmp_path / "src/test/java/com/example/arinfra/conf"
        path.mkdir(parents=True)
        facade = path / "FacadeIT.java"
        facade.write_text(FACADE_CONTENT, encoding="utf-8")
        return facade

    def _read(self, facade_path: Path) -> str:
        return facade_path.read_text(encoding="utf-8")

    def test_single_feature_enabled(self, facade_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            {TemplateFeature.POSTGRESQL},
        )

        content = self._read(facade_path)

        assert "POSTGRES_CONF" in content
        assert "RABBITMQ_CONF" not in content
        assert "BUCKET_CONF" not in content
        assert "EMAIL_CONF" not in content

    def test_multiple_features_enabled(self, facade_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            {TemplateFeature.POSTGRESQL, TemplateFeature.RABBITMQ},
        )

        content = self._read(facade_path)

        assert "POSTGRES_CONF" in content
        assert "RABBITMQ_CONF" in content
        assert "BUCKET_CONF" not in content
        assert "EMAIL_CONF" not in content

    def test_all_features_enabled(self, facade_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            set(TemplateFeature),
        )

        content = self._read(facade_path)

        assert "POSTGRES_CONF" in content
        assert "RABBITMQ_CONF" in content
        assert "BUCKET_CONF" in content
        assert "EMAIL_CONF" in content

    def test_before_all_removed_when_no_features_enabled(self, facade_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            set(),
        )

        content = self._read(facade_path)

        assert "@BeforeAll" not in content
        assert "static void beforeAll" not in content

    def test_no_features_enabled(self, facade_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            set(),
        )

        content = self._read(facade_path)

        assert "POSTGRES_CONF" not in content
        assert "RABBITMQ_CONF" not in content
        assert "BUCKET_CONF" not in content
        assert "EMAIL_CONF" not in content
        assert "class FacadeIT" in content

    def test_idempotency(self, facade_path: Path) -> None:
        handler = FacadeITHandler()
        template_dir = facade_path.parents[5]

        handler.apply_feature_selection(
            template_dir,
            {TemplateFeature.POSTGRESQL},
        )
        first = self._read(facade_path)

        handler.apply_feature_selection(
            template_dir,
            {TemplateFeature.POSTGRESQL},
        )
        second = self._read(facade_path)

        assert first == second

    def test_missing_facade_file_is_noop(self, tmp_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            tmp_path,
            {TemplateFeature.POSTGRESQL},
        )

    def test_unrelated_lines_are_preserved(self, facade_path: Path) -> None:
        extra_line = "// important comment\n"
        facade_path.write_text(extra_line + self._read(facade_path), encoding="utf-8")

        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            {TemplateFeature.POSTGRESQL},
        )

        content = self._read(facade_path)
        assert extra_line.strip() in content

    def test_file_not_emptied(self, facade_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            set(),
        )

        content = self._read(facade_path)
        assert content.strip() != ""

    def test_standard_imports_preserved(self, facade_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            set(),
        )

        content = self._read(facade_path)

        assert "import static java.lang.Runtime.getRuntime;" in content
        assert "import com.example.arinfra.InfraGenerated;" in content
        assert "import lombok.SneakyThrows;" in content
        assert "import lombok.extern.slf4j.Slf4j;" in content
        assert "import org.springframework.test.context.DynamicPropertySource;" in content
