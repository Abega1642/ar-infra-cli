"""Tests for GroupId value object."""

import pytest

from src.ar_infra.domain.exceptions.validation_error import InvalidGroupIdError
from src.ar_infra.domain.value_objects.group_id import GroupId


class TestGroupId:
    """Test suite for GroupId value object."""

    def test_create_valid_group_id(self) -> None:
        """Test creating a valid group ID."""
        group_id = GroupId("dev.razafindratelo")
        assert group_id.value == "dev.razafindratelo"
        assert str(group_id) == "dev.razafindratelo"

    def test_create_group_id_with_multiple_segments(self) -> None:
        """Test creating group ID with multiple segments."""
        group_id = GroupId("com.example.myapp.api")
        assert group_id.value == "com.example.myapp.api"
        assert group_id.segments == ["com", "example", "myapp", "api"]

    def test_group_id_immutability(self) -> None:
        """Test that GroupId is immutable."""
        group_id = GroupId("dev.razafindratelo")
        with pytest.raises(AttributeError):
            group_id.value = "com.evil"

    def test_reject_empty_group_id(self) -> None:
        """Test that empty group ID is rejected."""
        with pytest.raises(InvalidGroupIdError, match="cannot be empty"):
            GroupId("")

    def test_reject_group_id_with_invalid_characters(self) -> None:
        """Test that group ID with invalid characters is rejected."""
        invalid_group_ids = [
            "dev.razafindratelo!",
            "com/example",
            "dev razafindratelo",
            "com.example.",  # trailing dot
            ".com.example",  # leading dot
            "com..example",  # double dot
            "com.example-",  # trailing hyphen in segment
            "com.-example",  # leading hyphen in segment
        ]
        for invalid_id in invalid_group_ids:
            with pytest.raises(InvalidGroupIdError):
                GroupId(invalid_id)

    def test_reject_group_id_with_uppercase(self) -> None:
        """Test that group ID with uppercase letters is rejected."""
        with pytest.raises(InvalidGroupIdError, match="lowercase"):
            GroupId("com.Example")

    def test_reject_group_id_starting_with_number(self) -> None:
        """Test that group ID starting with number is rejected."""
        with pytest.raises(InvalidGroupIdError):
            GroupId("123.example.com")

    def test_reject_single_segment_group_id(self) -> None:
        """Test that single segment group ID is rejected."""
        with pytest.raises(InvalidGroupIdError, match="at least two segments"):
            GroupId("example")

    def test_group_id_equality(self) -> None:
        """Test GroupId equality."""
        group_id1 = GroupId("dev.razafindratelo")
        group_id2 = GroupId("dev.razafindratelo")
        group_id3 = GroupId("com.example")

        assert group_id1 == group_id2
        assert group_id1 != group_id3
        assert group_id1 != "dev.razafindratelo"  # Different type

    def test_group_id_hash(self) -> None:
        """Test that GroupId is hashable."""
        group_id1 = GroupId("dev.razafindratelo")
        group_id2 = GroupId("dev.razafindratelo")

        assert hash(group_id1) == hash(group_id2)
        assert len({group_id1, group_id2}) == 1  # Same in set

    def test_to_path(self) -> None:
        """Test converting GroupId to file path."""
        group_id = GroupId("dev.razafindratelo.myapp")
        assert group_id.to_path() == "dev/razafindratelo/myapp"

    def test_prevent_path_traversal_attack(self) -> None:
        """Test that path traversal attacks are prevented."""
        malicious_ids = [
            "../../../etc/passwd",
            "com.example../../../etc",
            "com/example",
        ]
        for malicious_id in malicious_ids:
            with pytest.raises(InvalidGroupIdError):
                GroupId(malicious_id)

    def test_prevent_command_injection(self) -> None:
        """Test that command injection attempts are prevented."""
        malicious_ids = [
            "com.example; rm -rf /",
            "com.example`whoami`",
            "com.example$(whoami)",
            "com.example&& malicious",
        ]
        for malicious_id in malicious_ids:
            with pytest.raises(InvalidGroupIdError):
                GroupId(malicious_id)

    def test_reject_reserved_keywords(self) -> None:
        """Test that Java reserved keywords are rejected."""
        reserved = [
            "java.class",
            "com.public.test",
            "dev.private.api",
            "com.static.util",
        ]
        for reserved_id in reserved:
            with pytest.raises(InvalidGroupIdError, match="reserved keyword"):
                GroupId(reserved_id)

    def test_group_id_length_limit(self) -> None:
        """Test that extremely long group IDs are rejected."""
        long_segment = "a" * 100
        long_id = ".".join([long_segment] * 10)  # 1000+ characters
        with pytest.raises(InvalidGroupIdError, match="too long"):
            GroupId(long_id)
