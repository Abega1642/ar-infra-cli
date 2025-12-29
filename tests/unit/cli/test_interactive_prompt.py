"""Tests for InteractivePrompt class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from src.ar_infra.cli.prompt.interactive_prompt import InteractivePrompt


class TestInteractivePrompt:
    """Test suite for InteractivePrompt class."""

    @pytest.fixture
    def prompt(self) -> InteractivePrompt:
        return InteractivePrompt()

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_success(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        test_path = tmp_path / "test"
        mock_text.return_value.ask.side_effect = [
            "com.example",
            "my-app",
            "1.0.0",
            str(test_path),
        ]
        mock_checkbox.return_value.ask.return_value = ["postgresql", "email"]
        mock_confirm.return_value.ask.return_value = True

        result = prompt.collect_inputs()

        assert result["group_id"] == "com.example"
        assert result["artifact_id"] == "my-app"
        assert result["version"] == "1.0.0"
        assert isinstance(result["destination"], Path)
        assert result["enabled_features"] == {"postgresql", "email"}
        assert result["use_template_cache"] is True

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_no_features(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
        tmp_path: Path,
    ) -> None:
        test_path = tmp_path / "backend-test"
        mock_text.return_value.ask.side_effect = [
            "dev.razafindratelo",
            "backend-api",
            "2.0.0",
            str(test_path),
        ]
        mock_checkbox.return_value.ask.return_value = []
        mock_confirm.return_value.ask.return_value = False

        result = prompt.collect_inputs()

        assert result["group_id"] == "dev.razafindratelo"
        assert result["artifact_id"] == "backend-api"
        assert result["version"] == "2.0.0"
        assert result["enabled_features"] == set()
        assert result["use_template_cache"] is False

    @patch("src.ar_infra.cli.prompt.interactive_prompt.text")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.checkbox")
    @patch("src.ar_infra.cli.prompt.interactive_prompt.confirm")
    def test_collect_inputs_all_features(
        self,
        mock_confirm: Mock,
        mock_checkbox: Mock,
        mock_text: Mock,
        prompt: InteractivePrompt,
    ) -> None:
        mock_text.return_value.ask.side_effect = [
            "com.company",
            "full-app",
            "1.0.0",
            "./",
        ]
        mock_checkbox.return_value.ask.return_value = [
            "postgresql",
            "rabbitmq",
            "s3_bucket",
            "email",
        ]
        mock_confirm.return_value.ask.return_value = True

        result = prompt.collect_inputs()

        assert len(result["enabled_features"]) == 4
        assert "postgresql" in result["enabled_features"]
        assert "rabbitmq" in result["enabled_features"]
        assert "s3_bucket" in result["enabled_features"]
        assert "email" in result["enabled_features"]

    def test_prompt_has_validators(self, prompt: InteractivePrompt) -> None:
        assert prompt.validators is not None
        assert hasattr(prompt.validators, "group_id")
        assert hasattr(prompt.validators, "artifact_id")
        assert hasattr(prompt.validators, "version")
        assert hasattr(prompt.validators, "path")
