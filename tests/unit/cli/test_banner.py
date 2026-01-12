"""Tests for Banner class."""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from src.ar_infra.cli.ui.banner import Banner


class TestBanner:
    def test_show_banner(self, capsys):
        Banner.show(wait_for_enter=False)
        captured = capsys.readouterr()
        assert len(captured.out) > 0, "Banner should produce output"

    def test_banner_contains_text(self, capsys):
        Banner.show(wait_for_enter=False)
        captured = capsys.readouterr()
        text_only = re.sub(r"\x1b\[[0-9;]*m", "", captured.out)
        assert "AR" in text_only or "INFRA" in text_only, "Banner should contain AR-INFRA text"

    def test_banner_waits_for_enter(self, capsys):
        with patch("builtins.input", return_value=""):
            Banner.show(wait_for_enter=True)
            captured = capsys.readouterr()
            assert "Press Enter to continue" in captured.out

    def test_banner_handles_keyboard_interrupt(self, capsys):
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with pytest.raises(KeyboardInterrupt, match="Banner display cancelled by user"):
                Banner.show(wait_for_enter=True)
            captured = capsys.readouterr()
            assert "Operation cancelled" in captured.out

    def test_banner_handles_eof_error(self, capsys):
        with patch("builtins.input", side_effect=EOFError):
            with pytest.raises(KeyboardInterrupt, match="Banner display cancelled by user"):
                Banner.show(wait_for_enter=True)
            captured = capsys.readouterr()
            assert "Operation cancelled" in captured.out

    def test_banner_has_ansi_codes(self):
        banner_path = Path("src/ar_infra/cli/resources/banner.txt")

        if banner_path.exists():
            banner = banner_path.read_text(encoding="utf-8")

            assert "\x1b[" in banner, "Banner should contain ANSI escape codes"

            has_color_codes = bool(re.search(r"38;5;\d+", banner))
            if not has_color_codes:
                pytest.skip("Banner generated without 256-color codes (CI environment)")

    def test_banner_ocean_palette_colors(self):
        banner_path = Path("src/ar_infra/cli/resources/banner.txt")

        if banner_path.exists():
            banner = banner_path.read_text(encoding="utf-8")

            if not re.search(r"38;5;\d+", banner):
                pytest.skip("Banner generated without 256-color codes (CI environment)")

            expected_colors = ["105", "104", "103", "97"]
            found_colors = [color for color in expected_colors if f"38;5;{color}" in banner]

            assert (
                len(found_colors) > 0
            ), f"Expected ocean palette colors not found. Found: {found_colors}"

    def test_banner_file_exists(self):
        banner_path = Path("src/ar_infra/cli/resources/banner.txt")
        assert banner_path.exists(), "Banner file should exist"

    def test_banner_file_not_empty(self):
        banner_path = Path("src/ar_infra/cli/resources/banner.txt")
        assert banner_path.stat().st_size > 0, "Banner file should not be empty"

    def test_banner_file_contains_block_characters(self):
        banner_path = Path("src/ar_infra/cli/resources/banner.txt")
        banner = banner_path.read_text(encoding="utf-8")
        assert any(
            char in banner for char in ["█", "▀", "▄", "▌", "▐", "░", "▒", "▓", "╔", "╗", "╚", "╝"]
        ), "Banner should contain block or box drawing characters"

    def test_banner_reasonable_size(self):
        banner_path = Path("src/ar_infra/cli/resources/banner.txt")
        size = banner_path.stat().st_size
        assert 100 < size < 5000, f"Banner file size should be reasonable (got {size} bytes)"

    def test_load_banner_returns_string(self):
        banner = Banner._load_banner()
        assert isinstance(banner, str), "Banner should be a string"
        assert len(banner) > 0, "Banner should not be empty"
