"""Tests for FacadeITHandler."""

from pathlib import Path

import pytest

from src.ar_infra.domain.enums.template_feature import TemplateFeature
from src.ar_infra.infrastructure.template.facadeit_handler import FacadeITHandler


FACADE_CONTENT = """
@Slf4j
@InfraGenerated
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc(addFilters = false)
public abstract class FacadeIT {

  private static final PostgresConf POSTGRES_CONF = new PostgresConf();
  private static final RabbitMQConf RABBITMQ_CONF = new RabbitMQConf();
  private static final BucketConf BUCKET_CONF = new BucketConf();
  private static final EmailConf EMAIL_CONF = new EmailConf();

  @BeforeAll
  static void beforeAll() {
    POSTGRES_CONF.start();
    RABBITMQ_CONF.start();
    BUCKET_CONF.start();
    EMAIL_CONF.start();

    getRuntime()
        .addShutdownHook(
            new Thread(
                () -> {
                  POSTGRES_CONF.stop();
                  RABBITMQ_CONF.stop();
                  BUCKET_CONF.stop();
                  EMAIL_CONF.stop();
                }));
  }

  @SneakyThrows
  @DynamicPropertySource
  static void configureProperties(DynamicPropertyRegistry registry) {
    POSTGRES_CONF.configureProperties(registry);
    RABBITMQ_CONF.configureProperties(registry);
    BUCKET_CONF.configureProperties(registry);
    EMAIL_CONF.configureProperties(registry);

    Class<?> envConfClazz = EnvConf.class;
    var configureMethod =
        envConfClazz.getDeclaredMethod("configureProperties", DynamicPropertyRegistry.class);
    var envConfInstance = envConfClazz.getConstructor().newInstance();
    configureMethod.invoke(envConfInstance, registry);
  }
}
""".lstrip()


class TestFacadeITHandler:
    """Exhaustive test suite for FacadeITHandler."""

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

        assert "PostgresConf" in content
        assert "RabbitMQConf" not in content
        assert "BucketConf" not in content
        assert "EmailConf" not in content

    def test_multiple_features_enabled(self, facade_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            {TemplateFeature.POSTGRESQL, TemplateFeature.RABBITMQ},
        )

        content = self._read(facade_path)

        assert "PostgresConf" in content
        assert "RabbitMQConf" in content
        assert "BucketConf" not in content
        assert "EmailConf" not in content

    def test_all_features_enabled(self, facade_path: Path) -> None:
        FacadeITHandler().apply_feature_selection(
            facade_path.parents[5],
            set(TemplateFeature),
        )

        content = self._read(facade_path)

        assert "PostgresConf" in content
        assert "RabbitMQConf" in content
        assert "BucketConf" in content
        assert "EmailConf" in content

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

        assert "PostgresConf" not in content
        assert "RabbitMQConf" not in content
        assert "BucketConf" not in content
        assert "EmailConf" not in content
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
