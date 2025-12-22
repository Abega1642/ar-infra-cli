"""Tests for ArtifactId value object."""

import pytest

from src.ar_infra.domain.exceptions.validation_error import InvalidArtifactIdError
from src.ar_infra.domain.value_objects.artifact_id import ArtifactId


class TestArtifactId:
    """Test suite for ArtifactId value object."""

    def test_create_valid_artifact_id(self) -> None:
        artifact_id = ArtifactId("backend-api")
        assert artifact_id.value == "backend-api"
        assert str(artifact_id) == "backend-api"

    def test_create_simple_artifact_id(self) -> None:
        artifact_id = ArtifactId("core")
        assert artifact_id.value == "core"

    def test_artifact_id_immutability(self) -> None:
        artifact_id = ArtifactId("backend-api")
        with pytest.raises(AttributeError):
            artifact_id.value = "evil"

    def test_reject_empty_artifact_id(self) -> None:
        with pytest.raises(InvalidArtifactIdError, match="cannot be empty"):
            ArtifactId("")

    def test_reject_whitespace_only(self) -> None:
        with pytest.raises(InvalidArtifactIdError, match="cannot be empty"):
            ArtifactId("   ")

    def test_reject_too_short_artifact_id(self) -> None:
        with pytest.raises(InvalidArtifactIdError, match="too short"):
            ArtifactId("ab")

    def test_reject_too_long_artifact_id(self) -> None:
        long_id = "a" * 51
        with pytest.raises(InvalidArtifactIdError, match="too long"):
            ArtifactId(long_id)

    def test_reject_uppercase_letters(self) -> None:
        with pytest.raises(InvalidArtifactIdError, match="lowercase"):
            ArtifactId("Backend-API")

    def test_reject_starting_with_number(self) -> None:
        with pytest.raises(InvalidArtifactIdError):
            ArtifactId("123api")

    def test_reject_starting_with_hyphen(self) -> None:
        with pytest.raises(InvalidArtifactIdError):
            ArtifactId("-backend")

    def test_reject_ending_with_hyphen(self) -> None:
        with pytest.raises(InvalidArtifactIdError):
            ArtifactId("backend-")

    def test_reject_consecutive_hyphens(self) -> None:
        with pytest.raises(InvalidArtifactIdError):
            ArtifactId("backend--api")

    def test_reject_invalid_characters(self) -> None:
        invalid_ids = [
            "backend_api",
            "backend.api",
            "backend/api",
            "backend api",
            "backend@api",
            "backend!api",
        ]
        for invalid_id in invalid_ids:
            with pytest.raises(InvalidArtifactIdError):
                ArtifactId(invalid_id)

    def test_artifact_id_equality(self) -> None:
        artifact1 = ArtifactId("backend-api")
        artifact2 = ArtifactId("backend-api")
        artifact3 = ArtifactId("frontend")

        assert artifact1 == artifact2
        assert artifact1 != artifact3
        assert artifact1 != "backend-api"

    def test_artifact_id_hash(self) -> None:
        artifact1 = ArtifactId("backend-api")
        artifact2 = ArtifactId("backend-api")

        assert hash(artifact1) == hash(artifact2)
        assert len({artifact1, artifact2}) == 1

    def test_prevent_path_traversal_attack(self) -> None:
        malicious_ids = [
            "../../../etc/passwd",
            "..",
            "../../api",
        ]
        for malicious_id in malicious_ids:
            with pytest.raises(InvalidArtifactIdError):
                ArtifactId(malicious_id)

    def test_prevent_command_injection(self) -> None:
        malicious_ids = [
            "api; rm -rf /",
            "api`whoami`",
            "api$(whoami)",
            "api&& malicious",
            "api|cat",
        ]
        for malicious_id in malicious_ids:
            with pytest.raises(InvalidArtifactIdError):
                ArtifactId(malicious_id)

    def test_reject_reserved_keywords(self) -> None:
        reserved = [
            "class",
            "public",
            "private",
            "static",
        ]
        for reserved_id in reserved:
            with pytest.raises(InvalidArtifactIdError, match="reserved keyword"):
                ArtifactId(reserved_id)

    def test_valid_artifact_ids_with_numbers(self) -> None:
        valid_ids = [
            "api1",
            "backend2api",
            "service123",
        ]
        for valid_id in valid_ids:
            artifact_id = ArtifactId(valid_id)
            assert artifact_id.value == valid_id

    def test_valid_artifact_ids_with_hyphens(self) -> None:
        valid_ids = [
            "backend-api",
            "user-service",
            "payment-gateway",
        ]
        for valid_id in valid_ids:
            artifact_id = ArtifactId(valid_id)
            assert artifact_id.value == valid_id
