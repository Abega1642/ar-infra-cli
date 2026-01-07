"""Tests for PackageName value object."""

import pytest

from src.ar_infra.domain.exceptions.validation_error import InvalidPackageNameError
from src.ar_infra.domain.value_objects.artifact_id import ArtifactId
from src.ar_infra.domain.value_objects.group_id import GroupId
from src.ar_infra.domain.value_objects.package_name import PackageName


class TestPackageName:
    def test_create_from_group_and_artifact(self) -> None:
        group = GroupId("dev.razafindratelo")
        artifact = ArtifactId("backend-api")
        package = PackageName.from_parts(group, artifact)

        assert package.value == "dev.razafindratelo.backend_api"

    def test_create_from_string(self) -> None:
        package = PackageName("com.example.userservice")
        assert package.value == "com.example.userservice"

    def test_artifact_name_hyphen_replacement(self) -> None:
        group = GroupId("com.example")
        artifact = ArtifactId("user-service")
        package = PackageName.from_parts(group, artifact)

        assert package.value == "com.example.user_service"

    def test_to_path(self) -> None:
        package = PackageName("dev.razafindratelo.backend_api")
        assert package.to_path() == "dev/razafindratelo/backend_api"

    def test_segments(self) -> None:
        package = PackageName("com.example.core")
        assert package.segments == ["com", "example", "core"]

    def test_base_package(self) -> None:
        package = PackageName("dev.razafindratelo.backend_api")
        assert package.base_package == "dev.razafindratelo"

    def test_artifact_segment(self) -> None:
        package = PackageName("com.example.user_service")
        assert package.artifact_segment == "user_service"

    def test_immutability(self) -> None:
        package = PackageName("com.example.core")
        with pytest.raises(AttributeError):
            package.value = "evil"  # type: ignore[misc]

    def test_reject_empty_package_name(self) -> None:
        with pytest.raises(InvalidPackageNameError, match="cannot be empty"):
            PackageName("")

    def test_reject_single_segment(self) -> None:
        with pytest.raises(InvalidPackageNameError, match="at least three segments"):
            PackageName("example")

    def test_reject_two_segments(self) -> None:
        with pytest.raises(InvalidPackageNameError, match="at least three segments"):
            PackageName("com.example")

    def test_reject_uppercase(self) -> None:
        with pytest.raises(InvalidPackageNameError):
            PackageName("com.Example.Core")

    def test_reject_invalid_characters(self) -> None:
        invalid_names = [
            "com.example.user-service",
            "com.example.user service",
        ]
        for invalid_name in invalid_names:
            with pytest.raises(InvalidPackageNameError):
                PackageName(invalid_name)

    def test_equality(self) -> None:
        package1 = PackageName("com.example.core")
        package2 = PackageName("com.example.core")
        package3 = PackageName("com.example.api")

        assert package1 == package2
        assert package1 != package3

    def test_hash(self) -> None:
        package1 = PackageName("com.example.core")
        package2 = PackageName("com.example.core")

        assert hash(package1) == hash(package2)
        assert len({package1, package2}) == 1

    def test_prevent_path_traversal(self) -> None:
        with pytest.raises(InvalidPackageNameError):
            PackageName("com.example../../../etc")

    def test_prevent_command_injection(self) -> None:
        malicious_names = [
            "com.example; rm -rf",
            "com.exampl`whoami`",
        ]
        for malicious_name in malicious_names:
            with pytest.raises(InvalidPackageNameError):
                PackageName(malicious_name)

    def test_reject_reserved_keywords_in_segments(self) -> None:
        with pytest.raises(InvalidPackageNameError):
            PackageName("com.class.static")
