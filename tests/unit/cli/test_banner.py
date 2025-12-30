"""Unit tests for banner module."""

import re
from pathlib import Path
from unittest.mock import patch

from src.ar_infra.cli.ui.banner import Banner


class TestBanner:
    """Test suite for Banner class."""

    def test_load_banner_file_exists(self):
        """Test loading banner when file exists."""
        banner = Banner._load_banner()

        assert banner is not None
        assert isinstance(banner, str)
        assert len(banner) > 0

    def test_banner_has_content(self):
        """Test that banner has substantial content."""
        banner = Banner._load_banner()

        assert len(banner) > 100, f"Banner too short: {len(banner)} characters"

    def test_banner_has_ansi_codes(self):
        """Test that banner contains ANSI color codes."""
        banner_path = Path("src/ar_infra/cli/resources/banner.txt")

        if banner_path.exists():
            banner = banner_path.read_text(encoding="utf-8")

            assert "\x1b[" in banner, "Banner should contain ANSI escape codes"

            assert re.search(r"38;5;\d+", banner), "Banner should contain 256-color codes"

    def test_banner_ocean_palette_colors(self):
        """Test that banner uses expected ocean palette colors."""
        banner_path = Path("src/ar_infra/cli/resources/banner.txt")

        if banner_path.exists():
            banner = banner_path.read_text(encoding="utf-8")

            expected_colors = ["105", "104", "103", "97"]

            found_colors = [color for color in expected_colors if f"38;5;{color}" in banner]
            assert (
                len(found_colors) > 0
            ), f"Expected ocean palette colors not found. Found: {found_colors}"

    def test_banner_contains_ascii_art(self):
        """Test that banner contains ASCII art characters."""
        banner = Banner._load_banner()

        box_chars = ["█", "╗", "╔", "═", "║", "╚", "╝"]
        has_box_chars = any(char in banner for char in box_chars)

        assert has_box_chars, "Banner should contain ASCII art box-drawing characters"

    def test_banner_fallback_when_file_missing(self, monkeypatch):
        """Fallback to default banner when banner file does not exist."""

        def fake_exists(self):
            return False

        monkeypatch.setattr(
            "pathlib.Path.exists",
            fake_exists,
        )

        banner = Banner._load_banner()

        assert "AR-INFRA CLI" in banner

    def test_banner_show_method_runs(self, capsys):
        """Test that Banner.show() runs without errors."""
        with patch("builtins.input", return_value=""):
            Banner.show()

    def test_banner_file_structure(self):
        """Banner should have a multi-line ASCII-art structure."""

        banner_path = Path("src/ar_infra/cli/resources/banner.txt")

        if banner_path.exists():
            banner = banner_path.read_text(encoding="utf-8")

            lines = [line for line in banner.splitlines() if line.strip()]

            assert len(lines) >= 6, "Banner should have at least 6 non-empty lines"

            assert any(
                len(line) > 20 for line in lines
            ), "Banner should contain visually significant lines"

    def test_banner_no_corruption(self):
        """Test that banner doesn't have obvious corruption."""
        banner = Banner._load_banner()

        assert "\x00" not in banner, "Banner should not contain null bytes"

        ansi_removed = re.sub(r"\x1b\[[0-9;]*m", "", banner)

        printable_or_box = sum(1 for c in ansi_removed if c.isprintable() or c in ["\n", "\r"])

        ratio = printable_or_box / len(ansi_removed) if ansi_removed else 0
        assert ratio > 0.9, f"Banner should be mostly printable, got {ratio:.2%}"
