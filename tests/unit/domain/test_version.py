"""Tests for Version value object."""

import pytest

from src.ar_infra.domain.exceptions.validation_error import InvalidVersionError
from src.ar_infra.domain.value_objects.version import Version


class TestVersion:
    def test_create_semantic_version(self) -> None:
        version = Version("1.0.0")
        assert version.value == "1.0.0"

    def test_create_snapshot_version(self) -> None:
        version = Version("1.0.0-SNAPSHOT")
        assert version.value == "1.0.0-SNAPSHOT"
        assert version.is_snapshot is True

    def test_create_version_with_qualifier(self) -> None:
        version = Version("2.1.3-beta")
        assert version.value == "2.1.3-beta"

    def test_version_properties(self) -> None:
        version = Version("1.2.3")
        assert version.major == 1
        assert version.minor == 2
        assert version.patch == 3
        assert version.qualifier is None

    def test_version_with_qualifier_properties(self) -> None:
        version = Version("2.0.0-RC1")
        assert version.major == 2
        assert version.minor == 0
        assert version.patch == 0
        assert version.qualifier == "RC1"

    def test_is_snapshot(self) -> None:
        assert Version("1.0.0-SNAPSHOT").is_snapshot is True
        assert Version("1.0.0").is_snapshot is False

    def test_immutability(self) -> None:
        version = Version("1.0.0")
        with pytest.raises(AttributeError):
            version.value = "2.0.0"  # type: ignore[misc]

    def test_reject_empty_version(self) -> None:
        with pytest.raises(InvalidVersionError):
            Version("")

    def test_reject_invalid_format(self) -> None:
        for invalid in ["1", "1.0", "a.b.c", "1.0.x"]:
            with pytest.raises(InvalidVersionError):
                Version(invalid)

    def test_reject_negative_numbers(self) -> None:
        with pytest.raises(InvalidVersionError):
            Version("-1.0.0")

    def test_version_comparison(self) -> None:
        assert Version("1.0.0") == Version("1.0.0")
        assert Version("1.0.0") < Version("2.0.0")

    def test_version_comparison_with_qualifiers(self) -> None:
        assert Version("1.0.0-SNAPSHOT") < Version("1.0.0-alpha")
        assert Version("1.0.0-alpha") < Version("1.0.0-beta")
        assert Version("1.0.0-beta") < Version("1.0.0-RC1")
        assert Version("1.0.0-RC1") < Version("1.0.0")

    def test_numeric_qualifier_ordering(self) -> None:
        assert Version("1.0.0-RC1") < Version("1.0.0-RC2")
        assert Version("1.0.0-M1") < Version("1.0.0-M2")

    def test_hash(self) -> None:
        assert len({Version("1.0.0"), Version("1.0.0")}) == 1

    def test_prevent_command_injection(self) -> None:
        for malicious in [
            "1.0.0; rm -rf",
            "1.0.`whoami`",
            "1.0.0$(cat /etc/passwd)",
        ]:
            with pytest.raises(InvalidVersionError):
                Version(malicious)

    def test_various_valid_qualifiers(self) -> None:
        for valid in [
            "1.0.0-alpha",
            "1.0.0-beta.1",
            "2.1.0-rc.2",
            "3.0.0-M1",
        ]:
            assert Version(valid).value == valid
