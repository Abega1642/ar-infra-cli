"""Tests for PackageRenamer."""

from pathlib import Path

import pytest

from src.ar_infra.domain.value_objects.package_name import PackageName
from src.ar_infra.infrastructure.processor.exception import (
    PackageRenameError,
    SecurityViolationError,
)
from src.ar_infra.infrastructure.processor.package_renamer import PackageRenamer


class TestPackageRenamer:
    @pytest.fixture
    def renamer(self) -> PackageRenamer:
        return PackageRenamer()

    @pytest.fixture
    def sample_java_project(self, tmp_path: Path) -> Path:
        src_main_java = tmp_path / "src" / "main" / "java"
        old_package_dir = src_main_java / "com" / "example" / "demo"
        old_package_dir.mkdir(parents=True)

        (old_package_dir / "Application.java").write_text(
            """package com.example.demo;

import com.example.demo.service.UserService;
import static com.example.demo.service.UserService.getAll;
import org.springframework.boot.SpringApplication;

public class Application {
    public static void main(String[] args) {
        SpringApplication.run(Application.class, args);
    }
}
"""
        )

        service_dir = old_package_dir / "service"
        service_dir.mkdir()
        (service_dir / "UserService.java").write_text(
            """package com.example.demo.service;

import com.example.demo.model.User;

public class UserService {
    private User user;
}
"""
        )

        model_dir = old_package_dir / "model"
        model_dir.mkdir()
        (model_dir / "User.java").write_text(
            """package com.example.demo.model;

public class User {
    private String name;
}
"""
        )

        return tmp_path

    def test_rename_package_structure(
        self, renamer: PackageRenamer, sample_java_project: Path
    ) -> None:
        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")

        renamer.rename_package(sample_java_project, old_package, new_package)

        new_dir = sample_java_project / "src" / "main" / "java" / "dev" / "razafindratelo" / "core"
        assert new_dir.exists()
        assert (new_dir / "Application.java").exists()
        assert (new_dir / "service" / "UserService.java").exists()
        assert (new_dir / "model" / "User.java").exists()

        old_dir = sample_java_project / "src" / "main" / "java" / "com"
        assert not old_dir.exists()

    def test_update_package_declarations(
        self, renamer: PackageRenamer, sample_java_project: Path
    ) -> None:
        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")

        renamer.rename_package(sample_java_project, old_package, new_package)

        application_file = (
            sample_java_project
            / "src"
            / "main"
            / "java"
            / "dev"
            / "razafindratelo"
            / "core"
            / "Application.java"
        )
        content = application_file.read_text()
        assert "package dev.razafindratelo.core;" in content
        assert "package com.example.demo;" not in content

    def test_update_import_statements(
        self, renamer: PackageRenamer, sample_java_project: Path
    ) -> None:
        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")

        renamer.rename_package(sample_java_project, old_package, new_package)

        application_file = (
            sample_java_project
            / "src"
            / "main"
            / "java"
            / "dev"
            / "razafindratelo"
            / "core"
            / "Application.java"
        )
        content = application_file.read_text()
        assert "import dev.razafindratelo.core.service.UserService;" in content
        assert "import com.example.demo.service.UserService;" not in content

    def test_update_nested_package_imports(
        self, renamer: PackageRenamer, sample_java_project: Path
    ) -> None:
        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")

        renamer.rename_package(sample_java_project, old_package, new_package)

        service_file = (
            sample_java_project
            / "src"
            / "main"
            / "java"
            / "dev"
            / "razafindratelo"
            / "core"
            / "service"
            / "UserService.java"
        )
        content = service_file.read_text()
        assert "package dev.razafindratelo.core.service;" in content
        assert "import dev.razafindratelo.core.model.User;" in content

    def test_preserve_external_imports(
        self, renamer: PackageRenamer, sample_java_project: Path
    ) -> None:
        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")

        renamer.rename_package(sample_java_project, old_package, new_package)

        application_file = (
            sample_java_project
            / "src"
            / "main"
            / "java"
            / "dev"
            / "razafindratelo"
            / "core"
            / "Application.java"
        )
        content = application_file.read_text()
        assert "import org.springframework.boot.SpringApplication;" in content

    def test_handle_nonexistent_package(self, renamer: PackageRenamer, tmp_path: Path) -> None:
        old_package = PackageName("com.nonexistent.missing")
        new_package = PackageName("dev.razafindratelo.core")

        (tmp_path / "src" / "main" / "java").mkdir(parents=True)

        with pytest.raises(PackageRenameError, match="Source package directory does not exist"):
            renamer.rename_package(tmp_path, old_package, new_package)

    def test_prevent_path_traversal(self, renamer: PackageRenamer, tmp_path: Path) -> None:
        (tmp_path / "src" / "main" / "java").mkdir(parents=True)

        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")
        malicious_path = tmp_path / ".." / ".." / "etc"

        with pytest.raises(SecurityViolationError):
            renamer.rename_package(malicious_path, old_package, new_package)

    def test_detect_symlink_attack(self, renamer: PackageRenamer, tmp_path: Path) -> None:
        src_dir = tmp_path / "src" / "main" / "java"
        package_dir = src_dir / "com" / "example" / "demo"
        package_dir.mkdir(parents=True)

        evil_dir = tmp_path / "evil"
        evil_dir.mkdir()

        symlink = package_dir / "symlink"
        symlink.symlink_to(evil_dir)

        (package_dir / "Application.java").write_text("package com.example.demo;\n")

        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")

        with pytest.raises(SecurityViolationError, match="Symlink detected"):
            renamer.rename_package(tmp_path, old_package, new_package)

    def test_preserve_file_permissions(
        self, renamer: PackageRenamer, sample_java_project: Path
    ) -> None:
        old_file = (
            sample_java_project
            / "src"
            / "main"
            / "java"
            / "com"
            / "example"
            / "demo"
            / "Application.java"
        )
        old_file.chmod(0o755)
        original_mode = old_file.stat().st_mode

        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")

        renamer.rename_package(sample_java_project, old_package, new_package)

        new_file = (
            sample_java_project
            / "src"
            / "main"
            / "java"
            / "dev"
            / "razafindratelo"
            / "core"
            / "Application.java"
        )
        new_mode = new_file.stat().st_mode
        assert new_mode == original_mode

    def test_handle_empty_subdirectories(self, renamer: PackageRenamer, tmp_path: Path) -> None:
        src_main_java = tmp_path / "src" / "main" / "java"
        package_dir = src_main_java / "com" / "example" / "demo"
        package_dir.mkdir(parents=True)

        (package_dir / "empty_dir").mkdir()
        (package_dir / "Application.java").write_text("package com.example.demo;\n")

        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")

        renamer.rename_package(tmp_path, old_package, new_package)

        new_dir = tmp_path / "src" / "main" / "java" / "dev" / "razafindratelo" / "core"
        assert new_dir.exists()
        assert (new_dir / "Application.java").exists()

    def test_rename_updates_test_sources(self, renamer: PackageRenamer, tmp_path: Path) -> None:
        src_test_java = tmp_path / "src" / "test" / "java"
        test_package = src_test_java / "com" / "example" / "demo"
        test_package.mkdir(parents=True)

        (test_package / "ApplicationTest.java").write_text(
            """package com.example.demo;

import com.example.demo.service.UserService;

public class ApplicationTest {
}
"""
        )

        src_main_java = tmp_path / "src" / "main" / "java"
        main_package = src_main_java / "com" / "example" / "demo"
        main_package.mkdir(parents=True)
        (main_package / "Application.java").write_text("package com.example.demo;\n")

        old_package = PackageName("com.example.demo")
        new_package = PackageName("dev.razafindratelo.core")

        renamer.rename_package(tmp_path, old_package, new_package)

        test_file = (
            tmp_path
            / "src"
            / "test"
            / "java"
            / "dev"
            / "razafindratelo"
            / "core"
            / "ApplicationTest.java"
        )
        content = test_file.read_text()
        assert "package dev.razafindratelo.core;" in content
        assert "import dev.razafindratelo.core.service.UserService;" in content
